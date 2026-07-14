from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from gen_retry.protocol.schema_loader import validate_instance


ROOT = Path(__file__).resolve().parents[2]


def load_planner_view() -> dict:
    with (ROOT / "tests" / "fixtures" / "planner_views" / "after_failed_attempt.json").open(
        "r", encoding="utf-8"
    ) as fh:
        return json.load(fh)


def test_planner_view_fixture_validates() -> None:
    validate_instance(load_planner_view(), "planner_view_v0_2.schema.json")


@pytest.mark.parametrize(
    "location,field,value",
    [
        (("latest_attempt",), "raw_output", "assistant text"),
        (("latest_attempt",), "image_path", "artifacts/images/img_000.png"),
        (("latest_transition",), "score", 0.75),
        (("visible_images", 0), "path", "artifacts/images/img_000.png"),
    ],
)
def test_planner_view_excludes_raw_outputs_and_paths(location: tuple, field: str, value) -> None:
    planner_view = load_planner_view()
    target = planner_view
    for part in location:
        target = target[part]
    target[field] = value

    with pytest.raises(ValidationError):
        validate_instance(planner_view, "planner_view_v0_2.schema.json")
