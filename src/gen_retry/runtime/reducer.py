from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from gen_retry.domain.score_policy import (
    candidate_is_better,
    primary_score_value,
    score_policy_from_task_payload,
)
from gen_retry.protocol.trajectory_validator import validate_trajectory_events


PASS = "pass"


@dataclass(frozen=True)
class AttemptRecord:
    attempt_id: str
    parent_attempt_id: str | None
    action_event_id: str
    action: dict[str, Any]
    operation: str
    image_artifact_id: str
    constraint_results: dict[str, dict[str, Any]]
    primary_score: float | None = None
    auxiliary_quality: dict[str, Any] | None = None

    @property
    def passed_constraint_ids(self) -> list[str]:
        return sorted(
            constraint_id
            for constraint_id, result in self.constraint_results.items()
            if result["status"] == PASS
        )

    @property
    def failed_constraint_ids(self) -> list[str]:
        return sorted(
            constraint_id
            for constraint_id, result in self.constraint_results.items()
            if result["status"] != PASS
        )

    @property
    def pass_count(self) -> int:
        return len(self.passed_constraint_ids)


@dataclass
class EpisodeState:
    schema_version: str
    episode_id: str
    task_spec: dict[str, Any]
    score_policy: dict[str, Any]
    attempts: dict[str, AttemptRecord] = field(default_factory=dict)
    attempt_order: list[str] = field(default_factory=list)
    latest_attempt_id: str | None = None
    best_attempt_id: str | None = None
    latest_transition: dict[str, Any] | None = None
    remaining_budget: int = 0
    submitted_attempt_id: str | None = None
    submitted_reason_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "task_spec": self.task_spec,
            "score_policy": self.score_policy,
            "attempt_order": self.attempt_order,
            "attempts": {
                attempt_id: attempt_to_dict(self.attempts[attempt_id])
                for attempt_id in self.attempt_order
            },
            "latest_attempt_id": self.latest_attempt_id,
            "best_attempt_id": self.best_attempt_id,
            "latest_transition": self.latest_transition,
            "remaining_budget": self.remaining_budget,
            "submitted_attempt_id": self.submitted_attempt_id,
            "submitted_reason_code": self.submitted_reason_code,
        }


def attempt_to_dict(attempt: AttemptRecord) -> dict[str, Any]:
    result = {
        "attempt_id": attempt.attempt_id,
        "parent_attempt_id": attempt.parent_attempt_id,
        "action_event_id": attempt.action_event_id,
        "action": attempt.action,
        "operation": attempt.operation,
        "image_artifact_id": attempt.image_artifact_id,
        "constraint_results": {
            key: attempt.constraint_results[key]
            for key in sorted(attempt.constraint_results)
        },
        "primary_score": attempt.primary_score,
        "passed_constraint_ids": attempt.passed_constraint_ids,
        "failed_constraint_ids": attempt.failed_constraint_ids,
    }
    if attempt.auxiliary_quality is not None:
        result["auxiliary_quality"] = attempt.auxiliary_quality
    return result


def build_transition(
    previous: AttemptRecord | None,
    current: AttemptRecord,
) -> dict[str, Any]:
    if previous is None:
        fixed: list[str] = []
        regressed: list[str] = []
        persistent_failed = current.failed_constraint_ids
        stable_pass = current.passed_constraint_ids
    else:
        previous_results = previous.constraint_results
        current_results = current.constraint_results
        fixed = sorted(
            cid
            for cid, result in current_results.items()
            if result["status"] == PASS and previous_results[cid]["status"] != PASS
        )
        regressed = sorted(
            cid
            for cid, result in current_results.items()
            if result["status"] != PASS and previous_results[cid]["status"] == PASS
        )
        persistent_failed = sorted(
            cid
            for cid, result in current_results.items()
            if result["status"] != PASS and previous_results[cid]["status"] != PASS
        )
        stable_pass = sorted(
            cid
            for cid, result in current_results.items()
            if result["status"] == PASS and previous_results[cid]["status"] == PASS
        )

    return {
        "from_attempt_id": previous.attempt_id if previous else None,
        "to_attempt_id": current.attempt_id,
        "fixed": fixed,
        "regressed": regressed,
        "persistent_failed": persistent_failed,
        "stable_pass": stable_pass,
        "new_failed": [],
    }


def choose_best_attempt(state: EpisodeState, candidate: AttemptRecord) -> str:
    if state.best_attempt_id is None:
        return candidate.attempt_id
    current_best = state.attempts[state.best_attempt_id]
    if candidate_is_better(
        candidate_pass_count=candidate.pass_count,
        candidate_primary_score=candidate.primary_score,
        current_pass_count=current_best.pass_count,
        current_primary_score=current_best.primary_score,
        score_policy=state.score_policy,
    ):
        return candidate.attempt_id
    return current_best.attempt_id


def reduce_events(events: list[dict[str, Any]]) -> EpisodeState:
    validate_trajectory_events(events)
    task_spec = events[0]["payload"]["task_spec"]
    score_policy = score_policy_from_task_payload(events[0]["payload"])
    state = EpisodeState(
        schema_version="0.2",
        episode_id=events[0]["episode_id"],
        task_spec=task_spec,
        score_policy=score_policy,
        remaining_budget=task_spec["max_image_attempts"],
    )
    action_by_event_id: dict[str, dict[str, Any]] = {}
    action_event_by_request_id: dict[str, str] = {}
    completion_by_attempt_id: dict[str, dict[str, Any]] = {}

    for event in events:
        event_type = event["event_type"]
        payload = event["payload"]
        if event_type == "action_validated":
            action_by_event_id[event["event_id"]] = payload["action"]
        elif event_type == "image_execution_started":
            action_event_id = next(
                ref for ref in event["input_refs"] if ref in action_by_event_id
            )
            action_event_by_request_id[payload["request_id"]] = action_event_id
        elif event_type == "image_execution_completed":
            completion_by_attempt_id[payload["attempt_id"]] = event
        elif event_type == "geneval2_completed":
            completion = completion_by_attempt_id[payload["attempt_id"]]
            action_event_id = action_event_by_request_id[completion["payload"]["request_id"]]
            action = action_by_event_id[action_event_id]
            constraint_results = {
                result["constraint_id"]: result
                for result in payload["constraint_results"]
            }
            attempt = AttemptRecord(
                attempt_id=payload["attempt_id"],
                parent_attempt_id=completion["payload"]["parent_attempt_id"],
                action_event_id=action_event_id,
                action=action,
                operation=completion["payload"]["operation"],
                image_artifact_id=completion["payload"]["image_artifact_id"],
                constraint_results=constraint_results,
                primary_score=primary_score_value(payload, score_policy),
            )
            if attempt.parent_attempt_id is not None:
                previous = state.attempts[attempt.parent_attempt_id]
            elif state.latest_attempt_id is not None:
                previous = state.attempts[state.latest_attempt_id]
            else:
                previous = None
            state.attempts[attempt.attempt_id] = attempt
            state.attempt_order.append(attempt.attempt_id)
            state.latest_attempt_id = attempt.attempt_id
            state.latest_transition = build_transition(previous, attempt)
            state.best_attempt_id = choose_best_attempt(state, attempt)
            state.remaining_budget = max(
                0, task_spec["max_image_attempts"] - len(state.attempt_order)
            )
        elif event_type == "auxiliary_quality_completed":
            attempt_id = payload["attempt_id"]
            if attempt_id not in state.attempts:
                raise ValueError(
                    f"auxiliary quality references unknown attempt {attempt_id}"
                )
            state.attempts[attempt_id] = replace(
                state.attempts[attempt_id],
                auxiliary_quality=payload,
            )
        elif event_type == "memory_reduced":
            if payload["latest_attempt_id"] != state.latest_attempt_id:
                raise ValueError("memory_reduced latest_attempt_id disagrees with reducer")
            if payload["best_attempt_id"] != state.best_attempt_id:
                raise ValueError("memory_reduced best_attempt_id disagrees with reducer")
            if payload["transition"] != {
                key: state.latest_transition[key]
                for key in ("fixed", "regressed", "persistent_failed", "stable_pass")
            }:
                raise ValueError("memory_reduced transition disagrees with reducer")
            if payload["remaining_budget"] != state.remaining_budget:
                raise ValueError("memory_reduced remaining_budget disagrees with reducer")
        elif event_type == "attempt_submitted":
            state.submitted_attempt_id = payload["selected_attempt_id"]
            state.submitted_reason_code = payload["reason_code"]

    return state


def default_tool_manifest() -> list[dict[str, str]]:
    return [
        {"tool_id": "query_skill", "action": "query_skill"},
        {"tool_id": "generate_image", "action": "generate_image"},
        {"tool_id": "edit_image", "action": "edit_image"},
        {"tool_id": "submit_attempt", "action": "submit_attempt"},
    ]
