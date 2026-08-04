from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.sft.llamafactory import audit_llamafactory_tokenization


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit labels emitted by LLaMA-Factory's real SFT tokenizer."
    )
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--max-samples", type=int)
    parser.add_argument(
        "--disable-version-check",
        action="store_true",
        help="Use only for a vendor-patched cluster stack after compatibility checks.",
    )
    args = parser.parse_args()
    result = audit_llamafactory_tokenization(
        runtime_config_path=args.runtime_config,
        report_path=args.report,
        max_samples=args.max_samples,
        disable_version_check=args.disable_version_check,
    )
    print(
        "LLaMA-Factory token-mask audit PASS: "
        f"samples={sum(result['split_counts'].values())} "
        f"complete={result['complete']}"
    )


if __name__ == "__main__":
    main()
