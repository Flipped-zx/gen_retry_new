from __future__ import annotations

import math
from typing import Any


LEGACY_POLICY_ID = "pass_count_only_then_earlier"
PRIMARY_POLICY_ID = "geneval2_pass_count_then_gm"
POLICY_VERSION = "1"
PRIMARY_METRIC_ID = "geneval2_soft_tifa_gm"
PRIMARY_METRIC_VERSION = "flow_dppo_v1"
PRIMARY_SELECTION_RULE = (
    "higher_pass_count_then_higher_primary_score_then_earlier"
)
LEGACY_SELECTION_RULE = "higher_pass_count_then_earlier"
PREFERRED_PRIMARY_PLANNER_CONTEXT_VERSION = "0.7"
PRIMARY_PLANNER_CONTEXT_VERSIONS = ("0.6", "0.7")
GM_PROBABILITY_FLOOR = 1e-300


def legacy_score_policy() -> dict[str, Any]:
    return {
        "policy_id": LEGACY_POLICY_ID,
        "policy_version": POLICY_VERSION,
        "primary_metric": None,
        "best_selection_rule": LEGACY_SELECTION_RULE,
    }


def primary_score_policy() -> dict[str, Any]:
    return {
        "policy_id": PRIMARY_POLICY_ID,
        "policy_version": POLICY_VERSION,
        "primary_metric": {
            "metric_id": PRIMARY_METRIC_ID,
            "metric_version": PRIMARY_METRIC_VERSION,
        },
        "best_selection_rule": PRIMARY_SELECTION_RULE,
    }


def score_policy_from_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    policy = payload.get("score_policy")
    if policy is None:
        return legacy_score_policy()
    validate_score_policy(policy)
    return policy


def score_policy_for_id(policy_id: str) -> dict[str, Any]:
    return _score_policy_for_id(policy_id)


def validate_score_policy(policy: dict[str, Any]) -> None:
    expected = _score_policy_for_id(policy.get("policy_id"))
    if policy != expected:
        raise ValueError(
            "score policy does not match its canonical version: "
            f"{policy.get('policy_id')}@{policy.get('policy_version')}"
        )


def _score_policy_for_id(policy_id: Any) -> dict[str, Any]:
    if policy_id == LEGACY_POLICY_ID:
        return legacy_score_policy()
    if policy_id == PRIMARY_POLICY_ID:
        return primary_score_policy()
    raise ValueError(f"unsupported score policy: {policy_id}")


def canonical_primary_score(
    constraint_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not constraint_results:
        raise ValueError("Soft-TIFA GM requires at least one atom probability")
    ordered = sorted(constraint_results, key=lambda item: item["constraint_id"])
    probabilities: list[float] = []
    for result in ordered:
        value = result.get("confidence")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                "Soft-TIFA GM requires confidence for every atom"
            )
        probability = float(value)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError(
                "Soft-TIFA atom probabilities must be finite values in [0, 1]"
            )
        probabilities.append(probability)
    value = soft_tifa_geometric_mean(probabilities)
    return {
        "metric_id": PRIMARY_METRIC_ID,
        "metric_version": PRIMARY_METRIC_VERSION,
        "value": value,
    }


def soft_tifa_geometric_mean(probabilities: list[float]) -> float:
    if not probabilities:
        raise ValueError("Soft-TIFA GM requires at least one atom probability")
    normalized: list[float] = []
    for value in probabilities:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Soft-TIFA probabilities must be numeric")
        probability = float(value)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError(
                "Soft-TIFA atom probabilities must be finite values in [0, 1]"
            )
        normalized.append(probability)
    return math.exp(
        math.fsum(
            math.log(max(probability, GM_PROBABILITY_FLOOR))
            for probability in normalized
        )
        / len(normalized)
    )


def validate_primary_score(
    primary_score: dict[str, Any],
    constraint_results: list[dict[str, Any]],
) -> None:
    expected = canonical_primary_score(constraint_results)
    if primary_score != expected:
        raise ValueError("persisted primary score disagrees with atom probabilities")


def primary_score_value(
    payload: dict[str, Any],
    score_policy: dict[str, Any],
) -> float | None:
    primary_score = payload.get("primary_score")
    if primary_score is None:
        if score_policy["policy_id"] == PRIMARY_POLICY_ID:
            raise ValueError("primary-score policy requires a Geneval2 primary score")
        return None
    validate_primary_score(primary_score, payload["constraint_results"])
    return float(primary_score["value"])


def candidate_is_better(
    *,
    candidate_pass_count: int,
    candidate_primary_score: float | None,
    current_pass_count: int,
    current_primary_score: float | None,
    score_policy: dict[str, Any],
) -> bool:
    if candidate_pass_count != current_pass_count:
        return candidate_pass_count > current_pass_count
    if score_policy["policy_id"] == LEGACY_POLICY_ID:
        return False
    if candidate_primary_score is None or current_primary_score is None:
        raise ValueError("primary-score policy requires scores for best selection")
    return candidate_primary_score > current_primary_score


def planner_context_version(score_policy: dict[str, Any]) -> str:
    return (
        PREFERRED_PRIMARY_PLANNER_CONTEXT_VERSION
        if score_policy["policy_id"] == PRIMARY_POLICY_ID
        else "0.5"
    )


def planner_context_version_is_compatible(
    score_policy: dict[str, Any],
    schema_version: str,
) -> bool:
    if score_policy["policy_id"] == PRIMARY_POLICY_ID:
        return schema_version in PRIMARY_PLANNER_CONTEXT_VERSIONS
    return schema_version == "0.5"


def score_policy_tuple(
    *,
    planner_context_schema_version: str,
    score_policy: dict[str, Any],
) -> tuple[str, str, str, str | None, str | None]:
    metric = score_policy["primary_metric"]
    return (
        planner_context_schema_version,
        score_policy["policy_id"],
        score_policy["policy_version"],
        None if metric is None else metric["metric_id"],
        None if metric is None else metric["metric_version"],
    )
