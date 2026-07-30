from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.rollout_prep import prepare_rollout_runs


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare fresh Phase 3 rollout run directories.")
    parser.add_argument(
        "--selected-prompts",
        type=Path,
        default=Path("artifacts/phase3/selected_ten_prompts.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("runs/phase3"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/phase3/prepared_rollouts.json"),
    )
    parser.add_argument("--max-image-attempts", type=int, default=5)
    parser.add_argument("--created-at", default="2026-07-14T00:00:00Z")
    parser.add_argument(
        "--limit",
        type=int,
        help="Prepare only the first N already-selected prompts without rerunning selection.",
    )
    parser.add_argument(
        "--prompt-id",
        action="append",
        dest="prompt_ids",
        help="Prepare only these already-selected prompt IDs; may be repeated.",
    )
    parser.add_argument(
        "--execution-profile-id",
        default="qwen_image_edit_only",
    )
    parser.add_argument(
        "--execution-profile-version",
        default="1",
    )
    parser.add_argument(
        "--score-policy-id",
        choices=[
            "geneval2_pass_count_then_gm",
            "pass_count_only_then_earlier",
        ],
        default="geneval2_pass_count_then_gm",
    )
    args = parser.parse_args()

    summary = prepare_rollout_runs(
        selected_prompts_path=args.selected_prompts,
        output_root=args.output_root,
        summary_output=args.summary_output,
        max_image_attempts=args.max_image_attempts,
        created_at=args.created_at,
        limit=args.limit,
        prompt_ids=args.prompt_ids,
        score_policy_id=args.score_policy_id,
        execution_profile_id=args.execution_profile_id,
        execution_profile_version=args.execution_profile_version,
    )
    print(f"prepared {summary['prepared_count']} Phase 3 rollout directories")


if __name__ == "__main__":
    main()
