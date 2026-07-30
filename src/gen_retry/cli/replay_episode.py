from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.domain.score_policy import (
    planner_context_version,
    score_policy_from_task_payload,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import build_planner_context_from_events
from gen_retry.runtime.planner_view import build_planner_view
from gen_retry.runtime.reducer import reduce_events


def replay(path: Path) -> dict:
    events = load_events_jsonl(path)
    state = reduce_events(events)
    planner_view = build_planner_view(state)
    context_version = planner_context_version(
        score_policy_from_task_payload(events[0]["payload"])
    )
    planner_context = build_planner_context_from_events(
        events,
        schema_version=context_version,
    )
    return {
        "state": state.to_dict(),
        "planner_view": planner_view,
        "planner_context": planner_context,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("events_jsonl", type=Path)
    parser.add_argument("--planner-view", action="store_true")
    parser.add_argument("--planner-context", action="store_true")
    args = parser.parse_args()
    result = replay(args.events_jsonl)
    key = "state"
    if args.planner_view:
        key = "planner_view"
    if args.planner_context:
        key = "planner_context"
    print(canonical_json(result[key]))


if __name__ == "__main__":
    main()
