from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gen_retry.protocol.schema_loader import PROJECT_ROOT, validate_instance
from gen_retry.protocol.trajectory_validator import (
    validate_artifact_manifest_semantics,
    validate_task_spec_semantics,
    validate_trajectory_events,
)


FIXTURE_SCHEMA_MAP = {
    "tests/fixtures/task_spec": "task_spec_v0_2.schema.json",
    "tests/fixtures/actions": "action_protocol_v0_5.schema.json",
    "tests/fixtures/events": "episode_event_v0_2.schema.json",
    "tests/fixtures/planner_views": "planner_view_v0_2.schema.json",
    "tests/fixtures/planner_contexts": "planner_context_v0_7.schema.json",
    "tests/fixtures/artifacts": "artifact_manifest_v0_2.schema.json",
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validate_jsonl(path: Path, schema_name: str) -> int:
    count = 0
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            validate_instance(record, schema_name)
            if schema_name == "episode_event_v0_2.schema.json":
                validate_nested_event_payload(record)
                records.append(record)
            count += 1
    if count == 0:
        raise ValueError(f"{path}:{lineno} contained no JSONL records")
    if schema_name == "episode_event_v0_2.schema.json":
        validate_trajectory_events(records)
    return count


def validate_nested_event_payload(event: dict[str, Any]) -> None:
    payload = event.get("payload", {})
    if event.get("event_type") == "task_created":
        validate_instance(payload["task_spec"], "task_spec_v0_2.schema.json")
    if event.get("event_type") == "action_validated":
        action_schema_by_version = {
            "0.2": "action_protocol_v0_2.schema.json",
            "0.3": "action_protocol_v0_3.schema.json",
            "0.4": "action_protocol_v0_4.schema.json",
            "0.5": "action_protocol_v0_5.schema.json",
        }
        schema_name = action_schema_by_version[payload["action"].get("schema_version")]
        validate_instance(payload["action"], schema_name)


def validate_fixture_tree(root: Path = PROJECT_ROOT) -> int:
    validated = 0
    for rel_dir, schema_name in FIXTURE_SCHEMA_MAP.items():
        directory = root / rel_dir
        for path in sorted(directory.glob("*.json")):
            record = _load_json(path)
            validate_instance(record, schema_name)
            if schema_name == "task_spec_v0_2.schema.json":
                validate_task_spec_semantics(record)
            if schema_name == "artifact_manifest_v0_2.schema.json":
                validate_artifact_manifest_semantics(record)
            validated += 1
        for path in sorted(directory.glob("*.jsonl")):
            validated += _validate_jsonl(path, schema_name)

    example = root / "examples" / "one_episode_trajectory.jsonl"
    if example.exists():
        validated += _validate_jsonl(example, "episode_event_v0_2.schema.json")

    mock_root = root / "tests" / "fixtures" / "mock_episodes"
    for path in sorted(mock_root.glob("*/events.jsonl")):
        validated += _validate_jsonl(path, "episode_event_v0_2.schema.json")

    return validated


def main() -> None:
    count = validate_fixture_tree()
    print(f"validated {count} fixture records")


if __name__ == "__main__":
    main()
