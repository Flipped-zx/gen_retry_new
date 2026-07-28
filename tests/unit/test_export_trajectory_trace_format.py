from __future__ import annotations

from gen_retry.cli.export_trajectory_trace import _image_labels_inline, _teacher_text_block


def test_trace_teacher_text_block_uses_exact_persisted_input() -> None:
    block = _teacher_text_block(
        {"teacher_text_input": "SYSTEM\nTaskSpec\nPlannerView"},
        planner_context={},
        task_spec={},
    )

    assert "Exact sanitized teacher text input" in block
    assert "SYSTEM\nTaskSpec\nPlannerView" in block


def test_trace_image_labels_are_unambiguous_for_latest_and_best() -> None:
    labels = _image_labels_inline(
        [
            {"role": "latest", "attempt_id": "a_001", "artifact_id": "img_001"},
            {"role": "best", "attempt_id": "a_000", "artifact_id": "img_000"},
        ],
        {
            "latest_attempt": {"attempt_id": "a_001"},
            "best_attempt": {"attempt_id": "a_000"},
        },
    )

    assert "LATEST_IMAGE:a_001:img_001" in labels
    assert "BEST_IMAGE:a_000:img_000" in labels
