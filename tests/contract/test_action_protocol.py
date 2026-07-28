from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from gen_retry.protocol.action_parser import ActionParseError, invalid_action_observation, parse_action
from gen_retry.protocol.reference_validator import (
    ActionReferenceError,
    reference_error_observation,
    validate_action_references,
)
from gen_retry.protocol.schema_loader import validate_instance


ROOT = Path(__file__).resolve().parents[2]


def load_action(name: str) -> dict:
    with (ROOT / "tests" / "fixtures" / "actions" / name).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_task_spec() -> dict:
    with (ROOT / "tests" / "fixtures" / "task_spec" / "geneval2_minimal.json").open(
        "r", encoding="utf-8"
    ) as fh:
        return json.load(fh)


@pytest.mark.parametrize(
    "filename",
    [
        "query_skill.json",
        "generate_image.json",
        "edit_image.json",
        "submit_attempt.json",
    ],
)
def test_action_fixtures_validate(filename: str) -> None:
    validate_instance(load_action(filename), "action_protocol_v0_5.schema.json")


def test_parser_accepts_exact_json_action() -> None:
    action = load_action("generate_image.json")
    parsed = parse_action(json.dumps(action))
    assert parsed.action == action


def test_parser_rejects_markdown_or_extra_text() -> None:
    with pytest.raises(ActionParseError) as excinfo:
        parse_action("```json\n{}\n```")

    observation = invalid_action_observation(excinfo.value)
    assert observation["observation_type"] == "format_error"
    assert observation["error_code"] == "invalid_json"


def test_generate_image_does_not_accept_source_attempt() -> None:
    action = load_action("generate_image.json")
    action["arguments"]["source_attempt_id"] = "a_000"
    with pytest.raises(ValidationError):
        validate_instance(action, "action_protocol_v0_5.schema.json")


def test_edit_image_requires_existing_source_attempt() -> None:
    action = load_action("edit_image.json")
    task_spec = load_task_spec()
    validate_action_references(
        action,
        task_spec,
        known_attempt_ids=["a_000"],
        available_skill_ids=["counting_and_instance_layout", "spatial_relation_layout"],
    )

    with pytest.raises(ActionReferenceError) as excinfo:
        validate_action_references(
            action,
            task_spec,
            known_attempt_ids=[],
            available_skill_ids=["counting_and_instance_layout"],
        )

    observation = reference_error_observation(excinfo.value)
    assert observation["observation_type"] == "reference_error"
    assert "source_attempt_id" in observation["message"]


def test_reference_validator_rejects_unknown_constraint_and_skill() -> None:
    action = load_action("query_skill.json")
    task_spec = load_task_spec()
    action["arguments"]["target_constraint_ids"] = ["c_999"]

    with pytest.raises(ActionReferenceError) as excinfo:
        validate_action_references(
            action,
            task_spec,
            available_skill_ids=["counting_and_instance_layout"],
        )

    message = str(excinfo.value)
    assert "c_999" in message
    assert "spatial_relation_layout" in message


@pytest.mark.parametrize(
    "field,value",
    [
        ("score", 0.75),
        ("fixed", ["c_001"]),
        ("regressed", []),
        ("best_attempt_id", "a_000"),
        ("remaining_budget", 1),
        ("image_path", "artifacts/images/img_000.png"),
        ("geneval2_results", {"c_001": "pass"}),
    ],
)
def test_environment_owned_facts_are_not_valid_action_arguments(field: str, value) -> None:
    action = copy.deepcopy(load_action("edit_image.json"))
    action["arguments"][field] = value

    with pytest.raises(ValidationError):
        validate_instance(action, "action_protocol_v0_5.schema.json")


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "initial"),
        ("strategy_tags", ["legacy_tag"]),
        ("skill_ids_used", ["counting_layout"]),
        ("decision_summary", "Post-hoc rationale"),
        ("diagnosis_summary", None),
        ("diagnostic_hypotheses", []),
        ("interventions", []),
        ("repair_plan", []),
        ("change", "add objects"),
    ],
)
def test_v0_5_rejects_removed_image_action_fields(field: str, value) -> None:
    action = load_action("generate_image.json")
    action["arguments"][field] = value

    with pytest.raises(ValidationError):
        validate_instance(action, "action_protocol_v0_5.schema.json")


def test_v0_5_submit_rejects_decision_summary() -> None:
    action = load_action("submit_attempt.json")
    action["arguments"]["decision_summary"] = "Submit the best attempt."

    with pytest.raises(ValidationError):
        validate_instance(action, "action_protocol_v0_5.schema.json")


def test_v0_5_rejects_legacy_instruction_field_names() -> None:
    for action_name, legacy_field in (
        ("generate_image.json", "generation_instruction"),
        ("edit_image.json", "edit_instruction"),
    ):
        action = load_action(action_name)
        action["arguments"][legacy_field] = action["arguments"].pop("instruction")
        with pytest.raises(ValidationError):
            validate_instance(action, "action_protocol_v0_5.schema.json")


def test_reference_validator_rejects_target_preserve_overlap() -> None:
    action = load_action("edit_image.json")
    action["arguments"]["preserve_constraint_ids"].append("c_001")

    with pytest.raises(ActionReferenceError, match="both targeted and preserved"):
        validate_action_references(
            action,
            load_task_spec(),
            known_attempt_ids=["a_000"],
        )
