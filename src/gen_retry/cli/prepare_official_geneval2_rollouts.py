from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.score_policy import (
    PRIMARY_POLICY_ID,
    planner_context_version,
    score_policy_for_id,
)
from gen_retry.phase3.rollout_prep import _prepare_one_run
from gen_retry.protocol.task_spec_builder import task_spec_from_geneval2_row
from gen_retry.runtime.json_canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a fresh production run from the official 800-row "
            "GenEval2 benchmark. Only benchmark rows are read; no prior "
            "trajectory artifacts are imported."
        )
    )
    parser.add_argument("--benchmark-data", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--max-image-attempts", type=int, default=5)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--execution-profile-id", default="qwen_dual_backend"
    )
    parser.add_argument("--execution-profile-version", default="1")
    args = parser.parse_args()

    if args.max_image_attempts < 1 or args.max_image_attempts > 10:
        raise SystemExit("--max-image-attempts must be in [1, 10]")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise SystemExit(f"refusing non-empty output root: {args.output_root}")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be positive")

    benchmark_bytes = args.benchmark_data.read_bytes()
    rows = _read_rows(benchmark_bytes)
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("benchmark data has no rows")

    score_policy = score_policy_for_id(PRIMARY_POLICY_ID)
    context_version = planner_context_version(score_policy)
    benchmark_sha = sha256_bytes(benchmark_bytes)
    prepared: list[dict[str, Any]] = []
    atom_counts: Counter[int] = Counter()
    skill_counts: Counter[str] = Counter()
    for rank, row in enumerate(rows, start=1):
        episode_id = f"phase3_ep_{rank:03d}"
        task_spec = task_spec_from_geneval2_row(
            row,
            episode_id=episode_id,
            max_image_attempts=args.max_image_attempts,
        )
        atom_counts[int(row["atom_count"])] += 1
        skill_counts.update(str(skill) for skill in row.get("skills", []))
        constraints = task_spec["constraints"]
        histogram = Counter(c["constraint_type"] for c in constraints)
        candidate = {
            "candidate_id": f"official_geneval2_{rank:04d}",
            "prompt_id": f"official_geneval2_{rank:04d}",
            "selection_rank": rank,
            "original_prompt": task_spec["original_prompt"],
            "atomic_constraints": constraints,
            "constraint_type_histogram": dict(sorted(histogram.items())),
            "provenance": {
                "source": "official_geneval2_benchmark",
                "benchmark_data_ref": str(args.benchmark_data.resolve()),
                "benchmark_data_sha256": benchmark_sha,
                "benchmark_row_index": rank - 1,
                "official_geneval2": True,
                "source_read_policy": "benchmark_row_prompt_vqa_skills_only",
                "legacy_artifacts_imported": False,
            },
        }
        prepared.append(
            _prepare_one_run(
                candidate=candidate,
                output_root=args.output_root,
                max_image_attempts=args.max_image_attempts,
                created_at="2026-08-04T00:00:00Z",
                execution_profile_id=args.execution_profile_id,
                execution_profile_version=str(args.execution_profile_version),
                score_policy=score_policy,
                planner_context_schema_version=context_version,
                selection_artifact_ref=str(args.benchmark_data.resolve()),
                selection_artifact_sha256=benchmark_sha,
            )
        )

    summary = {
        "schema_version": "0.2",
        "cohort": "official_geneval2_800_sft_production",
        "benchmark_data_ref": str(args.benchmark_data.resolve()),
        "benchmark_data_sha256": benchmark_sha,
        "benchmark_row_count": len(rows),
        "source_read_policy": "benchmark_row_prompt_vqa_skills_only",
        "legacy_artifacts_imported": False,
        "prepared_count": len(prepared),
        "fresh_run_root": str(args.output_root.resolve()),
        "max_image_attempts": args.max_image_attempts,
        "planner": {
            "provider": "local_transformers_service",
            "system_prompt": "phase4_sft_system_prompt_action_protocol_v0_5",
            "planner_context_schema_version": context_version,
            "action_protocol_version": "0.5",
            "teacher_fallback_allowed": False,
        },
        "execution_profile": {
            "profile_id": args.execution_profile_id,
            "profile_version": str(args.execution_profile_version),
            "generate_steps": 50,
            "edit_steps": 40,
            "width": 1024,
            "height": 1024,
        },
        "official_atom_count_histogram": dict(sorted(atom_counts.items())),
        "constraint_type_histogram": dict(sorted(skill_counts.items())),
        "episodes": prepared,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    print(
        f"prepared {len(prepared)} fresh official Geneval2 rollouts under "
        f"{args.output_root}; benchmark_sha256={benchmark_sha}"
    )


def _read_rows(raw: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"benchmark row {line_number} is not an object")
        if not isinstance(row.get("atom_count"), int):
            raise ValueError(f"benchmark row {line_number} has invalid atom_count")
        if not isinstance(row.get("skills"), list):
            raise ValueError(f"benchmark row {line_number} has invalid skills")
        rows.append(row)
    return rows


if __name__ == "__main__":
    main()
