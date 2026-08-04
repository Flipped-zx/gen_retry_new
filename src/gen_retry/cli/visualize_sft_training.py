from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.sft_training import (
    summarize_sft_training,
    write_sft_training_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize a LLaMA-Factory/Hugging Face trainer_state.json and "
            "render SFT training curves."
        )
    )
    parser.add_argument(
        "--trainer-state",
        type=Path,
        required=True,
        help="trainer_state.json or an output directory containing it",
    )
    parser.add_argument(
        "--action-metrics",
        type=Path,
        help="optional JSONL of structured action metrics",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", default="sft_training")
    args = parser.parse_args()

    summary = summarize_sft_training(
        trainer_state_path=args.trainer_state,
        action_metrics_path=args.action_metrics,
    )
    paths = write_sft_training_report(
        summary=summary,
        output_dir=args.output_dir,
        stem=args.name,
    )
    training = summary["training"]
    print(
        "SFT report written: "
        f"step={training['latest_step']}; "
        f"progress={training['progress_fraction']}; "
        f"summary={paths['summary']}"
    )


if __name__ == "__main__":
    main()
