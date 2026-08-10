"""Reward and credit-assignment primitives for Gen-Retry policy training."""

from gen_retry.rl.admission import (
    RolloutAdmission,
    admit_rollout_sample_batch,
)

from gen_retry.rl.credit import (
    AttemptScore,
    CreditCandidate,
    GroupAdvantageResult,
    PivotSignals,
    RewardConfig,
    combine_group_advantages,
    detect_pivot_reasons,
    image_transition_reward,
    invalid_action_reward,
    query_skill_credit,
    pivot_submit_reward,
    terminal_submit_reward,
)
from gen_retry.rl.objective import (
    ActionObjective,
    ObjectiveConfig,
    clipped_action_objective,
)
from gen_retry.rl.optimizer import (
    OptimizerBatch,
    OptimizerSample,
    optimizer_metrics,
    prepare_optimizer_batch,
)

__all__ = [
    "RolloutAdmission",
    "admit_rollout_sample_batch",
    "AttemptScore",
    "CreditCandidate",
    "GroupAdvantageResult",
    "PivotSignals",
    "RewardConfig",
    "combine_group_advantages",
    "detect_pivot_reasons",
    "image_transition_reward",
    "invalid_action_reward",
    "query_skill_credit",
    "pivot_submit_reward",
    "terminal_submit_reward",
    "ActionObjective",
    "ObjectiveConfig",
    "clipped_action_objective",
    "OptimizerBatch",
    "OptimizerSample",
    "optimizer_metrics",
    "prepare_optimizer_batch",
]
