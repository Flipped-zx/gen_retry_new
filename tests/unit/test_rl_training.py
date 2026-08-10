from __future__ import annotations

import json
import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from gen_retry.rl.admission import admit_rollout_sample_batch
from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.credit import RewardConfig
from gen_retry.rl.optimizer import optimizer_metrics, prepare_optimizer_batch
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.rl.training import (
    build_advantage_batch,
    load_objective_config,
    load_reward_config,
)


ROOT = Path(__file__).resolve().parents[2]


def _write_artifact(root: Path, ref: str, payload: bytes) -> dict[str, str]:
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"ref": ref, "sha256": hashlib.sha256(payload).hexdigest()}


def _rollout_admission_fixture(tmp_path: Path) -> dict[str, object]:
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
        prefix = f"candidate_{index}"
        response = _write_artifact(
            tmp_path, f"{prefix}/response.json", b'{"action":"submit_attempt"}'
        )
        candidates.append(
            {
                "candidate_id": prefix,
                "sample_sha256": response["sha256"],
                "outcome_kind": "success",
                "trainable_token_count": 2,
                "assistant_action_token_counts": [2],
                "sampled_response": response,
                "sampled_token_ids": _write_artifact(
                    tmp_path, f"{prefix}/ids.json", b"[11,12,13]"
                ),
                "assistant_action_mask": _write_artifact(
                    tmp_path, f"{prefix}/mask.json", b"[0,1,1]"
                ),
                "old_log_probs": _write_artifact(
                    tmp_path, f"{prefix}/old.json", b"[-0.3,-0.2,-0.1]"
                ),
                "reference_log_probs": _write_artifact(
                    tmp_path, f"{prefix}/reference.json", b"[-0.4,-0.3,-0.2]"
                ),
                "rollout_events": _write_artifact(
                    tmp_path, f"{prefix}/events.jsonl", b'{"event_id":"e1"}\n'
                ),
                "reward_components": _write_artifact(
                    tmp_path,
                    f"{prefix}/reward.json",
                    canonical_json(
                        {
                            "schema_version": "0.1",
                            "reward_policy_id": "geneval2_terminal_outcome@0.1",
                            "candidate_id": prefix,
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
                    ).encode("utf-8"),
                ),
                "infrastructure_retries": [],
            }
        )
    return {
        "schema_version": "0.1",
        "batch_id": "batch_001",
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
                    "sha256": "b2377728e0cd748447e27a9583c1456121a20aff84da9468da14e9cb16cd2718",
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


def _experiment_config():
    return load_experiment_config(
        ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    )


def test_build_advantage_batch_is_group_relative_and_hash_bound() -> None:
    fixture = (
        ROOT
        / "tests"
        / "fixtures"
        / "rl"
        / "candidate_return_batch_minimal.json"
    )
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    result = build_advantage_batch(payload, config=RewardConfig())
    candidates = result["groups"][0]["candidates"]
    assert candidates[0]["combined_advantage"] == pytest.approx(1.0)
    assert candidates[1]["combined_advantage"] == pytest.approx(-1.0)
    assert len(result["source_batch_sha256"]) == 64
    assert result["groups"][0]["advantage_stats"][
        "eligible_for_policy_loss"
    ]


def test_canonical_rl_config_loads() -> None:
    config = load_reward_config(
        ROOT / "configs" / "rl" / "atomic_branch_grpo_v0_1.yaml"
    )
    assert config.reward_policy_id == "geneval2_atomic_branch_credit"
    assert config.regression_weight > config.fixed_weight
    objective = load_objective_config(
        ROOT / "configs" / "rl" / "atomic_branch_grpo_v0_1.yaml"
    )
    assert objective.use_reference_kl is True
    assert objective.clip_ratio_high > objective.clip_ratio_low


def test_naive_grpo_config_is_strictly_terminal_only() -> None:
    path = ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    config = load_reward_config(path)
    assert config.reward_policy_id == "geneval2_terminal_outcome"
    assert config.episode_group_terminal_weight == 1.0
    assert config.fixed_weight == 0.0
    assert config.submit_regret_weight == 0.0


def test_advantage_batch_rejects_reward_policy_mismatch() -> None:
    fixture = (
        ROOT
        / "tests"
        / "fixtures"
        / "rl"
        / "candidate_return_batch_minimal.json"
    )
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    config = load_reward_config(
        ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    )
    with pytest.raises(ValueError, match="does not match"):
        build_advantage_batch(payload, config=config)


def test_naive_grpo_advantage_uses_only_episode_return() -> None:
    fixture = (
        ROOT
        / "tests"
        / "fixtures"
        / "rl"
        / "candidate_return_batch_minimal.json"
    )
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload["reward_policy_id"] = "geneval2_terminal_outcome@0.1"
    payload["groups"][0]["group_kind"] = "episode"
    payload["groups"][0]["candidates"][0]["local_return"] = -100.0
    payload["groups"][0]["candidates"][1]["local_return"] = 100.0
    config = load_reward_config(
        ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    )
    result = build_advantage_batch(payload, config=config)
    candidates = result["groups"][0]["candidates"]
    assert candidates[0]["combined_advantage"] == pytest.approx(1.0)
    assert candidates[1]["combined_advantage"] == pytest.approx(-1.0)
    assert result["groups"][0]["advantage_stats"]["terminal_weight"] == 1.0


def test_training_admission_hash_binds_rollout_and_returns(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    admission = admit_rollout_sample_batch(
        rollout,
        artifact_root=tmp_path,
        config=_experiment_config(),
    )
    assert admission.batch_id == "batch_001"
    assert admission.group_count == 1
    assert admission.candidate_count == 4
    assert admission.candidate_return_batch["groups"][0]["rollout_group_sha256"]


def test_training_admission_rejects_artifact_tampering(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    (tmp_path / "candidate_0" / "old.json").write_text("[0.0]", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        admit_rollout_sample_batch(
            rollout, artifact_root=tmp_path, config=_experiment_config()
        )


def test_training_admission_rejects_stale_policy(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    rollout["groups"][0]["policy_revision"] = "stale"
    with pytest.raises(ValueError, match="stale or unexpected policy revision"):
        admit_rollout_sample_batch(
            rollout, artifact_root=tmp_path, config=_experiment_config()
        )


def test_training_admission_rejects_unbound_sample_hash(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    rollout["groups"][0]["candidates"][0]["sample_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not bind sampled response"):
        admit_rollout_sample_batch(
            rollout, artifact_root=tmp_path, config=_experiment_config()
        )


def test_training_admission_allows_duplicate_sampled_actions(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    candidates = rollout["groups"][0]["candidates"]
    candidates[1]["sampled_response"] = candidates[0]["sampled_response"]
    candidates[1]["sample_sha256"] = candidates[0]["sample_sha256"]
    admission = admit_rollout_sample_batch(
        rollout, artifact_root=tmp_path, config=_experiment_config()
    )
    assert admission.candidate_count == 4


def test_training_admission_enforces_valid_group_fraction(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    rollout["planned_group_count"] = 2
    rollout["excluded_groups"] = [
        {
            "group_id": "group_excluded_001",
            "prompt_id": "prompt_excluded_001",
            "failure_kind": "infrastructure_failure",
            "component": "image_backend",
            "failure_record": _write_artifact(
                tmp_path,
                "excluded/failure.json",
                b'{"status":"failed_after_retries"}',
            ),
        }
    ]
    with pytest.raises(ValueError, match="valid-group fraction"):
        admit_rollout_sample_batch(
            rollout, artifact_root=tmp_path, config=_experiment_config()
        )


def test_training_admission_enforces_per_action_token_limit(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    rollout["groups"][0]["sampling_config"]["max_action_tokens"] = 1
    rollout["groups"][0]["sampling_config_sha256"] = hashlib.sha256(
        canonical_json(rollout["groups"][0]["sampling_config"]).encode("utf-8")
    ).hexdigest()
    config = _experiment_config()
    config = replace(
        config,
        rollout=replace(config.rollout, max_action_tokens=1),
    )
    with pytest.raises(ValueError, match="exceeds max_action_tokens"):
        admit_rollout_sample_batch(
            rollout, artifact_root=tmp_path, config=config
        )


def test_optimizer_batch_rejoins_admitted_token_provenance(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    config = _experiment_config()
    admission = admit_rollout_sample_batch(
        rollout, artifact_root=tmp_path, config=config
    )
    advantage = build_advantage_batch(
        admission.candidate_return_batch,
        config=config.reward,
    )
    optimizer_batch = prepare_optimizer_batch(
        rollout_payload=rollout,
        advantage_payload=advantage,
        artifact_root=tmp_path,
        config=config,
    )
    assert optimizer_batch.eligible_group_count == 1
    assert optimizer_batch.admitted_candidate_count == 4
    assert len(optimizer_batch.samples) == 4
    assert optimizer_batch.trained_token_count == 8
    assert optimizer_metrics(optimizer_batch)[
        "rl/zero_variance_group_fraction"
    ] == 0.0
    assert optimizer_metrics(optimizer_batch)["rl/admitted_candidates"] == 4


def test_optimizer_batch_rejects_advantage_drift(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    config = _experiment_config()
    admission = admit_rollout_sample_batch(
        rollout, artifact_root=tmp_path, config=config
    )
    advantage = build_advantage_batch(
        admission.candidate_return_batch,
        config=config.reward,
    )
    advantage["groups"][0]["candidates"][0]["combined_advantage"] = 0.0
    with pytest.raises(ValueError, match="does not exactly match"):
        prepare_optimizer_batch(
            rollout_payload=rollout,
            advantage_payload=advantage,
            artifact_root=tmp_path,
            config=config,
        )


def test_optimizer_batch_enforces_zero_variance_stage_gate(tmp_path: Path) -> None:
    rollout = _rollout_admission_fixture(tmp_path)
    for candidate in rollout["groups"][0]["candidates"]:
        reward_path = tmp_path / candidate["reward_components"]["ref"]
        reward = json.loads(reward_path.read_text(encoding="utf-8"))
        reward["submitted_score"]["pass_count"] = 0
        reward["terminal_utility"] = 0.125
        reward["total_return"] = 0.125
        candidate["reward_components"] = _write_artifact(
            tmp_path,
            candidate["reward_components"]["ref"],
            canonical_json(reward).encode("utf-8"),
        )
    config = _experiment_config()
    admission = admit_rollout_sample_batch(
        rollout, artifact_root=tmp_path, config=config
    )
    advantage = build_advantage_batch(
        admission.candidate_return_batch,
        config=config.reward,
    )
    with pytest.raises(ValueError, match="zero-variance group fraction"):
        prepare_optimizer_batch(
            rollout_payload=rollout,
            advantage_payload=advantage,
            artifact_root=tmp_path,
            config=config,
        )
