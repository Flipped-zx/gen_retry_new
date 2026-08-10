from __future__ import annotations

import pytest

from gen_retry.rl.objective import ObjectiveConfig, clipped_action_objective


def test_action_objective_masks_environment_tokens() -> None:
    config = ObjectiveConfig(reference_kl_coefficient=0.02)
    baseline = clipped_action_objective(
        new_log_probs=[-1.0, -0.8, -5.0],
        old_log_probs=[-1.1, -0.9, -1.0],
        reference_log_probs=[-1.2, -1.0, -1.0],
        assistant_action_mask=[1, 1, 0],
        advantage=0.75,
        config=config,
    )
    changed_observation = clipped_action_objective(
        new_log_probs=[-1.0, -0.8, 20.0],
        old_log_probs=[-1.1, -0.9, -20.0],
        reference_log_probs=[-1.2, -1.0, 10.0],
        assistant_action_mask=[1, 1, 0],
        advantage=0.75,
        config=config,
    )
    assert baseline == changed_observation
    assert baseline.trained_token_count == 2


def test_action_objective_applies_asymmetric_clipping_and_active_kl() -> None:
    result = clipped_action_objective(
        new_log_probs=[0.5],
        old_log_probs=[0.0],
        reference_log_probs=[0.0],
        assistant_action_mask=[1],
        advantage=1.0,
        config=ObjectiveConfig(
            clip_ratio_low=0.20,
            clip_ratio_high=0.28,
            reference_kl_coefficient=0.02,
        ),
    )
    assert result.policy_loss == pytest.approx(-1.28)
    assert result.sampled_reverse_kl > 0.0
    assert result.total_loss > result.policy_loss
    assert result.clip_fraction == 1.0


def test_objective_rejects_empty_action_mask() -> None:
    with pytest.raises(ValueError, match="at least one token"):
        clipped_action_objective(
            new_log_probs=[0.0],
            old_log_probs=[0.0],
            reference_log_probs=[0.0],
            assistant_action_mask=[0],
            advantage=1.0,
            config=ObjectiveConfig(),
        )


def test_v01_rejects_inert_reference_kl() -> None:
    with pytest.raises(ValueError, match="active reference-policy KL"):
        ObjectiveConfig(reference_kl_coefficient=0.0)
