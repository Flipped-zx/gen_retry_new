from __future__ import annotations

import json
import copy
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from gen_retry.cli.validate_fixtures import validate_nested_event_payload
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.trajectory_validator import (
    ProtocolValidationError,
    validate_artifact_manifest_semantics,
    validate_task_spec_semantics,
    validate_trajectory_events,
)


ROOT = Path(__file__).resolve().parents[2]


def load_events(path: Path) -> list[dict]:
    events = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                events.append(json.loads(line))
    return events


def test_event_fixture_validates_with_nested_payloads() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    assert {event["event_type"] for event in events} >= {
        "task_created",
        "planner_output_recorded",
        "action_validated",
        "image_execution_started",
        "image_execution_completed",
        "geneval2_completed",
        "memory_reduced",
        "format_error",
    }
    for event in events:
        validate_instance(event, "episode_event_v0_2.schema.json")
        validate_nested_event_payload(event)


def test_event_schema_accepts_nested_v0_5_action_without_breaking_v0_2() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    action_event = copy.deepcopy(
        next(event for event in events if event["event_type"] == "action_validated")
    )
    action_event["payload"]["action"] = json.loads(
        (ROOT / "tests" / "fixtures" / "actions" / "generate_image.json").read_text(
            encoding="utf-8"
        )
    )

    validate_instance(action_event, "episode_event_v0_2.schema.json")
    validate_nested_event_payload(action_event)
    legacy_action_event = next(
        event for event in events if event["event_type"] == "action_validated"
    )
    validate_instance(legacy_action_event, "episode_event_v0_2.schema.json")
    validate_nested_event_payload(legacy_action_event)
    validate_trajectory_events(events)


def test_query_skill_fixture_enforces_real_tool_response() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "query_skill_events.jsonl")
    assert [event["event_type"] for event in events] == [
        "task_created",
        "action_validated",
        "skill_returned",
    ]
    validate_trajectory_events(events)


def test_example_trajectory_events_validate() -> None:
    events = load_events(ROOT / "examples" / "one_episode_trajectory.jsonl")
    assert events[-1]["event_type"] == "attempt_submitted"
    for event in events:
        validate_instance(event, "episode_event_v0_2.schema.json")
        validate_nested_event_payload(event)
    validate_trajectory_events(events)


def test_planner_output_event_requires_ref_not_raw_text() -> None:
    event = {
        "schema_version": "0.2",
        "event_id": "evt_9999",
        "episode_id": "ep_demo_001",
        "turn_id": "turn_000",
        "event_type": "planner_output_recorded",
        "created_at": "2026-07-14T06:00:00Z",
        "producer": "teacher",
        "payload": {
            "raw_output": "{\"action\":\"generate_image\"}",
            "raw_output_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    }

    with pytest.raises(ValidationError):
        validate_instance(event, "episode_event_v0_2.schema.json")


def test_action_validated_event_schema_rejects_invalid_nested_action() -> None:
    event = {
        "schema_version": "0.2",
        "event_id": "evt_9998",
        "episode_id": "ep_demo_001",
        "turn_id": "turn_000",
        "event_type": "action_validated",
        "created_at": "2026-07-14T06:00:00Z",
        "producer": "action_validator",
        "input_refs": ["evt_9997"],
        "payload": {
            "action": {
                "schema_version": "0.2",
                "action": "generate_image",
                "arguments": {
                    "mode": "initial",
                    "target_constraint_ids": ["c_001"],
                    "preserve_constraint_ids": [],
                    "strategy_tags": ["layout"],
                    "skill_ids_used": [],
                    "generation_instruction": "Create the requested image.",
                    "score": 0.5,
                },
            }
        },
    }

    with pytest.raises(ValidationError):
        validate_instance(event, "episode_event_v0_2.schema.json")


def test_completed_edit_requires_replayable_identity_fields() -> None:
    event = {
        "schema_version": "0.2",
        "event_id": "evt_9997",
        "episode_id": "ep_demo_001",
        "turn_id": "turn_001",
        "event_type": "image_execution_completed",
        "created_at": "2026-07-14T06:00:00Z",
        "producer": "qianwen_image_edit_adapter",
        "input_refs": ["evt_9996"],
        "payload": {
            "request_id": "req_ep_demo_001_turn_001",
            "operation": "edit",
            "backend": "qianwen_image_edit",
        },
    }

    with pytest.raises(ValidationError):
        validate_instance(event, "episode_event_v0_2.schema.json")


def test_generate_payload_cannot_smuggle_source_attempt() -> None:
    event = {
        "schema_version": "0.2",
        "event_id": "evt_9996",
        "episode_id": "ep_demo_001",
        "turn_id": "turn_000",
        "event_type": "image_execution_started",
        "created_at": "2026-07-14T06:00:00Z",
        "producer": "qianwen_image_edit_adapter",
        "input_refs": ["evt_9995"],
        "payload": {
            "request_id": "req_ep_demo_001_turn_000",
            "operation": "generate",
            "backend": "qianwen_image_edit",
            "source_attempt_id": "a_000",
        },
    }

    with pytest.raises(ValidationError):
        validate_instance(event, "episode_event_v0_2.schema.json")


def test_image_start_cannot_declare_attempt_lineage() -> None:
    event = {
        "schema_version": "0.2",
        "event_id": "evt_9995",
        "episode_id": "ep_demo_001",
        "turn_id": "turn_000",
        "event_type": "image_execution_started",
        "created_at": "2026-07-14T06:00:00Z",
        "producer": "qianwen_image_edit_adapter",
        "input_refs": ["evt_9994"],
        "payload": {
            "request_id": "req_ep_demo_001_turn_000",
            "operation": "generate",
            "backend": "qianwen_image_edit",
            "attempt_id": "a_999",
            "parent_attempt_id": "a_998",
        },
    }

    with pytest.raises(ValidationError):
        validate_instance(event, "episode_event_v0_2.schema.json")


def test_unlinked_or_mismatched_skill_return_is_rejected() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "query_skill_events.jsonl")
    events[-1]["payload"]["query_action_event_id"] = "evt_0999"
    events[-1]["payload"]["skills"][0]["skill_id"] = "different_skill"

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    message = str(excinfo.value)
    assert "unlinked_skill_returned" in message
    assert "skill_payload_mismatch" in message


def test_duplicate_skill_response_for_query_is_rejected() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "query_skill_events.jsonl")
    duplicate = copy.deepcopy(events[-1])
    duplicate["event_id"] = "evt_0103"
    events.append(duplicate)

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "duplicate_skill_returned" in str(excinfo.value)


def test_duplicate_constraint_ids_are_semantically_invalid() -> None:
    task_spec = {
        "schema_version": "0.2",
        "episode_id": "ep_duplicate_constraints",
        "original_prompt": "Two equivalent IDs should be rejected.",
        "constraints": [
            {
                "constraint_id": "c_001",
                "constraint_type": "count",
                "requirement": "There is one apple.",
            },
            {
                "constraint_id": "c_001",
                "constraint_type": "spatial",
                "requirement": "The apple is left of the bowl.",
            },
        ],
        "max_image_attempts": 3,
    }

    with pytest.raises(ProtocolValidationError):
        validate_task_spec_semantics(task_spec)


def test_duplicate_artifact_ids_are_semantically_invalid() -> None:
    manifest = {
        "schema_version": "0.2",
        "episode_id": "ep_duplicate_artifacts",
        "artifacts": [
            {
                "artifact_id": "img_000",
                "artifact_type": "image",
                "uri": "artifacts/images/img_000.png",
                "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "media_type": "image/png",
                "producer": "fake_qianwen_image_edit_adapter",
            },
            {
                "artifact_id": "img_000",
                "artifact_type": "image",
                "uri": "artifacts/images/img_000_copy.png",
                "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "media_type": "image/png",
                "producer": "fake_qianwen_image_edit_adapter",
            },
        ],
    }

    with pytest.raises(ProtocolValidationError):
        validate_artifact_manifest_semantics(manifest)


def test_duplicate_constraint_observations_are_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    geneval_event = next(event for event in events if event["event_type"] == "geneval2_completed")
    geneval_event["payload"]["constraint_results"].append(
        {
            "constraint_id": "c_001",
            "status": "pass",
        }
    )

    with pytest.raises(ProtocolValidationError):
        validate_trajectory_events(events)


def test_incomplete_geneval2_result_is_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    geneval_event = next(event for event in events if event["event_type"] == "geneval2_completed")
    geneval_event["payload"]["constraint_results"] = [
        result
        for result in geneval_event["payload"]["constraint_results"]
        if result["constraint_id"] != "c_004"
    ]

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "incomplete_geneval2_result" in str(excinfo.value)


def test_cross_episode_skill_response_is_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "query_skill_events.jsonl")
    events[-1]["episode_id"] = "ep_other"

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "episode_id_mismatch" in str(excinfo.value)


def test_task_created_envelope_must_match_nested_task_episode() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "query_skill_events.jsonl")
    events[0]["payload"]["task_spec"]["episode_id"] = "ep_other"

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "task_episode_mismatch" in str(excinfo.value)


def test_actions_before_task_created_are_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "query_skill_events.jsonl")
    reordered = [events[1], events[0], events[2]]

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(reordered)

    message = str(excinfo.value)
    assert "task_created_not_first" in message
    assert "action_before_task_created" in message


def test_duplicate_geneval2_result_for_attempt_is_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    geneval_event = next(event for event in events if event["event_type"] == "geneval2_completed")
    duplicate = copy.deepcopy(geneval_event)
    duplicate["event_id"] = "evt_0998"
    events.append(duplicate)

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "duplicate_geneval2_result" in str(excinfo.value)


def test_orphan_completion_reusing_image_artifact_is_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    events.append(
        {
            "schema_version": "0.2",
            "event_id": "evt_0999",
            "episode_id": "ep_demo_001",
            "turn_id": "turn_099",
            "event_type": "image_execution_completed",
            "created_at": "2026-07-14T06:00:00Z",
            "producer": "qianwen_image_edit_adapter",
            "input_refs": ["evt_0990"],
            "payload": {
                "request_id": "req_missing",
                "attempt_id": "a_999",
                "parent_attempt_id": None,
                "operation": "generate",
                "backend": "qianwen_image_edit",
                "image_artifact_id": "img_000",
                "artifact_manifest_ref": "artifacts/manifest.json",
                "artifact_sha256": "9999999999999999999999999999999999999999999999999999999999999999",
            },
        }
    )

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    message = str(excinfo.value)
    assert "orphan_image_completion" in message
    assert "duplicate_image_artifact_id" in message


def test_image_start_without_validated_action_is_semantically_invalid() -> None:
    events = load_events(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    start_event = next(event for event in events if event["event_type"] == "image_execution_started")
    start_event["input_refs"] = ["evt_0001"]

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "image_start_action_ref" in str(excinfo.value)


def test_submission_without_validated_submit_action_is_semantically_invalid() -> None:
    events = load_events(ROOT / "examples" / "one_episode_trajectory.jsonl")
    submit_event = events[-1]
    assert submit_event["event_type"] == "attempt_submitted"
    submit_event["payload"]["submit_action_event_id"] = "evt_0999"
    submit_event["input_refs"] = ["a_002"]

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    message = str(excinfo.value)
    assert "unlinked_attempt_submission" in message
    assert "missing_submission_action_ref" in message


def test_submission_payload_must_match_submit_action() -> None:
    events = load_events(ROOT / "examples" / "one_episode_trajectory.jsonl")
    submit_event = events[-1]
    submit_event["payload"]["selected_attempt_id"] = "a_001"

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    assert "submission_attempt_mismatch" in str(excinfo.value)
