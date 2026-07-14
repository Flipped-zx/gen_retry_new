from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ReferenceProblem:
    field: str
    value: str
    message: str


class ActionReferenceError(ValueError):
    def __init__(self, problems: list[ReferenceProblem]):
        self.problems = problems
        message = "; ".join(f"{p.field}={p.value}: {p.message}" for p in problems)
        super().__init__(message)


def _constraint_ids(task_spec: dict[str, Any]) -> set[str]:
    return {constraint["constraint_id"] for constraint in task_spec.get("constraints", [])}


def _ensure_known_ids(
    problems: list[ReferenceProblem],
    field: str,
    values: Iterable[str],
    known: set[str],
    noun: str,
) -> None:
    for value in values:
        if value not in known:
            problems.append(ReferenceProblem(field, value, f"unknown {noun}"))


def validate_action_references(
    action: dict[str, Any],
    task_spec: dict[str, Any],
    known_attempt_ids: Iterable[str] | None = None,
    available_skill_ids: Iterable[str] | None = None,
) -> None:
    """Validate IDs whose existence cannot be proven by JSON Schema alone."""

    known_constraints = _constraint_ids(task_spec)
    known_attempts = set(known_attempt_ids or [])
    known_skills = set(available_skill_ids or [])
    check_skills = available_skill_ids is not None

    problems: list[ReferenceProblem] = []
    arguments = action.get("arguments", {})
    action_type = action.get("action")

    _ensure_known_ids(
        problems,
        "target_constraint_ids",
        arguments.get("target_constraint_ids", []),
        known_constraints,
        "constraint_id",
    )
    _ensure_known_ids(
        problems,
        "preserve_constraint_ids",
        arguments.get("preserve_constraint_ids", []),
        known_constraints,
        "constraint_id",
    )

    if action_type == "edit_image":
        source_attempt_id = arguments.get("source_attempt_id")
        if source_attempt_id not in known_attempts:
            problems.append(
                ReferenceProblem("source_attempt_id", str(source_attempt_id), "unknown attempt_id")
            )

    if action_type == "submit_attempt":
        selected_attempt_id = arguments.get("selected_attempt_id")
        if selected_attempt_id not in known_attempts:
            problems.append(
                ReferenceProblem("selected_attempt_id", str(selected_attempt_id), "unknown attempt_id")
            )

    if check_skills:
        skill_field = "skill_ids" if action_type == "query_skill" else "skill_ids_used"
        _ensure_known_ids(
            problems,
            skill_field,
            arguments.get(skill_field, []),
            known_skills,
            "skill_id",
        )

    if problems:
        raise ActionReferenceError(problems)


def reference_error_observation(error: ActionReferenceError) -> dict[str, str]:
    return {
        "schema_version": "0.2",
        "observation_type": "reference_error",
        "error_code": "invalid_reference",
        "message": str(error),
    }
