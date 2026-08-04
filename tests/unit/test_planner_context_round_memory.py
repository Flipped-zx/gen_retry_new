from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.score_policy import (
    canonical_primary_score,
    primary_score_policy,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import (
    _skill_guidance,
    build_planner_context_from_events,
    build_round_records_from_events,
    visible_images_from_state,
)
from gen_retry.runtime.reducer import AttemptRecord, EpisodeState, reduce_events
from gen_retry.phase3.live_runner import Phase3LiveRunner


ROOT = Path(__file__).resolve().parents[2]
GOLDEN_RUN = ROOT / "runs" / "teacher_prompt_v1_validation" / "phase3_ep_001" / "events.jsonl"


def _golden_events() -> list[dict]:
    if not GOLDEN_RUN.exists():
        pytest.skip("phase3_ep_001 golden live events are not present in this checkout")
    return load_events_jsonl(GOLDEN_RUN)


def _score_enabled_one_attempt_events() -> list[dict]:
    path = ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl"
    events = load_events_jsonl(path)
    events[0]["payload"]["score_policy"] = primary_score_policy()
    geneval = next(
        event for event in events if event["event_type"] == "geneval2_completed"
    )
    confidences = [0.10, 0.80, 0.90, 0.70]
    for result, confidence in zip(
        geneval["payload"]["constraint_results"],
        confidences,
        strict=True,
    ):
        result["confidence"] = confidence
    geneval["payload"]["primary_score"] = canonical_primary_score(
        geneval["payload"]["constraint_results"]
    )
    return events


def _score_enabled_two_attempt_events() -> list[dict]:
    events = _score_enabled_one_attempt_events()
    results = [
        {
            "constraint_id": "c_001",
            "status": "fail",
            "expected": "exactly three apples",
            "observed": "two apples",
            "confidence": 0.20,
        },
        {"constraint_id": "c_002", "status": "pass", "confidence": 0.95},
        {"constraint_id": "c_003", "status": "pass", "confidence": 0.95},
        {"constraint_id": "c_004", "status": "pass", "confidence": 0.95},
    ]
    events.extend(
        [
            {
                "schema_version": "0.2",
                "event_id": "evt_0010",
                "episode_id": "ep_demo_001",
                "turn_id": "turn_001",
                "event_type": "action_validated",
                "created_at": "2026-07-14T06:00:00Z",
                "producer": "action_validator",
                "input_refs": ["evt_0009"],
                "payload": {
                    "action": {
                        "schema_version": "0.5",
                        "action": "edit_image",
                        "arguments": {
                            "source_attempt_id": "a_000",
                            "target_constraint_ids": ["c_001"],
                            "preserve_constraint_ids": ["c_002", "c_003", "c_004"],
                            "instruction": "Add exactly one apple and preserve the bowl.",
                        },
                    }
                },
            },
            {
                "schema_version": "0.2",
                "event_id": "evt_0011",
                "episode_id": "ep_demo_001",
                "turn_id": "turn_001",
                "event_type": "image_execution_started",
                "created_at": "2026-07-14T06:00:00Z",
                "producer": "qianwen_image_edit_adapter",
                "input_refs": ["evt_0010"],
                "payload": {
                    "request_id": "req_ep_demo_001_turn_001",
                    "operation": "edit",
                    "backend": "qianwen_image_edit",
                    "source_attempt_id": "a_000",
                },
            },
            {
                "schema_version": "0.2",
                "event_id": "evt_0012",
                "episode_id": "ep_demo_001",
                "turn_id": "turn_001",
                "event_type": "image_execution_completed",
                "created_at": "2026-07-14T06:00:00Z",
                "producer": "qianwen_image_edit_adapter",
                "input_refs": ["evt_0011"],
                "payload": {
                    "request_id": "req_ep_demo_001_turn_001",
                    "attempt_id": "a_001",
                    "parent_attempt_id": "a_000",
                    "operation": "edit",
                    "backend": "qianwen_image_edit",
                    "source_attempt_id": "a_000",
                    "image_artifact_id": "img_001",
                    "artifact_manifest_ref": "artifacts/manifest.json",
                    "artifact_sha256": "e" * 64,
                },
            },
            {
                "schema_version": "0.2",
                "event_id": "evt_0013",
                "episode_id": "ep_demo_001",
                "turn_id": "turn_001",
                "event_type": "geneval2_completed",
                "created_at": "2026-07-14T06:00:00Z",
                "producer": "geneval2_adapter",
                "input_refs": ["evt_0012"],
                "payload": {
                    "attempt_id": "a_001",
                    "constraint_results": results,
                    "primary_score": canonical_primary_score(results),
                    "report_ref": "artifacts/geneval2/a_001.json",
                    "report_sha256": "f" * 64,
                },
            },
        ]
    )
    return events


def test_v0_6_context_exposes_observed_score_without_duplicating_best() -> None:
    events = _score_enabled_one_attempt_events()
    context = build_planner_context_from_events(events, schema_version="0.6")
    expected_score = events[6]["payload"]["primary_score"]["value"]

    assert context["planner_context_schema_version"] == "0.6"
    assert context["latest_attempt"]["primary_score"] == expected_score
    assert context["episode_memory"]["best_attempt"] == {
        "attempt_id": "a_000",
        "constraint_results_ref": "latest_attempt",
    }
    assert (
        context["episode_memory"]["last_completed_image_round"][
            "observed_outcome"
        ]["primary_score_delta"]
        is None
    )
    assert context["runtime_state"]["score_policy"] == primary_score_policy()


def test_v0_6_equal_pass_count_uses_gm_and_records_source_delta() -> None:
    events = _score_enabled_two_attempt_events()
    state = reduce_events(events)
    context = build_planner_context_from_events(events, schema_version="0.6")
    latest = context["latest_attempt"]
    outcome = context["episode_memory"]["last_completed_image_round"][
        "observed_outcome"
    ]

    assert state.attempts["a_000"].pass_count == state.attempts["a_001"].pass_count
    assert state.best_attempt_id == "a_001"
    assert latest["attempt_id"] == "a_001"
    assert context["episode_memory"]["best_attempt"] == {
        "attempt_id": "a_001",
        "constraint_results_ref": "latest_attempt",
    }
    assert outcome["baseline_attempt_id"] == "a_000"
    assert outcome["primary_score_delta"] == (
        state.attempts["a_001"].primary_score
        - state.attempts["a_000"].primary_score
    )


def test_v0_7_retains_prior_image_instructions() -> None:
    events = _score_enabled_two_attempt_events()
    context = build_planner_context_from_events(events, schema_version="0.7")

    assert context["planner_context_schema_version"] == "0.7"
    prior = context["episode_memory"]["prior_image_rounds"]
    assert len(prior) == 1
    assert prior[0]["result_attempt_id"] == "a_000"
    first_action = next(
        event["payload"]["action"]
        for event in events
        if event["event_type"] == "action_validated"
    )
    assert prior[0]["instruction"] == first_action["arguments"][
        "generation_instruction"
    ]


def test_skill_guidance_uses_hash_matched_retrieval_observation(
    tmp_path: Path,
) -> None:
    current_path = tmp_path / "SKILL.md"
    current_path.write_text("new content", encoding="utf-8")
    old_content = "old immutable content"

    skill = {
        "content_ref": str(current_path),
        "content_sha256": sha256_bytes(old_content.encode("utf-8")),
        "summary": "old summary",
    }

    assert _skill_guidance(
        skill,
        observed_skill={"content": old_content},
    ) == old_content
    assert _skill_guidance(skill) == "old summary"


def test_visible_images_include_same_count_historical_evidence_candidate() -> None:
    def attempt(
        attempt_id: str,
        statuses: dict[str, str],
        artifact_id: str,
    ) -> AttemptRecord:
        return AttemptRecord(
            attempt_id=attempt_id,
            parent_attempt_id=None,
            action_event_id=f"evt_{attempt_id[2:]}",
            action={
                "schema_version": "0.5",
                "action": "generate_image",
                "arguments": {
                    "target_constraint_ids": sorted(statuses),
                    "preserve_constraint_ids": [],
                    "instruction": "test",
                },
            },
            operation="generate",
            image_artifact_id=artifact_id,
            constraint_results={
                constraint_id: {"status": status}
                for constraint_id, status in statuses.items()
            },
            primary_score=0.5,
        )

    historical = attempt(
        "a_000",
        {"c_001": "pass", "c_002": "fail", "c_003": "pass"},
        "img_000",
    )
    best = attempt(
        "a_001",
        {"c_001": "pass", "c_002": "pass", "c_003": "fail"},
        "img_001",
    )
    state = EpisodeState(
        schema_version="0.2",
        episode_id="ep_visibility",
        task_spec={"max_image_attempts": 5},
        score_policy=primary_score_policy(),
        attempts={"a_000": historical, "a_001": best},
        attempt_order=["a_000", "a_001"],
        latest_attempt_id="a_001",
        best_attempt_id="a_001",
        remaining_budget=3,
    )

    assert visible_images_from_state(state) == [
        {"artifact_id": "img_001", "role": "latest", "attempt_id": "a_001"},
        {
            "artifact_id": "img_000",
            "role": "historical_candidate",
            "attempt_id": "a_000",
        },
    ]


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
