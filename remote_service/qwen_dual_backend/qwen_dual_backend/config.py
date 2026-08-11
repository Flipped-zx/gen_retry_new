from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = int(raw)
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _env_kind(name: str, default: str) -> str:
    value = os.getenv(name, default).strip().lower()
    if value not in {"generate", "edit"}:
        raise ValueError(f"{name} must be 'generate' or 'edit'")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    service_root: Path
    state_root: Path
    generate_model_path: Path
    edit_model_path: Path
    allowed_staging_root: Path
    queue_size: int = 4
    max_workers: int = 2
    max_body_bytes: int = 24 * 1024 * 1024
    max_source_bytes: int = 20 * 1024 * 1024
    max_image_pixels: int = 3_000_000
    max_source_pixels: int = 40_000_000
    queue_timeout_seconds: int = 600
    inference_timeout_seconds: int = 1800
    bearer_token: str | None = None
    preload_models: bool = False
    preload_kind: str = "generate"
    ready_kind: str = "generate"

    @classmethod
    def from_env(cls) -> "Settings":
        service_root = Path(os.getenv("QWEN_BACKEND_ROOT", str(SERVICE_ROOT))).resolve()
        state_root = Path(
            os.getenv("QWEN_STATE_ROOT", str(service_root / "state"))
        ).resolve()
        return cls(
            service_root=service_root,
            state_root=state_root,
            generate_model_path=Path(
                os.getenv(
                    "QWEN_GENERATE_MODEL_PATH",
                    str(service_root / "models" / "Qwen-Image-2512"),
                )
            ).resolve(),
            edit_model_path=Path(
                os.getenv(
                    "QWEN_EDIT_MODEL_PATH",
                    str(service_root / "models" / "Qwen-Image-Edit-2511"),
                )
            ).resolve(),
            allowed_staging_root=Path(
                os.getenv("QWEN_ALLOWED_STAGING_ROOT", str(state_root / "staging"))
            ).resolve(),
            queue_size=_env_int("QWEN_QUEUE_SIZE", 4, 1, 128),
            max_workers=_env_int("QWEN_MAX_WORKERS", 2, 1, 2),
            max_body_bytes=_env_int(
                "QWEN_MAX_BODY_BYTES", 24 * 1024 * 1024, 1024, 128 * 1024 * 1024
            ),
            max_source_bytes=_env_int(
                "QWEN_MAX_SOURCE_BYTES", 20 * 1024 * 1024, 1024, 100 * 1024 * 1024
            ),
            max_image_pixels=_env_int("QWEN_MAX_IMAGE_PIXELS", 3_000_000, 65_536, 8_000_000),
            max_source_pixels=_env_int(
                "QWEN_MAX_SOURCE_PIXELS", 40_000_000, 65_536, 100_000_000
            ),
            queue_timeout_seconds=_env_int("QWEN_QUEUE_TIMEOUT_SECONDS", 600, 1, 86_400),
            inference_timeout_seconds=_env_int(
                "QWEN_INFERENCE_TIMEOUT_SECONDS", 1800, 1, 86_400
            ),
            bearer_token=os.getenv("QWEN_BACKEND_BEARER_TOKEN") or None,
            preload_models=os.getenv("QWEN_PRELOAD_MODELS", "0") == "1",
            preload_kind=_env_kind("QWEN_PRELOAD_KIND", "generate"),
            ready_kind=_env_kind("QWEN_READY_KIND", "generate"),
        )

    def ensure_directories(self) -> None:
        for path in (
            self.state_root,
            self.state_root / "jobs",
            self.state_root / "artifacts",
            self.allowed_staging_root,
        ):
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
            path.chmod(0o700)
