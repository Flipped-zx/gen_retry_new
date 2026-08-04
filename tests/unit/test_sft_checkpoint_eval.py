from __future__ import annotations

import hashlib
import json
from pathlib import Path

from gen_retry.analysis.sft_checkpoint_eval import (
    ACTION_NAMES,
    build_sample_manifest,
    compare_checkpoint_summaries,
    evaluate_action_outputs,
    load_frozen_validation_samples,
    select_stratified_samples,
)
from gen_retry.runtime.json_canonical import canonical_json


def _action(action_name: str, suffix: int = 1) -> dict:
    constraint = f"c_{suffix:03d}"
    arguments = {
        "query_skill": {
            "skill_ids": ["counting_and_instance_layout"],
            "target_constraint_ids": [constraint],
        },
        "generate_image": {
            "target_constraint_ids": [constraint],
            "preserve_constraint_ids": [],
            "instruction": "Generate one visible object.",
        },
        "edit_image": {
            "source_attempt_id": "a_000",
            "target_constraint_ids": [constraint],
            "preserve_constraint_ids": ["c_999"],
            "instruction": "Edit only the requested object.",
        },
        "submit_attempt": {
            "selected_attempt_id": "a_000",
            "reason_code": "all_constraints_passed",
        },
    }
    return {
        "schema_version": "0.5",
        "action": action_name,
        "arguments": arguments[action_name],
    }


def _sample(action_name: str, suffix: int) -> dict:
    return {
        "sample_id": f"{action_name}_{suffix}",
        "row_index": suffix,
        "gold_action": _action(action_name, suffix),
        "prompt_messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "context"},
        ],
        "images": [],
        "dataset_images": [],
    }


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.write_text(
        "".join(canonical_json(value) + "\n" for value in values),
        encoding="utf-8",
    )


def test_load_frozen_validation_removes_gold_from_prompt(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    image = dataset / "image.png"
    image.write_bytes(b"image")
    gold = _action("edit_image")
    rows = [
        {
            "messages": [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "<image>\ncontext"},
                {"role": "assistant", "content": canonical_json(gold)},
            ],
            "images": ["image.png"],
        }
    ]
    validation = dataset / "validation.jsonl"
    _write_jsonl(validation, rows)
    provenance = dataset / "provenance.jsonl"
    _write_jsonl(
        provenance,
        [
            {
                "split": "validation",
                "row_index": 0,
                "sample_id": "sample-0",
                "action": "edit_image",
            }
        ],
    )
    validation_hash = hashlib.sha256(validation.read_bytes()).hexdigest()
    (dataset / "export_manifest.json").write_text(
        canonical_json(
            {
                "release_status": "frozen",
                "training_authorized": True,
                "split_counts": {"validation": 1},
                "artifacts": {"validation.jsonl": validation_hash},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    samples, source = load_frozen_validation_samples(validation)

    assert source["validation_sha256"] == validation_hash
    assert samples[0]["sample_id"] == "sample-0"
    assert samples[0]["gold_action"] == gold
    assert [message["role"] for message in samples[0]["prompt_messages"]] == [
        "system",
        "user",
    ]
    assert "assistant" not in canonical_json(samples[0]["prompt_messages"])
    assert samples[0]["images"] == [str(image.resolve())]


def test_stratified_selection_is_balanced_and_deterministic() -> None:
    samples = [
        _sample(action_name, suffix)
        for action_name in ACTION_NAMES
        for suffix in range(1, 6)
    ]

    first = select_stratified_samples(samples, samples_per_action=2, seed=7)
    second = select_stratified_samples(list(reversed(samples)), samples_per_action=2, seed=7)

    assert [item["sample_id"] for item in first] == [
        item["sample_id"] for item in second
    ]
    assert {
        action: sum(item["gold_action"]["action"] == action for item in first)
        for action in ACTION_NAMES
    } == {action: 2 for action in ACTION_NAMES}
    manifest = build_sample_manifest(
        first,
        source={"validation_sha256": "abc"},
        samples_per_action=2,
        seed=7,
    )
    assert manifest["selection"]["sample_count"] == 8


def test_metrics_count_strict_invalid_and_constraint_overlap(tmp_path: Path) -> None:
    samples = [
        _sample("query_skill", 1),
        _sample("generate_image", 2),
        _sample("edit_image", 3),
        _sample("submit_attempt", 4),
    ]
    partial_generate = _action("generate_image", 2)
    partial_generate["arguments"]["target_constraint_ids"] = ["c_002", "c_777"]
    wrong_edit = _action("generate_image", 3)
    outputs = {
        samples[0]["sample_id"]: "```json\n{}\n```",
        samples[1]["sample_id"]: canonical_json(partial_generate),
        samples[2]["sample_id"]: canonical_json(wrong_edit),
        samples[3]["sample_id"]: canonical_json(samples[3]["gold_action"]),
    }

    predictions, summary = evaluate_action_outputs(
        samples,
        outputs,
        checkpoint_label="checkpoint-100",
        checkpoint_path=tmp_path,
    )

    assert predictions[0]["error_code"] == "invalid_json"
    assert predictions[1]["metrics"]["target_constraint_jaccard"] == 0.5
    assert predictions[1]["metrics"]["target_constraint_recall"] == 1.0
    assert summary["metrics"]["schema_valid_rate"] == 0.75
    assert summary["metrics"]["invalid_rate"] == 0.25
    assert summary["metrics"]["action_type_accuracy"] == 0.5
    assert summary["metrics"]["exact_action_accuracy"] == 0.25
    assert summary["metrics"]["query_skill_rate"] == 0.0
    assert summary["predicted_action_distribution"] == {
        "generate_image": 2,
        "submit_attempt": 1,
    }


def test_checkpoint_comparison_reports_candidate_delta(tmp_path: Path) -> None:
    samples = [_sample(action_name, index + 1) for index, action_name in enumerate(ACTION_NAMES)]
    invalid_outputs = {sample["sample_id"]: "not json" for sample in samples}
    valid_outputs = {
        sample["sample_id"]: canonical_json(sample["gold_action"]) for sample in samples
    }
    _, baseline = evaluate_action_outputs(
        samples,
        invalid_outputs,
        checkpoint_label="checkpoint-100",
        checkpoint_path=tmp_path / "checkpoint-100",
    )
    _, final = evaluate_action_outputs(
        samples,
        valid_outputs,
        checkpoint_label="final",
        checkpoint_path=tmp_path / "final",
    )

    comparison = compare_checkpoint_summaries([baseline, final])

    assert comparison["baseline"] == "checkpoint-100"
    assert comparison["candidate"] == "final"
    assert comparison["metric_delta_candidate_minus_baseline"]["schema_valid_rate"] == 1.0
    assert comparison["metric_delta_candidate_minus_baseline"]["invalid_rate"] == -1.0
