from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.verb_generation_strategy import (
    STRATEGY_IDS,
    run_strategy_episode,
    summarize_strategy_root,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a resumable generation-only experiment for one verb prompt technique."
        )
    )
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=Path("runs/phase7_flow_dppo200_fresh8_v1"),
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--strategy", choices=STRATEGY_IDS, required=True)
    parser.add_argument("--episode-id", action="append", dest="episode_ids", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--image-steps", type=int, default=50)
    parser.add_argument("--image-height", type=int, default=1024)
    parser.add_argument("--image-width", type=int, default=1024)
    args = parser.parse_args()

    for index, episode_id in enumerate(args.episode_ids, 1):
        baseline_episode_dir = args.baseline_root / episode_id
        if not baseline_episode_dir.is_dir():
            raise SystemExit(f"missing baseline episode: {baseline_episode_dir}")
        result = run_strategy_episode(
            baseline_episode_dir=baseline_episode_dir,
            output_episode_dir=args.run_root / episode_id,
            strategy_id=args.strategy,
            seed=args.seed,
            num_inference_steps=args.image_steps,
            height=args.image_height,
            width=args.image_width,
        )
        summary = summarize_strategy_root(args.run_root)
        print(
            f"[{index}/{len(args.episode_ids)}] {episode_id}: "
            f"verb={result['verb']} candidate={result['candidate']['verb_status']} "
            f"confidence={result['candidate']['verb_confidence']:.6f}; "
            f"running_pass={summary['verb_pass']['candidate']}/{summary['completed']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
