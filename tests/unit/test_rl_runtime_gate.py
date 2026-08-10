from __future__ import annotations

import hashlib
from pathlib import Path

from gen_retry.rl.admission import admit_rollout_sample_batch
from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.runtime_gate import (
    probe_live_adapter_evidence,
    probe_smoke_report,
)
from gen_retry.rl.training import build_advantage_batch
from gen_retry.runtime.json_canonical import canonical_json


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_CHECK_IDS = (
    "strict_json_multi_turn_workflow",
    "qwen3_vl_multimodal_grid_preservation",
    "persisted_old_reference_log_probs",
    "tokenizer_derived_action_mask",
    "manifest_state_event_semantic_replay",
    "staged_service_release_handoff",
)
SMOKE_CHECK_IDS = (
    "interruption_resume_replay",
    "infrastructure_retry_exclusion",
    "active_reference_kl",
    "action_mask_alignment",
    "terminal_reward_event_replay",
    "service_release_before_fsdp",
)
RUNTIME_VERSIONS = {
    "rllm": "0.2.1",
    "verl": "0.6.1",
    "sglang": "0.4.6.post5",
}
CHECKPOINT_SHA256 = (
    "b2377728e0cd748447e27a9583c1456121a20aff84da9468da14e9cb16cd2718"
)


def _write(path: Path, payload: bytes) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {
        "ref": str(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _write_json(path: Path, payload: dict[str, object]) -> dict[str, str]:
    return _write(path, (canonical_json(payload) + "\n").encode("utf-8"))


def _check_report(
    *,
    check_id: str,
    bindings: dict[str, str | None],
) -> dict[str, str]:
    output = _write(
        Path("evidence/outputs") / f"{check_id}.txt",
        f"{check_id}: passed\n".encode("utf-8"),
    )
    return _write_json(
        Path("evidence/reports") / f"{check_id}.json",
        {
            "schema_version": "0.1",
            "check_id": check_id,
            "status": "PASS",
            "runner": "pytest",
            "command": ["pytest", f"tests/integration/test_{check_id}.py", "-q"],
            "exit_code": 0,
            "assertion_count": 1,
            "runtime_versions": RUNTIME_VERSIONS,
            "bindings": bindings,
            "output": output,
        },
    )


def _adapter_evidence(config_ref: dict[str, str]) -> dict[str, object]:
    implementation = _write(
        Path("implementation.py"),
        b"def collect_gen_retry_rollout():\n    raise NotImplementedError\n",
    )
    bindings = {
        "config_sha256": config_ref["sha256"],
        "implementation_sha256": implementation["sha256"],
        "policy_checkpoint_sha256": CHECKPOINT_SHA256,
        "adapter_evidence_sha256": None,
        "rollout_batch_sha256": None,
        "advantage_batch_sha256": None,
    }
    checks = {
        check_id: _check_report(check_id=check_id, bindings=bindings)
        for check_id in ADAPTER_CHECK_IDS
    }
    return {
        "schema_version": "0.1",
        "evidence_id": "adapter_fixture_001",
        "status": "PASS",
        "config": config_ref,
        "policy_checkpoint_sha256": CHECKPOINT_SHA256,
        "implementation": implementation,
        "runtime_versions": RUNTIME_VERSIONS,
        "checks": checks,
        "evidence_artifacts": list(checks.values()),
    }


def _config_fixture(*, smoke_prompts: int = 32) -> tuple[Path, object, dict[str, str]]:
    config_path = Path("config.yaml")
    config_text = (
        ROOT / "configs/rl/naive_geneval2_grpo_v0_1.yaml"
    ).read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace("smoke_prompts: 32", f"smoke_prompts: {smoke_prompts}"),
        encoding="utf-8",
    )
    config = load_experiment_config(config_path)
    config_ref = {
        "ref": str(config_path),
        "sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
    }
    return config_path, config, config_ref


def _write_rollout_artifact(
    artifact_root: Path, ref: str, payload: bytes
) -> dict[str, str]:
    path = artifact_root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"ref": ref, "sha256": hashlib.sha256(payload).hexdigest()}


def _rollout_fixture(artifact_root: Path) -> dict[str, object]:
    sampling = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": -1,
        "max_action_tokens": 1400,
        "max_episode_assistant_tokens": 16000,
        "seed": 42,
    }
    candidates = []
    for index in range(4):
        candidate_id = f"candidate_{index}"
        response = _write_rollout_artifact(
            artifact_root,
            f"{candidate_id}/response.json",
            b'{"action":"submit_attempt"}',
        )
        reward = {
            "schema_version": "0.1",
            "reward_policy_id": "geneval2_terminal_outcome@0.1",
            "candidate_id": candidate_id,
            "outcome_kind": "success",
            "submitted_attempt_id": f"attempt_{index}",
            "submitted_score": {
                "pass_count": index,
                "atom_count": 3,
                "primary_score": 0.5,
            },
            "terminal_utility": index + 0.125,
            "invalid_action_penalty": 0.0,
            "total_return": index + 0.125,
        }
        candidates.append(
            {
                "candidate_id": candidate_id,
                "sample_sha256": response["sha256"],
                "outcome_kind": "success",
                "trainable_token_count": 1,
                "assistant_action_token_counts": [1],
                "sampled_response": response,
                "sampled_token_ids": _write_rollout_artifact(
                    artifact_root, f"{candidate_id}/ids.json", b"[11]"
                ),
                "assistant_action_mask": _write_rollout_artifact(
                    artifact_root, f"{candidate_id}/mask.json", b"[1]"
                ),
                "old_log_probs": _write_rollout_artifact(
                    artifact_root, f"{candidate_id}/old.json", b"[-0.2]"
                ),
                "reference_log_probs": _write_rollout_artifact(
                    artifact_root, f"{candidate_id}/reference.json", b"[-0.3]"
                ),
                "rollout_events": _write_rollout_artifact(
                    artifact_root,
                    f"{candidate_id}/events.jsonl",
                    b'{"event_id":"fixture"}\n',
                ),
                "reward_components": _write_rollout_artifact(
                    artifact_root,
                    f"{candidate_id}/reward.json",
                    canonical_json(reward).encode("utf-8"),
                ),
                "infrastructure_retries": [],
            }
        )
    return {
        "schema_version": "0.1",
        "batch_id": "smoke_batch_fixture",
        "planned_group_count": 1,
        "excluded_groups": [],
        "groups": [
            {
                "group_id": "group_001",
                "group_kind": "episode",
                "state_id": "planner_context_sha256:" + "3" * 64,
                "prompt_id": "prompt_001",
                "prompt_sha256": "1" * 64,
                "atom_set_sha256": "2" * 64,
                "canonical_state_sha256": "3" * 64,
                "sampling_policy_id": "flow1000_v9_selective_skill_full_s42",
                "policy_checkpoint": {
                    "ref": "runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42",
                    "sha256": CHECKPOINT_SHA256,
                },
                "policy_revision": "flow1000_v9_selective_skill_full_s42",
                "sampling_config": sampling,
                "sampling_config_sha256": hashlib.sha256(
                    canonical_json(sampling).encode("utf-8")
                ).hexdigest(),
                "candidates": candidates,
            }
        ],
    }


def test_runtime_gate_requires_typed_adapter_reports_and_rejects_empty_smoke(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path, config, config_ref = _config_fixture()
    adapter_path = Path("adapter_evidence.json")
    adapter_ref = _write_json(adapter_path, _adapter_evidence(config_ref))
    adapter_ready, _, adapter_sha256 = probe_live_adapter_evidence(
        path=adapter_path,
        config_path=config_path,
        config=config,
        package_versions=RUNTIME_VERSIONS,
        repository_root=tmp_path,
    )
    assert adapter_ready is True
    assert adapter_sha256 == adapter_ref["sha256"]

    rollout_ref = _write(Path("smoke/rollouts.json"), b"{}\n")
    advantage_ref = _write(Path("smoke/advantages.json"), b"{}\n")
    placeholder_check = _write(Path("smoke/check.json"), b"{}\n")
    smoke_path = Path("smoke_report.json")
    smoke = {
        "schema_version": "0.1",
        "report_id": "smoke_fixture_001",
        "stage": "smoke_32",
        "status": "PASS",
        "config": config_ref,
        "adapter_evidence": adapter_ref,
        "rollout_batch": rollout_ref,
        "advantage_batch": advantage_ref,
        "artifact_root": "smoke",
        "planned_group_count": 32,
        "valid_group_count": 32,
        "excluded_group_count": 0,
        "zero_variance_group_count": 0,
        "policy_invalid_candidate_count": 0,
        "total_candidate_count": 128,
        "checks": {check_id: placeholder_check for check_id in SMOKE_CHECK_IDS},
    }
    _write_json(smoke_path, smoke)
    smoke_ready, detail = probe_smoke_report(
        path=smoke_path,
        config_path=config_path,
        adapter_evidence_path=adapter_path,
        adapter_evidence_sha256=adapter_ref["sha256"],
        config=config,
        repository_root=tmp_path,
    )
    assert smoke_ready is False
    assert "required" in detail


def test_runtime_gate_recomputes_complete_smoke_chain(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path, config, config_ref = _config_fixture(smoke_prompts=1)
    adapter_payload = _adapter_evidence(config_ref)
    adapter_path = Path("adapter_evidence.json")
    adapter_ref = _write_json(adapter_path, adapter_payload)
    adapter_ready, _, adapter_sha256 = probe_live_adapter_evidence(
        path=adapter_path,
        config_path=config_path,
        config=config,
        package_versions=RUNTIME_VERSIONS,
        repository_root=tmp_path,
    )
    assert adapter_ready is True
    assert adapter_sha256 == adapter_ref["sha256"]

    artifact_root = Path("smoke")
    rollout_payload = _rollout_fixture(artifact_root)
    admission = admit_rollout_sample_batch(
        rollout_payload,
        artifact_root=artifact_root,
        config=config,
    )
    advantage_payload = build_advantage_batch(
        admission.candidate_return_batch,
        config=config.reward,
    )
    rollout_ref = _write_json(artifact_root / "rollouts.json", rollout_payload)
    advantage_ref = _write_json(
        artifact_root / "advantages.json", advantage_payload
    )
    smoke_bindings = {
        "config_sha256": config_ref["sha256"],
        "implementation_sha256": adapter_payload["implementation"]["sha256"],
        "policy_checkpoint_sha256": CHECKPOINT_SHA256,
        "adapter_evidence_sha256": adapter_ref["sha256"],
        "rollout_batch_sha256": rollout_ref["sha256"],
        "advantage_batch_sha256": advantage_ref["sha256"],
    }
    smoke_checks = {
        check_id: _check_report(check_id=check_id, bindings=smoke_bindings)
        for check_id in SMOKE_CHECK_IDS
    }
    smoke = {
        "schema_version": "0.1",
        "report_id": "smoke_fixture_complete",
        "stage": "smoke_32",
        "status": "PASS",
        "config": config_ref,
        "adapter_evidence": adapter_ref,
        "rollout_batch": rollout_ref,
        "advantage_batch": advantage_ref,
        "artifact_root": str(artifact_root),
        "planned_group_count": 1,
        "valid_group_count": 1,
        "excluded_group_count": 0,
        "zero_variance_group_count": 0,
        "policy_invalid_candidate_count": 0,
        "total_candidate_count": 4,
        "checks": smoke_checks,
    }
    smoke_path = Path("smoke_report.json")
    _write_json(smoke_path, smoke)
    smoke_ready, detail = probe_smoke_report(
        path=smoke_path,
        config_path=config_path,
        adapter_evidence_path=adapter_path,
        adapter_evidence_sha256=adapter_ref["sha256"],
        config=config,
        repository_root=tmp_path,
    )
    assert smoke_ready is True, detail


def test_runtime_gate_rejects_repository_escape(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path, config, config_ref = _config_fixture()
    payload = _adapter_evidence(config_ref)
    outside = tmp_path.parent / f"{tmp_path.name}_outside.py"
    outside.write_text("outside = True\n", encoding="utf-8")
    payload["implementation"] = {
        "ref": f"../{outside.name}",
        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
    }
    adapter_path = Path("adapter_evidence.json")
    _write_json(adapter_path, payload)
    adapter_ready, detail, _ = probe_live_adapter_evidence(
        path=adapter_path,
        config_path=config_path,
        config=config,
        package_versions=RUNTIME_VERSIONS,
        repository_root=tmp_path,
    )
    assert adapter_ready is False
    assert "escapes repository root" in detail
