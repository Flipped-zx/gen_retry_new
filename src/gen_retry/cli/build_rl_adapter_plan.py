from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.verl_adapter import build_verl_adapter_plan
from gen_retry.runtime.json_canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the audited rLLM/verl parameter and integration plan."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/rl/naive_geneval2_grpo_v0_1.yaml"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    plan = build_verl_adapter_plan(load_experiment_config(args.config)).to_dict()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(canonical_json(plan) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
