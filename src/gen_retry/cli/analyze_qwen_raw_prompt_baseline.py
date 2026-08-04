from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.qwen_raw_prompt_baseline import summarize_raw_prompt_baseline


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a raw-prompt Qwen baseline.")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    summary = summarize_raw_prompt_baseline(
        run_root=args.run_root,
        artifact_path=args.artifact,
        report_path=args.report,
    )
    print(
        f"{summary['status']}: {summary['episode_count']} episodes, "
        f"{summary['total_image_calls']} image calls; "
        f"single_gm={summary['single']['gm_100']:.2f}; "
        f"best5_gm={summary['best_of_5_gm']['gm_100']:.2f}"
    )


if __name__ == "__main__":
    main()
