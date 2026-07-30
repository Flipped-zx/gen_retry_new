from __future__ import annotations

import pytest

from gen_retry.phase5.paired_rollout_comparison import (
    _compare_episode,
    _policy_behavior,
)


def _episode(
    *,
    best_attempt_id: str,
    attempts: list[dict],
    submitted_gm: float,
) -> dict:
    best = next(
        attempt
        for attempt in attempts
        if attempt["attempt_id"] == best_attempt_id
    )
    return {
        "episode_id": "phase3_ep_001",
        "prompt_id": "prompt_001",
        "difficulty_tier": "hard",
        "constraint_count": 4,
        "attempt_count": len(attempts),
        "initial_pass_count": attempts[0]["pass_count"],
        "best_pass_count": best["pass_count"],
        "first_agent_geneval2_score": attempts[0]["geneval2_score"],
        "submitted_geneval2_score": submitted_gm,
        "submitted_geneval2_am": 0.8,
        "submitted_attempt_id": best_attempt_id,
        "best_attempt_id": best_attempt_id,
        "attempts": attempts,
    }


def test_policy_behavior_detects_pass_primary_rejection_and_rollback() -> None:
    attempts = [
        {
            "attempt_id": "a_000",
            "action": "generate_image",
            "source_attempt_id": None,
            "pass_count": 3,
            "geneval2_score": 0.40,
        },
        {
            "attempt_id": "a_001",
            "action": "edit_image",
            "source_attempt_id": "a_000",
            "pass_count": 2,
            "geneval2_score": 0.60,
        },
        {
            "attempt_id": "a_002",
            "action": "edit_image",
            "source_attempt_id": "a_000",
            "pass_count": 3,
            "geneval2_score": 0.50,
        },
    ]

    behavior = _policy_behavior(
        _episode(
            best_attempt_id="a_002",
            attempts=attempts,
            submitted_gm=0.50,
        )
    )

    assert behavior == {
        "gm_tiebreak_changed_best": True,
        "gm_tiebreak_best_update_count": 1,
        "higher_gm_lower_pass_rejection_count": 1,
        "rollback_to_historical_source_count": 1,
        "regenerate_after_initial_count": 0,
    }


def test_paired_outcome_uses_pass_count_before_gm() -> None:
    attempts = [
        {
            "attempt_id": "a_000",
            "action": "generate_image",
            "source_attempt_id": None,
            "pass_count": 3,
            "geneval2_score": 0.20,
        }
    ]
    baseline = _episode(
        best_attempt_id="a_000",
        attempts=attempts,
        submitted_gm=0.20,
    )
    candidate_attempts = [
        {
            "attempt_id": "a_000",
            "action": "generate_image",
            "source_attempt_id": None,
            "pass_count": 2,
            "geneval2_score": 0.80,
        }
    ]
    candidate = _episode(
        best_attempt_id="a_000",
        attempts=candidate_attempts,
        submitted_gm=0.80,
    )

    comparison = _compare_episode(
        baseline=baseline,
        candidate=candidate,
    )

    assert comparison["paired_outcome"] == "negative_fewer_atoms"


def test_paired_comparison_rejects_mismatched_prompt_ids() -> None:
    attempts = [
        {
            "attempt_id": "a_000",
            "action": "generate_image",
            "source_attempt_id": None,
            "pass_count": 3,
            "geneval2_score": 0.20,
        }
    ]
    baseline = _episode(
        best_attempt_id="a_000",
        attempts=attempts,
        submitted_gm=0.20,
    )
    candidate = {
        **baseline,
        "prompt_id": "different_prompt",
    }

    with pytest.raises(ValueError, match="prompt IDs"):
        _compare_episode(
            baseline=baseline,
            candidate=candidate,
        )
