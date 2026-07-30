from pathlib import Path

import pytest

from gen_retry.cli.analyze_phase3_rollouts import _resolve_episode_ids
from gen_retry.phase3.trajectory_analysis import (
    LABEL_TRAINABLE,
    _base_label,
    _label_query_skill_action,
    _select_analysis_run_dirs,
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


def test_select_analysis_run_dirs_limits_checkpoint_subset(tmp_path: Path) -> None:
    for episode_id in ("phase3_ep_001", "phase3_ep_002", "phase3_ep_003"):
        (tmp_path / episode_id).mkdir()

    assert _select_analysis_run_dirs(
        tmp_path,
        ["phase3_ep_003", "phase3_ep_001"],
    ) == [
        tmp_path / "phase3_ep_001",
        tmp_path / "phase3_ep_003",
    ]


def test_select_analysis_run_dirs_rejects_missing_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="phase3_ep_001"):
        _select_analysis_run_dirs(tmp_path, ["phase3_ep_001"])


def test_analysis_cli_resolves_inclusive_episode_range() -> None:
    assert _resolve_episode_ids(
        episode_ids=None,
        episode_start=41,
        episode_end=50,
    ) == [f"phase3_ep_{index:03d}" for index in range(41, 51)]
