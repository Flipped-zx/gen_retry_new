from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from gen_retry.domain.artifacts import sha256_bytes, sha256_file


@dataclass(frozen=True)
class QwenImageResult:
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


def model_revision_or_fingerprint(model_path: Path) -> str:
    model_index = model_path / "model_index.json"
    if model_index.is_file():
        return "model_index_sha256:" + sha256_file(model_index)
    return "path_sha256:" + sha256_bytes(str(model_path.resolve()).encode("utf-8"))


def save_output_image(image: Any, output_path: Path) -> None:
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
