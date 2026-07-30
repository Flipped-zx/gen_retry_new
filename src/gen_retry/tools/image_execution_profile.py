from __future__ import annotations

from dataclasses import dataclass

from gen_retry.phase3.model_config import ImageBackendConfig, ImageExecutionConfig


DUAL_PROFILE_ID = "qwen_dual_backend"
DUAL_PROFILE_VERSION = "1"
LEGACY_PROFILE_ID = "qwen_image_edit_only"
LEGACY_PROFILE_VERSION = "1"


@dataclass(frozen=True)
class ExecutionRoute:
    logical_action: str
    operation: str
    backend: ImageBackendConfig
    producer: str


def validate_execution_profile(config: ImageExecutionConfig) -> None:
    if not config.profile_id or not config.profile_version:
        raise ValueError("execution profile id and version must be non-empty")
    if config.profile_id == DUAL_PROFILE_ID:
        if config.profile_version != DUAL_PROFILE_VERSION:
            raise ValueError(
                f"unsupported {DUAL_PROFILE_ID} version: {config.profile_version}"
            )
        if config.generate_backend.backend_id != "qwen_image":
            raise ValueError("qwen_dual_backend generate route must use qwen_image")
        if config.edit_backend.backend_id != "qianwen_image_edit":
            raise ValueError(
                "qwen_dual_backend edit route must use qianwen_image_edit"
            )
    if not config.generate_backend.supports_generate:
        raise ValueError("configured generate backend does not support generation")
    if not config.edit_backend.supports_edit:
        raise ValueError("configured edit backend does not support editing")


def resolve_execution_route(
    config: ImageExecutionConfig,
    logical_action: str,
) -> ExecutionRoute:
    validate_execution_profile(config)
    if logical_action == "generate_image":
        backend = config.generate_backend
        producer = (
            "qwen_image_adapter"
            if backend.backend_id == "qwen_image"
            else "qianwen_image_edit_adapter"
        )
        return ExecutionRoute(
            logical_action=logical_action,
            operation="generate",
            backend=backend,
            producer=producer,
        )
    if logical_action == "edit_image":
        return ExecutionRoute(
            logical_action=logical_action,
            operation="edit",
            backend=config.edit_backend,
            producer="qianwen_image_edit_adapter",
        )
    raise ValueError(f"action has no image execution route: {logical_action}")
