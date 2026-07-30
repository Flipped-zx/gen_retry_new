from pathlib import Path
from types import SimpleNamespace

import pytest

from gen_retry.cli.analyze_phase3_rollouts import _resolve_episode_ids
from gen_retry.domain.score_policy import primary_score_policy
from gen_retry.phase3.trajectory_analysis import (
    LABEL_TRAINABLE,
    AttemptContext,
    _base_label,
    _choose_best_after,
    _label_image_action,
    _label_query_skill_action,
    _select_analysis_run_dirs,
)
from gen_retry.runtime.reducer import AttemptRecord


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


def _attempt(attempt_id: str, score: float) -> AttemptRecord:
    return AttemptRecord(
        attempt_id=attempt_id,
        parent_attempt_id="a_000" if attempt_id != "a_000" else None,
        action_event_id=f"evt_{attempt_id}",
        action={
            "schema_version": "0.5",
            "action": "edit_image" if attempt_id != "a_000" else "generate_image",
            "arguments": {
                "source_attempt_id": "a_000",
                "target_constraint_ids": ["c_002"],
                "preserve_constraint_ids": ["c_001"],
                "instruction": "keep the first atom and improve the second",
            },
        },
        operation="edit" if attempt_id != "a_000" else "generate",
        image_artifact_id=f"img_{attempt_id}",
        constraint_results={
            "c_001": {"constraint_id": "c_001", "status": "pass"},
            "c_002": {"constraint_id": "c_002", "status": "fail"},
        },
        primary_score=score,
    )


def test_analysis_uses_primary_score_for_equal_pass_best_and_label() -> None:
    source = _attempt("a_000", 0.20)
    candidate = _attempt("a_001", 0.80)
    state = SimpleNamespace(
        attempts={"a_000": source, "a_001": candidate},
        score_policy=primary_score_policy(),
    )

    assert _choose_best_after(state, "a_000", candidate) == "a_001"

    context = AttemptContext(
        attempt=candidate,
        attempt_index=1,
        latest_before="a_000",
        best_before="a_000",
        best_before_pass_count=1,
        previous_for_transition=source,
        transition={
            "fixed": [],
            "regressed": [],
            "persistent_failed": ["c_002"],
            "stable_pass": ["c_001"],
        },
        best_after="a_001",
    )
    action_record = {
        "request_id": "req_002",
        "turn_id": "turn_002",
        "action_event_id": "evt_a_001",
        "action": candidate.action,
    }

    label = _label_image_action(
        episode_id="ep_001",
        action_record=action_record,
        context=context,
        task_constraint_count=2,
        score_policy=primary_score_policy(),
    )

    assert label["label"] == LABEL_TRAINABLE
    assert label["sft_candidate"] is True
    assert label["label_rationale"] == "image action improved the best-so-far score"
