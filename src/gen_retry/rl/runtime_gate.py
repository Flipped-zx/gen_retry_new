from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema.exceptions import ValidationError

from gen_retry.domain.artifacts import sha256_file
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.rl.config import RlExperimentConfig
from gen_retry.rl.optimizer import prepare_optimizer_batch


ADAPTER_EVIDENCE_SCHEMA = "rl_live_adapter_evidence_v0_1.schema.json"
RUNTIME_CHECK_REPORT_SCHEMA = "rl_runtime_check_report_v0_1.schema.json"
SMOKE_REPORT_SCHEMA = "rl_smoke_report_v0_1.schema.json"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def probe_live_adapter_evidence(
    *,
    path: Path,
    config_path: Path,
    config: RlExperimentConfig,
    package_versions: Mapping[str, str | None],
    repository_root: Path | None = None,
) -> tuple[bool, str, str | None]:
    root = (repository_root or PROJECT_ROOT).resolve()
    try:
        path = _resolve_input_path(path, root=root)
    except ValueError as exc:
        return False, str(exc), None
    if not path.is_file():
        return False, f"missing required adapter evidence: {path}", None
    try:
        payload = _load_json(path, ADAPTER_EVIDENCE_SCHEMA)
        _validate_ref(payload["config"], root=root, expected_path=config_path)
        if payload["policy_checkpoint_sha256"] != config.checkpoint_sha256:
            raise ValueError("adapter evidence checkpoint SHA256 mismatch")
        implementation_path = _validate_ref(payload["implementation"], root=root)
        implementation_sha256 = sha256_file(implementation_path)
        for artifact in payload["evidence_artifacts"]:
            _validate_ref(artifact, root=root)
        for package in ("rllm", "verl", "sglang"):
            installed = package_versions.get(package)
            if installed is None:
                raise ValueError(f"adapter evidence requires installed {package}")
            if payload["runtime_versions"][package] != installed:
                raise ValueError(f"adapter evidence {package} version mismatch")
        for check_id, report_ref in payload["checks"].items():
            report_path = _validate_ref(report_ref, root=root)
            _validate_runtime_check_report(
                report_path,
                root=root,
                check_id=check_id,
                config_sha256=payload["config"]["sha256"],
                implementation_sha256=implementation_sha256,
                checkpoint_sha256=config.checkpoint_sha256,
                runtime_versions=payload["runtime_versions"],
                adapter_evidence_sha256=None,
                rollout_batch_sha256=None,
                advantage_batch_sha256=None,
            )
    except (KeyError, OSError, TypeError, ValueError, ValidationError) as exc:
        return False, str(exc), None
    return True, f"validated {path}", sha256_file(path)


def probe_smoke_report(
    *,
    path: Path,
    config_path: Path,
    adapter_evidence_path: Path,
    adapter_evidence_sha256: str,
    config: RlExperimentConfig,
    repository_root: Path | None = None,
) -> tuple[bool, str]:
    root = (repository_root or PROJECT_ROOT).resolve()
    try:
        path = _resolve_input_path(path, root=root)
    except ValueError as exc:
        return False, str(exc)
    if not path.is_file():
        return False, f"pending 32-group smoke report: {path}"
    try:
        payload = _load_json(path, SMOKE_REPORT_SCHEMA)
        _validate_ref(payload["config"], root=root, expected_path=config_path)
        adapter_path = _validate_ref(
            payload["adapter_evidence"],
            root=root,
            expected_path=adapter_evidence_path,
        )
        if payload["adapter_evidence"]["sha256"] != adapter_evidence_sha256:
            raise ValueError("smoke report adapter-evidence SHA256 mismatch")
        adapter_payload = _load_json(adapter_path, ADAPTER_EVIDENCE_SCHEMA)
        implementation_path = _validate_ref(
            adapter_payload["implementation"], root=root
        )
        rollout_path = _validate_ref(payload["rollout_batch"], root=root)
        advantage_path = _validate_ref(payload["advantage_batch"], root=root)
        artifact_root = _resolve_input_path(
            Path(payload["artifact_root"]), root=root
        )
        if not rollout_path.is_relative_to(artifact_root):
            raise ValueError("smoke rollout batch is outside artifact_root")
        if not advantage_path.is_relative_to(artifact_root):
            raise ValueError("smoke advantage batch is outside artifact_root")
        rollout_payload = _load_json(
            rollout_path, "rl_rollout_sample_batch_v0_1.schema.json"
        )
        advantage_payload = _load_json(
            advantage_path, "rl_advantage_batch_v0_1.schema.json"
        )
        optimizer_batch = prepare_optimizer_batch(
            rollout_payload=rollout_payload,
            advantage_payload=advantage_payload,
            artifact_root=artifact_root,
            config=config,
        )
        recomputed = {
            "planned_group_count": rollout_payload["planned_group_count"],
            "valid_group_count": len(rollout_payload["groups"]),
            "excluded_group_count": len(rollout_payload["excluded_groups"]),
            "zero_variance_group_count": optimizer_batch.zero_variance_group_count,
            "policy_invalid_candidate_count": optimizer_batch.policy_invalid_count,
            "total_candidate_count": optimizer_batch.admitted_candidate_count,
        }
        for name, expected in recomputed.items():
            if payload[name] != expected:
                raise ValueError(
                    f"smoke report {name}={payload[name]!r}, recomputed {expected!r}"
                )
        planned = recomputed["planned_group_count"]
        valid = recomputed["valid_group_count"]
        excluded = recomputed["excluded_group_count"]
        zero_variance = recomputed["zero_variance_group_count"]
        invalid = recomputed["policy_invalid_candidate_count"]
        candidates = recomputed["total_candidate_count"]
        if planned != config.admission.smoke_prompts:
            raise ValueError("smoke report planned-group count is not the frozen smoke size")
        if valid + excluded != planned:
            raise ValueError("smoke report group accounting mismatch")
        if valid / planned < config.admission.minimum_valid_group_fraction:
            raise ValueError("smoke report valid-group fraction is below threshold")
        if zero_variance / valid > (
            config.admission.maximum_zero_variance_group_fraction
        ):
            raise ValueError("smoke report zero-variance fraction exceeds threshold")
        if invalid / candidates > config.admission.maximum_policy_invalid_fraction:
            raise ValueError("smoke report policy-invalid fraction exceeds threshold")
        for check_id, report_ref in payload["checks"].items():
            report_path = _validate_ref(report_ref, root=root)
            _validate_runtime_check_report(
                report_path,
                root=root,
                check_id=check_id,
                config_sha256=payload["config"]["sha256"],
                implementation_sha256=sha256_file(implementation_path),
                checkpoint_sha256=config.checkpoint_sha256,
                runtime_versions=adapter_payload["runtime_versions"],
                adapter_evidence_sha256=adapter_evidence_sha256,
                rollout_batch_sha256=payload["rollout_batch"]["sha256"],
                advantage_batch_sha256=payload["advantage_batch"]["sha256"],
            )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        ValidationError,
        ZeroDivisionError,
    ) as exc:
        return False, str(exc)
    return True, f"validated {path}"


def _load_json(path: Path, schema_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON evidence: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"evidence must be a JSON object: {path}")
    validate_instance(payload, schema_name)
    return payload


def _validate_runtime_check_report(
    path: Path,
    *,
    root: Path,
    check_id: str,
    config_sha256: str,
    implementation_sha256: str,
    checkpoint_sha256: str,
    runtime_versions: Mapping[str, str],
    adapter_evidence_sha256: str | None,
    rollout_batch_sha256: str | None,
    advantage_batch_sha256: str | None,
) -> None:
    report = _load_json(path, RUNTIME_CHECK_REPORT_SCHEMA)
    if report["check_id"] != check_id:
        raise ValueError(f"runtime check ID mismatch: {report['check_id']} != {check_id}")
    if report["runtime_versions"] != dict(runtime_versions):
        raise ValueError(f"{check_id}: runtime-version binding mismatch")
    expected_bindings = {
        "config_sha256": config_sha256,
        "implementation_sha256": implementation_sha256,
        "policy_checkpoint_sha256": checkpoint_sha256,
        "adapter_evidence_sha256": adapter_evidence_sha256,
        "rollout_batch_sha256": rollout_batch_sha256,
        "advantage_batch_sha256": advantage_batch_sha256,
    }
    if report["bindings"] != expected_bindings:
        raise ValueError(f"{check_id}: runtime-check bindings mismatch")
    _validate_ref(report["output"], root=root)


def _validate_ref(
    artifact: Mapping[str, str],
    *,
    root: Path,
    expected_path: Path | None = None,
) -> Path:
    ref = Path(artifact["ref"])
    if ref.is_absolute():
        raise ValueError(f"evidence ref must be repository-relative: {ref}")
    path = _resolve_input_path(ref, root=root)
    if expected_path is not None:
        expected = _resolve_input_path(expected_path, root=root)
        if path != expected:
            raise ValueError(f"evidence ref mismatch: {ref} != {expected_path}")
    if not path.is_file():
        raise ValueError(f"evidence ref is missing: {ref}")
    if sha256_file(path) != artifact["sha256"]:
        raise ValueError(f"evidence ref SHA256 mismatch: {ref}")
    return path


def _resolve_input_path(path: Path, *, root: Path) -> Path:
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"runtime evidence path escapes repository root: {path}")
    return resolved
