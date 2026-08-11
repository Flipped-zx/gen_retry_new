from __future__ import annotations

import gc
import importlib.metadata
import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat

from .config import Settings
from .errors import ServiceError, safe_error_summary
from .utils import sha256_file, utc_now


EXPECTED_PIPELINE_CLASSES = {
    "generate": "QwenImagePipeline",
    "edit": "QwenImageEditPlusPipeline",
}


@dataclass(frozen=True, slots=True)
class Accelerator:
    index: int
    name: str
    total_memory_bytes: int


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def probe_accelerators() -> tuple[list[Accelerator], dict[str, Any]]:
    try:
        import torch

        # The DTK build exposes PyTorch's flash SDP path but this image does not
        # ship its matching flash_attn_2_cuda shared library.
        torch.backends.cuda.enable_flash_sdp(False)
        torch.backends.cuda.enable_mem_efficient_sdp(False)
        torch.backends.cuda.enable_math_sdp(True)

        accelerators = []
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            accelerators.append(
                Accelerator(
                    index=index,
                    name=properties.name,
                    total_memory_bytes=properties.total_memory,
                )
            )
        versions = {
            "torch": torch.__version__,
            "hip": getattr(torch.version, "hip", None),
            "diffusers": package_version("diffusers"),
            "accelerate": package_version("accelerate"),
            "transformers": package_version("transformers"),
        }
        return accelerators, versions
    except Exception as exc:
        return [], {
            "torch": package_version("torch"),
            "hip": None,
            "diffusers": package_version("diffusers"),
            "accelerate": package_version("accelerate"),
            "transformers": package_version("transformers"),
            "probe_error": safe_error_summary(exc),
        }


class DeviceRuntime:
    def __init__(self, registry: "RuntimeRegistry", accelerator: Accelerator) -> None:
        self.registry = registry
        self.accelerator = accelerator
        self.device = f"cuda:{accelerator.index}"
        self.pipeline: Any | None = None
        self.loaded_kind: str | None = None
        self._lock = threading.RLock()

    def _unload(self) -> None:
        if self.pipeline is not None:
            del self.pipeline
        self.pipeline = None
        self.loaded_kind = None
        gc.collect()
        try:
            import torch

            torch.cuda.empty_cache()
        except Exception:
            pass

    def ensure_loaded(self, kind: str) -> Any:
        with self._lock:
            if self.pipeline is not None and self.loaded_kind == kind:
                return self.pipeline

            path = self.registry.model_path(kind)
            if not path.is_dir():
                raise ServiceError(
                    503,
                    f"{kind}_model_unavailable",
                    f"{kind} model weights are not present",
                    retryable=True,
                    details={"model_path": str(path)},
                )

            self._unload()
            self.registry.set_device_state(
                self.accelerator.index, kind=kind, state="loading", error=None
            )
            try:
                import torch
                from diffusers import DiffusionPipeline

                pipeline = DiffusionPipeline.from_pretrained(
                    str(path),
                    torch_dtype=torch.bfloat16,
                    local_files_only=True,
                )
                class_name = type(pipeline).__name__
                expected = EXPECTED_PIPELINE_CLASSES[kind]
                if class_name != expected:
                    raise RuntimeError(
                        f"model resolved to unexpected pipeline {class_name}; expected {expected}"
                    )
                pipeline.set_progress_bar_config(disable=True)
                pipeline = pipeline.to(self.device)
                self.pipeline = pipeline
                self.loaded_kind = kind
                self.registry.set_device_state(
                    self.accelerator.index,
                    kind=kind,
                    state="smoke_testing",
                    pipeline_class=class_name,
                    error=None,
                )
                self._smoke_test(kind)
                self.registry.set_device_state(
                    self.accelerator.index,
                    kind=kind,
                    state="ready",
                    pipeline_class=class_name,
                    smoke_tested_at=utc_now(),
                    error=None,
                )
                return pipeline
            except Exception as exc:
                summary = safe_error_summary(exc)
                self.registry.set_device_state(
                    self.accelerator.index, kind=kind, state="failed", error=summary
                )
                self._unload()
                if isinstance(exc, ServiceError):
                    raise
                raise ServiceError(
                    503,
                    f"{kind}_model_load_failed",
                    f"{kind} model failed to load or pass its smoke test",
                    retryable=True,
                    details={"device_index": self.accelerator.index, "summary": summary},
                ) from exc

    def _smoke_test(self, kind: str) -> None:
        import torch

        assert self.pipeline is not None
        generator = torch.Generator(device=self.device).manual_seed(0)
        arguments: dict[str, Any] = {
            "prompt": "a plain gray square",
            "width": 256,
            "height": 256,
            "num_inference_steps": 1,
            "true_cfg_scale": 1.0,
            "generator": generator,
        }
        if kind == "generate":
            arguments["negative_prompt"] = ""
        else:
            arguments["image"] = Image.new("RGB", (256, 256), (128, 128, 128))
            arguments["guidance_scale"] = 1.0
        with torch.inference_mode():
            result = self.pipeline(**arguments)
        if not getattr(result, "images", None):
            raise RuntimeError("smoke test returned no image")
        image = result.images[0]
        if not isinstance(image, Image.Image) or image.size != (256, 256):
            raise RuntimeError("smoke test returned an invalid image")
        extrema = ImageStat.Stat(image.convert("RGB")).extrema
        if not extrema or any(low < 0 or high > 255 for low, high in extrema):
            raise RuntimeError("smoke test image pixels are invalid")

    def infer(
        self, kind: str, payload: dict[str, Any], source_path: Path | None
    ) -> tuple[Image.Image, dict[str, Any]]:
        import torch

        pipeline = self.ensure_loaded(kind)
        generator = torch.Generator(device=self.device).manual_seed(payload["seed"])
        arguments: dict[str, Any] = {
            "prompt": payload["prompt"],
            "negative_prompt": payload.get("negative_prompt"),
            "width": payload["width"],
            "height": payload["height"],
            "num_inference_steps": payload["num_inference_steps"],
            "true_cfg_scale": payload["true_cfg_scale"],
            "generator": generator,
        }
        if kind == "edit":
            if source_path is None:
                raise RuntimeError("edit source artifact is missing")
            with Image.open(source_path) as source:
                arguments["image"] = source.convert("RGB")
            arguments["guidance_scale"] = payload["guidance_scale"]
        with torch.inference_mode():
            result = pipeline(**arguments)
        if not getattr(result, "images", None):
            raise RuntimeError("pipeline returned no image")
        image = result.images[0]
        if not isinstance(image, Image.Image):
            raise RuntimeError("pipeline returned a non-image result")
        state = self.registry.device_state(self.accelerator.index)
        provenance = {
            "device_index": self.accelerator.index,
            "device_name": self.accelerator.name,
            "pipeline_class": state.get("pipeline_class"),
            "attention_backend": "math_sdp",
            "execution_mode": "one_full_pipeline_replica_per_device",
            "model_sharded": False,
        }
        return image, provenance


class RuntimeRegistry:
    def __init__(
        self,
        settings: Settings,
        accelerators: list[Accelerator] | None = None,
        versions: dict[str, Any] | None = None,
    ) -> None:
        self.settings = settings
        probed_accelerators, probed_versions = probe_accelerators()
        self.accelerators = probed_accelerators if accelerators is None else accelerators
        self.versions = probed_versions if versions is None else versions
        self._lock = threading.RLock()
        self._states: dict[int, dict[str, Any]] = {
            item.index: {
                "device_index": item.index,
                "device_name": item.name,
                "state": "not_loaded",
                "kind": None,
                "pipeline_class": None,
                "smoke_tested_at": None,
                "error": None,
            }
            for item in self.accelerators
        }
        self._runtimes = {item.index: DeviceRuntime(self, item) for item in self.accelerators}
        self._model_identities = {
            kind: self._model_identity(self.model_path(kind)) for kind in ("generate", "edit")
        }

    def model_path(self, kind: str) -> Path:
        return (
            self.settings.generate_model_path
            if kind == "generate"
            else self.settings.edit_model_path
        )

    @staticmethod
    def _model_identity(path: Path) -> dict[str, Any]:
        model_index = path / "model_index.json"
        identity: dict[str, Any] = {
            "path": str(path),
            "present": path.is_dir(),
            "model_index_present": model_index.is_file(),
            "model_index_sha256": sha256_file(model_index) if model_index.is_file() else None,
            "pipeline_class": None,
        }
        if model_index.is_file():
            try:
                identity["pipeline_class"] = json.loads(model_index.read_text())["_class_name"]
            except (OSError, KeyError, json.JSONDecodeError):
                pass
        return identity

    def model_identity(self, kind: str) -> dict[str, Any]:
        return dict(self._model_identities[kind])

    def public_model_identity(self, kind: str) -> dict[str, Any]:
        identity = self._model_identities[kind]
        return {
            "id": self.model_path(kind).name,
            "pipeline_class": identity.get("pipeline_class"),
            "model_index_sha256": identity.get("model_index_sha256"),
        }

    def device_count(self) -> int:
        return len(self.accelerators)

    def worker_devices(self) -> list[int]:
        return [item.index for item in self.accelerators[: self.settings.max_workers]]

    def availability_error(self, kind: str) -> ServiceError | None:
        identity = self._model_identities[kind]
        if not identity["present"] or not identity["model_index_present"]:
            return ServiceError(
                503,
                f"{kind}_model_unavailable",
                f"{kind} model weights are not present or incomplete",
                retryable=True,
            )
        if not self.accelerators:
            return ServiceError(
                503,
                "accelerator_unavailable",
                "no compatible accelerator is visible",
                retryable=True,
                details={"accelerator_count": 0},
            )
        return None

    def runtime(self, device_index: int) -> DeviceRuntime:
        return self._runtimes[device_index]

    def set_device_state(self, device_index: int, **updates: Any) -> None:
        with self._lock:
            self._states[device_index].update(updates)

    def device_state(self, device_index: int) -> dict[str, Any]:
        with self._lock:
            return dict(self._states[device_index])

    def readiness(self) -> dict[str, Any]:
        with self._lock:
            states = [dict(value) for value in self._states.values()]
        result: dict[str, Any] = {
            "accelerator_count": len(self.accelerators),
            "accelerators": [asdict(item) for item in self.accelerators],
            "versions": dict(self.versions),
            "execution_mode": "one_full_pipeline_replica_per_device",
            "model_sharded": False,
            "devices": states,
        }
        for kind in ("generate", "edit"):
            identity = self.model_identity(kind)
            ready_devices = [
                item["device_index"]
                for item in states
                if item["kind"] == kind and item["state"] == "ready"
            ]
            failures = [
                item["error"]
                for item in states
                if item["kind"] == kind and item["error"]
            ]
            result[kind] = {
                "ready": bool(ready_devices),
                "model": identity,
                "ready_device_indices": ready_devices,
                "safe_error": failures[-1] if failures else None,
            }
        return result

    def public_readiness(self) -> dict[str, Any]:
        with self._lock:
            states = [dict(value) for value in self._states.values()]
        response: dict[str, Any] = {"accelerator_count": len(self.accelerators)}
        for kind in ("generate", "edit"):
            available = self.availability_error(kind) is None
            ready_workers = sum(
                1
                for item in states
                if item["kind"] == kind and item["state"] == "ready"
            )
            response[kind] = {
                "available": available,
                "ready": ready_workers > 0,
                "ready_workers": ready_workers,
                "model": self.public_model_identity(kind),
            }
        return response
