"""Deterministic action-level evaluation for full-SFT checkpoints."""

from __future__ import annotations

import gc
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from gen_retry.protocol.action_parser import ActionParseError, parse_action
from gen_retry.runtime.json_canonical import canonical_json


EVALUATION_FORMAT_VERSION = "gen_retry_sft_checkpoint_eval_v1"
ACTION_NAMES = ("query_skill", "generate_image", "edit_image", "submit_attempt")
_LABEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def load_frozen_validation_samples(
    validation_path: Path,
    *,
    provenance_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load a hash-bound frozen validation split without exposing gold as input."""

    validation_path = validation_path.resolve()
    dataset_dir = validation_path.parent
    manifest_path = dataset_dir / "export_manifest.json"
    if not validation_path.is_file():
        raise FileNotFoundError(validation_path)
    if not manifest_path.is_file():
        raise FileNotFoundError(f"export manifest not found: {manifest_path}")
    manifest = _load_json(manifest_path)
    if manifest.get("release_status") != "frozen":
        raise ValueError("checkpoint evaluation requires a frozen dataset export")
    if manifest.get("training_authorized") is not True:
        raise ValueError("frozen dataset is not training-authorized")
    expected_hash = (manifest.get("artifacts") or {}).get(validation_path.name)
    actual_hash = _sha256_file(validation_path)
    if expected_hash != actual_hash:
        raise ValueError("validation JSONL hash does not match export manifest")

    provenance_path = (
        provenance_path.resolve()
        if provenance_path is not None
        else dataset_dir / "provenance.jsonl"
    )
    provenance_by_row: dict[int, dict[str, Any]] = {}
    if provenance_path.is_file():
        for item in _load_jsonl(provenance_path):
            if item.get("split") != "validation":
                continue
            row_index = item.get("row_index")
            if not isinstance(row_index, int) or row_index in provenance_by_row:
                raise ValueError("invalid or duplicate validation provenance row")
            provenance_by_row[row_index] = item

    samples: list[dict[str, Any]] = []
    for row_index, row in enumerate(_load_jsonl(validation_path)):
        messages = row.get("messages")
        images = row.get("images")
        if not isinstance(messages, list) or len(messages) != 3:
            raise ValueError(f"validation row {row_index} must have three messages")
        if [message.get("role") for message in messages] != [
            "system",
            "user",
            "assistant",
        ]:
            raise ValueError(f"validation row {row_index} has invalid roles")
        if not isinstance(images, list) or not all(
            isinstance(image, str) and image for image in images
        ):
            raise ValueError(f"validation row {row_index} has invalid images")
        prompt_messages = [
            {"role": message["role"], "content": message.get("content", "")}
            for message in messages[:2]
        ]
        if not all(isinstance(message["content"], str) for message in prompt_messages):
            raise ValueError(f"validation row {row_index} has non-string prompt content")
        placeholder_count = sum(
            message["content"].count("<image>") for message in prompt_messages
        )
        if placeholder_count != len(images):
            raise ValueError(
                f"validation row {row_index} image placeholder mismatch"
            )
        resolved_images: list[str] = []
        for image in images:
            image_path = (dataset_dir / image).resolve()
            if not image_path.is_relative_to(dataset_dir):
                raise ValueError(f"validation row {row_index} image escapes dataset")
            if not image_path.is_file():
                raise FileNotFoundError(image_path)
            resolved_images.append(str(image_path))

        raw_gold = messages[-1].get("content")
        if not isinstance(raw_gold, str):
            raise ValueError(f"validation row {row_index} has non-string gold action")
        gold_action = parse_action(raw_gold).action
        provenance = provenance_by_row.get(row_index)
        if provenance_by_row and provenance is None:
            raise ValueError(f"validation row {row_index} has no provenance")
        if provenance is not None and provenance.get("action") != gold_action["action"]:
            raise ValueError(f"validation row {row_index} provenance action mismatch")
        sample_id = (
            str(provenance["sample_id"])
            if provenance is not None and provenance.get("sample_id")
            else f"validation_row_{row_index:06d}"
        )
        samples.append(
            {
                "sample_id": sample_id,
                "row_index": row_index,
                "gold_action": gold_action,
                "prompt_messages": prompt_messages,
                "images": resolved_images,
                "dataset_images": list(images),
            }
        )

    expected_count = (manifest.get("split_counts") or {}).get("validation")
    if expected_count != len(samples):
        raise ValueError("validation row count does not match export manifest")
    source = {
        "dataset_dir": str(dataset_dir),
        "validation_path": str(validation_path),
        "validation_sha256": actual_hash,
        "export_manifest_path": str(manifest_path),
        "export_manifest_sha256": _sha256_file(manifest_path),
        "release_status": manifest["release_status"],
        "record_count": len(samples),
    }
    return samples, source


def select_stratified_samples(
    samples: list[dict[str, Any]],
    *,
    samples_per_action: int = 4,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Select a stable, balanced subset using hashes instead of RNG state."""

    if samples_per_action < 1:
        raise ValueError("samples_per_action must be positive")
    selected: list[dict[str, Any]] = []
    for action_name in ACTION_NAMES:
        bucket = [
            sample
            for sample in samples
            if sample.get("gold_action", {}).get("action") == action_name
        ]
        if len(bucket) < samples_per_action:
            raise ValueError(
                f"validation split has only {len(bucket)} {action_name} rows; "
                f"requested {samples_per_action}"
            )
        ranked = sorted(
            bucket,
            key=lambda sample: (
                hashlib.sha256(
                    f"{seed}:{sample['sample_id']}".encode("utf-8")
                ).hexdigest(),
                sample["sample_id"],
            ),
        )
        selected.extend(ranked[:samples_per_action])
    return selected


def build_sample_manifest(
    samples: list[dict[str, Any]],
    *,
    source: dict[str, Any],
    samples_per_action: int,
    seed: int,
) -> dict[str, Any]:
    return {
        "schema_version": EVALUATION_FORMAT_VERSION,
        "selection": {
            "strategy": "sha256_stratified_by_gold_action",
            "seed": seed,
            "samples_per_action": samples_per_action,
            "sample_count": len(samples),
        },
        "source": source,
        "samples": [
            {
                "sample_id": sample["sample_id"],
                "row_index": sample["row_index"],
                "gold_action": sample["gold_action"]["action"],
                "gold_action_sha256": hashlib.sha256(
                    canonical_json(sample["gold_action"]).encode("utf-8")
                ).hexdigest(),
                "images": sample["dataset_images"],
            }
            for sample in samples
        ],
    }


def evaluate_action_outputs(
    samples: list[dict[str, Any]],
    outputs: dict[str, str],
    *,
    checkpoint_label: str,
    checkpoint_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Parse strict actions and compute deterministic action-level metrics."""

    if set(outputs) != {sample["sample_id"] for sample in samples}:
        raise ValueError("outputs must contain exactly one result for every sample")
    predictions = [
        _evaluate_one(sample, outputs[sample["sample_id"]]) for sample in samples
    ]
    summary = summarize_action_predictions(
        predictions,
        checkpoint_label=checkpoint_label,
        checkpoint_path=checkpoint_path,
    )
    return predictions, summary


def summarize_action_predictions(
    predictions: list[dict[str, Any]],
    *,
    checkpoint_label: str,
    checkpoint_path: Path,
) -> dict[str, Any]:
    if not _LABEL_PATTERN.fullmatch(checkpoint_label):
        raise ValueError(f"invalid checkpoint label: {checkpoint_label}")
    if not predictions:
        raise ValueError("cannot summarize an empty prediction set")

    total = len(predictions)
    valid_count = sum(bool(item["schema_valid"]) for item in predictions)
    predicted_actions = Counter(
        item["predicted_action"]["action"]
        for item in predictions
        if item["schema_valid"]
    )
    gold_actions = Counter(item["gold_action"]["action"] for item in predictions)
    invalid_errors = Counter(
        str(item["error_code"])
        for item in predictions
        if not item["schema_valid"]
    )
    target_items = [
        item for item in predictions if item["metrics"]["target_constraint_jaccard"] is not None
    ]
    preserve_items = [
        item
        for item in predictions
        if item["metrics"]["preserve_constraint_jaccard"] is not None
    ]
    by_gold_action: dict[str, Any] = {}
    for action_name in ACTION_NAMES:
        rows = [item for item in predictions if item["gold_action"]["action"] == action_name]
        by_gold_action[action_name] = {
            "count": len(rows),
            "schema_valid_rate": _mean_bool(rows, "schema_valid"),
            "action_type_accuracy": _mean_metric(rows, "action_type_match"),
            "exact_action_accuracy": _mean_metric(rows, "exact_action_match"),
        }

    metrics = {
        "schema_valid_rate": valid_count / total,
        "invalid_rate": (total - valid_count) / total,
        "action_type_accuracy": _mean_metric(predictions, "action_type_match"),
        "exact_action_accuracy": _mean_metric(predictions, "exact_action_match"),
        "query_skill_rate": predicted_actions["query_skill"] / total,
        "target_constraint_jaccard": _mean_metric(
            target_items, "target_constraint_jaccard"
        ),
        "target_constraint_recall": _mean_metric(
            target_items, "target_constraint_recall"
        ),
        "preserve_constraint_jaccard": _mean_metric(
            preserve_items, "preserve_constraint_jaccard"
        ),
        "attempt_reference_accuracy": _mean_metric(
            [
                item
                for item in predictions
                if item["metrics"]["attempt_reference_match"] is not None
            ],
            "attempt_reference_match",
        ),
    }
    return {
        "schema_version": EVALUATION_FORMAT_VERSION,
        "checkpoint": {
            "label": checkpoint_label,
            "path": str(checkpoint_path.resolve()),
        },
        "sample_count": total,
        "schema_valid_count": valid_count,
        "invalid_count": total - valid_count,
        "invalid_error_counts": dict(sorted(invalid_errors.items())),
        "gold_action_distribution": dict(sorted(gold_actions.items())),
        "predicted_action_distribution": dict(sorted(predicted_actions.items())),
        "metrics": metrics,
        "by_gold_action": by_gold_action,
    }


def compare_checkpoint_summaries(
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(summaries) < 2:
        raise ValueError("checkpoint comparison requires at least two summaries")
    baseline = summaries[0]
    candidate = summaries[-1]
    comparable = (
        "schema_valid_rate",
        "invalid_rate",
        "action_type_accuracy",
        "exact_action_accuracy",
        "query_skill_rate",
        "target_constraint_jaccard",
        "target_constraint_recall",
        "preserve_constraint_jaccard",
        "attempt_reference_accuracy",
    )
    delta = {}
    for key in comparable:
        before = baseline["metrics"].get(key)
        after = candidate["metrics"].get(key)
        delta[key] = None if before is None or after is None else after - before
    return {
        "schema_version": EVALUATION_FORMAT_VERSION,
        "baseline": baseline["checkpoint"]["label"],
        "candidate": candidate["checkpoint"]["label"],
        "sample_count": baseline["sample_count"],
        "metric_delta_candidate_minus_baseline": delta,
        "summaries": {
            summary["checkpoint"]["label"]: summary for summary in summaries
        },
    }


class LlamaFactoryActionGenerator:
    """Lazy LLaMA-Factory HF inference wrapper for one full checkpoint."""

    def __init__(
        self,
        checkpoint_path: Path,
        *,
        max_new_tokens: int = 512,
        template: str = "qwen3_vl_nothink",
        flash_attn: str = "fa2",
        image_max_pixels: int = 262144,
    ) -> None:
        checkpoint_path = checkpoint_path.resolve()
        _validate_full_checkpoint(checkpoint_path)
        if max_new_tokens < 1:
            raise ValueError("max_new_tokens must be positive")
        try:
            from llamafactory.chat import ChatModel
        except ImportError as exc:  # pragma: no cover - runtime environment only
            raise RuntimeError(
                "LLaMA-Factory is required; activate runs/sft_runtime_v2/venv"
            ) from exc
        self._max_new_tokens = max_new_tokens
        self._chat_model = ChatModel(
            {
                "model_name_or_path": str(checkpoint_path),
                "template": template,
                "stage": "sft",
                "finetuning_type": "full",
                "infer_backend": "huggingface",
                "infer_dtype": "bfloat16",
                "flash_attn": flash_attn,
                "image_max_pixels": image_max_pixels,
                "trust_remote_code": True,
                "do_sample": False,
                "temperature": 0.0,
                "max_new_tokens": max_new_tokens,
            }
        )

    def __call__(self, sample: dict[str, Any]) -> str:
        prompt_messages = sample["prompt_messages"]
        responses = self._chat_model.chat(
            messages=[dict(prompt_messages[1])],
            system=prompt_messages[0]["content"],
            images=list(sample["images"]),
            do_sample=False,
            temperature=0.0,
            max_new_tokens=self._max_new_tokens,
        )
        if len(responses) != 1:
            raise RuntimeError(f"expected one response, received {len(responses)}")
        return responses[0].response_text

    def close(self) -> None:
        chat_model = getattr(self, "_chat_model", None)
        if chat_model is None:
            return
        loop = getattr(chat_model, "_loop", None)
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        engine = getattr(chat_model, "engine", None)
        if engine is not None and hasattr(engine, "model"):
            del engine.model
        del self._chat_model
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:  # pragma: no cover - runtime environment only
            pass


def generate_outputs(
    samples: list[dict[str, Any]],
    generator: Callable[[dict[str, Any]], str],
    *,
    progress: Callable[[int, int, str], None] | None = None,
) -> dict[str, str]:
    outputs: dict[str, str] = {}
    total = len(samples)
    for index, sample in enumerate(samples, start=1):
        raw_output = generator(sample)
        if not isinstance(raw_output, str):
            raise TypeError("checkpoint generator must return a string")
        outputs[sample["sample_id"]] = raw_output
        if progress is not None:
            progress(index, total, sample["sample_id"])
    return outputs


def write_checkpoint_evaluation(
    *,
    output_dir: Path,
    predictions: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_jsonl(output_dir / "predictions.jsonl", predictions)
    _write_json(output_dir / "summary.json", summary)


def render_comparison_markdown(comparison: dict[str, Any]) -> str:
    labels = list(comparison["summaries"])
    lines = [
        "# SFT Checkpoint Action Evaluation",
        "",
        f"Fixed sample count: {comparison['sample_count']}.",
        "",
        "| Metric | " + " | ".join(labels) + " | Final delta |",
        "| --- | " + " | ".join("---:" for _ in labels) + " | ---: |",
    ]
    deltas = comparison["metric_delta_candidate_minus_baseline"]
    for metric in deltas:
        values = [comparison["summaries"][label]["metrics"].get(metric) for label in labels]
        lines.append(
            f"| {metric} | "
            + " | ".join(_format_metric(value) for value in values)
            + f" | {_format_metric(deltas[metric])} |"
        )
    lines.extend(
        [
            "",
            "`invalid_rate` is expected to decrease; all other deltas are descriptive. "
            "The action metrics do not execute images or rerun Geneval2.",
        ]
    )
    return "\n".join(lines) + "\n"


def _evaluate_one(sample: dict[str, Any], raw_output: str) -> dict[str, Any]:
    gold = sample["gold_action"]
    parsed: dict[str, Any] | None = None
    error_code = None
    error_message = None
    try:
        parsed = parse_action(raw_output).action
    except ActionParseError as exc:
        error_code = exc.error_code
        error_message = exc.message

    gold_arguments = gold["arguments"]
    predicted_arguments = parsed["arguments"] if parsed is not None else {}
    target_metrics = _set_overlap(
        gold_arguments.get("target_constraint_ids"),
        predicted_arguments.get("target_constraint_ids"),
    )
    preserve_metrics = _set_overlap(
        gold_arguments.get("preserve_constraint_ids"),
        predicted_arguments.get("preserve_constraint_ids"),
    )
    gold_reference = gold_arguments.get(
        "source_attempt_id", gold_arguments.get("selected_attempt_id")
    )
    predicted_reference = predicted_arguments.get(
        "source_attempt_id", predicted_arguments.get("selected_attempt_id")
    )
    return {
        "sample_id": sample["sample_id"],
        "row_index": sample["row_index"],
        "gold_action": gold,
        "raw_output": raw_output,
        "schema_valid": parsed is not None,
        "error_code": error_code,
        "error_message": error_message,
        "predicted_action": parsed,
        "metrics": {
            "action_type_match": bool(parsed and parsed["action"] == gold["action"]),
            "exact_action_match": bool(parsed == gold),
            "target_constraint_jaccard": target_metrics["jaccard"],
            "target_constraint_recall": target_metrics["recall"],
            "preserve_constraint_jaccard": preserve_metrics["jaccard"],
            "attempt_reference_match": (
                None
                if gold_reference is None
                else bool(parsed is not None and predicted_reference == gold_reference)
            ),
        },
    }


def _set_overlap(gold: Any, predicted: Any) -> dict[str, float | None]:
    if not isinstance(gold, list):
        return {"jaccard": None, "recall": None}
    gold_set = set(gold)
    predicted_set = set(predicted) if isinstance(predicted, list) else set()
    union = gold_set | predicted_set
    intersection = gold_set & predicted_set
    return {
        "jaccard": len(intersection) / len(union) if union else 1.0,
        "recall": len(intersection) / len(gold_set) if gold_set else 1.0,
    }


def _mean_bool(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return sum(bool(row[key]) for row in rows) / len(rows)


def _mean_metric(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [row["metrics"].get(key) for row in rows]
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else None


def _validate_full_checkpoint(checkpoint_path: Path) -> None:
    if not checkpoint_path.is_dir():
        raise FileNotFoundError(checkpoint_path)
    if not (checkpoint_path / "config.json").is_file():
        raise FileNotFoundError(f"checkpoint config not found: {checkpoint_path}")
    weight_files = list(checkpoint_path.glob("*.safetensors")) + list(
        checkpoint_path.glob("pytorch_model*.bin")
    )
    if not weight_files:
        raise FileNotFoundError(f"full checkpoint weights not found: {checkpoint_path}")


def _format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"expected JSON object at {path}:{line_number}")
        records.append(value)
    return records


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(canonical_json(value) + "\n" for value in values),
        encoding="utf-8",
    )
