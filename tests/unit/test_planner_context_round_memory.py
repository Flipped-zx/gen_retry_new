from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import (
    build_planner_context_from_events,
    build_round_records_from_events,
)
from gen_retry.runtime.reducer import reduce_events
from gen_retry.phase3.live_runner import Phase3LiveRunner


ROOT = Path(__file__).resolve().parents[2]
GOLDEN_RUN = ROOT / "runs" / "teacher_prompt_v1_validation" / "phase3_ep_001" / "events.jsonl"


def _golden_events() -> list[dict]:
    if not GOLDEN_RUN.exists():
        pytest.skip("phase3_ep_001 golden live events are not present in this checkout")
    return load_events_jsonl(GOLDEN_RUN)


def test_golden_replay_round_memory_tracks_query_and_image_rounds() -> None:
    events = _golden_events()
    rounds = build_round_records_from_events(events)
    state = reduce_events(events)

    assert len(rounds) == 5
    assert state.attempt_order == ["a_000", "a_001", "a_002", "a_003", "a_004"]
    assert rounds[0]["round_id"] == "r_000"
    assert rounds[0]["skill_queries"] == [
        {
            "skill_id": "counting_and_instance_layout",
            "target_constraint_ids": ["c_001", "c_005", "c_009"],
        },
        {
            "skill_id": "spatial_relation_layout",
            "target_constraint_ids": ["c_004", "c_008"],
        },
    ]
    assert rounds[0]["image_action"]["action"] == "generate_image"
    assert rounds[0]["result_attempt_id"] == "a_000"


def test_golden_replay_rollback_outcome_uses_action_source_not_latest() -> None:
    rounds = build_round_records_from_events(_golden_events())
    rollback_round = rounds[4]

    assert rollback_round["image_action"]["action"] == "edit_image"
    assert rollback_round["image_action"]["source_attempt_id"] == "a_002"
    assert rollback_round["result_attempt_id"] == "a_004"
    assert rollback_round["observed_outcome"]["comparison_attempt_id"] == "a_002"
    assert rollback_round["observed_outcome"]["regressed_constraint_ids"] == []
    assert rollback_round["observed_outcome"]["persistent_failed_constraint_ids"] == [
        "c_004",
        "c_008",
    ]


def test_golden_replay_latest_best_and_submit_are_separate() -> None:
    events = _golden_events()
    state = reduce_events(events)
    context = build_planner_context_from_events(events)

    assert state.latest_attempt_id == "a_004"
    assert state.best_attempt_id == "a_002"
    assert state.submitted_attempt_id == "a_002"
    assert context["latest_attempt"]["attempt_id"] == "a_004"
    assert context["episode_memory"]["best_attempt"]["attempt_id"] == "a_002"
    assert "constraint_results_ref" not in context["episode_memory"]["best_attempt"]
    assert context["runtime_state"] == {
        "remaining_image_budget": 0,
        "available_actions": ["submit_attempt"],
    }
    assert len(state.attempt_order) == 5


def test_planner_context_is_deterministic_for_same_event_prefix() -> None:
    events = _golden_events()
    prefix = events[:24]

    first = build_planner_context_from_events(prefix)
    second = build_planner_context_from_events(prefix)

    assert canonical_json(first) == canonical_json(second)


def test_planner_context_does_not_include_future_rounds() -> None:
    events = _golden_events()
    prefix = events[:24]
    context = build_planner_context_from_events(prefix)

    assert context["latest_attempt"]["attempt_id"] == "a_001"
    assert context["episode_memory"]["best_attempt"]["attempt_id"] == "a_001"
    assert context["episode_memory"]["best_attempt"]["constraint_results_ref"] == "latest_attempt"
    assert (
        context["episode_memory"]["last_completed_image_round"]["result_attempt_id"]
        == "a_001"
    )
    assert all(
        item["result_attempt_id"] != "a_002"
        for item in context["episode_memory"]["prior_image_rounds"]
    )


def test_v0_5_prior_rounds_exclude_last_round_and_best_deduplicates_latest() -> None:
    events = _golden_events()
    prefix = events[:24]
    context = build_planner_context_from_events(prefix)
    memory = context["episode_memory"]

    last_attempt_id = memory["last_completed_image_round"]["result_attempt_id"]
    assert all(
        item["result_attempt_id"] != last_attempt_id
        for item in memory["prior_image_rounds"]
    )
    assert memory["best_attempt"] == {
        "attempt_id": context["latest_attempt"]["attempt_id"],
        "constraint_results_ref": "latest_attempt",
    }


def test_v0_4_planner_context_remains_available_for_historical_replay() -> None:
    context = build_planner_context_from_events(_golden_events()[:24], schema_version="0.4")

    assert context["latest_observation"]["attempt_id"] == "a_001"
    assert context["episode_memory"]["recent_round"]["result_attempt_id"] == "a_001"
    assert "earlier_rounds" in context["episode_memory"]


def test_live_runner_persists_completed_round_record(tmp_path: Path) -> None:
    events = _golden_events()
    first_memory_index = next(
        index for index, event in enumerate(events) if event["event_type"] == "memory_reduced"
    )
    prefix = events[: first_memory_index + 1]
    task_spec = prefix[0]["payload"]["task_spec"]
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "task_spec.json").write_text(canonical_json(task_spec) + "\n", encoding="utf-8")
    (run_dir / "manifest.json").write_text(
        canonical_json(
            {
                "schema_version": "0.2",
                "episode_id": task_spec["episode_id"],
                "artifacts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text(
        "\n".join(canonical_json(event) for event in prefix) + "\n",
        encoding="utf-8",
    )

    runner = object.__new__(Phase3LiveRunner)
    event = runner._persist_latest_round_record(  # noqa: SLF001
        run_dir,
        turn_id="turn_test",
        input_refs=[prefix[-1]["event_id"]],
    )

    assert event["event_type"] == "round_record_persisted"
    assert event["payload"]["round_id"] == "r_000"
    assert event["payload"]["result_attempt_id"] == "a_000"
    assert (run_dir / "round_records" / "round_record_000.json").exists()
    manifest = canonical_json(
        {
            artifact["artifact_id"]: artifact["artifact_type"]
            for artifact in json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))[
                "artifacts"
            ]
        }
    )
    assert '"round_record_000":"round_record"' in manifest
