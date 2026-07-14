from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from gen_retry.protocol.reference_validator import validate_action_references
from gen_retry.protocol.schema_loader import validate_instance


@dataclass(frozen=True)
class ProtocolProblem:
    code: str
    message: str


class ProtocolValidationError(ValueError):
    def __init__(self, problems: list[ProtocolProblem]):
        self.problems = problems
        super().__init__("; ".join(f"{problem.code}: {problem.message}" for problem in problems))


def _duplicates(values: Iterable[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _problem(problems: list[ProtocolProblem], code: str, message: str) -> None:
    problems.append(ProtocolProblem(code=code, message=message))


def validate_task_spec_semantics(task_spec: dict[str, Any]) -> None:
    validate_instance(task_spec, "task_spec_v0_2.schema.json")
    problems: list[ProtocolProblem] = []
    duplicates = _duplicates(
        constraint["constraint_id"] for constraint in task_spec.get("constraints", [])
    )
    if duplicates:
        _problem(
            problems,
            "duplicate_constraint_id",
            f"TaskSpec has duplicate constraint IDs: {', '.join(duplicates)}",
        )
    if problems:
        raise ProtocolValidationError(problems)


def validate_artifact_manifest_semantics(manifest: dict[str, Any]) -> None:
    validate_instance(manifest, "artifact_manifest_v0_2.schema.json")
    problems: list[ProtocolProblem] = []
    duplicates = _duplicates(artifact["artifact_id"] for artifact in manifest.get("artifacts", []))
    if duplicates:
        _problem(
            problems,
            "duplicate_artifact_id",
            f"Artifact manifest has duplicate artifact IDs: {', '.join(duplicates)}",
        )
    if problems:
        raise ProtocolValidationError(problems)


def validate_geneval2_result_semantics(event: dict[str, Any]) -> None:
    validate_instance(event, "episode_event_v0_2.schema.json")
    problems: list[ProtocolProblem] = []
    if event.get("event_type") == "geneval2_completed":
        duplicate_constraints = _duplicates(
            result["constraint_id"]
            for result in event.get("payload", {}).get("constraint_results", [])
        )
        if duplicate_constraints:
            _problem(
                problems,
                "duplicate_constraint_observation",
                "Geneval2 event has duplicate observations for: "
                + ", ".join(duplicate_constraints),
            )
    if problems:
        raise ProtocolValidationError(problems)


def validate_trajectory_events(events: list[dict[str, Any]]) -> None:
    problems: list[ProtocolProblem] = []
    event_ids: set[str] = set()
    attempts: set[str] = set()
    image_artifact_ids: set[str] = set()
    evaluated_attempts: set[str] = set()
    completed_request_ids: set[str] = set()
    task_spec: dict[str, Any] | None = None
    episode_id: str | None = None
    query_actions: dict[str, dict[str, Any]] = {}
    consumed_query_actions: set[str] = set()
    validated_actions: dict[str, dict[str, Any]] = {}
    submit_actions: dict[str, dict[str, Any]] = {}
    starts_by_request_id: dict[str, dict[str, Any]] = {}
    action_execution_started: set[str] = set()

    if not events:
        raise ProtocolValidationError(
            [ProtocolProblem("empty_trajectory", "trajectory must contain events")]
        )

    for index, event in enumerate(events):
        try:
            validate_instance(event, "episode_event_v0_2.schema.json")
        except Exception as exc:  # jsonschema exceptions expose verbose reprs.
            _problem(problems, "schema_error", f"event {index}: {exc}")
            continue

        event_id = event["event_id"]
        if event_id in event_ids:
            _problem(problems, "duplicate_event_id", f"duplicate event_id {event_id}")
        event_ids.add(event_id)

        if episode_id is None:
            episode_id = event["episode_id"]
        elif event["episode_id"] != episode_id:
            _problem(
                problems,
                "episode_id_mismatch",
                f"event {event_id} has episode_id {event['episode_id']} but expected {episode_id}",
            )

        event_type = event["event_type"]
        payload = event["payload"]

        if index == 0 and event_type != "task_created":
            _problem(problems, "task_created_not_first", "first trajectory event must be task_created")

        if event_type == "task_created":
            if task_spec is not None:
                _problem(problems, "duplicate_task_created", "trajectory has multiple task_created events")
            task_spec = payload["task_spec"]
            if task_spec.get("episode_id") != event["episode_id"]:
                _problem(
                    problems,
                    "task_episode_mismatch",
                    "task_created envelope episode_id must match nested TaskSpec episode_id",
                )
            try:
                validate_task_spec_semantics(task_spec)
            except ProtocolValidationError as exc:
                problems.extend(exc.problems)

        if event_type == "action_validated":
            if task_spec is None:
                _problem(
                    problems,
                    "action_before_task_created",
                    f"action_validated {event_id} occurs before task_created",
                )
            action = payload["action"]
            validated_actions[event_id] = event
            if action.get("action") == "query_skill":
                query_actions[event_id] = event
            if action.get("action") == "submit_attempt":
                submit_actions[event_id] = event
            if task_spec is not None:
                try:
                    validate_action_references(action, task_spec, known_attempt_ids=attempts)
                except Exception as exc:
                    _problem(problems, "invalid_action_reference", str(exc))

        if event_type == "skill_returned":
            query_event_id = payload["query_action_event_id"]
            query_event = query_actions.get(query_event_id)
            if query_event is None:
                _problem(
                    problems,
                    "unlinked_skill_returned",
                    f"skill_returned references unknown query action {query_event_id}",
                )
            else:
                if query_event_id in consumed_query_actions:
                    _problem(
                        problems,
                        "duplicate_skill_returned",
                        f"query action {query_event_id} already has a skill response",
                    )
                consumed_query_actions.add(query_event_id)
                if query_event_id not in event.get("input_refs", []):
                    _problem(
                        problems,
                        "missing_skill_input_ref",
                        f"skill_returned input_refs do not include {query_event_id}",
                    )
                if event.get("turn_id") != query_event.get("turn_id"):
                    _problem(
                        problems,
                        "skill_turn_mismatch",
                        "skill_returned turn_id differs from query action turn_id",
                    )
                if event.get("episode_id") != query_event.get("episode_id"):
                    _problem(
                        problems,
                        "skill_episode_mismatch",
                        "skill_returned episode_id differs from query action episode_id",
                    )
                query_args = query_event["payload"]["action"]["arguments"]
                if payload["skill_ids"] != query_args["skill_ids"]:
                    _problem(
                        problems,
                        "skill_ids_mismatch",
                        "skill_returned.skill_ids differ from query_skill action",
                    )
                if payload["target_constraint_ids"] != query_args["target_constraint_ids"]:
                    _problem(
                        problems,
                        "skill_targets_mismatch",
                        "skill_returned target_constraint_ids differ from query_skill action",
                    )
            returned_skill_ids = [skill["skill_id"] for skill in payload["skills"]]
            duplicates = _duplicates(returned_skill_ids)
            if duplicates:
                _problem(
                    problems,
                    "duplicate_returned_skill",
                    f"skill_returned has duplicate skill IDs: {', '.join(duplicates)}",
                )
            if sorted(returned_skill_ids) != sorted(payload["skill_ids"]):
                _problem(
                    problems,
                    "skill_payload_mismatch",
                    "skills[].skill_id must match skill_returned.skill_ids",
                )

        if event_type == "image_execution_started":
            action_refs = [
                ref for ref in event.get("input_refs", []) if ref in validated_actions
            ]
            if len(action_refs) != 1:
                _problem(
                    problems,
                    "image_start_action_ref",
                    f"image start {event_id} must reference exactly one validated action event",
                )
                action_event = None
                action_event_id = None
            else:
                action_event_id = action_refs[0]
                action_event = validated_actions[action_event_id]
                if action_event_id in action_execution_started:
                    _problem(
                        problems,
                        "duplicate_execution_for_action",
                        f"action {action_event_id} already has an image execution start",
                    )
                action_execution_started.add(action_event_id)

            if action_event is not None:
                action = action_event["payload"]["action"]
                action_type = action["action"]
                expected_action = (
                    "edit_image" if payload["operation"] == "edit" else "generate_image"
                )
                if action_type != expected_action:
                    _problem(
                        problems,
                        "image_action_operation_mismatch",
                        f"{event_id} operation {payload['operation']} cannot execute {action_type}",
                    )
                if payload["operation"] == "edit":
                    action_source = action["arguments"].get("source_attempt_id")
                    if payload.get("source_attempt_id") != action_source:
                        _problem(
                            problems,
                            "image_start_source_mismatch",
                            "image start source_attempt_id must match edit action source_attempt_id",
                        )

            if payload["operation"] == "edit" and payload["source_attempt_id"] not in attempts:
                _problem(
                    problems,
                    "unknown_edit_source",
                    f"edit source attempt {payload['source_attempt_id']} is not known",
                )
            request_id = payload["request_id"]
            if request_id in starts_by_request_id:
                _problem(
                    problems,
                    "duplicate_request_start",
                    f"request_id {request_id} already has an image start event",
                )
            starts_by_request_id[request_id] = {
                "event_id": event_id,
                "event": event,
                "action_event_id": action_event_id,
            }

        if event_type == "image_execution_completed":
            attempt_id = payload["attempt_id"]
            if attempt_id in attempts:
                _problem(problems, "duplicate_attempt_id", f"duplicate attempt_id {attempt_id}")
            request_id = payload["request_id"]
            start = starts_by_request_id.get(request_id)
            if start is None:
                _problem(
                    problems,
                    "orphan_image_completion",
                    f"image completion {event_id} has no matching start for request_id {request_id}",
                )
            else:
                start_event = start["event"]
                start_payload = start_event["payload"]
                if start["event_id"] not in event.get("input_refs", []):
                    _problem(
                        problems,
                        "missing_completion_start_ref",
                        f"image completion input_refs do not include {start['event_id']}",
                    )
                for field in ("operation", "backend"):
                    if payload[field] != start_payload[field]:
                        _problem(
                            problems,
                            "image_start_completion_mismatch",
                            f"image completion {field} differs from matching start",
                        )
                for field in ("attempt_id", "parent_attempt_id"):
                    if field in start_payload and start_payload[field] != payload[field]:
                        _problem(
                            problems,
                            "image_start_completion_lineage_mismatch",
                            f"image completion {field} differs from matching start",
                        )
                if payload["operation"] == "edit" and payload.get("source_attempt_id") != start_payload.get(
                    "source_attempt_id"
                ):
                    _problem(
                        problems,
                        "image_completion_source_mismatch",
                        "image completion source_attempt_id differs from matching start",
                    )
            if request_id in completed_request_ids:
                _problem(
                    problems,
                    "duplicate_request_completion",
                    f"request_id {request_id} already has an image completion",
                )
            completed_request_ids.add(request_id)

            image_artifact_id = payload["image_artifact_id"]
            if image_artifact_id in image_artifact_ids:
                _problem(
                    problems,
                    "duplicate_image_artifact_id",
                    f"duplicate image_artifact_id {image_artifact_id}",
                )
            image_artifact_ids.add(image_artifact_id)

            if payload["operation"] == "edit":
                source_attempt_id = payload["source_attempt_id"]
                if source_attempt_id not in attempts:
                    _problem(
                        problems,
                        "unknown_edit_source",
                        f"edit source attempt {source_attempt_id} is not known",
                    )
                if payload["parent_attempt_id"] != source_attempt_id:
                    _problem(
                        problems,
                        "edit_parent_source_mismatch",
                        "edit parent_attempt_id must equal source_attempt_id",
                    )
            attempts.add(attempt_id)

        if event_type == "geneval2_completed":
            try:
                validate_geneval2_result_semantics(event)
            except ProtocolValidationError as exc:
                problems.extend(exc.problems)
            if payload["attempt_id"] in evaluated_attempts:
                _problem(
                    problems,
                    "duplicate_geneval2_result",
                    f"attempt {payload['attempt_id']} has multiple Geneval2 results",
                )
            evaluated_attempts.add(payload["attempt_id"])
            if payload["attempt_id"] not in attempts:
                _problem(
                    problems,
                    "unknown_evaluated_attempt",
                    f"Geneval2 result references unknown attempt {payload['attempt_id']}",
                )
            if task_spec is not None:
                known_constraints = {
                    constraint["constraint_id"] for constraint in task_spec["constraints"]
                }
                observed_constraints = {
                    result["constraint_id"] for result in payload["constraint_results"]
                }
                missing_constraints = sorted(known_constraints - observed_constraints)
                if missing_constraints:
                    _problem(
                        problems,
                        "incomplete_geneval2_result",
                        "Geneval2 result omits TaskSpec constraints: "
                        + ", ".join(missing_constraints),
                    )
                for result in payload["constraint_results"]:
                    if result["constraint_id"] not in known_constraints:
                        _problem(
                            problems,
                            "unknown_observed_constraint",
                            f"Geneval2 result references unknown constraint {result['constraint_id']}",
                        )

        if event_type == "attempt_submitted":
            submit_action_event_id = payload["submit_action_event_id"]
            submit_action_event = submit_actions.get(submit_action_event_id)
            if submit_action_event_id not in event.get("input_refs", []):
                _problem(
                    problems,
                    "missing_submission_action_ref",
                    f"attempt_submitted input_refs do not include {submit_action_event_id}",
                )
            if submit_action_event is None:
                _problem(
                    problems,
                    "unlinked_attempt_submission",
                    f"attempt_submitted references unknown submit action {submit_action_event_id}",
                )
            else:
                if event.get("turn_id") != submit_action_event.get("turn_id"):
                    _problem(
                        problems,
                        "submission_turn_mismatch",
                        "attempt_submitted turn_id differs from submit action turn_id",
                    )
                submit_args = submit_action_event["payload"]["action"]["arguments"]
                if payload["selected_attempt_id"] != submit_args["selected_attempt_id"]:
                    _problem(
                        problems,
                        "submission_attempt_mismatch",
                        "attempt_submitted selected_attempt_id differs from submit action",
                    )
                if payload["reason_code"] != submit_args["reason_code"]:
                    _problem(
                        problems,
                        "submission_reason_mismatch",
                        "attempt_submitted reason_code differs from submit action",
                    )
            if payload["selected_attempt_id"] not in attempts:
                _problem(
                    problems,
                    "unknown_submitted_attempt",
                    f"submission references unknown attempt {payload['selected_attempt_id']}",
                )

    if task_spec is None:
        _problem(problems, "missing_task_created", "trajectory must include task_created")

    if problems:
        raise ProtocolValidationError(problems)
