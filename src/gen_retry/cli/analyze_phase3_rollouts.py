from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.trajectory_analysis import analyze_phase3_rollouts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze completed Phase 3 fresh live rollouts.",
    )
    parser.add_argument("--run-root", type=Path, default=Path("runs/phase3"))
    parser.add_argument(
        "--invalid-run-root",
        type=Path,
        default=Path("runs/phase3_invalid"),
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("artifacts/phase3"),
    )
    parser.add_argument("--docs-root", type=Path, default=Path("docs/phase3"))
    parser.add_argument("--expected-count", type=int, default=10)
    args = parser.parse_args()
    result = analyze_phase3_rollouts(
        run_root=args.run_root,
        invalid_run_root=args.invalid_run_root,
        artifact_root=args.artifact_root,
        docs_root=args.docs_root,
        expected_count=args.expected_count,
    )
    print(
        "analyzed {episode_count} episodes; labeled {action_label_count} actions; "
        "archived invalid runs={invalid_run_count}".format(**result)
    )


if __name__ == "__main__":
    main()
