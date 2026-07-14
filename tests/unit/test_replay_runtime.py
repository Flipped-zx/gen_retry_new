from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.cli.replay_episode import replay
from gen_retry.runtime.event_io import AppendOnlyEventStore, load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_view import build_planner_view
from gen_retry.runtime.reducer import reduce_events


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "one_episode_trajectory.jsonl"


def test_replay_is_byte_deterministic() -> None:
    first = replay(EXAMPLE)
    second = replay(EXAMPLE)

    assert canonical_json(first["state"]) == canonical_json(second["state"])
    assert canonical_json(first["planner_view"]) == canonical_json(second["planner_view"])


def test_reducer_reconstructs_non_monotonic_best_and_branch() -> None:
    state = reduce_events(load_events_jsonl(EXAMPLE))

    assert state.attempt_order == ["a_000", "a_001", "a_002"]
    assert state.latest_attempt_id == "a_002"
    assert state.best_attempt_id == "a_002"
    assert state.attempts["a_001"].parent_attempt_id == "a_000"
    assert state.attempts["a_002"].parent_attempt_id == "a_000"
    assert state.attempts["a_001"].failed_constraint_ids == ["c_004"]
    assert state.attempts["a_002"].failed_constraint_ids == []
    assert state.submitted_attempt_id == "a_002"


def test_planner_view_builder_outputs_schema_valid_compact_view() -> None:
    state = reduce_events(load_events_jsonl(EXAMPLE))
    view = build_planner_view(state)

    assert view["latest_attempt"]["attempt_id"] == "a_002"
    assert view["best_attempt"]["attempt_id"] == "a_002"
    assert view["remaining_budget"] == 0
    assert [item["attempt_id"] for item in view["compact_history"]] == [
        "a_000",
        "a_001",
        "a_002",
    ]
    assert {image["role"] for image in view["visible_images"]} == {"latest", "best"}


def test_append_only_event_store_deduplicates_event_ids(tmp_path: Path) -> None:
    events = load_events_jsonl(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    store = AppendOnlyEventStore(tmp_path / "events.jsonl")

    store.append(events[0])
    store.append(events[0])

    lines = store.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event_id"] == events[0]["event_id"]


def test_memory_reduced_mismatch_is_rejected() -> None:
    events = load_events_jsonl(ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl")
    memory_event = next(event for event in events if event["event_type"] == "memory_reduced")
    memory_event["payload"]["best_attempt_id"] = "a_999"

    with pytest.raises(ValueError, match="best_attempt_id"):
        reduce_events(events)
