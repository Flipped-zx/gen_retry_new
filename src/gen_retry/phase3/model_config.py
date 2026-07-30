from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml


LOCAL_TEACHER_ENV_FILE = ".env.teacher.local"
LOCAL_TEACHER_ENV_KEYS = frozenset({"TEACHER_API_KEY", "TEACHER_BASE_URL"})


@dataclass(frozen=True)
class TeacherConfig:
    provider: str
    model_id: str
    api_key_env: str
    base_url_env: str


@dataclass(frozen=True)
class ImageBackendConfig:
    provider: str
    backend_id: str
    model_id: str
    model_path: Path
    supports_generate: bool
    supports_edit: bool
    num_inference_steps: int | None = None
    true_cfg_scale: float = 4.0
    guidance_scale: float | None = None


@dataclass(frozen=True)
class ImageExecutionConfig:
    profile_id: str
    profile_version: str
    generate_backend: ImageBackendConfig
    edit_backend: ImageBackendConfig


@dataclass(frozen=True)
class EvaluatorConfig:
    backend_id: str
    config_path: Path


@dataclass(frozen=True)
class ModelConfig:
    teacher: TeacherConfig
    image_backend: ImageBackendConfig
    image_execution: ImageExecutionConfig | None
    evaluator: EvaluatorConfig

    @property
    def resolved_image_execution(self) -> ImageExecutionConfig:
        if self.image_execution is not None:
            return self.image_execution
        return ImageExecutionConfig(
            profile_id="qwen_image_edit_only",
            profile_version="1",
            generate_backend=self.image_backend,
            edit_backend=self.image_backend,
        )


def load_local_teacher_environment(path: Path = Path(LOCAL_TEACHER_ENV_FILE)) -> None:
    """Load project-local Teacher credentials without overriding shell exports."""

    if not path.exists():
        return
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or key not in LOCAL_TEACHER_ENV_KEYS:
            raise ValueError(f"invalid Teacher environment entry at {path}:{line_number}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if not value:
            raise ValueError(f"empty Teacher environment value at {path}:{line_number}")
        os.environ.setdefault(key, value)


def load_model_config(path: Path = Path("configs/models/local.yaml")) -> ModelConfig:
    if not path.exists():
        raise FileNotFoundError(f"missing model config: {path}")
    resolved_path = path.resolve()
    project_root = resolved_path.parents[2]
    load_local_teacher_environment(project_root / LOCAL_TEACHER_ENV_FILE)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    teacher = payload.get("teacher") or {}
    image_backend = payload.get("image_backend") or {}
    image_execution = payload.get("image_execution") or None
    evaluator = payload.get("evaluator") or {}
    legacy_backend = _parse_image_backend(image_backend)
    parsed_execution = None
    if image_execution is not None:
        parsed_execution = ImageExecutionConfig(
            profile_id=str(image_execution["profile_id"]),
            profile_version=str(image_execution["profile_version"]),
            generate_backend=_parse_image_backend(image_execution["generate_backend"]),
            edit_backend=_parse_image_backend(image_execution["edit_backend"]),
        )
    return ModelConfig(
        teacher=TeacherConfig(
            provider=str(teacher["provider"]),
            model_id=str(teacher["model_id"]),
            api_key_env=str(teacher.get("api_key_env", "TEACHER_API_KEY")),
            base_url_env=str(teacher.get("base_url_env", "TEACHER_BASE_URL")),
        ),
        image_backend=legacy_backend,
        image_execution=parsed_execution,
        evaluator=EvaluatorConfig(
            backend_id=str(evaluator["backend_id"]),
            config_path=Path(str(evaluator["config_path"])).expanduser(),
        ),
    )


def select_image_execution_profile(
    config: ModelConfig,
    profile_id: str | None,
) -> ModelConfig:
    if profile_id is None or profile_id == config.resolved_image_execution.profile_id:
        return config
    if profile_id == "qwen_image_edit_only":
        return replace(config, image_execution=None)
    raise ValueError(f"execution profile is not configured: {profile_id}")


def _parse_image_backend(payload: dict[str, Any]) -> ImageBackendConfig:
    supports = payload.get("supports") or {}
    guidance_scale = payload.get("guidance_scale")
    return ImageBackendConfig(
        provider=str(payload.get("provider", "http")),
        backend_id=str(payload["backend_id"]),
        model_id=str(payload["model_id"]),
        model_path=Path(str(payload["model_path"])).expanduser(),
        supports_generate=bool(supports.get("generate", False)),
        supports_edit=bool(supports.get("edit", False)),
        num_inference_steps=(
            int(payload["num_inference_steps"])
            if payload.get("num_inference_steps") is not None
            else None
        ),
        true_cfg_scale=float(payload.get("true_cfg_scale", 4.0)),
        guidance_scale=(
            float(guidance_scale) if guidance_scale is not None else None
        ),
    )
