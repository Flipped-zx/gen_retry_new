from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from gen_retry.analysis.qwen_best_of_5_baseline import (
    analyze_qwen_best_of_5_baseline,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _variant(index: int, scores: list[float]) -> dict:
    return {
        "variant_idx": index,
        "image_path": f"/external/image_{index}.png",
        "atom_scores": scores,
        "prompt_score": math.exp(
            sum(math.log(score) for score in scores) / len(scores)
        ),
    }


def _inputs(tmp_path: Path) -> dict[str, Path]:
    variants = [
        _variant(0, [0.99, 0.49, 0.49]),
        _variant(1, [0.51, 0.51, 0.51]),
        _variant(2, [0.20, 0.20, 0.20]),
        _variant(3, [0.10, 0.10, 0.10]),
        _variant(4, [0.05, 0.05, 0.05]),
    ]
    baseline = {
        "0": {
            "prompt": "three red cats",
            "vqa_list": [
                ["How many cats?", "three"],
                ["Are the cats red?", "Yes"],
                ["Are there cats?", "Yes"],
            ],
            "all_variants": variants,
            "best_variant_idx": 0,
            "best_image_path": "/external/image_0.png",
            "best_atom_scores": variants[0]["atom_scores"],
            "best_prompt_score": variants[0]["prompt_score"],
        }
    }
    selection = {
        "selected_prompts": [
            {
                "prompt_id": "prompt_001",
                "original_prompt": "three red cats",
                "difficulty_tier": "easy",
                "vqa_list": baseline["0"]["vqa_list"],
                "atomic_constraints": [
                    {"constraint_id": "c_001", "constraint_type": "count"},
                    {
                        "constraint_id": "c_002",
                        "constraint_type": "attribute",
                    },
                    {"constraint_id": "c_003", "constraint_type": "object"},
                ],
            }
        ]
    }
    submitted_scores = [0.9, 0.8, 0.7]
    submitted_gm = math.exp(
        sum(math.log(score) for score in submitted_scores)
        / len(submitted_scores)
    )
    agent = {
        "episodes": [
            {
                "episode_id": "phase3_ep_001",
                "prompt_id": "prompt_001",
                "constraint_count": 3,
                "attempt_count": 2,
                "initial_pass_count": 2,
                "first_agent_geneval2_am": 0.7,
                "first_agent_geneval2_score": 0.6,
                "best_pass_count": 3,
                "submitted_attempt_id": "a_001",
                "submitted_geneval2_am": sum(submitted_scores) / 3,
                "submitted_geneval2_score": submitted_gm,
            }
        ]
    }
    report = {
        "constraint_results": [
            {
                "constraint_id": "c_001",
                "confidence": submitted_scores[0],
                "status": "pass",
            },
            {
                "constraint_id": "c_002",
                "confidence": submitted_scores[1],
                "status": "pass",
            },
            {
                "constraint_id": "c_003",
                "confidence": submitted_scores[2],
                "status": "pass",
            },
        ]
    }
    paths = {
        "baseline": tmp_path / "evaluation_detail.json",
        "selection": tmp_path / "selection.json",
        "agent": tmp_path / "summary.json",
        "run_root": tmp_path / "runs",
    }
    _write_json(paths["baseline"], baseline)
    _write_json(paths["selection"], selection)
    _write_json(paths["agent"], agent)
    _write_json(
        paths["run_root"]
        / "phase3_ep_001"
        / "geneval2"
        / "a_001.json",
        report,
    )
    return paths


def test_analysis_separates_gm_and_protocol_baseline_selectors(
    tmp_path: Path,
) -> None:
    paths = _inputs(tmp_path)

    summary = analyze_qwen_best_of_5_baseline(
        baseline_detail_path=paths["baseline"],
        selection_path=paths["selection"],
        agent_summary_path=paths["agent"],
        agent_run_root=paths["run_root"],
        bootstrap_samples=20,
        bootstrap_seed=7,
    )

    aggregate = summary["aggregate"]
    assert aggregate["baseline_gm_selected"]["passed_atoms"] == 1
    assert aggregate["baseline_protocol_selected"]["passed_atoms"] == 3
    assert aggregate["agent_submitted"]["passed_atoms"] == 3
    assert aggregate["agent_vs_baseline"]["passed_atoms"] == 2
    assert summary["selector_sensitivity"]["selection_changed_episode_count"] == 1
    assert summary["atom_types"] == [
        {
            "atom_type": "object",
            "total": 1,
            "baseline_pass": 0,
            "baseline_pass_rate": 0.0,
            "agent_pass": 1,
            "agent_pass_rate": 1.0,
            "pass_delta": 1,
            "pass_rate_delta": 1.0,
        },
        {
            "atom_type": "attribute",
            "total": 1,
            "baseline_pass": 0,
            "baseline_pass_rate": 0.0,
            "agent_pass": 1,
            "agent_pass_rate": 1.0,
            "pass_delta": 1,
            "pass_rate_delta": 1.0,
        },
        {
            "atom_type": "count",
            "total": 1,
            "baseline_pass": 1,
            "baseline_pass_rate": 1.0,
            "agent_pass": 1,
            "agent_pass_rate": 1.0,
            "pass_delta": 0,
            "pass_rate_delta": 0.0,
        },
    ]


def test_analysis_rejects_prompt_alignment_mismatch(tmp_path: Path) -> None:
    paths = _inputs(tmp_path)
    baseline = json.loads(paths["baseline"].read_text(encoding="utf-8"))
    baseline["0"]["prompt"] = "different prompt"
    _write_json(paths["baseline"], baseline)

    with pytest.raises(ValueError, match="prompt mismatch"):
        analyze_qwen_best_of_5_baseline(
            baseline_detail_path=paths["baseline"],
            selection_path=paths["selection"],
            agent_summary_path=paths["agent"],
            agent_run_root=paths["run_root"],
            bootstrap_samples=1,
        )
