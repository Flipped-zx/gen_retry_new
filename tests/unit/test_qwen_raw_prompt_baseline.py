from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.analysis.qwen_raw_prompt_baseline import (
    prepare_raw_prompt_baseline,
    summarize_raw_prompt_baseline,
)
from gen_retry.cli.run_qwen_raw_prompt_baseline_parallel import _pending_jobs


def _task_spec(episode_id: str, prompt: str) -> dict:
    return {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "original_prompt": prompt,
        "constraints": [
            {
                "constraint_id": "c_001",
                "constraint_type": "object",
                "requirement": "A cat is present.",
                "evaluator_question": "Is there a cat?",
                "priority": 3,
            },
            {
                "constraint_id": "c_002",
                "constraint_type": "attribute",
                "requirement": "The cat is red.",
                "evaluator_question": "Is the cat red?",
                "priority": 3,
            },
        ],
        "max_image_attempts": 5,
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _prepare(tmp_path: Path) -> tuple[Path, dict]:
    source = tmp_path / "source"
    episode_ids = ["phase3_ep_001", "phase3_ep_002"]
    for index, episode_id in enumerate(episode_ids):
        _write_json(
            source / episode_id / "task_spec.json",
            _task_spec(episode_id, f"red cat {index}"),
        )
    output = tmp_path / "baseline"
    plan = prepare_raw_prompt_baseline(
        source_run_root=source,
        episode_ids=episode_ids,
        output_root=output,
        plan_output=tmp_path / "plan.json",
        variant_count=5,
    )
    return output, plan


def test_prepare_raw_prompt_baseline_is_fresh_task_spec_only(tmp_path: Path) -> None:
    output, plan = _prepare(tmp_path)

    assert plan["source_read_policy"] == "task_spec_only"
    assert plan["prompt_policy"] == "exact_task_spec_original_prompt_no_rewrite"
    assert plan["fresh_start_policy"] == {
        "sft_images_imported": False,
        "sft_events_imported": False,
        "sft_geneval2_imported": False,
        "teacher_used": False,
    }
    assert len(list(output.glob("phase3_ep_*/variant_*/task_spec.json"))) == 10
    assert not list(output.glob("phase3_ep_*/variant_*/images/*.png"))

    with pytest.raises(FileExistsError, match="non-empty baseline root"):
        prepare_raw_prompt_baseline(
            source_run_root=tmp_path / "source",
            episode_ids=["phase3_ep_001"],
            output_root=output,
            plan_output=tmp_path / "second.json",
        )


def test_summarize_raw_prompt_baseline_reports_single_and_best_of_5(
    tmp_path: Path,
) -> None:
    output, plan = _prepare(tmp_path)
    for episode in plan["episodes"]:
        for variant_index in range(5):
            passed = 1 if variant_index == 0 else (2 if variant_index == 1 else 0)
            gm = [0.4, 0.3, 0.9, 0.2, 0.1][variant_index]
            _write_json(
                output
                / episode["episode_id"]
                / f"variant_{variant_index:03d}"
                / "result.json",
                {
                    "episode_id": episode["episode_id"],
                    "variant_index": variant_index,
                    "prompt": episode["original_prompt"],
                    "constraint_count": 2,
                    "passed_atoms": passed,
                    "am": passed / 2,
                    "gm": gm,
                    "all_pass": passed == 2,
                },
            )

    summary = summarize_raw_prompt_baseline(
        run_root=output,
        artifact_path=tmp_path / "summary.json",
        report_path=tmp_path / "report.md",
    )

    assert summary["single"]["passed_atoms"] == 2
    assert summary["best_of_5_gm"]["passed_atoms"] == 0
    assert summary["best_of_5_gm"]["gm_100"] == pytest.approx(90.0)
    assert summary["best_of_5_pass_count"]["passed_atoms"] == 4
    assert summary["best_of_5_pass_count"]["all_pass_episodes"] == 2
    assert summary["total_image_calls"] == 10
    assert _pending_jobs(output, plan) == []
