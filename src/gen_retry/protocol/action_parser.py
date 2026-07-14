from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from jsonschema.exceptions import ValidationError

from gen_retry.protocol.schema_loader import validate_instance


class ActionParseError(ValueError):
    """Raised when assistant output is not one strict canonical action."""

    def __init__(self, error_code: str, message: str):
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class ParsedAction:
    action: dict[str, Any]


def parse_action(raw_text: str) -> ParsedAction:
    """Parse a raw assistant turn as one strict v0.2 action JSON object."""

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ActionParseError("invalid_json", exc.msg) from exc

    if not isinstance(parsed, dict):
        raise ActionParseError("not_json_object", "Planner output must be a JSON object.")

    try:
        validate_instance(parsed, "action_protocol_v0_2.schema.json")
    except ValidationError as exc:
        raise ActionParseError("schema_validation_failed", str(exc)) from exc

    return ParsedAction(action=parsed)


def invalid_action_observation(error: ActionParseError) -> dict[str, str]:
    return {
        "schema_version": "0.2",
        "observation_type": "format_error",
        "error_code": error.error_code,
        "message": error.message,
    }
