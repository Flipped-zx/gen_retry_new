from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_retry.rl.admission import admit_rollout_sample_batch
from gen_retry.rl.config import load_experiment_config
from gen_retry.runtime.json_canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate materialized on-policy rollout provenance and build a "
            "terminal-only candidate-return batch."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/rl/naive_geneval2_grpo_v0_1.yaml"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    admission = admit_rollout_sample_batch(
        payload,
        artifact_root=args.artifact_root,
        config=load_experiment_config(args.config),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        canonical_json(admission.candidate_return_batch) + "\n",
        encoding="utf-8",
    )
    print(
        f"admitted {admission.group_count} groups / "
        f"{admission.candidate_count} candidates to {args.output}"
    )


if __name__ == "__main__":
    main()
