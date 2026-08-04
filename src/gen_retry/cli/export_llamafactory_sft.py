from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.sft.llamafactory import export_llamafactory_dataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export audited Gen-Retry targets for LLaMA-Factory."
    )
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path)
    parser.add_argument("--supervision-policy", type=Path)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--source-audit", type=Path)
    parser.add_argument(
        "--release-status",
        choices=["provisional", "frozen"],
        default="provisional",
    )
    parser.add_argument("--gate-approval-ref", type=Path)
    parser.add_argument("--dataset-prefix", default="gen_retry_sft")
    args = parser.parse_args()
    result = export_llamafactory_dataset(
        records_path=args.records,
        run_root=args.run_root,
        output_dir=args.output_dir,
        split_manifest_path=args.split_manifest,
        supervision_policy_path=args.supervision_policy,
        decisions_path=args.decisions,
        source_audit_path=args.source_audit,
        release_status=args.release_status,
        gate_approval_ref=args.gate_approval_ref,
        dataset_prefix=args.dataset_prefix,
    )
    print(
        "LLaMA-Factory export PASS: "
        f"records={result['record_count']} "
        f"images={result['image_binding_count']} "
        f"release_status={result['release_status']}"
    )


if __name__ == "__main__":
    main()
