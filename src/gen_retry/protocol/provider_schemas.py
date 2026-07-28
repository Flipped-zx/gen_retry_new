from __future__ import annotations

from typing import Any


ALLOWED_ACTIONS = {"query_skill", "generate_image", "edit_image", "submit_attempt"}


def provider_response_schema_for_action(action: str) -> dict[str, Any]:
    """Return a conservative action-specific JSON schema for provider response_format.

    Some OpenAI-compatible endpoints reject full local schemas with top-level oneOf
    or uniqueItems. Runtime validation remains authoritative; this schema is only
    a provider-side formatting aid.
    """

    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"unknown planner action: {action}")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "action", "arguments"],
        "properties": {
            "schema_version": {"const": "0.5"},
            "action": {"const": action},
            "arguments": _provider_arguments_schema(action),
        },
    }


def _provider_arguments_schema(action: str) -> dict[str, Any]:
    if action == "query_skill":
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["skill_ids", "target_constraint_ids"],
            "properties": {
                "skill_ids": _string_array(min_items=1, max_items=3),
                "target_constraint_ids": _constraint_array(min_items=1),
            },
        }
    if action == "generate_image":
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "target_constraint_ids",
                "preserve_constraint_ids",
                "instruction",
            ],
            "properties": {
                "target_constraint_ids": _constraint_array(min_items=1),
                "preserve_constraint_ids": _constraint_array(min_items=0),
                "instruction": {"type": "string"},
            },
        }
    if action == "edit_image":
        return {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "source_attempt_id",
                "target_constraint_ids",
                "preserve_constraint_ids",
                "instruction",
            ],
            "properties": {
                "source_attempt_id": {"type": "string"},
                "target_constraint_ids": _constraint_array(min_items=1),
                "preserve_constraint_ids": _constraint_array(min_items=0),
                "instruction": {"type": "string"},
            },
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["selected_attempt_id", "reason_code"],
        "properties": {
            "selected_attempt_id": {"type": "string"},
            "reason_code": {
                "type": "string",
                "enum": [
                    "all_constraints_passed",
                    "best_available_under_budget",
                    "no_productive_action_remaining",
                ],
            },
        },
    }


def _constraint_array(*, min_items: int) -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": min_items,
        "items": {"type": "string", "pattern": "^c_[0-9]{3,}$"},
    }


def _string_array(*, min_items: int, max_items: int) -> dict[str, Any]:
    return {
        "type": "array",
        "minItems": min_items,
        "maxItems": max_items,
        "items": {"type": "string"},
    }
