from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.qwen_best_of_5_baseline import (
    analyze_qwen_best_of_5_baseline,
    write_qwen_best_of_5_analysis,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare a Qwen-Image Best-of-5 detail file with the paired "
            "200-trajectory Agent summary."
        )
    )
    parser.add_argument("--baseline-detail", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--agent-summary", type=Path, required=True)
    parser.add_argument("--agent-run-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=20_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_260_731)
    args = parser.parse_args()

    summary = analyze_qwen_best_of_5_baseline(
        baseline_detail_path=args.baseline_detail,
        selection_path=args.selection,
        agent_summary_path=args.agent_summary,
        agent_run_root=args.agent_run_root,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
    )
    write_qwen_best_of_5_analysis(
        summary=summary,
        artifact_path=args.artifact,
        report_path=args.report,
    )
    aggregate = summary["aggregate"]
    baseline = aggregate["baseline_gm_selected"]
    agent = aggregate["agent_submitted"]
    delta = aggregate["agent_vs_baseline"]
    print(
        f"paired={summary['scope']['paired_episode_count']}; "
        f"baseline_pass={baseline['passed_atoms']}/"
        f"{baseline['constraint_slots']}; "
        f"agent_pass={agent['passed_atoms']}/{agent['constraint_slots']}; "
        f"pass_delta={delta['passed_atoms']:+d}; "
        f"gm_delta_100={delta['soft_tifa_gm'] * 100:+.2f}"
    )


if __name__ == "__main__":
    main()
