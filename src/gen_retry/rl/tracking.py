from __future__ import annotations

import os
import re
from importlib import import_module
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from gen_retry.rl.config import TrackingConfig


_SECRET_PARTS = ("api_key", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class WandbRuntime:
    enabled: bool
    mode: str
    project: str
    entity: str | None
    group: str
    run_name: str
    run_id: str
    tags: tuple[str, ...]
    directory: Path
    environment: dict[str, str]


def build_wandb_runtime(
    config: TrackingConfig,
    *,
    run_suffix: str,
    environment: Mapping[str, str] | None = None,
) -> WandbRuntime:
    env = dict(os.environ if environment is None else environment)
    suffix = _safe_identifier(run_suffix, "run_suffix")
    run_name = f"{config.run_name_prefix}-{suffix}"
    run_id = _safe_identifier(run_name, "W&B run ID")
    entity = env.get(config.entity_env) or None
    mode = env.get(config.mode_env, config.mode).strip().lower()
    if mode not in {"online", "offline", "disabled"}:
        raise ValueError(
            f"{config.mode_env} must be online, offline, or disabled"
        )
    if mode == "online" and not env.get(config.api_key_env):
        raise ValueError(
            f"online W&B requires {config.api_key_env} in the environment"
        )
    runtime_env = {
        "WANDB_MODE": mode,
        "WANDB_PROJECT": config.project,
        "WANDB_RUN_GROUP": config.group,
        "WANDB_JOB_TYPE": config.job_type,
        "WANDB_NAME": run_name,
        "WANDB_RUN_ID": run_id,
        "WANDB_TAGS": ",".join(config.tags),
        "WANDB_DIR": str(config.directory),
        "WANDB_RESUME": config.resume,
        "WANDB_LOG_MODEL": "true" if config.log_model else "false",
    }
    if entity:
        runtime_env["WANDB_ENTITY"] = entity
    return WandbRuntime(
        enabled=mode != "disabled",
        mode=mode,
        project=config.project,
        entity=entity,
        group=config.group,
        run_name=run_name,
        run_id=run_id,
        tags=config.tags,
        directory=config.directory,
        environment=runtime_env,
    )


def sanitized_tracking_payload(payload: Any) -> Any:
    """Remove credential-shaped values before a config is sent to W&B."""

    if isinstance(payload, Mapping):
        result: dict[str, Any] = {}
        for raw_key, value in payload.items():
            key = str(raw_key)
            if any(part in key.lower() for part in _SECRET_PARTS):
                result[key] = "REDACTED"
            else:
                result[key] = sanitized_tracking_payload(value)
        return result
    if isinstance(payload, (list, tuple)):
        return [sanitized_tracking_payload(value) for value in payload]
    if isinstance(payload, Path):
        return str(payload)
    return payload


def initialize_wandb_run(
    config: TrackingConfig,
    *,
    run_suffix: str,
    run_config: Mapping[str, Any],
    environment: Mapping[str, str] | None = None,
    wandb_module: Any | None = None,
) -> Any | None:
    """Initialize W&B without ever forwarding credential values as config."""

    runtime = build_wandb_runtime(
        config,
        run_suffix=run_suffix,
        environment=environment,
    )
    if not runtime.enabled:
        return None
    client = wandb_module if wandb_module is not None else import_module("wandb")
    initializer = getattr(client, "init", None)
    if not callable(initializer):
        raise RuntimeError("installed wandb module does not expose wandb.init")
    runtime.directory.mkdir(parents=True, exist_ok=True)
    return initializer(
        project=runtime.project,
        entity=runtime.entity,
        group=runtime.group,
        job_type=config.job_type,
        name=runtime.run_name,
        id=runtime.run_id,
        tags=list(runtime.tags),
        dir=str(runtime.directory),
        mode=runtime.mode,
        resume=config.resume,
        config=sanitized_tracking_payload(run_config),
    )


def _safe_identifier(value: str, name: str) -> str:
    normalized = value.strip().replace("/", "-")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", normalized):
        raise ValueError(
            f"{name} must contain only letters, digits, dot, dash, or underscore"
        )
    return normalized
