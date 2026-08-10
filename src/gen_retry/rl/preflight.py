from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from gen_retry.agent.sft_planner import checkpoint_fingerprint
from gen_retry.phase3.model_config import load_model_config
from gen_retry.rl.config import RlExperimentConfig, load_experiment_config
from gen_retry.rl.data import validate_frozen_rl_data
from gen_retry.rl.runtime_gate import (
    probe_live_adapter_evidence,
    probe_smoke_report,
)
from gen_retry.rl.tracking import build_wandb_runtime


_REQUIRED_DISTRIBUTIONS = {
    "torch": "torch",
    "transformers": "transformers",
    "ray": "ray",
    "wandb": "wandb",
    "verl": "verl",
    "sglang": "sglang",
    "rllm": "rllm",
}


def run_rl_preflight(
    *,
    config_path: Path,
    model_config_path: Path = Path("configs/models/local.yaml"),
    environment: Mapping[str, str] | None = None,
    check_accelerator: bool = True,
) -> dict[str, Any]:
    config = load_experiment_config(config_path)
    env = dict(os.environ if environment is None else environment)
    checks: list[dict[str, str]] = []

    def record(
        check_id: str,
        passed: bool,
        detail: str,
        *,
        gate: str = "control_plane",
        warning: bool = False,
        pending: bool = False,
    ) -> None:
        status = (
            "PASS"
            if passed
            else "WARN"
            if warning
            else "PENDING"
            if pending
            else "BLOCKED"
        )
        checks.append(
            {
                "check_id": check_id,
                "gate": gate,
                "status": status,
                "detail": detail,
            }
        )

    record(
        "execution_profile",
        config.execution_profile == "qwen_dual_backend@1",
        config.execution_profile,
    )
    model_config = load_model_config(model_config_path)
    execution = model_config.resolved_image_execution
    dual_backend_ok = (
        f"{execution.profile_id}@{execution.profile_version}"
        == config.execution_profile
        and execution.generate_backend.model_id == "Qwen-Image-2512"
        and execution.generate_backend.supports_generate
        and not execution.generate_backend.supports_edit
        and execution.edit_backend.model_id == "Qwen-Image-Edit-2511"
        and execution.edit_backend.supports_edit
        and not execution.edit_backend.supports_generate
    )
    record(
        "dual_backend_routes",
        dual_backend_ok,
        (
            f"generate={execution.generate_backend.model_id}; "
            f"edit={execution.edit_backend.model_id}"
        ),
    )
    record(
        "generate_model_path",
        execution.generate_backend.model_path.is_dir(),
        str(execution.generate_backend.model_path),
    )
    record(
        "edit_model_path",
        execution.edit_backend.model_path.is_dir(),
        str(execution.edit_backend.model_path),
    )
    record(
        "geneval2_path",
        model_config.evaluator.config_path.is_dir(),
        str(model_config.evaluator.config_path),
    )

    checkpoint_ok = config.base_checkpoint.is_dir()
    actual_fingerprint = None
    if checkpoint_ok:
        try:
            actual_fingerprint = checkpoint_fingerprint(config.base_checkpoint)
        except (FileNotFoundError, OSError) as exc:
            checkpoint_ok = False
            actual_fingerprint = f"ERROR:{type(exc).__name__}"
    fingerprint_ok = checkpoint_ok and actual_fingerprint == (
        "sha256:" + config.checkpoint_sha256
    )
    record("base_checkpoint", checkpoint_ok, str(config.base_checkpoint))
    record(
        "base_checkpoint_fingerprint",
        fingerprint_ok,
        str(actual_fingerprint),
    )

    package_versions = _package_versions()
    for package, version in package_versions.items():
        record(
            f"package_{package}",
            version is not None,
            version or "not installed in the current Python environment",
        )

    wandb_runtime = None
    try:
        wandb_runtime = build_wandb_runtime(
            config.tracking,
            run_suffix="preflight",
            environment=env,
        )
    except ValueError as exc:
        record("wandb_configuration", False, str(exc))
    else:
        record(
            "wandb_configuration",
            True,
            (
                f"mode={wandb_runtime.mode}; project={wandb_runtime.project}; "
                f"entity={'environment' if wandb_runtime.entity else 'unset'}"
            ),
        )
        config.tracking.directory.mkdir(parents=True, exist_ok=True)
        record(
            "wandb_directory",
            config.tracking.directory.is_dir(),
            str(config.tracking.directory),
        )

    manifest_paths = {
        "train_manifest": config.admission.train_manifest,
        "development_manifest": config.admission.development_manifest,
        "confirmation_manifest": config.admission.confirmation_manifest,
        "experiment_declaration": config.admission.experiment_declaration,
    }
    for name, path in manifest_paths.items():
        record(name, path.is_file(), str(path))
    frozen_data = None
    if all(path.is_file() for path in manifest_paths.values()):
        try:
            frozen_data = validate_frozen_rl_data(
                config=config,
                config_path=config_path,
            )
        except (KeyError, OSError, TypeError, ValueError) as exc:
            record("frozen_data_contract", False, str(exc))
        else:
            record(
                "frozen_data_contract",
                True,
                "; ".join(
                    f"{split}={item['selected_count']}"
                    for split, item in sorted(frozen_data.items())
                ),
            )

    accelerator = _probe_accelerator() if check_accelerator else {
        "checked": False,
        "available": None,
        "device_count": None,
        "devices": [],
        "error": None,
    }
    if check_accelerator:
        accelerator_ok = bool(accelerator["available"]) and int(
            accelerator["device_count"] or 0
        ) >= config.resources.accelerator_count
        record(
            "accelerator_topology",
            accelerator_ok,
            (
                f"visible={accelerator['device_count']}; "
                f"required={config.resources.accelerator_count}; "
                f"error={accelerator['error']}"
            ),
            gate="smoke",
        )
    else:
        record(
            "accelerator_topology",
            False,
            "accelerator probe skipped",
            gate="smoke",
            pending=True,
        )

    adapter_ready, adapter_detail, adapter_sha256 = probe_live_adapter_evidence(
        path=config.admission.live_adapter_evidence,
        config_path=config_path,
        config=config,
        package_versions=package_versions,
    )
    record(
        "live_adapter_evidence",
        adapter_ready,
        adapter_detail,
        gate="smoke",
    )
    if adapter_ready and adapter_sha256 is not None:
        smoke_passed, smoke_detail = probe_smoke_report(
            path=config.admission.smoke_report,
            config_path=config_path,
            adapter_evidence_path=config.admission.live_adapter_evidence,
            adapter_evidence_sha256=adapter_sha256,
            config=config,
        )
    else:
        smoke_passed = False
        smoke_detail = "adapter evidence must pass before smoke-report admission"
    record(
        "smoke_report",
        smoke_passed,
        smoke_detail,
        gate="optimization",
        pending=not smoke_passed,
    )

    blocked = [item for item in checks if item["status"] == "BLOCKED"]
    warnings = [item for item in checks if item["status"] == "WARN"]
    pending = [item for item in checks if item["status"] == "PENDING"]
    control_plane_ready = not any(
        item["status"] == "BLOCKED" and item["gate"] == "control_plane"
        for item in checks
    )
    ready_for_smoke = control_plane_ready and all(
        item["status"] == "PASS"
        for item in checks
        if item["gate"] == "smoke"
    )
    ready_for_optimization = ready_for_smoke and all(
        item["status"] == "PASS"
        for item in checks
        if item["gate"] == "optimization"
    )
    if not control_plane_ready:
        status = "BLOCKED"
    elif not ready_for_smoke:
        status = "CONTROL_PLANE_READY"
    elif not ready_for_optimization:
        status = "READY_FOR_SMOKE"
    else:
        status = "READY_FOR_OPTIMIZATION"
    return {
        "schema_version": "0.1",
        "preflight_type": "naive_geneval2_grpo_runtime",
        "status": status,
        "control_plane_ready": control_plane_ready,
        "ready_for_smoke": ready_for_smoke,
        "ready_for_optimization": ready_for_optimization,
        "python": {
            "version": platform.python_version(),
            "executable": os.path.realpath(os.sys.executable),
        },
        "method": f"{config.method_id}@{config.method_version}",
        "execution_profile": config.execution_profile,
        "policy_revision": config.policy_revision,
        "resource_topology": asdict(config.resources),
        "packages": package_versions,
        "accelerator": accelerator,
        "wandb": None if wandb_runtime is None else {
            "mode": wandb_runtime.mode,
            "project": wandb_runtime.project,
            "entity_set": wandb_runtime.entity is not None,
            "group": wandb_runtime.group,
            "directory": str(wandb_runtime.directory),
        },
        "frozen_data": frozen_data,
        "checks": checks,
        "blocked_count": len(blocked),
        "pending_count": len(pending),
        "warning_count": len(warnings),
    }


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for import_name, distribution_name in _REQUIRED_DISTRIBUTIONS.items():
        try:
            version = importlib.metadata.version(distribution_name)
        except importlib.metadata.PackageNotFoundError:
            version = None
        if version is None:
            spec = importlib.util.find_spec(import_name)
            # A run-artifact directory such as ``wandb/`` is importable as an
            # empty namespace package. It is not an installed client library.
            if spec is not None and spec.loader is not None:
                version = "importable-without-distribution-metadata"
        versions[import_name] = version
    return versions


def _probe_accelerator() -> dict[str, Any]:
    try:
        import torch

        available = bool(torch.cuda.is_available())
        count = int(torch.cuda.device_count())
        devices = []
        for index in range(count):
            properties = torch.cuda.get_device_properties(index)
            devices.append(
                {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                    "memory_bytes": int(properties.total_memory),
                }
            )
        return {
            "checked": True,
            "available": available,
            "device_count": count,
            "devices": devices,
            "torch_version": str(torch.__version__),
            "torch_hip": str(torch.version.hip),
            "error": None,
        }
    except Exception as exc:
        return {
            "checked": True,
            "available": False,
            "device_count": 0,
            "devices": [],
            "torch_version": None,
            "torch_hip": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
