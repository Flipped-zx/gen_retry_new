from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.sft_rollout_prep import prepare_frozen_test_rollouts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare fresh rollouts from frozen SFT-test TaskSpecs only."
    )
    parser.add_argument("--source-run-root", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    summary = prepare_frozen_test_rollouts(
        source_run_root=args.source_run_root,
        split_manifest_path=args.split_manifest,
        output_root=args.output_root,
        summary_output=args.summary_output,
        checkpoint_path=args.checkpoint,
        limit=args.limit,
    )
    print(
        f"prepared {summary['prepared_count']} fresh frozen-test rollouts: "
        + ",".join(summary["episode_ids"])
    )


if __name__ == "__main__":
    main()
