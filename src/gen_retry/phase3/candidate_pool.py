from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from gen_retry.runtime.json_canonical import canonical_json


GENEVAL2_COMMIT = "a6e82d2289e8d418f27f0adee77908b07060eea3"


def build_candidate_pool(
    *,
    geneval2_data_path: Path,
    legacy_analysis_path: Path | None = None,
) -> list[dict[str, Any]]:
    historical_by_prompt = (
        _historical_evidence_by_prompt(legacy_analysis_path)
        if legacy_analysis_path is not None and legacy_analysis_path.exists()
        else {}
    )
    candidates: list[dict[str, Any]] = []
    with geneval2_data_path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row_hash = hashlib.sha256(canonical_json(row).encode("utf-8")).hexdigest()[:12]
            prompt_id = f"geneval2_{line_number:04d}_{row_hash}"
            prompt = row["prompt"].strip()
            skills = row.get("skills") or []
            constraints = _constraints(row)
            histogram = dict(Counter(skills))
            historical = historical_by_prompt.get(_normalize_prompt(prompt), {})
            candidates.append(
                {
                    "schema_version": "0.2",
                    "candidate_id": f"cand_{line_number:04d}_{row_hash}",
                    "prompt_id": prompt_id,
                    "original_prompt": prompt,
                    "atomic_constraints": constraints,
                    "constraint_count": len(constraints),
                    "constraint_type_histogram": histogram,
                    "constraint_type_combination": sorted(histogram),
                    "baseline_difficulty_evidence": {
                        "geneval2_atom_count": row.get("atom_count"),
                        "vqa_constraint_count": len(constraints),
                        "difficulty_source": "Geneval2 prompt metadata only; no live baseline evaluation run.",
                    },
                    "historical_difficulty_evidence": historical.get("historical_difficulty_evidence", {}),
                    "historical_unresolved_evidence": historical.get("historical_unresolved_evidence", {}),
                    "semantic_duplication_group": _semantic_group(prompt),
                    "provenance": {
                        "source": "geneval2",
                        "source_ref": (
                            f"geneval2@{GENEVAL2_COMMIT}:geneval2_data.jsonl:{line_number}"
                        ),
                        "row_sha256_prefix": row_hash,
                    },
                    "selection_eligibility": True,
                }
            )
    return candidates


def write_candidate_pool_artifacts(
    *,
    candidates: list[dict[str, Any]],
    jsonl_path: Path,
    report_path: Path,
) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for candidate in candidates:
            fh.write(canonical_json(candidate))
            fh.write("\n")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_candidate_pool_report(candidates), encoding="utf-8")


def _constraints(row: dict[str, Any]) -> list[dict[str, Any]]:
    vqa_list = row.get("vqa_list") or []
    skills = row.get("skills") or []
    constraints = []
    for index, item in enumerate(vqa_list, start=1):
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"Geneval2 VQA atom {index} is not a [question, answer] pair")
        question, expected = item
        constraints.append(
            {
                "constraint_id": f"c_{index:03d}",
                "constraint_type": str(skills[index - 1]),
                "requirement": f"Expected answer: {expected}",
                "evaluator_question": question,
                "priority": 3,
            }
        )
    return constraints


def _historical_evidence_by_prompt(path: Path) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                record = json.loads(line)
                prompt = record.get("original_prompt")
                if isinstance(prompt, str) and prompt.strip():
                    grouped[_normalize_prompt(prompt)].append(record)

    evidence: dict[str, dict[str, Any]] = {}
    for prompt, records in grouped.items():
        plausibility = Counter(record["edit_plausibility"] for record in records)
        retry_depth = max(len(records), 0)
        unresolved_count = sum(1 for record in records if record.get("unresolved"))
        evidence[prompt] = {
            "historical_difficulty_evidence": {
                "matched_legacy_transition_count": len(records),
                "max_observed_retry_depth": retry_depth,
                "edit_plausibility_counts": dict(sorted(plausibility.items())),
                "source": "legacy_counterfactual_analysis",
            },
            "historical_unresolved_evidence": {
                "unresolved_count": unresolved_count,
                "matched_legacy_record_ids": [
                    record["legacy_record_id"] for record in records[:20]
                ],
            },
        }
    return evidence


def _candidate_pool_report(candidates: list[dict[str, Any]]) -> str:
    type_counts = Counter(
        constraint_type
        for candidate in candidates
        for constraint_type in candidate["constraint_type_histogram"]
        for _ in range(candidate["constraint_type_histogram"][constraint_type])
    )
    constraint_count_dist = Counter(candidate["constraint_count"] for candidate in candidates)
    historical_matches = sum(
        1
        for candidate in candidates
        if candidate["historical_difficulty_evidence"].get("matched_legacy_transition_count")
    )
    lines = [
        "# Phase 3 Candidate Pool Report",
        "",
        "Candidate pool source is Geneval2 prompt metadata. No live image generation",
        "or evaluator calls were run while constructing this pool.",
        "",
        f"- Candidate count: {len(candidates)}",
        f"- Historical-evidence matched candidates: {historical_matches}",
        f"- Constraint type counts: {dict(sorted(type_counts.items()))}",
        f"- Constraint-count distribution: {dict(sorted(constraint_count_dist.items()))}",
        "",
        "The actual Geneval2 skill taxonomy is preserved as constraint types:",
        "`attribute`, `count`, `object`, `position`, and `verb`.",
        "",
        "Legacy evidence, when present, is difficulty/context evidence only. It",
        "does not import legacy images or legacy attempts into Phase 3 episodes.",
        "",
    ]
    return "\n".join(lines)


def _normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.strip().lower())


def _semantic_group(prompt: str) -> str:
    normalized = _normalize_prompt(prompt)
    token_prefix = "_".join(re.findall(r"[a-z0-9]+", normalized)[:6]) or "prompt"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{token_prefix}_{digest}"
