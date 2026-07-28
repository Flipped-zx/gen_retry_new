from __future__ import annotations

import gc
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_file
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.tools.model_load_lock import exclusive_model_load


@dataclass(frozen=True)
class Geneval2Report:
    attempt_id: str
    constraint_results: list[dict[str, Any]]
    raw_results: list[dict[str, Any]]
    report_ref: str
    report_sha256: str
    manifest_entry: dict[str, Any]
    normalization: dict[str, Any]


class LocalGeneval2Adapter:
    def __init__(
        self,
        *,
        evaluator_root: Path,
        vqa_model_path: Path = Path("/root/private_data/agentic_image/models/Qwen3-VL-8B-Instruct"),
        artifact_root: Path,
        pass_threshold: float = 0.50,
        fail_threshold: float = 0.20,
    ):
        if pass_threshold <= fail_threshold:
            raise ValueError("pass_threshold must be greater than fail_threshold")
        self.evaluator_root = evaluator_root
        self.vqa_model_path = vqa_model_path
        self.artifact_root = artifact_root
        self.pass_threshold = pass_threshold
        self.fail_threshold = fail_threshold

    def evaluate_to_report(
        self,
        *,
        task_spec: dict[str, Any],
        attempt_id: str,
        image_path: Path,
        report_ref: str | None = None,
    ) -> Geneval2Report:
        if not self.evaluator_root.exists():
            raise FileNotFoundError(f"missing Geneval2 root: {self.evaluator_root}")
        if not self.vqa_model_path.exists():
            raise FileNotFoundError(f"missing local VQA model path: {self.vqa_model_path}")
        if not image_path.exists():
            raise FileNotFoundError(f"missing image for Geneval2 evaluation: {image_path}")

        report_ref = report_ref or f"geneval2/{attempt_id}.json"
        report_path = self.artifact_root / report_ref
        if report_path.exists():
            return self._load_cached_report(
                task_spec=task_spec,
                attempt_id=attempt_id,
                report_ref=report_ref,
                report_path=report_path,
            )

        raw_results = self._evaluate(task_spec=task_spec, image_path=image_path)
        constraint_results = [
            {
                "constraint_id": result["constraint_id"],
                "status": result["status"],
                "expected": result["expected"],
                "observed": result["observed"],
                "confidence": result["confidence"],
            }
            for result in raw_results
        ]
        expected = {constraint["constraint_id"] for constraint in task_spec["constraints"]}
        observed = {result["constraint_id"] for result in constraint_results}
        if observed != expected:
            raise ValueError(
                "constraint coverage mismatch "
                f"missing={sorted(expected - observed)} extra={sorted(observed - expected)}"
            )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_payload = {
            "schema_version": "0.2",
            "attempt_id": attempt_id,
            "evaluator": "geneval2",
            "method": "soft_tifa_local_qwen3_vl",
            "normalization": self.normalization_policy(),
            "constraint_results": constraint_results,
            "raw_results": raw_results,
        }
        report_path.write_text(canonical_json(report_payload) + "\n", encoding="utf-8")
        report_sha256 = sha256_file(report_path)
        manifest_entry = artifact_manifest_entry(
            artifact_id=_report_artifact_id(attempt_id),
            attempt_id=attempt_id,
            artifact_type="geneval2_report",
            uri=report_ref,
            sha256=report_sha256,
            media_type="application/json",
            producer="local_geneval2_adapter",
            metadata={
                "method": "soft_tifa_local_qwen3_vl",
                "pass_threshold": self.pass_threshold,
                "fail_threshold": self.fail_threshold,
            },
        )
        return Geneval2Report(
            attempt_id=attempt_id,
            constraint_results=constraint_results,
            raw_results=raw_results,
            report_ref=report_ref,
            report_sha256=report_sha256,
            manifest_entry=manifest_entry,
            normalization=self.normalization_policy(),
        )

    def _load_cached_report(
        self,
        *,
        task_spec: dict[str, Any],
        attempt_id: str,
        report_ref: str,
        report_path: Path,
    ) -> Geneval2Report:
        import json

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if payload.get("attempt_id") != attempt_id:
            raise ValueError(f"cached Geneval2 report attempt mismatch: {report_path}")
        constraint_results = payload.get("constraint_results")
        raw_results = payload.get("raw_results")
        normalization = payload.get("normalization")
        if not isinstance(constraint_results, list) or not isinstance(raw_results, list):
            raise ValueError(f"cached Geneval2 report is incomplete: {report_path}")
        expected = {
            constraint["constraint_id"]
            for constraint in task_spec["constraints"]
        }
        observed = {
            result.get("constraint_id")
            for result in constraint_results
        }
        if observed != expected:
            raise ValueError(
                "cached Geneval2 constraint coverage mismatch "
                f"missing={sorted(expected - observed)} extra={sorted(observed - expected)}"
            )
        report_sha256 = sha256_file(report_path)
        manifest_entry = artifact_manifest_entry(
            artifact_id=_report_artifact_id(attempt_id),
            attempt_id=attempt_id,
            artifact_type="geneval2_report",
            uri=report_ref,
            sha256=report_sha256,
            media_type="application/json",
            producer="local_geneval2_adapter",
            metadata={
                "method": payload.get("method", "soft_tifa_local_qwen3_vl"),
                "pass_threshold": self.pass_threshold,
                "fail_threshold": self.fail_threshold,
                "cache_hit": True,
            },
        )
        return Geneval2Report(
            attempt_id=attempt_id,
            constraint_results=constraint_results,
            raw_results=raw_results,
            report_ref=report_ref,
            report_sha256=report_sha256,
            manifest_entry=manifest_entry,
            normalization=normalization or self.normalization_policy(),
        )

    def normalization_policy(self) -> dict[str, Any]:
        return {
            "schema_version": "0.2",
            "method": "soft_tifa_answer_probability_thresholds",
            "pass_threshold": self.pass_threshold,
            "fail_threshold": self.fail_threshold,
            "status_rule": (
                "pass when answer probability >= pass_threshold; "
                "fail when <= fail_threshold; otherwise uncertain"
            ),
        }

    def _evaluate(self, *, task_spec: dict[str, Any], image_path: Path) -> list[dict[str, Any]]:
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        from gen_retry.tools.torch_compat import patch_torch_from_numpy_if_needed

        patch_torch_from_numpy_if_needed()
        with exclusive_model_load():
            processor = AutoProcessor.from_pretrained(
                str(self.vqa_model_path),
                torch_dtype="auto",
                device_map="auto",
                local_files_only=True,
            )
            model = Qwen3VLForConditionalGeneration.from_pretrained(
                str(self.vqa_model_path),
                dtype="auto",
                device_map="auto",
                local_files_only=True,
            )
        try:
            results = []
            for constraint in task_spec["constraints"]:
                question = constraint["evaluator_question"]
                expected_answer = _expected_answer(constraint)
                answer_list = _answer_variants(question, expected_answer)
                prompt = f"{question} Answer in one word."
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": str(image_path)},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ]
                inputs = processor.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_dict=True,
                    return_tensors="pt",
                )
                inputs = inputs.to(model.device)
                with torch.inference_mode():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=1,
                        do_sample=False,
                        output_scores=True,
                        return_dict_in_generate=True,
                    )
                probs = torch.nn.functional.softmax(outputs.scores[0], dim=-1)
                answer_probability = 0.0
                token_ids = []
                for answer in answer_list:
                    encoded = processor.tokenizer.encode(answer, add_special_tokens=False)
                    if encoded:
                        token_id = encoded[0]
                        token_ids.append(token_id)
                        answer_probability += probs[0, token_id].item()
                pred = processor.batch_decode([torch.argmax(probs, dim=-1)[0]])[0]
                results.append(
                    {
                        "constraint_id": constraint["constraint_id"],
                        "question": question,
                        "expected": expected_answer,
                        "answer_variants": answer_list,
                        "answer_token_ids": token_ids,
                        "observed": pred,
                        "confidence": min(1.0, float(answer_probability)),
                        "status": self._status(float(answer_probability)),
                    }
                )
            return results
        finally:
            del model
            del processor
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def _status(self, answer_probability: float) -> str:
        if answer_probability >= self.pass_threshold:
            return "pass"
        if answer_probability <= self.fail_threshold:
            return "fail"
        return "uncertain"


def _expected_answer(constraint: dict[str, Any]) -> str:
    requirement = constraint.get("requirement") or ""
    match = re.search(r"Expected answer:\s*(.+)$", requirement)
    if match:
        return match.group(1).strip()
    return requirement.strip()


def _answer_variants(question: str, expected_answer: str) -> list[str]:
    expected = expected_answer.strip()
    if question.startswith("How many"):
        numeric = _numeric_string(expected)
        variants = [expected, expected.capitalize(), f" {expected}", f" {expected.capitalize()}"]
        if numeric != "other":
            variants.extend([numeric, f" {numeric}"])
        return _dedupe(variants)
    if expected.lower() in {"yes", "no"}:
        return _dedupe([expected, expected.lower(), f" {expected.lower()}", f" {expected.capitalize()}"])
    return _dedupe([expected, expected.lower(), f" {expected}", f" {expected.lower()}"])


def _numeric_string(number: str) -> str:
    return {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "ten": "10",
    }.get(number.lower(), "other")


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _report_artifact_id(attempt_id: str) -> str:
    if not attempt_id.startswith("a_") or not attempt_id[2:].isdigit():
        raise ValueError(f"cannot derive Geneval2 report artifact ID from {attempt_id}")
    return f"geneval2_report_{attempt_id[2:]}"
