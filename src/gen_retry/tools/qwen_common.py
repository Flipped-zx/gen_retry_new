from __future__ import annotations

import os
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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(
        f".{output_path.name}.{os.getpid()}.tmp.png"
    )
    temporary_path.unlink(missing_ok=True)
    try:
        _save_image_payload(image, temporary_path)
        validate_cached_image(temporary_path)
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def validate_cached_image(
    image_path: Path,
    *,
    expected_size: tuple[int, int] | None = None,
) -> None:
    with Image.open(image_path) as image:
        actual_size = image.size
        image.verify()
    if expected_size is not None and actual_size != expected_size:
        raise ValueError(
            f"cached image size mismatch: expected {expected_size}, got {actual_size}"
        )
    sha256_file(image_path)


def reuse_valid_cached_image(
    image_path: Path,
    *,
    expected_size: tuple[int, int],
) -> bool:
    if not image_path.exists():
        return False
    try:
        validate_cached_image(image_path, expected_size=expected_size)
    except (OSError, ValueError):
        image_path.unlink(missing_ok=True)
        return False
    return True


def _save_image_payload(image: Any, output_path: Path) -> None:
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
