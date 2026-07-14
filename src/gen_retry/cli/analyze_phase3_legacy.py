from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.config import configured_path
from gen_retry.phase3.legacy_analysis import (
    build_legacy_analysis_records,
    write_legacy_analysis_artifacts,
)


def analyze_phase3_legacy(
    *,
    trajectory_path: Path | None = None,
    output_jsonl: Path = Path("artifacts/phase3/legacy_diagnostic_action_analysis.jsonl"),
    plausibility_report: Path = Path("docs/phase3/legacy_edit_plausibility_analysis.md"),
    signature_report: Path = Path("docs/phase3/legacy_failure_signature_summary.md"),
) -> list[dict]:
    if trajectory_path is None:
        trajectory_path = (
            configured_path("legacy_gen_retry_root")
            / "data"
            / "trajectories"
            / "geneval2_balanced100x5_normal_round0_4_master_trajectories.jsonl"
        )
    records = build_legacy_analysis_records(trajectory_path)
    write_legacy_analysis_artifacts(
        records=records,
        jsonl_path=output_jsonl,
        plausibility_report_path=plausibility_report,
        signature_report_path=signature_report,
    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 3 legacy counterfactual analysis.")
    parser.add_argument("--trajectory-path", type=Path)
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("artifacts/phase3/legacy_diagnostic_action_analysis.jsonl"),
    )
    parser.add_argument(
        "--plausibility-report",
        type=Path,
        default=Path("docs/phase3/legacy_edit_plausibility_analysis.md"),
    )
    parser.add_argument(
        "--signature-report",
        type=Path,
        default=Path("docs/phase3/legacy_failure_signature_summary.md"),
    )
    args = parser.parse_args()
    records = analyze_phase3_legacy(
        trajectory_path=args.trajectory_path,
        output_jsonl=args.output_jsonl,
        plausibility_report=args.plausibility_report,
        signature_report=args.signature_report,
    )
    print(f"wrote {len(records)} legacy analysis records")


if __name__ == "__main__":
    main()
