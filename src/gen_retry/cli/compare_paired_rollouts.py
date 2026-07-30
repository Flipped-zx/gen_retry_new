from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase5.paired_rollout_comparison import (
    compare_paired_rollout_summaries,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare a candidate rollout batch with paired baseline episodes."
    )
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--candidate-summary", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    summary = compare_paired_rollout_summaries(
        baseline_summary_path=args.baseline_summary,
        candidate_summary_path=args.candidate_summary,
        artifact_path=args.artifact,
        report_path=args.report,
    )
    aggregate = summary["aggregate"]
    print(
        f"paired={summary['paired_episode_count']}; "
        f"pass_delta={aggregate['submitted_pass_count_delta']:+d}; "
        f"gm_delta_100={aggregate['submitted_gm_delta'] * 100:+.2f}"
    )


if __name__ == "__main__":
    main()
