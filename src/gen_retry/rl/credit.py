from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REWARD_POLICY_ID = "geneval2_atomic_branch_credit"
NAIVE_REWARD_POLICY_ID = "geneval2_terminal_outcome"
REWARD_POLICY_VERSION = "0.1"
SUPPORTED_REWARD_POLICY_IDS = {
    REWARD_POLICY_ID,
    NAIVE_REWARD_POLICY_ID,
}


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


@dataclass(frozen=True)
class AttemptScore:
    """The environment-owned Geneval2 score for one image Attempt."""

    pass_count: int
    atom_count: int
    primary_score: float

    def __post_init__(self) -> None:
        if isinstance(self.pass_count, bool) or not isinstance(self.pass_count, int):
            raise ValueError("pass_count must be an integer")
        if isinstance(self.atom_count, bool) or not isinstance(self.atom_count, int):
            raise ValueError("atom_count must be an integer")
        if self.atom_count <= 0:
            raise ValueError("atom_count must be positive")
        if not 0 <= self.pass_count <= self.atom_count:
            raise ValueError("pass_count must be in [0, atom_count]")
        primary_score = _finite_number(self.primary_score, "primary_score")
        if not 0.0 <= primary_score <= 1.0:
            raise ValueError("primary_score must be in [0, 1]")
        object.__setattr__(self, "primary_score", primary_score)

    def utility(self, *, gm_tie_break_scale: float) -> float:
        """Embed the canonical lexicographic comparator in one scalar.

        A scale strictly below one guarantees that one additional passed atom
        dominates every possible Soft-TIFA GM difference. Group normalization
        must only compare candidates for the same prompt/atom count.
        """

        scale = _finite_number(gm_tie_break_scale, "gm_tie_break_scale")
        if not 0.0 < scale < 1.0:
            raise ValueError("gm_tie_break_scale must be in (0, 1)")
        return self.pass_count + scale * self.primary_score


@dataclass(frozen=True)
class RewardConfig:
    reward_policy_id: str = REWARD_POLICY_ID
    reward_policy_version: str = REWARD_POLICY_VERSION
    gm_tie_break_scale: float = 0.25
    fixed_weight: float = 1.0
    regression_weight: float = 1.25
    gm_transition_weight: float = 0.10
    best_progress_weight: float = 0.50
    no_progress_penalty: float = 0.10
    image_call_cost: float = 0.02
    all_pass_bonus: float = 0.25
    submit_regret_weight: float = 1.0
    query_skill_cost: float = 0.01
    repeated_query_penalty: float = 0.05
    invalid_action_penalty: float = 1.00
    query_delayed_credit_fraction: float = 0.20
    episode_group_terminal_weight: float = 0.35
    pivot_group_terminal_weight: float = 0.0

    def __post_init__(self) -> None:
        if self.reward_policy_id not in SUPPORTED_REWARD_POLICY_IDS:
            raise ValueError(f"unsupported reward policy: {self.reward_policy_id}")
        if self.reward_policy_version != REWARD_POLICY_VERSION:
            raise ValueError(
                f"unsupported reward policy version: {self.reward_policy_version}"
            )
        if not 0.0 < _finite_number(
            self.gm_tie_break_scale, "gm_tie_break_scale"
        ) < 1.0:
            raise ValueError("gm_tie_break_scale must be in (0, 1)")
        for name in (
            "fixed_weight",
            "regression_weight",
            "gm_transition_weight",
            "best_progress_weight",
            "no_progress_penalty",
            "image_call_cost",
            "all_pass_bonus",
            "submit_regret_weight",
            "query_skill_cost",
            "repeated_query_penalty",
            "invalid_action_penalty",
        ):
            if _finite_number(getattr(self, name), name) < 0.0:
                raise ValueError(f"{name} must be non-negative")
        for name in (
            "query_delayed_credit_fraction",
            "episode_group_terminal_weight",
            "pivot_group_terminal_weight",
        ):
            value = _finite_number(getattr(self, name), name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.reward_policy_id == NAIVE_REWARD_POLICY_ID:
            shaping_fields = (
                "fixed_weight",
                "regression_weight",
                "gm_transition_weight",
                "best_progress_weight",
                "no_progress_penalty",
                "image_call_cost",
                "all_pass_bonus",
                "submit_regret_weight",
                "query_skill_cost",
                "repeated_query_penalty",
                "query_delayed_credit_fraction",
            )
            nonzero = [
                name for name in shaping_fields if getattr(self, name) != 0.0
            ]
            if nonzero:
                raise ValueError(
                    "terminal-outcome baseline forbids reward shaping: "
                    + ", ".join(nonzero)
                )
            if self.episode_group_terminal_weight != 1.0:
                raise ValueError(
                    "terminal-outcome baseline requires episode terminal weight 1"
                )
            if self.pivot_group_terminal_weight != 0.0:
                raise ValueError(
                    "terminal-outcome baseline does not train pivot groups"
                )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RewardConfig":
        unknown = set(payload) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown reward config fields: {sorted(unknown)}")
        return cls(**dict(payload))

    def to_dict(self) -> dict[str, Any]:
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
        }


@dataclass(frozen=True)
class ImageTransitionReward:
    comparison_basis: str
    fixed_fraction: float
    regressed_fraction: float
    gm_tie_break_delta: float
    intervention_credit: float
    best_progress: float
    no_progress_penalty: float
    image_cost: float
    total: float


def image_transition_reward(
    *,
    action_type: str,
    source: AttemptScore | None,
    best_before: AttemptScore | None,
    result: AttemptScore,
    fixed_constraint_ids: Iterable[str],
    regressed_constraint_ids: Iterable[str],
    strict_no_progress: bool,
    charge_image_cost: bool,
    config: RewardConfig,
) -> ImageTransitionReward:
    """Score one image action from canonical verifier facts.

    Edit effectiveness is measured against its declared source. A source-free
    generation is measured against the reducer best that existed before the
    action. Every non-initial action also receives normalized progress relative
    to that pre-action best, preventing an easy repair of a weak historical
    source from earning positive global credit while remaining below best.
    """

    if action_type not in {"generate_image", "edit_image"}:
        raise ValueError("action_type must be generate_image or edit_image")
    if action_type == "edit_image" and source is None:
        raise ValueError("edit_image requires a declared source score")
    if action_type == "generate_image" and source is not None:
        raise ValueError("generate_image must not have a source score")
    if action_type == "edit_image" and best_before is None:
        raise ValueError("edit_image requires a pre-action best score")
    for label, score in (("source", source), ("best_before", best_before)):
        if score is not None and score.atom_count != result.atom_count:
            raise ValueError(f"{label} and result must have the same atom_count")

    comparison = source if action_type == "edit_image" else best_before
    comparison_basis = (
        "source"
        if action_type == "edit_image"
        else "best_before"
        if best_before is not None
        else "initial"
    )
    fixed = _validated_constraint_ids(fixed_constraint_ids, "fixed_constraint_ids")
    regressed = _validated_constraint_ids(
        regressed_constraint_ids, "regressed_constraint_ids"
    )
    if fixed & regressed:
        raise ValueError("fixed and regressed constraint IDs must be disjoint")
    if not isinstance(strict_no_progress, bool):
        raise ValueError("strict_no_progress must be boolean")
    if not isinstance(charge_image_cost, bool):
        raise ValueError("charge_image_cost must be boolean")
    if strict_no_progress and (fixed or regressed):
        raise ValueError("strict_no_progress cannot include fixed/regressed atoms")

    if comparison is None:
        if fixed or regressed:
            raise ValueError("initial generation cannot claim transition atoms")
        if strict_no_progress:
            raise ValueError("initial generation cannot be strict no-progress")
        fixed_fraction = 0.0
        regressed_fraction = 0.0
        gm_delta = 0.0
    else:
        comparison_failed = comparison.atom_count - comparison.pass_count
        if len(fixed) > comparison_failed:
            raise ValueError("fixed count exceeds the comparison failed-atom count")
        if len(regressed) > comparison.pass_count:
            raise ValueError("regressed count exceeds the comparison passed-atom count")
        expected_pass_count = comparison.pass_count + len(fixed) - len(regressed)
        if result.pass_count != expected_pass_count:
            raise ValueError(
                "result pass_count disagrees with fixed/regressed transition facts"
            )
        fixed_fraction = len(fixed) / max(1, comparison_failed)
        regressed_fraction = len(regressed) / max(1, comparison.pass_count)
        gm_delta = 0.0
        if comparison.pass_count == result.pass_count:
            gm_delta = result.primary_score - comparison.primary_score

    intervention_credit = (
        config.fixed_weight * fixed_fraction
        - config.regression_weight * regressed_fraction
        + config.gm_transition_weight * gm_delta
    )
    if best_before is None:
        best_progress = result.utility(
            gm_tie_break_scale=config.gm_tie_break_scale
        ) / result.atom_count
    else:
        best_progress = (
            result.utility(gm_tie_break_scale=config.gm_tie_break_scale)
            - best_before.utility(gm_tie_break_scale=config.gm_tie_break_scale)
        ) / result.atom_count
    no_progress = config.no_progress_penalty if strict_no_progress else 0.0
    image_cost = config.image_call_cost if charge_image_cost else 0.0
    total = (
        intervention_credit
        + config.best_progress_weight * best_progress
        - no_progress
        - image_cost
    )
    return ImageTransitionReward(
        comparison_basis=comparison_basis,
        fixed_fraction=fixed_fraction,
        regressed_fraction=regressed_fraction,
        gm_tie_break_delta=gm_delta,
        intervention_credit=intervention_credit,
        best_progress=best_progress,
        no_progress_penalty=no_progress,
        image_cost=image_cost,
        total=total,
    )


@dataclass(frozen=True)
class TerminalReward:
    submitted_utility: float
    all_pass_bonus: float
    submission_regret: float
    image_cost: float
    total: float


def terminal_submit_reward(
    *,
    submitted: AttemptScore,
    environment_best: AttemptScore,
    image_call_count: int,
    config: RewardConfig,
) -> TerminalReward:
    """Reward the explicit submit choice without replacing reducer ordering."""

    if submitted.atom_count != environment_best.atom_count:
        raise ValueError("submitted and best scores must have the same atom_count")
    if isinstance(image_call_count, bool) or not isinstance(image_call_count, int):
        raise ValueError("image_call_count must be an integer")
    if image_call_count < 1:
        raise ValueError("image_call_count must be positive")
    submitted_utility = submitted.utility(
        gm_tie_break_scale=config.gm_tie_break_scale
    )
    best_utility = environment_best.utility(
        gm_tie_break_scale=config.gm_tie_break_scale
    )
    regret = best_utility - submitted_utility
    if regret < -1e-12:
        raise ValueError("environment_best is worse than the submitted Attempt")
    regret = max(0.0, regret)
    image_cost = config.image_call_cost * image_call_count
    all_pass_bonus = (
        config.all_pass_bonus
        if submitted.pass_count == submitted.atom_count
        else 0.0
    )
    total = (
        submitted_utility
        + all_pass_bonus
        - config.submit_regret_weight * regret
        - image_cost
    )
    return TerminalReward(
        submitted_utility=submitted_utility,
        all_pass_bonus=all_pass_bonus,
        submission_regret=regret,
        image_cost=image_cost,
        total=total,
    )


def pivot_submit_reward(
    *,
    submitted: AttemptScore,
    environment_best: AttemptScore,
    image_call_count: int,
    config: RewardConfig,
) -> float:
    """Normalize a one-step submit sibling to the local-credit scale."""

    terminal = terminal_submit_reward(
        submitted=submitted,
        environment_best=environment_best,
        image_call_count=image_call_count,
        config=config,
    )
    return terminal.total / submitted.atom_count


@dataclass(frozen=True)
class QuerySkillCredit:
    query_credit: float
    downstream_credit: float
    total_after_cost: float


def query_skill_credit(
    *,
    downstream_image_credit: float,
    repeated_query: bool,
    config: RewardConfig,
) -> QuerySkillCredit:
    """Split delayed image credit instead of duplicating it onto a Skill call."""

    credit = _finite_number(downstream_image_credit, "downstream_image_credit")
    if not isinstance(repeated_query, bool):
        raise ValueError("repeated_query must be boolean")
    cost = config.query_skill_cost
    if repeated_query:
        cost += config.repeated_query_penalty
    query_share = credit * config.query_delayed_credit_fraction - cost
    downstream_share = credit * (1.0 - config.query_delayed_credit_fraction)
    return QuerySkillCredit(
        query_credit=query_share,
        downstream_credit=downstream_share,
        total_after_cost=query_share + downstream_share,
    )


@dataclass(frozen=True)
class PivotSignals:
    regressed_constraint_count: int = 0
    latest_attempt_id: str | None = None
    best_attempt_id: str | None = None
    consecutive_no_progress: int = 0
    remaining_image_budget: int = 0
    action_margin: float | None = None


def detect_pivot_reasons(signals: PivotSignals) -> tuple[str, ...]:
    """Return deterministic reasons for permitting one local branch group."""

    for name in (
        "regressed_constraint_count",
        "consecutive_no_progress",
        "remaining_image_budget",
    ):
        value = getattr(signals, name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    reasons: list[str] = []
    if signals.regressed_constraint_count:
        reasons.append("regression")
    if (
        signals.latest_attempt_id is not None
        and signals.best_attempt_id is not None
        and signals.latest_attempt_id != signals.best_attempt_id
    ):
        reasons.append("latest_best_divergence")
    if signals.consecutive_no_progress >= 2:
        reasons.append("repeated_no_progress")
    if 0 < signals.remaining_image_budget <= 2:
        reasons.append("low_remaining_budget")
    if signals.action_margin is not None:
        margin = _finite_number(signals.action_margin, "action_margin")
        if not 0.0 <= margin <= 1.0:
            raise ValueError("action_margin must be in [0, 1]")
        if margin <= 0.10:
            reasons.append("action_uncertainty")
    return tuple(reasons)


@dataclass(frozen=True)
class CreditCandidate:
    candidate_id: str
    state_id: str
    sampling_policy_id: str
    sample_sha256: str
    rollout_sample_sha256: str
    reward_components_sha256: str
    trainable_token_count: int
    on_policy: bool
    outcome_kind: str
    local_return: float
    episode_return: float

    def __post_init__(self) -> None:
        for name in ("candidate_id", "state_id", "sampling_policy_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        for name in (
            "sample_sha256",
            "rollout_sample_sha256",
            "reward_components_sha256",
        ):
            digest = getattr(self, name)
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        if not isinstance(self.on_policy, bool):
            raise ValueError("on_policy must be boolean")
        if (
            isinstance(self.trainable_token_count, bool)
            or not isinstance(self.trainable_token_count, int)
            or self.trainable_token_count <= 0
        ):
            raise ValueError("trainable_token_count must be a positive integer")
        if self.outcome_kind not in {"success", "policy_invalid"}:
            raise ValueError(
                "infrastructure failures are tracked outside the advantage "
                "batch and retried with the same semantic request"
            )
        object.__setattr__(
            self, "local_return", _finite_number(self.local_return, "local_return")
        )
        object.__setattr__(
            self,
            "episode_return",
            _finite_number(self.episode_return, "episode_return"),
        )


@dataclass(frozen=True)
class CandidateAdvantage:
    candidate_id: str
    local_advantage: float
    episode_advantage: float
    combined_advantage: float


@dataclass(frozen=True)
class GroupAdvantageResult:
    candidates: tuple[CandidateAdvantage, ...]
    local_return_std: float
    episode_return_std: float
    combined_advantage_std: float
    terminal_weight: float
    eligible_for_policy_loss: bool


def combine_group_advantages(
    candidates: Sequence[CreditCandidate],
    *,
    group_kind: str,
    config: RewardConfig,
) -> GroupAdvantageResult:
    """Compute node-local and episode-level GRPO advantages.

    Every candidate must come from the exact same canonical state and sampling
    policy. Off-policy Teacher trajectories are rejected rather than silently
    treated as policy-gradient data.
    """

    if len(candidates) < 2:
        raise ValueError("a relative-advantage group requires at least two candidates")
    if group_kind not in {"episode", "pivot"}:
        raise ValueError("group_kind must be episode or pivot")
    state_ids = {candidate.state_id for candidate in candidates}
    if len(state_ids) != 1:
        raise ValueError("all group candidates must share one state_id")
    policy_ids = {candidate.sampling_policy_id for candidate in candidates}
    if len(policy_ids) != 1:
        raise ValueError("all group candidates must share one sampling policy")
    if not all(candidate.on_policy for candidate in candidates):
        raise ValueError("policy-gradient groups must contain only on-policy samples")
    candidate_ids = [candidate.candidate_id for candidate in candidates]
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("candidate_id values must be unique within a group")

    local, local_std = _z_scores(
        [candidate.local_return for candidate in candidates]
    )
    episode, episode_std = _z_scores(
        [candidate.episode_return for candidate in candidates]
    )
    terminal_weight = (
        config.episode_group_terminal_weight
        if group_kind == "episode"
        else config.pivot_group_terminal_weight
    )
    advantages = tuple(
        CandidateAdvantage(
            candidate_id=candidate.candidate_id,
            local_advantage=local[index],
            episode_advantage=episode[index],
            combined_advantage=(
                (1.0 - terminal_weight) * local[index]
                + terminal_weight * episode[index]
            ),
        )
        for index, candidate in enumerate(candidates)
    )
    combined_std = _population_std(
        [item.combined_advantage for item in advantages]
    )
    return GroupAdvantageResult(
        candidates=advantages,
        local_return_std=local_std,
        episode_return_std=episode_std,
        combined_advantage_std=combined_std,
        terminal_weight=terminal_weight,
        eligible_for_policy_loss=combined_std > 1e-12,
    )


def _validated_constraint_ids(values: Iterable[str], name: str) -> set[str]:
    result = list(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{name} must contain non-empty strings")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicates")
    return set(result)


def invalid_action_reward(*, config: RewardConfig) -> float:
    """Penalize an on-policy parse/reference failure without executing it."""

    return -config.invalid_action_penalty


def _z_scores(values: Sequence[float]) -> tuple[list[float], float]:
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / len(values)
    standard_deviation = math.sqrt(variance)
    if standard_deviation <= 1e-12:
        return [0.0 for _ in values], standard_deviation
    return (
        [(value - mean) / standard_deviation for value in values],
        standard_deviation,
    )


def _population_std(values: Sequence[float]) -> float:
    mean = math.fsum(values) / len(values)
    return math.sqrt(
        math.fsum((value - mean) ** 2 for value in values) / len(values)
    )
