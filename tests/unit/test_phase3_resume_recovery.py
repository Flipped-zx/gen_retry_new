from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.domain.artifacts import artifact_manifest_entry
from gen_retry.phase3.live_runner import (
    Phase3LiveRunner,
    _latest_image_round_chain,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.reducer import reduce_events


ROOT = Path(__file__).resolve().parents[2]
GOLDEN_EVENTS = (
    ROOT
    / "runs"
    / "teacher_prompt_v1_validation"
    / "phase3_ep_001"
    / "events.jsonl"
)


def _golden_events() -> list[dict]:
    if not GOLDEN_EVENTS.exists():
        pytest.skip("live golden events are not available")
    return load_events_jsonl(GOLDEN_EVENTS)


def _prefix_through(event_type: str) -> list[dict]:
    events = _golden_events()
    index = next(
        index
        for index, event in enumerate(events)
        if event["event_type"] == event_type
    )
    return events[: index + 1]


def _run_dir(tmp_path: Path, events: list[dict]) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    task_spec = events[0]["payload"]["task_spec"]
    (run_dir / "task_spec.json").write_text(
        canonical_json(task_spec) + "\n",
        encoding="utf-8",
    )
    artifacts = []
    completion = next(
        (
            event
            for event in events
            if event["event_type"] == "image_execution_completed"
        ),
        None,
    )
    if completion is not None:
        payload = completion["payload"]
        artifacts.append(
            artifact_manifest_entry(
                artifact_id=payload["image_artifact_id"],
                attempt_id=payload["attempt_id"],
                artifact_type="image",
                uri=f"images/{payload['image_artifact_id']}.png",
                sha256=payload["artifact_sha256"],
                media_type="image/png",
                producer="test",
                metadata={"cache_hit": True},
            )
        )
    (run_dir / "manifest.json").write_text(
        canonical_json(
            {
                "schema_version": "0.2",
                "episode_id": task_spec["episode_id"],
                "artifacts": artifacts,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "events.jsonl").write_text(
        "".join(canonical_json(event) + "\n" for event in events),
        encoding="utf-8",
    )
    geneval = next(
        (
            event
            for event in events
            if event["event_type"] == "geneval2_completed"
        ),
        None,
    )
    if geneval is not None:
        report_path = run_dir / geneval["payload"]["report_ref"]
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            canonical_json(
                {
                    "normalization": {"method": "test"},
                    "constraint_results": geneval["payload"]["constraint_results"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
    return run_dir


def test_image_round_chain_tracks_every_recovery_stage() -> None:
    events = [
        {"event_id": "e1", "event_type": "image_execution_started", "input_refs": ["a1"]},
        {"event_id": "e2", "event_type": "image_execution_completed", "input_refs": ["e1"]},
        {"event_id": "e3", "event_type": "geneval2_completed", "input_refs": ["e2"]},
        {"event_id": "e4", "event_type": "memory_reduced", "input_refs": ["e3"]},
        {"event_id": "e5", "event_type": "round_record_persisted", "input_refs": ["e4"]},
        {"event_id": "e6", "event_type": "planner_context_built", "input_refs": ["e5"]},
    ]

    for end, expected_missing in (
        (1, "complete"),
        (2, "geneval"),
        (3, "memory"),
        (4, "round_record"),
        (5, "planner_context"),
    ):
        chain = _latest_image_round_chain(events[:end])
        assert chain is not None
        assert chain[expected_missing] is None
    complete = _latest_image_round_chain(events)
    assert complete is not None
    assert complete["planner_context"] == events[-1]


def test_recovery_from_geneval_completes_memory_round_and_context(tmp_path: Path) -> None:
    prefix = _prefix_through("geneval2_completed")
    run_dir = _run_dir(tmp_path, prefix)
    runner = object.__new__(Phase3LiveRunner)

    recovered = runner._recover_incomplete_image_round(  # noqa: SLF001
        run_dir,
        task_spec=prefix[0]["payload"]["task_spec"],
        events=prefix,
        state=reduce_events(prefix),
    )

    assert recovered is True
    event_types = [event["event_type"] for event in load_events_jsonl(run_dir / "events.jsonl")]
    assert event_types[-3:] == [
        "memory_reduced",
        "round_record_persisted",
        "planner_context_built",
    ]
    assert (run_dir / "round_records" / "round_record_000.json").is_file()
    assert (run_dir / "planner_contexts" / "planner_context_000.json").is_file()


def test_recovery_from_memory_does_not_duplicate_memory(tmp_path: Path) -> None:
    prefix = _prefix_through("memory_reduced")
    run_dir = _run_dir(tmp_path, prefix)
    runner = object.__new__(Phase3LiveRunner)

    runner._recover_incomplete_image_round(  # noqa: SLF001
        run_dir,
        task_spec=prefix[0]["payload"]["task_spec"],
        events=prefix,
        state=reduce_events(prefix),
    )

    recovered = load_events_jsonl(run_dir / "events.jsonl")
    assert sum(event["event_type"] == "memory_reduced" for event in recovered) == 1
    assert [event["event_type"] for event in recovered[-2:]] == [
        "round_record_persisted",
        "planner_context_built",
    ]


def test_recovery_from_image_completion_evaluates_without_regeneration(
    tmp_path: Path,
    monkeypatch,
) -> None:
    prefix = _prefix_through("image_execution_completed")
    golden_geneval = next(
        event
        for event in _golden_events()
        if event["event_type"] == "geneval2_completed"
    )
    run_dir = _run_dir(tmp_path, prefix)
    runner = object.__new__(Phase3LiveRunner)
    calls = {"evaluate": 0, "generate": 0}

    def fake_evaluate(run_dir_arg, *, action_event, complete_event, **kwargs):
        del kwargs
        calls["evaluate"] += 1
        return runner._append_event(  # noqa: SLF001
            run_dir_arg,
            event_type="geneval2_completed",
            turn_id=action_event["turn_id"],
            producer="test_geneval2",
            input_refs=[complete_event["event_id"]],
            payload=golden_geneval["payload"],
        )

    def fail_generate(*args, **kwargs):
        del args, kwargs
        calls["generate"] += 1
        raise AssertionError("resume must not regenerate a completed image")

    monkeypatch.setattr(runner, "_evaluate_completed_image", fake_evaluate)
    monkeypatch.setattr(runner, "_execute_image_attempt", fail_generate)
    runner._recover_incomplete_image_round(  # noqa: SLF001
        run_dir,
        task_spec=prefix[0]["payload"]["task_spec"],
        events=prefix,
        state=reduce_events(prefix),
    )

    assert calls == {"evaluate": 1, "generate": 0}
    assert _latest_image_round_chain(load_events_jsonl(run_dir / "events.jsonl"))[
        "planner_context"
    ] is not None
