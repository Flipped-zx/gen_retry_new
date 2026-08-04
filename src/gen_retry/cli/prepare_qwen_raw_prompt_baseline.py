from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.qwen_raw_prompt_baseline import prepare_raw_prompt_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a fresh raw-prompt Qwen baseline.")
    parser.add_argument("--source-run-root", type=Path, required=True)
    parser.add_argument("--episode-id", action="append", dest="episode_ids", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--variant-count", type=int, default=5)
    parser.add_argument("--image-steps", type=int, default=50)
    parser.add_argument("--image-height", type=int, default=1024)
    parser.add_argument("--image-width", type=int, default=1024)
    args = parser.parse_args()
    plan = prepare_raw_prompt_baseline(
        source_run_root=args.source_run_root,
        episode_ids=args.episode_ids,
        output_root=args.output_root,
        plan_output=args.plan,
        variant_count=args.variant_count,
        image_steps=args.image_steps,
        height=args.image_height,
        width=args.image_width,
    )
    print(
        f"prepared {plan['episode_count']} episodes x {plan['variant_count']} variants: "
        f"{args.output_root}"
    )


if __name__ == "__main__":
    main()
