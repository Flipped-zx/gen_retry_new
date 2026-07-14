from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gen_retry.phase3.selection import select_candidates
from gen_retry.runtime.json_canonical import canonical_json


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(data) + "\n", encoding="utf-8")


def select_phase3_prompts(
    *,
    candidate_pool: Path,
    selected_output: Path,
    coverage_output: Path,
    prompt_selection_report: Path = Path("docs/phase3/prompt_selection_report.md"),
    selection_provenance: Path = Path("docs/phase3/selection_provenance.md"),
    limit: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected, coverage = select_candidates(load_jsonl(candidate_pool), limit=limit)
    selected_payload = {
        "schema_version": "0.2",
        "selection_method": "deterministic_greedy_v0_2",
        "selected_count": len(selected),
        "selected_prompts": selected,
    }
    write_json(selected_output, selected_payload)
    write_json(coverage_output, coverage)
    prompt_selection_report.parent.mkdir(parents=True, exist_ok=True)
    prompt_selection_report.write_text(
        build_prompt_selection_report(selected_payload, coverage),
        encoding="utf-8",
    )
    selection_provenance.parent.mkdir(parents=True, exist_ok=True)
    selection_provenance.write_text(
        build_selection_provenance_report(
            candidate_pool=candidate_pool,
            selected_output=selected_output,
            coverage_output=coverage_output,
            selected=selected,
        ),
        encoding="utf-8",
    )
    return selected, coverage


def build_prompt_selection_report(
    selected_payload: dict[str, Any],
    coverage: dict[str, Any],
) -> str:
    lines = [
        "# Phase 3 Prompt Selection Report",
        "",
        f"Selection method: `{selected_payload['selection_method']}`.",
        "",
        "The selector optimizes high metadata difficulty, new constraint-type",
        "coverage, difficult multi-type combinations, low semantic duplication,",
        "and grounded historical difficulty evidence when available.",
        "",
        f"- Selected prompts: {selected_payload['selected_count']}",
        f"- Aggregate constraint coverage: {coverage['aggregate_type_counts']}",
        "",
        "## Selected Prompts",
        "",
    ]
    for candidate in selected_payload["selected_prompts"]:
        reason = candidate["selection_reason"]
        historical = candidate.get("historical_difficulty_evidence") or {}
        lines.extend(
            [
                f"### {candidate['selection_rank']}. `{candidate['candidate_id']}`",
                "",
                f"- Prompt ID: `{candidate['prompt_id']}`",
                f"- Prompt: {candidate['original_prompt']}",
                f"- Selection score: {candidate['selection_score']}",
                f"- Constraint count: {candidate['constraint_count']}",
                f"- Constraint type histogram: {candidate['constraint_type_histogram']}",
                f"- Historical transition matches: {historical.get('matched_legacy_transition_count', 0)}",
                (
                    "- Grounded difficulty evidence: "
                    f"difficulty={reason['difficulty_score']}, "
                    f"new_coverage={reason['new_coverage_bonus']}, "
                    f"rare_type={reason['rare_type_bonus']}, "
                    f"combination={reason['combination_bonus']}, "
                    f"duplication_penalty={reason['duplication_penalty']}, "
                    f"imbalance_penalty={reason['imbalance_penalty']}"
                ),
                f"- Duplication group: `{candidate['semantic_duplication_group']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitations",
            "",
            "- No live baseline image generation or Geneval2 evaluation was run during selection.",
            "- Historical evidence is counterfactual prompt-difficulty evidence only.",
            "- Missing behavior coverage after live rollouts must be reported as a limitation,",
            "  not manufactured by replacing valid trajectories.",
            "",
        ]
    )
    return "\n".join(lines)


def build_selection_provenance_report(
    *,
    candidate_pool: Path,
    selected_output: Path,
    coverage_output: Path,
    selected: list[dict[str, Any]],
) -> str:
    source_refs = sorted(
        candidate["provenance"]["source_ref"]
        for candidate in selected
        if isinstance(candidate.get("provenance"), dict)
        and "source_ref" in candidate["provenance"]
    )
    lines = [
        "# Phase 3 Selection Provenance",
        "",
        "This selection was made before any Phase 3 live rollout.",
        "",
        f"- Candidate pool artifact: `{candidate_pool}`",
        f"- Selected prompts artifact: `{selected_output}`",
        f"- Coverage matrix artifact: `{coverage_output}`",
        "- Selector: deterministic greedy `difficulty + new_coverage + "
        "rare_combination_bonus - imbalance_penalty - semantic_duplication_penalty`.",
        "- Legacy evidence use: difficulty and failure-signature context only.",
        "- Legacy images or attempts imported: no.",
        "- First action requirement for future rollouts: fresh `generate_image` or",
        "  allowed `query_skill` followed by fresh generation.",
        "",
        "## Selected Source Rows",
        "",
    ]
    lines.extend(f"- `{source_ref}`" for source_ref in source_refs)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Select deterministic Phase 3 prompts.")
    parser.add_argument(
        "--candidate-pool",
        type=Path,
        default=Path("artifacts/phase3/candidate_pool.jsonl"),
    )
    parser.add_argument(
        "--selected-output",
        type=Path,
        default=Path("artifacts/phase3/selected_ten_prompts.json"),
    )
    parser.add_argument(
        "--coverage-output",
        type=Path,
        default=Path("artifacts/phase3/constraint_coverage_matrix.json"),
    )
    parser.add_argument(
        "--prompt-selection-report",
        type=Path,
        default=Path("docs/phase3/prompt_selection_report.md"),
    )
    parser.add_argument(
        "--selection-provenance",
        type=Path,
        default=Path("docs/phase3/selection_provenance.md"),
    )
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    selected, _coverage = select_phase3_prompts(
        candidate_pool=args.candidate_pool,
        selected_output=args.selected_output,
        coverage_output=args.coverage_output,
        prompt_selection_report=args.prompt_selection_report,
        selection_provenance=args.selection_provenance,
        limit=args.limit,
    )
    print(f"selected {len(selected)} Phase 3 prompts")


if __name__ == "__main__":
    main()
