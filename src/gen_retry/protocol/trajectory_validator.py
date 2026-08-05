from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.score_policy import (
    PRIMARY_POLICY_ID,
    legacy_score_policy,
    planner_context_version_is_compatible,
    score_policy_from_task_payload,
    validate_primary_score,
)
from gen_retry.domain.auxiliary_quality import (
    quality_risk_for_source_delta,
    validate_auxiliary_quality_observation,
)
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


def _lineage_root_for_attempt(
    attempt_id: str,
    parent_by_attempt_id: dict[str, str | None],
) -> str | None:
    """Return the immutable edit-lineage root, or null for a root Attempt."""

    parent_id = parent_by_attempt_id.get(attempt_id)
    if parent_id is None:
        return None
    root_id = parent_id
    while True:
        parent_id = parent_by_attempt_id.get(root_id)
        if parent_id is None:
            return root_id
        root_id = parent_id


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
    quality_attempts: set[str] = set()
    quality_observations: dict[str, dict[str, Any]] = {}
    quality_profiles: set[tuple[Any, ...]] = set()
    artifact_by_attempt_id: dict[str, str] = {}
    artifact_sha256_by_attempt_id: dict[str, str] = {}
    parent_by_attempt_id: dict[str, str | None] = {}
    completed_request_ids: set[str] = set()
    task_spec: dict[str, Any] | None = None
    episode_id: str | None = None
    query_actions: dict[str, dict[str, Any]] = {}
    consumed_query_actions: set[str] = set()
    validated_actions: dict[str, dict[str, Any]] = {}
    submit_actions: dict[str, dict[str, Any]] = {}
    starts_by_request_id: dict[str, dict[str, Any]] = {}
    action_execution_started: set[str] = set()
    execution_profiles: set[tuple[str, str]] = set()
    planner_context_versions: set[str] = set()
    score_policy = legacy_score_policy()

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
            try:
                score_policy = score_policy_from_task_payload(payload)
            except ValueError as exc:
                _problem(problems, "invalid_score_policy", str(exc))
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

        if event_type == "planner_context_built":
            actual_context_version = str(
                payload.get("planner_context_schema_version", "0.5")
            )
            planner_context_versions.add(actual_context_version)
            if not planner_context_version_is_compatible(
                score_policy,
                actual_context_version,
            ):
                _problem(
                    problems,
                    "planner_context_score_policy_mismatch",
                    "planner context version "
                    f"{actual_context_version} is incompatible with score policy "
                    f"{score_policy['policy_id']}",
                )
            if actual_context_version == "0.8":
                missing_quality = sorted(evaluated_attempts - quality_attempts)
                if missing_quality:
                    _problem(
                        problems,
                        "planner_context_missing_auxiliary_quality",
                        "PlannerContext v0.8 requires an explicit success, failed, or "
                        "missing HPSv3 event for every evaluated Attempt; missing: "
                        + ", ".join(missing_quality),
                    )

        if event_type == "image_execution_started":
            if payload.get("execution_profile_id"):
                execution_profiles.add(
                    (
                        payload["execution_profile_id"],
                        payload["execution_profile_version"],
                    )
                )
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
                if (
                    payload.get("logical_action") is not None
                    and payload["logical_action"] != action_type
                ):
                    _problem(
                        problems,
                        "image_logical_action_mismatch",
                        f"{event_id} logical_action differs from canonical action {action_type}",
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
                for field in (
                    "operation",
                    "backend",
                    "execution_profile_id",
                    "execution_profile_version",
                    "logical_action",
                    "model_id",
                    "model_revision_or_fingerprint",
                    "pipeline_id",
                    "adapter_version",
                    "sampling",
                ):
                    if field not in payload and field not in start_payload:
                        continue
                    if payload.get(field) != start_payload.get(field):
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
                if payload["operation"] == "edit" and payload.get(
                    "source_artifact_sha256"
                ) != start_payload.get("source_artifact_sha256"):
                    _problem(
                        problems,
                        "image_completion_source_digest_mismatch",
                        "image completion source digest differs from matching start",
                    )
            if payload.get("execution_profile_id"):
                execution_profiles.add(
                    (
                        payload["execution_profile_id"],
                        payload["execution_profile_version"],
                    )
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
            artifact_by_attempt_id[attempt_id] = image_artifact_id
            artifact_sha256_by_attempt_id[attempt_id] = payload["artifact_sha256"]
            parent_by_attempt_id[attempt_id] = payload["parent_attempt_id"]

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
            primary_score = payload.get("primary_score")
            if score_policy["policy_id"] == PRIMARY_POLICY_ID and primary_score is None:
                _problem(
                    problems,
                    "missing_primary_score",
                    "primary-score policy requires primary_score on every Geneval2 result",
                )
            if primary_score is not None:
                try:
                    validate_primary_score(
                        primary_score,
                        payload["constraint_results"],
                    )
                except ValueError as exc:
                    _problem(problems, "invalid_primary_score", str(exc))

        if event_type == "auxiliary_quality_completed":
            observation_is_valid = True
            try:
                validate_auxiliary_quality_observation(payload)
            except Exception as exc:
                observation_is_valid = False
                _problem(problems, "invalid_auxiliary_quality", str(exc))
            attempt_id = payload.get("attempt_id")
            if attempt_id in quality_attempts:
                _problem(
                    problems,
                    "duplicate_auxiliary_quality_result",
                    f"attempt {attempt_id} has multiple auxiliary quality results",
                )
            quality_attempts.add(attempt_id)
            if attempt_id not in attempts:
                _problem(
                    problems,
                    "unknown_auxiliary_quality_attempt",
                    f"auxiliary quality references unknown attempt {attempt_id}",
                )
            if attempt_id not in evaluated_attempts:
                _problem(
                    problems,
                    "auxiliary_quality_before_geneval2",
                    f"auxiliary quality for {attempt_id} must follow its Geneval2 result",
                )
            if attempt_id in attempts:
                expected_artifact = artifact_by_attempt_id.get(attempt_id)
                if expected_artifact is not None and payload.get("image_artifact_id") != expected_artifact:
                    _problem(
                        problems,
                        "auxiliary_quality_artifact_mismatch",
                        "auxiliary quality image_artifact_id does not match attempt output",
                    )
                expected_image_sha256 = artifact_sha256_by_attempt_id.get(attempt_id)
                if (
                    expected_image_sha256 is not None
                    and payload.get("image_sha256") != expected_image_sha256
                ):
                    _problem(
                        problems,
                        "auxiliary_quality_image_digest_mismatch",
                        "auxiliary quality image_sha256 does not match the evaluated image artifact",
                    )
                if payload.get("image_artifact_id") not in event.get("input_refs", []):
                    _problem(
                        problems,
                        "auxiliary_quality_image_ref",
                        "auxiliary quality input_refs must include the evaluated image artifact",
                    )
                expected_source = parent_by_attempt_id.get(attempt_id)
                if payload.get("source_attempt_id") != expected_source:
                    _problem(
                        problems,
                        "auxiliary_quality_source_mismatch",
                        "auxiliary quality source_attempt_id must match attempt parent",
                    )
                expected_anchor = _lineage_root_for_attempt(
                    attempt_id,
                    parent_by_attempt_id,
                )
                if payload.get("quality_anchor_attempt_id") != expected_anchor:
                    _problem(
                        problems,
                        "auxiliary_quality_anchor_mismatch",
                        "quality_anchor_attempt_id must equal the deterministic lineage root "
                        "and must be null for a root Attempt",
                    )
            anchor_id = payload.get("quality_anchor_attempt_id")
            if anchor_id is not None and anchor_id not in attempts:
                _problem(
                    problems,
                    "unknown_quality_anchor",
                    f"auxiliary quality anchor {anchor_id} is not a known attempt",
                )
            if task_spec is not None:
                expected_prompt_sha = sha256_bytes(
                    task_spec.get("original_prompt", "").encode("utf-8")
                )
                if payload.get("prompt_sha256") != expected_prompt_sha:
                    _problem(
                        problems,
                        "auxiliary_quality_prompt_mismatch",
                        "HPSv3 must score every attempt against the immutable original prompt",
                    )
            if observation_is_valid:
                quality_profiles.add(
                    (
                        payload["evaluator_id"],
                        payload["evaluator_version"],
                        payload["checkpoint_sha256"],
                        payload["preprocess_version"],
                        payload["prompt_hash_policy_id"],
                        payload["quality_anchor_policy_id"],
                        payload["delta_policy_id"],
                        payload["risk_policy_sha256"],
                    )
                )
                if len(quality_profiles) > 1:
                    _problem(
                        problems,
                        "auxiliary_quality_profile_changed",
                        "HPSv3 evaluator, checkpoint, preprocessing, or policy changed "
                        "inside one episode",
                    )

                for baseline_field, delta_field in (
                    ("source_attempt_id", "delta_from_source"),
                    ("quality_anchor_attempt_id", "delta_from_anchor"),
                ):
                    baseline_id = payload[baseline_field]
                    baseline = quality_observations.get(baseline_id)
                    delta = payload[delta_field]
                    baseline_has_score = (
                        baseline is not None
                        and baseline.get("status") == "success"
                        and baseline.get("mu") is not None
                    )
                    current_has_score = payload["status"] == "success"
                    if baseline_id is not None and baseline_has_score and current_has_score:
                        expected_delta = float(payload["mu"]) - float(baseline["mu"])
                        if delta is None or not math.isclose(
                            float(delta),
                            expected_delta,
                            rel_tol=0.0,
                            abs_tol=1e-9,
                        ):
                            _problem(
                                problems,
                                "auxiliary_quality_delta_mismatch",
                                f"{delta_field} must equal child_mu - baseline_mu",
                            )
                    elif delta is not None:
                        _problem(
                            problems,
                            "auxiliary_quality_delta_without_baseline_score",
                            f"{delta_field} must be null when its baseline has no prior "
                            "successful HPSv3 score",
                        )

                expected_risk = quality_risk_for_source_delta(
                    payload["delta_from_source"],
                    payload["risk_policy"],
                )
                if payload["quality_risk"] != expected_risk:
                    _problem(
                        problems,
                        "auxiliary_quality_risk_mismatch",
                        "quality_risk does not match delta_from_source and the frozen risk policy",
                    )
                if attempt_id not in quality_observations:
                    quality_observations[attempt_id] = payload

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
    if len(execution_profiles) > 1:
        labels = sorted(f"{profile_id}@{version}" for profile_id, version in execution_profiles)
        _problem(
            problems,
            "mixed_execution_profiles",
            "one episode cannot mix execution profiles: " + ", ".join(labels),
        )
    if len(planner_context_versions) > 1:
        _problem(
            problems,
            "mixed_planner_context_versions",
            "one episode cannot mix PlannerContext versions: "
            + ", ".join(sorted(planner_context_versions)),
        )

    if problems:
        raise ProtocolValidationError(problems)
