from __future__ import annotations

import gc
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_file
from gen_retry.tools.model_load_lock import exclusive_model_load
from gen_retry.tools.qwen_common import (
    QwenImageResult,
    model_revision_or_fingerprint,
    reuse_valid_cached_image,
    save_output_image,
)
from gen_retry.tools.resource_locks import exclusive_device_execution


class QwenImageAdapter:
    backend = "qwen_image"
    pipeline_id = "QwenImagePipeline"
    adapter_version = "1"

    def __init__(
        self,
        *,
        provider: str,
        model_id: str,
        model_path: Path,
        artifact_root: Path,
        height: int = 1024,
        width: int = 1024,
        num_inference_steps: int = 50,
        true_cfg_scale: float = 4.0,
        seed: int = 0,
        negative_prompt: str = (
            "low resolution, low quality, deformed anatomy, oversaturated, "
            "blurry text, distorted text, chaotic composition"
        ),
        cpu_offload: bool = False,
    ):
        if provider != "local":
            raise ValueError(f"unsupported Qwen-Image provider: {provider}")
        self.provider = provider
        self.model_id = model_id
        self.model_path = model_path
        self.artifact_root = artifact_root
        self.height = height
        self.width = width
        self.num_inference_steps = num_inference_steps
        self.true_cfg_scale = true_cfg_scale
        self.seed = seed
        self.negative_prompt = negative_prompt
        self.cpu_offload = cpu_offload

    @property
    def uses_http_endpoint(self) -> bool:
        return False

    def execution_metadata(self, *, cache_hit: bool) -> dict[str, Any]:
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
                "guidance_scale": None,
                "width": self.width,
                "height": self.height,
                "negative_prompt": self.negative_prompt,
            },
            "model_path_exists": self.model_path.exists(),
            "local_runtime": "diffusers.QwenImagePipeline",
            "cpu_offload": self.cpu_offload,
        }

    def generate(
        self,
        *,
        request_id: str,
        attempt_id: str,
        image_artifact_id: str,
        instruction: str,
    ) -> QwenImageResult:
        if not self.model_path.exists():
            raise FileNotFoundError(f"missing Qwen-Image model path: {self.model_path}")
        artifact_uri = f"images/{image_artifact_id}.png"
        output_path = self.artifact_root / artifact_uri
        if reuse_valid_cached_image(
            output_path,
            expected_size=(self.width, self.height),
        ):
            return self._result(
                request_id=request_id,
                attempt_id=attempt_id,
                image_artifact_id=image_artifact_id,
                artifact_uri=artifact_uri,
                artifact_sha256=sha256_file(output_path),
                metadata=self.execution_metadata(cache_hit=True),
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with exclusive_device_execution():
            pipeline = None
            output = None
            try:
                with exclusive_model_load():
                    pipeline = self._load_pipeline()
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
                generator = torch.Generator(device=device).manual_seed(self.seed)
                pipeline.set_progress_bar_config(disable=True)
                with torch.inference_mode():
                    output = pipeline(
                        prompt=instruction,
                        negative_prompt=self.negative_prompt,
                        width=self.width,
                        height=self.height,
                        num_inference_steps=self.num_inference_steps,
                        true_cfg_scale=self.true_cfg_scale,
                        generator=generator,
                        output_type="pt",
                    )
                save_output_image(output.images[0], output_path)
            finally:
                del output
                del pipeline
                gc.collect()
                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.synchronize()
                        torch.cuda.empty_cache()
                except Exception:
                    pass

        return self._result(
            request_id=request_id,
            attempt_id=attempt_id,
            image_artifact_id=image_artifact_id,
            artifact_uri=artifact_uri,
            artifact_sha256=sha256_file(output_path),
            metadata=self.execution_metadata(cache_hit=False),
        )

    def _load_pipeline(self) -> Any:
        import torch
        from diffusers import QwenImagePipeline

        from gen_retry.tools.torch_compat import patch_torch_from_numpy_if_needed

        patch_torch_from_numpy_if_needed()
        pipeline = QwenImagePipeline.from_pretrained(
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
            producer="qwen_image_adapter",
            metadata={
                "backend": self.backend,
                "operation": "generate",
                "request_id": request_id,
                **metadata,
            },
        )
        return QwenImageResult(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=None,
            operation="generate",
            backend=self.backend,
            image_artifact_id=image_artifact_id,
            artifact_uri=artifact_uri,
            artifact_manifest_ref="manifest.json",
            artifact_sha256=artifact_sha256,
            manifest_entry=manifest_entry,
            metadata=metadata,
        )
