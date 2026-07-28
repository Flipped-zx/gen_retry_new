from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_retry.phase5.flow_dppo_selection import (
    FLOW_DPPO_COMMIT,
    select_flow_dppo_prompts,
    selection_report,
)
from gen_retry.runtime.json_canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select a deterministic hard-heavy prompt set from Flow-DPPO Geneval2 data."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--heldout-dataset",
        type=Path,
        required=True,
        help="Official 800-row Geneval2 test JSONL used only for leakage exclusion.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/phase5/flow_dppo_selected_20_prompts.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/phase5/flow_dppo_selected_20_report.md"),
    )
    parser.add_argument("--source-commit", default=FLOW_DPPO_COMMIT)
    parser.add_argument("--hard", type=int, default=12)
    parser.add_argument("--medium", type=int, default=5)
    parser.add_argument("--easy", type=int, default=3)
    args = parser.parse_args()

    payload = select_flow_dppo_prompts(
        args.dataset,
        heldout_dataset_path=args.heldout_dataset,
        tier_counts={
            "hard": args.hard,
            "medium": args.medium,
            "easy": args.easy,
        },
        source_commit=args.source_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(selection_report(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "selected_count": payload["selected_count"],
                "tier_counts": payload["tier_counts"],
                "output": str(args.output),
                "report": str(args.report),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
