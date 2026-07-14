from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.trajectory_validator import validate_trajectory_events
from gen_retry.runtime.json_canonical import canonical_json


def load_events_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                event = json.loads(line)
                validate_instance(event, "episode_event_v0_2.schema.json")
                events.append(event)
    validate_trajectory_events(events)
    return events


class AppendOnlyEventStore:
    def __init__(self, path: Path):
        self.path = path

    def append(self, event: dict[str, Any]) -> None:
        validate_instance(event, "episode_event_v0_2.schema.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing_ids = set()
        if self.path.exists():
            for existing in load_events_jsonl(self.path):
                existing_ids.add(existing["event_id"])
        if event["event_id"] in existing_ids:
            return
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(event))
            fh.write("\n")
