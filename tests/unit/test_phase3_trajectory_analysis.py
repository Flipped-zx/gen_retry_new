from gen_retry.phase3.trajectory_analysis import (
    LABEL_TRAINABLE,
    _base_label,
    _label_query_skill_action,
)


def _action_record(action: str, schema_version: str = "0.5") -> dict:
    return {
        "request_id": "req_001",
        "turn_id": "turn_001",
        "action_event_id": "evt_001",
        "action": {
            "schema_version": schema_version,
            "action": action,
            "arguments": {},
        },
    }


def test_query_skill_is_valid_context_but_not_an_sft_candidate() -> None:
    record = _label_query_skill_action(
        "ep_001",
        _action_record("query_skill"),
        has_skill_return=True,
    )

    assert record["label"] == LABEL_TRAINABLE
    assert record["sft_candidate"] is False
    assert "loss-0 context" in record["label_rationale"]


def test_only_native_v05_targetable_actions_can_be_sft_candidates() -> None:
    native_generate = _base_label(
        "ep_001",
        _action_record("generate_image"),
        LABEL_TRAINABLE,
        "productive generation",
    )
    legacy_generate = _base_label(
        "ep_001",
        _action_record("generate_image", schema_version="0.3"),
        LABEL_TRAINABLE,
        "legacy generation",
    )

    assert native_generate["sft_candidate"] is True
    assert legacy_generate["sft_candidate"] is False
