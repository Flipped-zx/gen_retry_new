from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.sft.llamafactory import (
    prepare_llamafactory_training,
    run_llamafactory_training,
)


def _csv_tags(value: str) -> list[str]:
    tags = [item.strip() for item in value.split(",") if item.strip()]
    if any("," in item for item in tags):
        raise argparse.ArgumentTypeError("W&B tags must be comma-separated values")
    return tags


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a frozen Gen-Retry dataset for LLaMA-Factory and optionally "
            "launch training."
        )
    )
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument(
        "--base-config",
        type=Path,
        default=Path("configs/sft/llamafactory/qwen3_vl_8b_lora_sft.yaml"),
    )
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument(
        "--allow-provisional",
        action="store_true",
        help=(
            "Allow an explicit smoke test before Gate 3; never use for final training."
        ),
    )
    parser.add_argument("--smoke-max-samples", type=int, default=8)
    parser.add_argument("--smoke-max-steps", type=int, default=2)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--token-audit-report", type=Path)
    parser.add_argument("--llamafactory-cli", default="llamafactory-cli")
    parser.add_argument(
        "--wandb-mode",
        choices=("auto", "online", "offline", "disabled"),
        default="auto",
        help=(
            "W&B mode. auto uses online when WANDB_API_KEY or a user-level "
            "wandb login is present and otherwise writes an offline run."
        ),
    )
    parser.add_argument("--wandb-entity", default="Gen_retry")
    parser.add_argument("--wandb-project", default="gen-retry-sft")
    parser.add_argument("--wandb-group", default="v9-cold-start")
    parser.add_argument(
        "--wandb-run-name",
        help="Override the run name in the base YAML; defaults to its run_name.",
    )
    parser.add_argument(
        "--wandb-tags",
        type=_csv_tags,
        default=["sft", "cold-start"],
        help="Comma-separated W&B tags.",
    )
    parser.add_argument("--wandb-dir", type=Path)
    args = parser.parse_args()
    if args.execute and args.allow_provisional:
        parser.error("--execute cannot be combined with --allow-provisional")
    if args.execute and args.token_audit_report is None:
        parser.error("--execute requires --token-audit-report")
    result = prepare_llamafactory_training(
        dataset_dir=args.dataset_dir,
        base_config_path=args.base_config,
        model_name_or_path=args.model_name_or_path,
        output_dir=args.output_dir,
        runtime_config_path=args.runtime_config,
        allow_provisional=args.allow_provisional,
        smoke_max_samples=args.smoke_max_samples,
        smoke_max_steps=args.smoke_max_steps,
        wandb_mode=args.wandb_mode,
        wandb_run_name=args.wandb_run_name,
    )
    print(
        "LLaMA-Factory training preflight READY: "
        f"release_status={result['dataset_release_status']} "
        f"config={result['runtime_config_path']}"
    )
    if args.execute:
        run_llamafactory_training(
            runtime_config_path=args.runtime_config,
            dataset_dir=args.dataset_dir,
            token_audit_report_path=args.token_audit_report,
            cli_path=args.llamafactory_cli,
            wandb_mode=args.wandb_mode,
            wandb_entity=args.wandb_entity,
            wandb_project=args.wandb_project,
            wandb_group=args.wandb_group,
            wandb_tags=args.wandb_tags,
            wandb_dir=args.wandb_dir,
        )


if __name__ == "__main__":
    main()
