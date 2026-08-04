from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.domain.score_policy import (
    candidate_is_better,
    canonical_primary_score,
    legacy_score_policy,
    primary_score_policy,
    planner_context_version,
    planner_context_version_is_compatible,
    score_policy_from_task_payload,
    soft_tifa_geometric_mean,
)
from gen_retry.phase3.live_runner import Phase3LiveRunner
from gen_retry.runtime.json_canonical import canonical_json


ROOT = Path(__file__).resolve().parents[2]


def test_soft_tifa_gm_uses_canonical_flow_dppo_formula() -> None:
    assert soft_tifa_geometric_mean([1.0, 0.25]) == pytest.approx(0.5)
    assert soft_tifa_geometric_mean([1.0, 0.0]) == pytest.approx(1e-150)
    assert canonical_primary_score(
        [
            {"constraint_id": "c_002", "confidence": 0.25},
            {"constraint_id": "c_001", "confidence": 1.0},
        ]
    )["value"] == pytest.approx(0.5)


def test_pass_count_dominates_primary_score() -> None:
    assert not candidate_is_better(
        candidate_pass_count=3,
        candidate_primary_score=0.99,
        current_pass_count=4,
        current_primary_score=0.10,
        score_policy=primary_score_policy(),
    )


def test_primary_score_breaks_only_equal_pass_count_ties() -> None:
    assert candidate_is_better(
        candidate_pass_count=4,
        candidate_primary_score=0.70,
        current_pass_count=4,
        current_primary_score=0.60,
        score_policy=primary_score_policy(),
    )
    assert not candidate_is_better(
        candidate_pass_count=4,
        candidate_primary_score=0.60,
        current_pass_count=4,
        current_primary_score=0.60,
        score_policy=primary_score_policy(),
    )


def test_primary_score_policy_prefers_v0_7_and_replays_v0_6() -> None:
    policy = primary_score_policy()

    assert planner_context_version(policy) == "0.7"
    assert planner_context_version_is_compatible(policy, "0.6")
    assert planner_context_version_is_compatible(policy, "0.7")
    assert not planner_context_version_is_compatible(policy, "0.5")


def test_missing_score_policy_replays_with_legacy_ordering() -> None:
    assert score_policy_from_task_payload({}) == legacy_score_policy()
    assert not candidate_is_better(
        candidate_pass_count=4,
        candidate_primary_score=0.90,
        current_pass_count=4,
        current_primary_score=0.10,
        score_policy=legacy_score_policy(),
    )


def test_runner_score_policy_lock_accepts_match_and_rejects_drift(
    tmp_path: Path,
) -> None:
    task_event = json.loads(
        (
            ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl"
        ).read_text(encoding="utf-8").splitlines()[0]
    )
    task_event["payload"]["score_policy"] = primary_score_policy()
    (tmp_path / "events.jsonl").write_text(
        canonical_json(task_event) + "\n",
        encoding="utf-8",
    )
    plan = {
        "planner_context_schema_version": "0.6",
        "score_policy": primary_score_policy(),
    }
    (tmp_path / "rollout_plan.json").write_text(
        canonical_json(plan) + "\n",
        encoding="utf-8",
    )
    runner = object.__new__(Phase3LiveRunner)

    runner._validate_score_policy_lock(tmp_path)

    plan["planner_context_schema_version"] = "0.5"
    (tmp_path / "rollout_plan.json").write_text(
        canonical_json(plan) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="score policy mismatch"):
        runner._validate_score_policy_lock(tmp_path)


@pytest.mark.parametrize("probabilities", [[], [float("nan")], [-0.1], [1.1]])
def test_soft_tifa_gm_rejects_invalid_probabilities(
    probabilities: list[float],
) -> None:
    with pytest.raises(ValueError):
        soft_tifa_geometric_mean(probabilities)
