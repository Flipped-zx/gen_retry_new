from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.sft_rollout import analyze_sft_rollouts


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit local-SFT production rollouts.")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--episode-id", action="append", dest="episode_ids", required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    summary = analyze_sft_rollouts(
        run_root=args.run_root,
        episode_ids=args.episode_ids,
        artifact_path=args.artifact,
        report_path=args.report,
    )
    print(
        f"{summary['status']}: {summary['episode_count']} episodes, "
        f"{summary['image_call_count']} image calls, "
        f"format_valid={summary['format']['valid_rate']:.2%}"
    )


if __name__ == "__main__":
    main()
