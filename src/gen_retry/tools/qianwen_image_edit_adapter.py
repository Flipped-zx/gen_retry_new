from __future__ import annotations

import gc
from pathlib import Path
from typing import Any

from PIL import Image

from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_file
from gen_retry.tools.model_load_lock import exclusive_model_load
from gen_retry.tools.qwen_common import (
    QwenImageResult,
    model_revision_or_fingerprint,
    save_output_image,
)


class QianwenImageEditAdapter:
    backend = "qianwen_image_edit"
    pipeline_id = "QwenImageEditPlusPipeline"
    adapter_version = "2"

    def __init__(
        self,
        *,
        provider: str,
        model_id: str = "Qwen-Image-Edit-2511",
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
        self.model_id = model_id
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
    ) -> QwenImageResult:
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
    ) -> QwenImageResult:
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
    ) -> QwenImageResult:
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
                metadata=self.execution_metadata(
                    cache_hit=True,
                    internal_generation_canvas=source_image_path is None,
                ),
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
            save_output_image(output.images[0], output_path)
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
            metadata=self.execution_metadata(
                cache_hit=False,
                internal_generation_canvas=source_image_path is None,
            ),
        )

    def execution_metadata(
        self,
        *,
        cache_hit: bool,
        internal_generation_canvas: bool,
    ) -> dict[str, Any]:
        return {
            "cache_hit": cache_hit,
            "provider": self.provider,
            "backend_id": self.backend,
            "model_id": self.model_id,
            "model_revision_or_fingerprint": model_revision_or_fingerprint(self.model_path),
            "pipeline_id": self.pipeline_id,
            "adapter_version": self.adapter_version,
            "sampling": {
                "seed": self.seed,
                "num_inference_steps": self.num_inference_steps,
                "true_cfg_scale": self.true_cfg_scale,
                "guidance_scale": self.guidance_scale,
                "width": self.width,
                "height": self.height,
                "negative_prompt": " ",
            },
            "model_path_exists": self.model_path.exists(),
            "local_runtime": "diffusers.QwenImageEditPlusPipeline",
            "internal_generation_canvas": internal_generation_canvas,
            "cpu_offload": self.cpu_offload,
        }

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
    ) -> QwenImageResult:
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
        return QwenImageResult(
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
