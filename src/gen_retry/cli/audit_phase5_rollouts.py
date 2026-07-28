from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase5.rollout_audit import audit_rollout_batch


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit a completed Flow-DPPO Geneval2 rollout batch."
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=20)
    args = parser.parse_args()
    summary = audit_rollout_batch(
        run_root=args.run_root,
        selection_path=args.selection,
        artifact_path=args.artifact,
        report_path=args.report,
        expected_count=args.expected_count,
    )
    print(
        f"{summary['status']}: {summary['validated_episode_count']} episodes, "
        f"{summary['total_image_attempts']} attempts"
    )


if __name__ == "__main__":
    main()
