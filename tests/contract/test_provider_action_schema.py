from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from gen_retry.protocol.provider_schemas import provider_response_schema_for_action
from gen_retry.protocol.reference_validator import ActionReferenceError, validate_action_references


ROOT = Path(__file__).resolve().parents[2]


def _load_action(name: str) -> dict:
    return json.loads((ROOT / "tests" / "fixtures" / "actions" / name).read_text(encoding="utf-8"))


def _load_task_spec() -> dict:
    return json.loads(
        (ROOT / "tests" / "fixtures" / "task_spec" / "geneval2_minimal.json").read_text(
            encoding="utf-8"
        )
    )


def _contains_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


@pytest.mark.parametrize("action_name", ["query_skill", "generate_image", "edit_image", "submit_attempt"])
def test_provider_schema_avoids_known_unsupported_keywords(action_name: str) -> None:
    schema = provider_response_schema_for_action(action_name)

    assert not _contains_key(schema, "oneOf")
    assert not _contains_key(schema, "uniqueItems")


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "initial"),
        ("strategy_tags", ["legacy"]),
        ("skill_ids_used", ["counting_edit"]),
        ("decision_summary", "rationale"),
        ("diagnosis_summary", None),
        ("diagnostic_hypotheses", []),
        ("interventions", []),
    ],
)
def test_provider_schema_rejects_removed_image_fields(field: str, value) -> None:
    action = _load_action("generate_image.json")
    action["arguments"][field] = value
    schema = provider_response_schema_for_action("generate_image")

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(action)


def test_runtime_validator_rejects_semantic_bindings_provider_cannot_know() -> None:
    action = copy.deepcopy(_load_action("edit_image.json"))
    task_spec = _load_task_spec()

    with pytest.raises(ActionReferenceError):
        validate_action_references(
            action,
            task_spec,
            known_attempt_ids=[],
            available_skill_ids=["counting_and_instance_layout"],
        )
