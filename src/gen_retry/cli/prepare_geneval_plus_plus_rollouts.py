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
from gen_retry.protocol.task_spec_builder import (
    GENEVAL_PLUS_PLUS_TAGS,
    task_spec_from_geneval_plus_plus_row,
)
from gen_retry.runtime.json_canonical import canonical_json


PROTOCOL_ID = "geneval_plus_plus_metadata_aware_agent"
PROTOCOL_VERSION = "1"
UPSTREAM_URL = "https://github.com/yejy53/Echo-4o.git"
UPSTREAM_COMMIT = "28f36d76558e5f53b9deceda78bf025ef0d0ea24"
OFFICIAL_ROW_COUNT = 280


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare metadata-aware SFT Agent rollouts for Geneval++."
    )
    parser.add_argument("--benchmark-data", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--max-image-attempts", type=int, default=5)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    args.output_root = args.output_root.resolve()
    args.summary_output = args.summary_output.resolve()
    if not 1 <= args.max_image_attempts <= 10:
        raise SystemExit("--max-image-attempts must be in [1, 10]")
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be positive")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise SystemExit(f"refusing non-empty output root: {args.output_root}")

    benchmark_bytes = args.benchmark_data.read_bytes()
    rows = read_official_rows(benchmark_bytes)
    selected = rows[: args.limit] if args.limit is not None else rows
    benchmark_sha = sha256_bytes(benchmark_bytes)
    score_policy = score_policy_for_id(PRIMARY_POLICY_ID)
    context_version = planner_context_version(score_policy)
    prepared: list[dict[str, Any]] = []
    tag_counts: Counter[str] = Counter()

    for rank, source in enumerate(selected, start=1):
        row = source["row"]
        episode_id = f"phase3_ep_{rank:03d}"
        task_spec = task_spec_from_geneval_plus_plus_row(
            row,
            episode_id=episode_id,
            max_image_attempts=args.max_image_attempts,
        )
        metadata_ref = "geneval_plus_plus_metadata.json"
        run_dir = args.output_root / episode_id
        constraints = task_spec["constraints"]
        candidate = {
            "candidate_id": f"geneval_plus_plus_{source['row_index'] + 1:03d}",
            "prompt_id": f"geneval_plus_plus_{source['row_index'] + 1:03d}",
            "selection_rank": rank,
            "original_prompt": task_spec["original_prompt"],
            "atomic_constraints": constraints,
            "constraint_type_histogram": dict(
                sorted(Counter(c["constraint_type"] for c in constraints).items())
            ),
            "provenance": {
                "protocol_id": PROTOCOL_ID,
                "protocol_version": PROTOCOL_VERSION,
                "planner_visibility": "metadata_derived_rubric_visible_before_first_action",
                "online_feedback_role": "geneval2_compatible_vqa_proxy_only",
                "official_score_role": "post_submission_echo4o_gpt_4_1_evaluator",
                "upstream_url": UPSTREAM_URL,
                "upstream_commit": UPSTREAM_COMMIT,
                "benchmark_data_ref": str(args.benchmark_data.resolve()),
                "benchmark_data_sha256": benchmark_sha,
                "benchmark_row_index": source["row_index"],
                "row_raw_sha256": source["raw_sha256"],
                "row_semantic_sha256": source["semantic_sha256"],
                "source_metadata_ref": metadata_ref,
            },
        }
        result = _prepare_one_run(
            candidate=candidate,
            output_root=args.output_root,
            max_image_attempts=args.max_image_attempts,
            created_at="2026-08-14T00:00:00Z",
            execution_profile_id="qwen_dual_backend",
            execution_profile_version="1",
            score_policy=score_policy,
            planner_context_schema_version=context_version,
            selection_artifact_ref=str(args.benchmark_data.resolve()),
            selection_artifact_sha256=benchmark_sha,
        )
        (run_dir / metadata_ref).write_text(
            canonical_json(row) + "\n", encoding="utf-8"
        )
        result.update(
            {
                "benchmark_row_index": source["row_index"],
                "row_raw_sha256": source["raw_sha256"],
                "row_semantic_sha256": source["semantic_sha256"],
                "source_metadata_ref": metadata_ref,
            }
        )
        prepared.append(result)
        tag_counts[row["tag"]] += 1

    summary = {
        "schema_version": "0.1",
        "protocol": {"protocol_id": PROTOCOL_ID, "protocol_version": PROTOCOL_VERSION},
        "disclosure": (
            "Planner sees metadata-derived rubric before its first action; "
            "online VQA is proxy feedback and not the Geneval++ GPT-4.1 score."
        ),
        "benchmark": {
            "upstream_url": UPSTREAM_URL,
            "upstream_commit": UPSTREAM_COMMIT,
            "data_ref": str(args.benchmark_data.resolve()),
            "data_sha256": benchmark_sha,
            "validated_row_count": len(rows),
            "selected_row_count": len(selected),
            "tag_histogram": dict(sorted(tag_counts.items())),
        },
        "planner": {
            "provider": "sft",
            "planner_context_schema_version": context_version,
            "action_protocol_version": "0.5",
        },
        "execution_profile": {"profile_id": "qwen_dual_backend", "profile_version": "1"},
        "max_image_attempts": args.max_image_attempts,
        "online_selection": {
            "role": "proxy",
            "evaluator": "Geneval2-compatible VQA",
            "score_policy": score_policy,
        },
        "final_evaluation": {
            "images_per_prompt": 1,
            "image_policy": "canonical_reducer_submitted_attempt_only",
            "image_naming": "one_based_row_index_jpeg",
            "evaluator": "Echo-4o Eval-gpt-4.1-geneval++.py",
        },
        "fresh_run_root": str(args.output_root),
        "episodes": prepared,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    print(f"prepared {len(prepared)} {PROTOCOL_ID}@{PROTOCOL_VERSION} rollouts")


def read_official_rows(raw: bytes) -> list[dict[str, Any]]:
    lines = [line for line in raw.splitlines() if line.strip()]
    if len(lines) != OFFICIAL_ROW_COUNT:
        raise ValueError(
            f"Geneval++ benchmark must contain exactly {OFFICIAL_ROW_COUNT} "
            f"non-empty rows; found {len(lines)}"
        )
    rows: list[dict[str, Any]] = []
    tags: Counter[str] = Counter()
    for index, line in enumerate(lines):
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"benchmark row {index} is not an object")
        task_spec_from_geneval_plus_plus_row(
            row, episode_id=f"validation_{index:03d}"
        )
        tags[row["tag"]] += 1
        rows.append(
            {
                "row_index": index,
                "row": row,
                "raw_sha256": sha256_bytes(line),
                "semantic_sha256": sha256_bytes(canonical_json(row).encode("utf-8")),
            }
        )
    if set(tags) != GENEVAL_PLUS_PLUS_TAGS or set(tags.values()) != {40}:
        raise ValueError(f"Geneval++ tag coverage mismatch: {dict(sorted(tags.items()))}")
    return rows


if __name__ == "__main__":
    main()
