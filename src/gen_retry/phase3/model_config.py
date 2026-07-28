from __future__ import annotations

import os
from dataclasses import dataclass
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


@dataclass(frozen=True)
class EvaluatorConfig:
    backend_id: str
    config_path: Path


@dataclass(frozen=True)
class ModelConfig:
    teacher: TeacherConfig
    image_backend: ImageBackendConfig
    evaluator: EvaluatorConfig


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
    evaluator = payload.get("evaluator") or {}
    supports = image_backend.get("supports") or {}
    return ModelConfig(
        teacher=TeacherConfig(
            provider=str(teacher["provider"]),
            model_id=str(teacher["model_id"]),
            api_key_env=str(teacher.get("api_key_env", "TEACHER_API_KEY")),
            base_url_env=str(teacher.get("base_url_env", "TEACHER_BASE_URL")),
        ),
        image_backend=ImageBackendConfig(
            provider=str(image_backend.get("provider", "http")),
            backend_id=str(image_backend["backend_id"]),
            model_id=str(image_backend["model_id"]),
            model_path=Path(str(image_backend["model_path"])).expanduser(),
            supports_generate=bool(supports.get("generate", False)),
            supports_edit=bool(supports.get("edit", False)),
        ),
        evaluator=EvaluatorConfig(
            backend_id=str(evaluator["backend_id"]),
            config_path=Path(str(evaluator["config_path"])).expanduser(),
        ),
    )
