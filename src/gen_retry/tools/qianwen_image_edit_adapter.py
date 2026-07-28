from __future__ import annotations

import gc
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_file
from gen_retry.tools.model_load_lock import exclusive_model_load


@dataclass(frozen=True)
class QianwenImageResult:
    request_id: str
    attempt_id: str
    parent_attempt_id: str | None
    operation: str
    backend: str
    image_artifact_id: str
    artifact_uri: str
    artifact_manifest_ref: str
    artifact_sha256: str
    manifest_entry: dict[str, Any]
    metadata: dict[str, Any]


class QianwenImageEditAdapter:
    backend = "qianwen_image_edit"

    def __init__(
        self,
        *,
        provider: str,
        model_path: Path,
        artifact_root: Path,
        height: int = 1024,
        width: int = 1024,
        num_inference_steps: int = 40,
        true_cfg_scale: float = 4.0,
        guidance_scale: float = 1.0,
        seed: int = 0,
        cpu_offload: bool = False,
    ):
        if provider != "local":
            raise ValueError(f"unsupported Qianwen provider for Phase 3: {provider}")
        self.provider = provider
        self.model_path = model_path
        self.artifact_root = artifact_root
        self.height = height
        self.width = width
        self.num_inference_steps = num_inference_steps
        self.true_cfg_scale = true_cfg_scale
        self.guidance_scale = guidance_scale
        self.seed = seed
        self.cpu_offload = cpu_offload

    @property
    def uses_http_endpoint(self) -> bool:
        return False

    def generate(
        self,
        *,
        request_id: str,
        attempt_id: str,
        image_artifact_id: str,
        instruction: str,
    ) -> QianwenImageResult:
        return self._run(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=None,
            operation="generate",
            instruction=instruction,
            image_artifact_id=image_artifact_id,
            source_image_path=None,
        )

    def edit(
        self,
        *,
        request_id: str,
        attempt_id: str,
        source_attempt_id: str,
        source_image_path: Path,
        image_artifact_id: str,
        instruction: str,
    ) -> QianwenImageResult:
        return self._run(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=source_attempt_id,
            operation="edit",
            instruction=instruction,
            image_artifact_id=image_artifact_id,
            source_image_path=source_image_path,
        )

    def _run(
        self,
        *,
        request_id: str,
        attempt_id: str,
        parent_attempt_id: str | None,
        operation: str,
        instruction: str,
        image_artifact_id: str,
        source_image_path: Path | None,
    ) -> QianwenImageResult:
        if not self.model_path.exists():
            raise FileNotFoundError(f"missing Qwen-Image-Edit model path: {self.model_path}")
        artifact_uri = f"images/{image_artifact_id}.png"
        output_path = self.artifact_root / artifact_uri
        if output_path.exists():
            artifact_sha256 = sha256_file(output_path)
            return self._result(
                request_id=request_id,
                attempt_id=attempt_id,
                parent_attempt_id=parent_attempt_id,
                operation=operation,
                image_artifact_id=image_artifact_id,
                artifact_uri=artifact_uri,
                artifact_sha256=artifact_sha256,
                metadata={"cache_hit": True, "provider": self.provider},
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with exclusive_model_load():
            pipeline = self._load_pipeline()
        source_image = (
            Image.open(source_image_path).convert("RGB")
            if source_image_path is not None
            else Image.new("RGB", (self.width, self.height), color="white")
        )
        try:
            import torch

            generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu")
            generator = generator.manual_seed(self.seed)
            pipeline.set_progress_bar_config(disable=True)
            with torch.inference_mode():
                output = pipeline(
                    image=source_image,
                    prompt=instruction,
                    generator=generator,
                    true_cfg_scale=self.true_cfg_scale,
                    negative_prompt=" ",
                    num_inference_steps=self.num_inference_steps,
                    guidance_scale=self.guidance_scale,
                    num_images_per_prompt=1,
                    height=self.height,
                    width=self.width,
                    output_type="pt",
                )
            _save_output_image(output.images[0], output_path)
        finally:
            del pipeline
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

        artifact_sha256 = sha256_file(output_path)
        return self._result(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=parent_attempt_id,
            operation=operation,
            image_artifact_id=image_artifact_id,
            artifact_uri=artifact_uri,
            artifact_sha256=artifact_sha256,
            metadata={
                "cache_hit": False,
                "provider": self.provider,
                "model_path_exists": True,
                "local_runtime": "diffusers.QwenImageEditPlusPipeline",
                "internal_generation_canvas": source_image_path is None,
                "height": self.height,
                "width": self.width,
                "num_inference_steps": self.num_inference_steps,
                "true_cfg_scale": self.true_cfg_scale,
                "guidance_scale": self.guidance_scale,
                "seed": self.seed,
                "cpu_offload": self.cpu_offload,
            },
        )

    def _load_pipeline(self) -> Any:
        import torch
        from diffusers import QwenImageEditPlusPipeline

        from gen_retry.tools.torch_compat import patch_torch_from_numpy_if_needed

        patch_torch_from_numpy_if_needed()
        pipeline = QwenImageEditPlusPipeline.from_pretrained(
            str(self.model_path),
            torch_dtype=torch.bfloat16,
            local_files_only=True,
        )
        if self.cpu_offload and torch.cuda.is_available():
            pipeline.enable_model_cpu_offload()
        elif torch.cuda.is_available():
            pipeline.to("cuda")
        return pipeline

    def _result(
        self,
        *,
        request_id: str,
        attempt_id: str,
        parent_attempt_id: str | None,
        operation: str,
        image_artifact_id: str,
        artifact_uri: str,
        artifact_sha256: str,
        metadata: dict[str, Any],
    ) -> QianwenImageResult:
        manifest_entry = artifact_manifest_entry(
            artifact_id=image_artifact_id,
            attempt_id=attempt_id,
            artifact_type="image",
            uri=artifact_uri,
            sha256=artifact_sha256,
            media_type="image/png",
            producer="qianwen_image_edit_adapter",
            metadata={
                "backend": self.backend,
                "operation": operation,
                "request_id": request_id,
                **metadata,
            },
        )
        return QianwenImageResult(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=parent_attempt_id,
            operation=operation,
            backend=self.backend,
            image_artifact_id=image_artifact_id,
            artifact_uri=artifact_uri,
            artifact_manifest_ref="manifest.json",
            artifact_sha256=artifact_sha256,
            manifest_entry=manifest_entry,
            metadata=metadata,
        )


def _save_output_image(image: Any, output_path: Path) -> None:
    if isinstance(image, Image.Image):
        image.save(output_path)
        return
    try:
        import torch

        if isinstance(image, torch.Tensor):
            tensor = image.detach().float().clamp(0, 1).cpu()
            if tensor.ndim == 4:
                tensor = tensor[0]
            if tensor.shape[0] == 1:
                tensor = tensor.repeat(3, 1, 1)
            if tensor.shape[0] == 4:
                tensor = tensor[:3]
            if tensor.shape[0] != 3:
                raise ValueError(f"unexpected image tensor shape: {tuple(tensor.shape)}")
            tensor = (tensor * 255).round().to(torch.uint8)
            tensor = tensor.permute(1, 2, 0).contiguous()
            height, width = tensor.shape[:2]
            pil_image = Image.frombytes("RGB", (width, height), tensor.numpy().tobytes())
            pil_image.save(output_path)
            return
    except ImportError:
        pass
    raise TypeError(f"unsupported Qwen image output type: {type(image)}")
