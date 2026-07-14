from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.candidate_pool import (
    build_candidate_pool,
    write_candidate_pool_artifacts,
)
from gen_retry.phase3.config import configured_path


def build_phase3_candidate_pool(
    *,
    geneval2_data_path: Path | None = None,
    legacy_analysis_path: Path | None = Path("artifacts/phase3/legacy_diagnostic_action_analysis.jsonl"),
    output_jsonl: Path = Path("artifacts/phase3/candidate_pool.jsonl"),
    report_path: Path = Path("docs/phase3/candidate_pool_report.md"),
) -> list[dict]:
    if geneval2_data_path is None:
        geneval2_data_path = configured_path("geneval2_root") / "geneval2_data.jsonl"
    candidates = build_candidate_pool(
        geneval2_data_path=geneval2_data_path,
        legacy_analysis_path=legacy_analysis_path,
    )
    write_candidate_pool_artifacts(
        candidates=candidates,
        jsonl_path=output_jsonl,
        report_path=report_path,
    )
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 3 Geneval2 candidate pool.")
    parser.add_argument("--geneval2-data-path", type=Path)
    parser.add_argument(
        "--legacy-analysis-path",
        type=Path,
        default=Path("artifacts/phase3/legacy_diagnostic_action_analysis.jsonl"),
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("artifacts/phase3/candidate_pool.jsonl"),
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("docs/phase3/candidate_pool_report.md"),
    )
    args = parser.parse_args()
    candidates = build_phase3_candidate_pool(
        geneval2_data_path=args.geneval2_data_path,
        legacy_analysis_path=args.legacy_analysis_path,
        output_jsonl=args.output_jsonl,
        report_path=args.report_path,
    )
    print(f"wrote {len(candidates)} candidate records")


if __name__ == "__main__":
    main()
