from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from gen_retry.runtime.json_canonical import canonical_json


LOCALIZED_SKILLS = {"attribute", "count", "object", "position", "verb"}


def build_legacy_analysis_records(trajectory_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with trajectory_path.open("r", encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            trajectory = json.loads(line)
            attempts = trajectory.get("attempts") or []
            by_round = {attempt.get("round"): attempt for attempt in attempts}
            for attempt in attempts:
                if attempt.get("round") in {None, 0}:
                    continue
                previous = by_round.get(attempt.get("round", 0) - 1)
                if previous is None:
                    continue
                transition = attempt.get("transition_from_previous") or {}
                teacher_action = attempt.get("teacher_action") or {}
                previous_report = previous.get("normalized_report") or {}
                record = _record_from_transition(
                    trajectory=trajectory,
                    line_number=line_number,
                    attempt=attempt,
                    previous_report=previous_report,
                    transition=transition,
                    teacher_action=teacher_action,
                )
                records.append(record)
    return records


def write_legacy_analysis_artifacts(
    *,
    records: list[dict[str, Any]],
    jsonl_path: Path,
    plausibility_report_path: Path,
    signature_report_path: Path,
) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(canonical_json(record))
            fh.write("\n")

    plausibility_report_path.parent.mkdir(parents=True, exist_ok=True)
    plausibility_report_path.write_text(
        _plausibility_report(records),
        encoding="utf-8",
    )
    signature_report_path.parent.mkdir(parents=True, exist_ok=True)
    signature_report_path.write_text(
        _signature_report(records),
        encoding="utf-8",
    )


def _record_from_transition(
    *,
    trajectory: dict[str, Any],
    line_number: int,
    attempt: dict[str, Any],
    previous_report: dict[str, Any],
    transition: dict[str, Any],
    teacher_action: dict[str, Any],
) -> dict[str, Any]:
    failed_before = [_compact_constraint(item) for item in previous_report.get("failed_constraints", [])]
    passed_before = [_compact_constraint(item) for item in previous_report.get("passed_constraints", [])]
    fixed = [_compact_constraint(item) for item in transition.get("fixed_constraints", [])]
    regressed = [_compact_constraint(item) for item in transition.get("regressed_constraints", [])]
    persistent = [_compact_constraint(item) for item in transition.get("persistent_failures", [])]
    failed_skills = sorted({item.get("skill") for item in failed_before if item.get("skill")})
    plausibility, evidence, strategy, confidence = _edit_plausibility(
        failed_before=failed_before,
        passed_before=passed_before,
        failed_skills=failed_skills,
        transition=transition,
    )

    prompt_id = str(trajectory.get("prompt_id") or trajectory.get("trajectory_id"))
    round_id = attempt.get("round")
    return {
        "schema_version": "0.2",
        "legacy_record_id": f"{trajectory.get('trajectory_id')}::round_{round_id}",
        "source_ref": (
            "legacy_gen_retry@2f03532e5f4685eafd2e47b23f14a3f2f8660aa3:"
            f"data/trajectories/geneval2_balanced100x5_normal_round0_4_master_trajectories.jsonl:{line_number}"
        ),
        "prompt_id": prompt_id,
        "original_prompt": trajectory.get("original_prompt"),
        "constraint_signature": {
            "failed_skill_histogram": dict(Counter(item.get("skill") for item in failed_before if item.get("skill"))),
            "failed_count": len(failed_before),
            "passed_count": len(passed_before),
            "transition_type": transition.get("transition_type"),
        },
        "pre_action_failed_constraints": failed_before,
        "pre_action_passed_constraints": passed_before,
        "historical_action": {
            "legacy_action_type": teacher_action.get("action_type"),
            "legacy_decision": teacher_action.get("decision"),
            "source_round": teacher_action.get("branch_source_round"),
        },
        "historical_strategy_tags": sorted(
            set((teacher_action.get("failure_types") or []) + failed_skills)
        ),
        "post_action_fixed_constraints": fixed,
        "post_action_regressed_constraints": regressed,
        "post_action_persistent_constraints": persistent,
        "edit_plausibility": plausibility,
        "edit_plausibility_evidence": evidence,
        "counterfactual_edit_strategy": strategy,
        "confidence": confidence,
        "limitations": [
            "Counterfactual analysis only; not experimentally verified.",
            "Legacy action was not a v0.2 edit_image execution.",
            "Legacy image bytes were not loaded into this analysis.",
            "Legacy records are not current-protocol positive SFT targets.",
        ],
        "final_status": trajectory.get("final_status"),
        "unresolved": bool(trajectory.get("unresolved")),
    }


def _compact_constraint(item: dict[str, Any]) -> dict[str, Any]:
    details = item.get("details") or {}
    atom_index = item.get("atom_index", details.get("atom_index"))
    return {
        "constraint_ref": f"atom:{atom_index}" if atom_index is not None else item.get("constraint_id"),
        "skill": item.get("skill") or details.get("skill"),
        "type": item.get("type"),
        "target": item.get("target") or details.get("question"),
        "expected": item.get("expected"),
    }


def _edit_plausibility(
    *,
    failed_before: list[dict[str, Any]],
    passed_before: list[dict[str, Any]],
    failed_skills: list[str],
    transition: dict[str, Any],
) -> tuple[str, list[str], str, float]:
    failed_count = len(failed_before)
    passed_count = len(passed_before)
    total = failed_count + passed_count
    pass_ratio = passed_count / total if total else 0.0
    localized = bool(failed_skills) and set(failed_skills).issubset(LOCALIZED_SKILLS)
    persistent_count = len(transition.get("persistent_failures", []) or [])
    regressed_count = len(transition.get("regressed_constraints", []) or [])

    evidence = [
        f"pre_action_failed_count={failed_count}",
        f"pre_action_pass_ratio={pass_ratio:.3f}",
        f"failed_skills={','.join(failed_skills) if failed_skills else 'unknown'}",
        f"post_regressed_count={regressed_count}",
        f"post_persistent_count={persistent_count}",
    ]
    if failed_count == 0:
        return (
            "undetermined",
            evidence + ["No pre-action failures were available."],
            "No counterfactual edit strategy inferred.",
            0.2,
        )
    if failed_count <= 2 and pass_ratio >= 0.75 and localized:
        plausibility = "high"
        confidence = 0.75
    elif failed_count <= 4 and pass_ratio >= 0.55 and localized:
        plausibility = "medium"
        confidence = 0.6
    elif failed_count >= 6 or pass_ratio < 0.4:
        plausibility = "low"
        confidence = 0.55
    else:
        plausibility = "undetermined"
        confidence = 0.4

    targets = "; ".join(
        item.get("target") or item.get("constraint_ref") or "unknown target"
        for item in failed_before[:4]
    )
    strategy = (
        "Counterfactual v0.2 edit hypothesis: edit the prior same-episode attempt "
        f"to repair localized failed constraints ({targets}) while preserving the "
        f"{passed_count} previously passed constraints."
    )
    return plausibility, evidence, strategy, confidence


def _plausibility_report(records: list[dict[str, Any]]) -> str:
    counts = Counter(record["edit_plausibility"] for record in records)
    action_counts = Counter(
        record["historical_action"].get("legacy_decision") or record["historical_action"].get("legacy_action_type")
        for record in records
    )
    lines = [
        "# Legacy Edit Plausibility Analysis",
        "",
        "This report is counterfactual evidence only. It does not describe executed",
        "v0.2 edit actions and must not be used as positive SFT supervision.",
        "",
        f"- Records analyzed: {len(records)}",
        f"- Historical action decisions: {dict(sorted(action_counts.items()))}",
        f"- Edit plausibility counts: {dict(sorted(counts.items()))}",
        "",
        "Legacy records are used only for difficulty estimation, failure-signature",
        "analysis, prompt-selection evidence, and strategy hypotheses for fresh Phase 3 rollouts.",
        "",
    ]
    return "\n".join(lines)


def _signature_report(records: list[dict[str, Any]]) -> str:
    signature_counts: Counter[str] = Counter()
    by_plausibility: dict[str, Counter[str]] = defaultdict(Counter)
    unresolved_by_signature: Counter[str] = Counter()
    for record in records:
        signature = ",".join(
            f"{key}:{value}"
            for key, value in sorted(record["constraint_signature"]["failed_skill_histogram"].items())
        ) or "unknown"
        signature_counts[signature] += 1
        by_plausibility[record["edit_plausibility"]][signature] += 1
        if record.get("unresolved"):
            unresolved_by_signature[signature] += 1

    lines = [
        "# Legacy Failure Signature Summary",
        "",
        "Source: legacy Gen-Retry trajectory JSONL. Legacy images were not loaded.",
        "",
        "## Top Failed-Skill Signatures",
        "",
    ]
    for signature, count in signature_counts.most_common(20):
        lines.append(
            f"- `{signature}`: {count} records, {unresolved_by_signature[signature]} from unresolved trajectories"
        )
    lines.extend(["", "## Plausibility By Signature", ""])
    for plausibility in sorted(by_plausibility):
        top = ", ".join(
            f"{signature}={count}"
            for signature, count in by_plausibility[plausibility].most_common(8)
        )
        lines.append(f"- `{plausibility}`: {top}")
    lines.append("")
    return "\n".join(lines)
