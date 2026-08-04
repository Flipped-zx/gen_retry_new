from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.sft.supervision import (
    run_phase4_sft_dry_run,
    skill_supervision_policy,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 4 SFT supervision dry run.")
    parser.add_argument("--run-root", type=Path, default=Path("runs/phase3"))
    parser.add_argument(
        "--labels-path",
        type=Path,
        default=Path("artifacts/phase3/action_supervision_labels.jsonl"),
    )
    parser.add_argument("--output-root", type=Path, default=Path("artifacts/phase4"))
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("docs/phase4/sft_export_dry_run_report.md"),
    )
    parser.add_argument(
        "--skill-supervision",
        action="store_true",
        help="enable utility-linked positive query_skill targets",
    )
    args = parser.parse_args()
    audit = run_phase4_sft_dry_run(
        run_root=args.run_root,
        labels_path=args.labels_path,
        output_root=args.output_root,
        report_path=args.report_path,
        policy=skill_supervision_policy() if args.skill_supervision else None,
    )
    status = "PASS" if audit["gate2_validation_experiment_passed"] else "FAIL"
    print(
        f"phase4 dry run {status}: targets={audit['target_record_count']} "
        f"context_only={audit['context_only_record_count']}"
    )


if __name__ == "__main__":
    main()
