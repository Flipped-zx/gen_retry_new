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
    args = parser.parse_args()

    summary = prepare_rollout_runs(
        selected_prompts_path=args.selected_prompts,
        output_root=args.output_root,
        summary_output=args.summary_output,
        max_image_attempts=args.max_image_attempts,
        created_at=args.created_at,
    )
    print(f"prepared {summary['prepared_count']} Phase 3 rollout directories")


if __name__ == "__main__":
    main()
