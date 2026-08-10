from __future__ import annotations

import pytest

from gen_retry.rl.credit import (
    AttemptScore,
    CreditCandidate,
    PivotSignals,
    RewardConfig,
    combine_group_advantages,
    detect_pivot_reasons,
    image_transition_reward,
    invalid_action_reward,
    pivot_submit_reward,
    query_skill_credit,
    terminal_submit_reward,
)


def score(pass_count: int, gm: float, atom_count: int = 5) -> AttemptScore:
    return AttemptScore(
        pass_count=pass_count,
        atom_count=atom_count,
        primary_score=gm,
    )


def test_geneval2_utility_preserves_pass_count_priority() -> None:
    config = RewardConfig()
    fewer_passes_high_gm = score(3, 1.0).utility(
        gm_tie_break_scale=config.gm_tie_break_scale
    )
    more_passes_low_gm = score(4, 0.0).utility(
        gm_tie_break_scale=config.gm_tie_break_scale
    )
    assert more_passes_low_gm > fewer_passes_high_gm


def test_image_transition_distinguishes_fix_and_regression() -> None:
    reward = image_transition_reward(
        action_type="edit_image",
        source=score(3, 0.40),
        best_before=score(3, 0.40),
        result=score(3, 0.60),
        fixed_constraint_ids=["c_004"],
        regressed_constraint_ids=["c_002"],
        strict_no_progress=False,
        charge_image_cost=True,
        config=RewardConfig(),
    )
    assert reward.fixed_fraction == 0.5
    assert reward.regressed_fraction == pytest.approx(1.0 / 3.0)
    assert reward.gm_tie_break_delta == pytest.approx(0.20)
    assert reward.comparison_basis == "source"
    assert reward.best_progress == pytest.approx(0.01)
    assert reward.total == pytest.approx(
        0.5 - 1.25 / 3 + 0.02 + 0.5 * 0.01 - 0.02
    )


def test_transition_rejects_inconsistent_environment_facts() -> None:
    with pytest.raises(ValueError, match="disagrees"):
        image_transition_reward(
            action_type="edit_image",
            source=score(3, 0.40),
            best_before=score(3, 0.40),
            result=score(5, 0.80),
            fixed_constraint_ids=["c_004"],
            regressed_constraint_ids=[],
            strict_no_progress=False,
            charge_image_cost=True,
            config=RewardConfig(),
        )


def test_weak_historical_source_repair_is_penalized_if_still_below_best() -> None:
    reward = image_transition_reward(
        action_type="edit_image",
        source=score(1, 0.20),
        best_before=score(4, 0.40),
        result=score(2, 0.50),
        fixed_constraint_ids=["c_002"],
        regressed_constraint_ids=[],
        strict_no_progress=False,
        charge_image_cost=True,
        config=RewardConfig(best_progress_weight=1.0),
    )
    assert reward.intervention_credit > 0.0
    assert reward.best_progress < 0.0
    assert reward.total < 0.0


def test_initial_generation_gets_quality_credit_without_fake_transition() -> None:
    reward = image_transition_reward(
        action_type="generate_image",
        source=None,
        best_before=None,
        result=score(4, 0.50),
        fixed_constraint_ids=[],
        regressed_constraint_ids=[],
        strict_no_progress=False,
        charge_image_cost=True,
        config=RewardConfig(),
    )
    assert reward.comparison_basis == "initial"
    assert reward.intervention_credit == 0.0
    assert reward.best_progress > 0.0


def test_episode_process_return_can_defer_image_cost_to_terminal() -> None:
    reward = image_transition_reward(
        action_type="generate_image",
        source=None,
        best_before=None,
        result=score(4, 0.50),
        fixed_constraint_ids=[],
        regressed_constraint_ids=[],
        strict_no_progress=False,
        charge_image_cost=False,
        config=RewardConfig(),
    )
    assert reward.image_cost == 0.0


def test_terminal_reward_penalizes_wrong_historical_submission() -> None:
    reward = terminal_submit_reward(
        submitted=score(3, 0.90),
        environment_best=score(4, 0.10),
        image_call_count=4,
        config=RewardConfig(),
    )
    assert reward.submission_regret > 0.0
    assert reward.image_cost == pytest.approx(0.08)
    assert reward.all_pass_bonus == 0.0
    assert reward.total < reward.submitted_utility


def test_pivot_submit_reward_is_normalized_to_local_scale() -> None:
    reward = pivot_submit_reward(
        submitted=score(4, 0.50),
        environment_best=score(4, 0.50),
        image_call_count=3,
        config=RewardConfig(),
    )
    assert 0.0 < reward < 1.0


def test_query_skill_splits_delayed_credit_without_duplication() -> None:
    reward = query_skill_credit(
        downstream_image_credit=1.0,
        repeated_query=False,
        config=RewardConfig(),
    )
    assert reward.query_credit == pytest.approx(0.19)
    assert reward.downstream_credit == pytest.approx(0.80)
    assert reward.total_after_cost == pytest.approx(0.99)


def test_pivot_detection_uses_environment_and_policy_signals() -> None:
    reasons = detect_pivot_reasons(
        PivotSignals(
            regressed_constraint_count=1,
            latest_attempt_id="a_003",
            best_attempt_id="a_001",
            consecutive_no_progress=2,
            remaining_image_budget=1,
            action_margin=0.05,
        )
    )
    assert reasons == (
        "regression",
        "latest_best_divergence",
        "repeated_no_progress",
        "low_remaining_budget",
        "action_uncertainty",
    )


def test_group_advantage_requires_same_state_on_policy_candidates() -> None:
    config = RewardConfig(pivot_group_terminal_weight=0.25)
    candidates = (
        CreditCandidate(
            candidate_id="c1",
            state_id="s1",
            sampling_policy_id="p1",
            sample_sha256="1" * 64,
            rollout_sample_sha256="a" * 64,
            reward_components_sha256="b" * 64,
            trainable_token_count=10,
            on_policy=True,
            outcome_kind="success",
            local_return=2.0,
            episode_return=4.0,
        ),
        CreditCandidate(
            candidate_id="c2",
            state_id="s1",
            sampling_policy_id="p1",
            sample_sha256="2" * 64,
            rollout_sample_sha256="c" * 64,
            reward_components_sha256="d" * 64,
            trainable_token_count=10,
            on_policy=True,
            outcome_kind="success",
            local_return=0.0,
            episode_return=2.0,
        ),
    )
    advantages = combine_group_advantages(
        candidates, group_kind="pivot", config=config
    )
    assert advantages.eligible_for_policy_loss is True
    assert advantages.candidates[0].combined_advantage == pytest.approx(1.0)
    assert advantages.candidates[1].combined_advantage == pytest.approx(-1.0)

    off_policy = CreditCandidate(
        candidate_id="c3",
        state_id="s1",
        sampling_policy_id="p1",
        sample_sha256="3" * 64,
        rollout_sample_sha256="e" * 64,
        reward_components_sha256="f" * 64,
        trainable_token_count=10,
        on_policy=False,
        outcome_kind="success",
        local_return=1.0,
        episode_return=1.0,
    )
    with pytest.raises(ValueError, match="on-policy"):
        combine_group_advantages(
            (candidates[0], off_policy), group_kind="pivot", config=config
        )


def test_zero_variance_group_is_not_eligible_for_policy_loss() -> None:
    candidates = tuple(
        CreditCandidate(
            candidate_id=f"c{index}",
            state_id="s1",
            sampling_policy_id="p1",
            sample_sha256=str(index) * 64,
            rollout_sample_sha256="a" * 64,
            reward_components_sha256="b" * 64,
            trainable_token_count=10,
            on_policy=True,
            outcome_kind="success",
            local_return=1.0,
            episode_return=2.0,
        )
        for index in (1, 2)
    )
    result = combine_group_advantages(
        candidates, group_kind="pivot", config=RewardConfig()
    )
    assert result.eligible_for_policy_loss is False
    assert all(item.combined_advantage == 0.0 for item in result.candidates)


def test_infrastructure_failure_cannot_enter_credit_group() -> None:
    with pytest.raises(ValueError, match="tracked outside"):
        CreditCandidate(
            candidate_id="c1",
            state_id="s1",
            sampling_policy_id="p1",
            sample_sha256="1" * 64,
            rollout_sample_sha256="a" * 64,
            reward_components_sha256="b" * 64,
            trainable_token_count=10,
            on_policy=True,
            outcome_kind="infrastructure_failure",
            local_return=0.0,
            episode_return=0.0,
        )


def test_policy_invalid_sample_receives_creditable_negative_return() -> None:
    config = RewardConfig(invalid_action_penalty=1.5)
    penalty = invalid_action_reward(config=config)
    candidate = CreditCandidate(
        candidate_id="invalid_1",
        state_id="s1",
        sampling_policy_id="p1",
        sample_sha256="4" * 64,
        rollout_sample_sha256="c" * 64,
        reward_components_sha256="d" * 64,
        trainable_token_count=8,
        on_policy=True,
        outcome_kind="policy_invalid",
        local_return=penalty,
        episode_return=penalty,
    )
    assert candidate.local_return == -1.5


def test_naive_reward_policy_rejects_hidden_process_shaping() -> None:
    with pytest.raises(ValueError, match="forbids reward shaping"):
        RewardConfig(
            reward_policy_id="geneval2_terminal_outcome",
            fixed_weight=0.1,
            regression_weight=0.0,
            gm_transition_weight=0.0,
            best_progress_weight=0.0,
            no_progress_penalty=0.0,
            image_call_cost=0.0,
            all_pass_bonus=0.0,
            submit_regret_weight=0.0,
            query_skill_cost=0.0,
            repeated_query_penalty=0.0,
            query_delayed_credit_fraction=0.0,
            episode_group_terminal_weight=1.0,
        )
