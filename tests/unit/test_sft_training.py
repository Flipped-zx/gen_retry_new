from __future__ import annotations

import json
from pathlib import Path

from gen_retry.analysis.sft_training import (
    summarize_sft_training,
    write_sft_training_report,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_summarize_trainer_state_and_missing_fields(tmp_path: Path) -> None:
    state = tmp_path / "run" / "trainer_state.json"
    state.parent.mkdir()
    _write_json(
        state,
        {
            "global_step": 4,
            "max_steps": 10,
            "run_name": "safe-run",
            "api_key": "must-not-be-copied",
            "log_history": [
                {"step": 1, "loss": 1.5, "learning_rate": 1e-5, "epoch": 0.25},
                {"step": 2, "loss": 1.0, "grad_norm": 2.0, "epoch": 0.5},
                {"step": 4, "eval_loss": 0.75, "train_runtime": 20.0, "epoch": 1.0},
            ],
        },
    )

    summary = summarize_sft_training(trainer_state_path=state.parent)

    assert summary["training"]["latest_step"] == 4
    assert summary["training"]["max_steps"] == 10
    assert summary["training"]["progress_fraction"] == 0.4
    assert summary["training"]["train_loss"]["latest"] == 1.0
    assert summary["training"]["eval_loss"]["latest"] == 0.75
    assert summary["timing"]["median_step_seconds"] == 5.0
    assert "api_key" not in json.dumps(summary)
    assert summary["training"]["grad_norm"]["count"] == 1


def test_action_metrics_are_aggregated_and_secrets_ignored(tmp_path: Path) -> None:
    state = tmp_path / "trainer_state.json"
    _write_json(state, {"log_history": [{"step": 1, "loss": 2.0}]})
    metrics = tmp_path / "action_metrics.jsonl"
    metrics.write_text(
        "\n".join(
            [
                json.dumps({"step": 1, "metrics": {"schema_valid": 1, "gm": 0.4}}),
                json.dumps({"global_step": 2, "schema_valid": True, "api_token": "x"}),
                "not json",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = summarize_sft_training(
        trainer_state_path=state,
        action_metrics_path=metrics,
    )

    action = summary["action_metrics"]
    assert action["record_count"] == 2
    assert action["malformed_line_count"] == 1
    assert action["metrics"]["schema_valid"]["mean"] == 1.0
    assert action["metrics"]["gm"]["latest"] == 0.4
    assert "api_token" not in json.dumps(summary)


def test_report_writes_json_markdown_html_and_png(tmp_path: Path) -> None:
    state = tmp_path / "trainer_state.json"
    _write_json(
        state,
        {
            "global_step": 2,
            "max_steps": 2,
            "log_history": [
                {"step": 1, "loss": 1.0, "learning_rate": 1e-5},
                {"step": 2, "loss": 0.5, "eval_loss": 0.7},
            ],
        },
    )
    output = tmp_path / "report"
    paths = write_sft_training_report(
        summary=summarize_sft_training(trainer_state_path=state),
        output_dir=output,
        stem="run",
    )

    assert {path.name for path in paths.values()} == {
        "run.summary.json",
        "run.report.md",
        "run.report.html",
        "run.curves.png",
    }
    assert paths["plot"].read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert "SFT Training Report" in paths["markdown"].read_text(encoding="utf-8")
    assert "trainer_state_or_log_history" in paths["summary"].read_text(
        encoding="utf-8"
    )


def test_standalone_log_history_list_is_supported(tmp_path: Path) -> None:
    history = tmp_path / "history.json"
    _write_json(history, [{"step": 1, "loss": 0.9}, {"step": 2, "loss": 0.4}])

    summary = summarize_sft_training(trainer_state_path=history)

    assert summary["training"]["latest_step"] == 2
    assert summary["training"]["train_loss"]["latest"] == 0.4
