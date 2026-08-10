from __future__ import annotations

import argparse
import json
from pathlib import Path

from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.data import (
    build_naive_grpo_experiment_declaration,
    build_naive_grpo_prompt_manifests,
)
from gen_retry.runtime.json_canonical import canonical_json


DEFAULT_EXCLUSIONS = (
    Path("artifacts/phase5/flow_dppo_selected_20_prompts.json"),
    Path("artifacts/phase7/flow_dppo200_official_mix_selected_prompts.json"),
    Path("artifacts/phase7/flow_dppo1000_v9_official_mix_selected_prompts.json"),
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze fresh, official-held-out, cross-split-family-disjoint "
            "Flow-DPPO prompt manifests for naive GRPO."
        )
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--heldout-dataset", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/rl/naive_geneval2_grpo_v0_1.yaml"),
    )
    parser.add_argument(
        "--exclude-selection",
        type=Path,
        action="append",
        default=None,
    )
    parser.add_argument("--train-count", type=int, default=1000)
    parser.add_argument("--development-count", type=int, default=200)
    parser.add_argument("--confirmation-count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    config = load_experiment_config(args.config)
    manifests = build_naive_grpo_prompt_manifests(
        dataset_path=args.dataset,
        heldout_dataset_path=args.heldout_dataset,
        excluded_selection_paths=list(
            DEFAULT_EXCLUSIONS
            if args.exclude_selection is None
            else args.exclude_selection
        ),
        split_counts={
            "train": args.train_count,
            "development": args.development_count,
            "confirmation": args.confirmation_count,
        },
        seed=args.seed,
    )
    paths = {
        "train": config.admission.train_manifest,
        "development": config.admission.development_manifest,
        "confirmation": config.admission.confirmation_manifest,
    }
    for split, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(manifests[split]) + "\n", encoding="utf-8")
    declaration = build_naive_grpo_experiment_declaration(
        config=config,
        config_path=args.config,
        manifest_paths=paths,
    )
    config.admission.experiment_declaration.write_text(
        canonical_json(declaration) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "split_counts": {
                    split: manifest["selected_count"]
                    for split, manifest in manifests.items()
                },
                "experiment_declaration": str(
                    config.admission.experiment_declaration
                ),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
