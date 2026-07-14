from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_view import build_planner_view
from gen_retry.runtime.reducer import reduce_events


def replay(path: Path) -> dict:
    events = load_events_jsonl(path)
    state = reduce_events(events)
    planner_view = build_planner_view(state)
    return {
        "state": state.to_dict(),
        "planner_view": planner_view,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("events_jsonl", type=Path)
    parser.add_argument("--planner-view", action="store_true")
    args = parser.parse_args()
    result = replay(args.events_jsonl)
    print(canonical_json(result["planner_view" if args.planner_view else "state"]))


if __name__ == "__main__":
    main()
