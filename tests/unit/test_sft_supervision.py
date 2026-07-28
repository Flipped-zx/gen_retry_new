from __future__ import annotations

import pytest

from pathlib import Path

from gen_retry.sft.supervision import (
    _index_identical_records,
    decide_supervision,
    render_messages,
)


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
