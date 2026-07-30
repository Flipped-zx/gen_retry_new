from __future__ import annotations

import json
import pytest

from pathlib import Path

from gen_retry.domain.score_policy import (
    canonical_primary_score,
    primary_score_policy,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import build_planner_context_from_events
from gen_retry.sft.supervision import (
    _execution_profile_for_run,
    _index_identical_records,
    _validate_planner_context_prefix,
    decide_supervision,
    render_messages,
)

ROOT = Path(__file__).resolve().parents[2]


def _label(action: str, label: str = "trainable_positive") -> dict:
    record = {
        "schema_version": "0.5",
        "episode_id": "phase3_ep_001",
        "request_id": "phase3_ep_001_turn_001",
        "turn_id": "turn_001",
        "action_event_id": "evt_0004",
        "action": action,
        "label": label,
    }
    if action != "invalid_raw_output":
        record["canonical_action"] = {
            "schema_version": "0.5",
            "action": action,
            "arguments": {
                "selected_attempt_id": "a_000",
                "reason_code": "all_constraints_passed",
            },
        }
    return record


def test_supervision_decision_targets_positive_image_and_submit_actions() -> None:
    decision = decide_supervision(_label("submit_attempt", "recovery_positive"))

    assert decision["include_as_target"] is True
    assert decision["loss_weight"] == 1
    assert decision["decision_reason"] == "positive_or_recovery_canonical_action"


def test_supervision_decision_masks_positive_query_skill() -> None:
    decision = decide_supervision(_label("query_skill", "trainable_positive"))

    assert decision["include_as_target"] is False
    assert decision["loss_weight"] == 0
    assert decision["decision_reason"] == "query_skill_context_only_until_utility_validated"


def test_supervision_decision_excludes_harmful_and_raw_records() -> None:
    harmful = decide_supervision(_label("edit_image", "history_only_harmful"))
    raw = decide_supervision(_label("invalid_raw_output", "excluded_invalid"))

    assert harmful["include_as_target"] is False
    assert harmful["decision_reason"] == "label_history_only_harmful_context_only"
    assert raw["include_as_target"] is False
    assert raw["decision_reason"] == "raw_teacher_output_excluded"


def test_supervision_decision_excludes_legacy_protocol_actions() -> None:
    label = _label("generate_image")
    label["canonical_action"]["schema_version"] = "0.4"

    decision = decide_supervision(label)

    assert decision["include_as_target"] is False
    assert decision["decision_reason"] == "non_v0_5_action_context_only"


def test_render_messages_masks_only_assistant_target() -> None:
    messages = render_messages(
        task_spec={
            "schema_version": "0.2",
            "episode_id": "phase3_ep_001",
            "original_prompt": "make a red cube",
            "constraints": [],
            "max_image_attempts": 5,
        },
        planner_context={
            "task_context": {
                "original_prompt": "make a red cube",
                "max_image_attempts": 5,
                "atom_constraints": [
                    {
                        "constraint_id": "c_001",
                        "constraint_type": "attribute",
                        "requirement": "The cube is red.",
                        "evaluator_question": "Is the cube red?",
                    }
                ],
            },
            "latest_attempt": None,
            "skill_context": {"active_skills": []},
            "episode_memory": {
                "last_completed_image_round": None,
                "prior_image_rounds": [],
                "best_attempt": None,
            },
            "runtime_state": {
                "remaining_image_budget": 5,
                "available_actions": ["query_skill", "generate_image"],
            },
        },
        visible_images=[],
        target_action={
            "schema_version": "0.5",
            "action": "generate_image",
            "arguments": {
                "target_constraint_ids": ["c_001"],
                "preserve_constraint_ids": [],
                "instruction": "Create a red cube.",
            },
        },
    )

    assert [message["role"] for message in messages] == ["system", "user", "assistant"]
    assert [message["loss_weight"] for message in messages] == [0, 0, 1]
    assert messages[-1]["token_source"] == "canonical_action"
    assert "action_protocol_v0_5" in messages[1]["content"]
    assert "decision_summary" not in messages[-1]["content"]


def test_render_messages_rejects_query_skill_as_loss_one_target() -> None:
    with pytest.raises(ValueError, match="context-only"):
        render_messages(
            task_spec={},
            planner_context={},
            visible_images=[],
            target_action={
                "schema_version": "0.5",
                "action": "query_skill",
                "arguments": {
                    "skill_ids": ["counting_and_instance_layout"],
                    "target_constraint_ids": ["c_001"],
                },
            },
        )


def test_request_index_deduplicates_only_identical_resume_records() -> None:
    request = {"request_id": "req_001", "planner_context_ref": "context.json"}

    index = _index_identical_records(
        [request, dict(request)],
        key="request_id",
        source=Path("planner_requests.jsonl"),
    )

    assert index == {"req_001": request}


def test_request_index_rejects_conflicting_resume_records() -> None:
    with pytest.raises(ValueError, match="conflicting duplicate request_id=req_001"):
        _index_identical_records(
            [
                {"request_id": "req_001", "planner_context_ref": "context_1.json"},
                {"request_id": "req_001", "planner_context_ref": "context_2.json"},
            ],
            key="request_id",
            source=Path("planner_requests.jsonl"),
        )


def test_sft_profile_defaults_legacy_and_reads_dual_lock(tmp_path: Path) -> None:
    assert _execution_profile_for_run(tmp_path) == {
        "profile_id": "qwen_image_edit_only",
        "profile_version": "1",
    }
    (tmp_path / "rollout_plan.json").write_text(
        '{"execution_profile":{"profile_id":"qwen_dual_backend","profile_version":"1"}}',
        encoding="utf-8",
    )

    assert _execution_profile_for_run(tmp_path) == {
        "profile_id": "qwen_dual_backend",
        "profile_version": "1",
    }


def test_sft_rebuilds_context_from_exact_temporal_prefix(tmp_path: Path) -> None:
    events = load_events_jsonl(
        ROOT / "tests" / "fixtures" / "events" / "one_attempt_events.jsonl"
    )
    events[0]["payload"]["score_policy"] = primary_score_policy()
    geneval = next(
        event for event in events if event["event_type"] == "geneval2_completed"
    )
    for result, confidence in zip(
        geneval["payload"]["constraint_results"],
        [0.10, 0.80, 0.90, 0.70],
        strict=True,
    ):
        result["confidence"] = confidence
    geneval["payload"]["primary_score"] = canonical_primary_score(
        geneval["payload"]["constraint_results"]
    )
    context = build_planner_context_from_events(events, schema_version="0.6")
    context_ref = "planner_contexts/planner_context_001.json"
    (tmp_path / "planner_contexts").mkdir()
    (tmp_path / context_ref).write_text(
        canonical_json(context) + "\n",
        encoding="utf-8",
    )
    events.extend(
        [
            {
                "schema_version": "0.2",
                "event_id": "evt_0010",
                "episode_id": "ep_demo_001",
                "turn_id": "turn_001",
                "event_type": "planner_context_built",
                "created_at": "2026-07-14T06:00:00Z",
                "producer": "planner_context_builder",
                "input_refs": ["evt_0008"],
                "payload": {
                    "planner_context_ref": context_ref,
                    "planner_context_sha256": "a" * 64,
                    "planner_context_schema_version": "0.6",
                },
            },
            {
                "schema_version": "0.2",
                "event_id": "evt_0011",
                "episode_id": "ep_demo_001",
                "turn_id": "turn_001",
                "event_type": "action_validated",
                "created_at": "2026-07-14T06:00:00Z",
                "producer": "action_validator",
                "input_refs": ["evt_0010"],
                "payload": {
                    "action": {
                        "schema_version": "0.5",
                        "action": "submit_attempt",
                        "arguments": {
                            "selected_attempt_id": "a_000",
                            "reason_code": "best_available_under_budget",
                        },
                    }
                },
            },
        ]
    )
    (tmp_path / "events.jsonl").write_text(
        "".join(canonical_json(event) + "\n" for event in events),
        encoding="utf-8",
    )

    contract = _validate_planner_context_prefix(
        run_dir=tmp_path,
        context_ref=context_ref,
        planner_context=context,
        target_action_event_id="evt_0011",
    )

    assert contract == {
        "planner_context_schema_version": "0.6",
        "score_policy": primary_score_policy(),
    }

    leaked = json.loads(canonical_json(context))
    leaked["latest_attempt"]["primary_score"] += 0.01
    with pytest.raises(ValueError, match="not reproducible"):
        _validate_planner_context_prefix(
            run_dir=tmp_path,
            context_ref=context_ref,
            planner_context=leaked,
            target_action_event_id="evt_0011",
        )
