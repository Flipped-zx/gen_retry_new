from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_retry.rl.preflight import run_rl_preflight
from gen_retry.runtime.json_canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the naive Geneval2 GRPO config and runtime."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/rl/naive_geneval2_grpo_v0_1.yaml"),
    )
    parser.add_argument(
        "--model-config",
        type=Path,
        default=Path("configs/models/local.yaml"),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--skip-accelerator",
        action="store_true",
        help="Skip the Torch/device probe for a CPU-only control-plane check.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when the requested readiness target is not met.",
    )
    parser.add_argument(
        "--target",
        choices=("smoke", "optimization"),
        default="smoke",
        help="Readiness gate checked by --strict (default: smoke).",
    )
    args = parser.parse_args()
    report = run_rl_preflight(
        config_path=args.config,
        model_config_path=args.model_config,
        check_accelerator=not args.skip_accelerator,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical_json(report) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.strict:
        readiness_key = f"ready_for_{args.target}"
        if not report[readiness_key]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
