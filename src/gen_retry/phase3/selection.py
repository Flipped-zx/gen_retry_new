from __future__ import annotations

from collections import Counter
from typing import Any


ELIGIBLE_VALUES = {True, "eligible", "yes", "true", "1"}


def select_candidates(
    candidates: list[dict[str, Any]],
    *,
    limit: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    eligible = [candidate for candidate in candidates if _is_eligible(candidate)]
    if len(eligible) < limit:
        raise ValueError(f"need at least {limit} eligible candidates, found {len(eligible)}")

    type_frequency = Counter(
        constraint_type
        for candidate in eligible
        for constraint_type in _constraint_types(candidate)
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_groups: set[str] = set()
    selected_type_counts: Counter[str] = Counter()

    for rank in range(1, limit + 1):
        scored = [
            _score_candidate(
                candidate,
                rank=rank,
                selected_type_counts=selected_type_counts,
                selected_groups=selected_groups,
                type_frequency=type_frequency,
            )
            for candidate in eligible
            if candidate["candidate_id"] not in selected_ids
        ]
        scored.sort(key=lambda item: item["sort_key"], reverse=True)
        winner = scored[0]
        selected_candidate = {
            **winner["candidate"],
            "selection_rank": rank,
            "selection_score": round(winner["score"], 6),
            "selection_reason": winner["reason"],
        }
        selected.append(selected_candidate)
        selected_ids.add(selected_candidate["candidate_id"])
        selected_groups.add(str(selected_candidate.get("semantic_duplication_group", "")))
        selected_type_counts.update(_constraint_types(selected_candidate))

    coverage_matrix = build_coverage_matrix(selected)
    return selected, coverage_matrix


def build_coverage_matrix(selected: list[dict[str, Any]]) -> dict[str, Any]:
    all_types = sorted(
        {
            constraint_type
            for candidate in selected
            for constraint_type in _constraint_types(candidate)
        }
    )
    rows = []
    aggregate = Counter()
    for candidate in selected:
        histogram = _histogram(candidate)
        aggregate.update(histogram)
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "prompt_id": candidate["prompt_id"],
                "semantic_duplication_group": candidate.get("semantic_duplication_group"),
                "constraint_count": int(candidate.get("constraint_count", 0)),
                "constraint_type_histogram": {
                    constraint_type: histogram.get(constraint_type, 0)
                    for constraint_type in all_types
                },
            }
        )

    return {
        "schema_version": "0.2",
        "selected_count": len(selected),
        "constraint_types": all_types,
        "aggregate_type_counts": {
            constraint_type: aggregate.get(constraint_type, 0)
            for constraint_type in all_types
        },
        "rows": rows,
    }


def _score_candidate(
    candidate: dict[str, Any],
    *,
    rank: int,
    selected_type_counts: Counter[str],
    selected_groups: set[str],
    type_frequency: Counter[str],
) -> dict[str, Any]:
    types = _constraint_types(candidate)
    histogram = _histogram(candidate)
    difficulty = _difficulty_score(candidate)
    new_coverage_bonus = sum(8.0 for constraint_type in types if selected_type_counts[constraint_type] == 0)
    rare_type_bonus = sum(3.0 / max(type_frequency[constraint_type], 1) for constraint_type in types)
    combination_bonus = max(0, len(types) - 1) * 2.0
    group = str(candidate.get("semantic_duplication_group", ""))
    duplication_penalty = 18.0 if group and group in selected_groups else 0.0

    projected_counts = selected_type_counts.copy()
    projected_counts.update(histogram)
    imbalance_penalty = _imbalance_penalty(projected_counts)

    score = (
        difficulty
        + new_coverage_bonus
        + rare_type_bonus
        + combination_bonus
        - duplication_penalty
        - imbalance_penalty
    )
    reason = {
        "difficulty_score": round(difficulty, 6),
        "new_coverage_bonus": round(new_coverage_bonus, 6),
        "rare_type_bonus": round(rare_type_bonus, 6),
        "combination_bonus": round(combination_bonus, 6),
        "duplication_penalty": round(duplication_penalty, 6),
        "imbalance_penalty": round(imbalance_penalty, 6),
        "rank_iteration": rank,
    }
    return {
        "candidate": candidate,
        "score": score,
        "reason": reason,
        "sort_key": (
            score,
            difficulty,
            new_coverage_bonus,
            -duplication_penalty,
            str(candidate["candidate_id"]),
        ),
    }


def _difficulty_score(candidate: dict[str, Any]) -> float:
    score = float(candidate.get("constraint_count", 0)) * 4.0
    baseline = candidate.get("baseline_difficulty_evidence") or {}
    historical = candidate.get("historical_difficulty_evidence") or {}
    unresolved = candidate.get("historical_unresolved_evidence")

    failed_atoms = _number_from_keys(
        baseline,
        ("failed_atom_count", "baseline_failed_atom_count", "failed_constraint_count"),
    )
    if failed_atoms is not None:
        score += failed_atoms * 3.0

    pass_ratio = _number_from_keys(baseline, ("pass_ratio", "baseline_pass_ratio"))
    if pass_ratio is not None:
        score += max(0.0, 1.0 - min(max(pass_ratio, 0.0), 1.0)) * 10.0

    retry_depth = _number_from_keys(
        historical,
        ("retry_depth", "max_retry_depth", "historical_retry_depth"),
    )
    if retry_depth is not None:
        score += retry_depth * 2.0

    unresolved_count = _unresolved_count(unresolved)
    score += unresolved_count * 5.0
    score += max(0, len(_constraint_types(candidate)) - 1) * 1.5
    return score


def _imbalance_penalty(counts: Counter[str]) -> float:
    if not counts:
        return 0.0
    values = list(counts.values())
    return (max(values) - min(values)) * 0.75


def _histogram(candidate: dict[str, Any]) -> dict[str, int]:
    histogram = candidate.get("constraint_type_histogram") or {}
    return {
        str(key): int(value)
        for key, value in histogram.items()
        if int(value) > 0
    }


def _constraint_types(candidate: dict[str, Any]) -> list[str]:
    histogram_types = set(_histogram(candidate))
    combination = candidate.get("constraint_type_combination") or []
    combination_types = {str(item) for item in combination}
    return sorted(histogram_types | combination_types)


def _is_eligible(candidate: dict[str, Any]) -> bool:
    value = candidate.get("selection_eligibility")
    if isinstance(value, str):
        value = value.lower()
    return value in ELIGIBLE_VALUES


def _number_from_keys(data: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key not in data:
            continue
        try:
            return float(data[key])
        except (TypeError, ValueError):
            return None
    return None


def _unresolved_count(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("unresolved_count", "final_unresolved_count", "historical_unresolved_count"):
            if key in value:
                try:
                    return float(value[key])
                except (TypeError, ValueError):
                    return 0.0
        if value.get("unresolved") is True:
            return 1.0
    if isinstance(value, list):
        return float(len(value))
    return 0.0
