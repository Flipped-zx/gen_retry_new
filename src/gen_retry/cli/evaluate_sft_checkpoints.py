from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.sft_checkpoint_eval import (
    LlamaFactoryActionGenerator,
    build_sample_manifest,
    compare_checkpoint_summaries,
    evaluate_action_outputs,
    generate_outputs,
    load_frozen_validation_samples,
    render_comparison_markdown,
    select_stratified_samples,
    write_checkpoint_evaluation,
)
from gen_retry.runtime.json_canonical import canonical_json


def _checkpoint(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("checkpoint must use LABEL=/absolute/path")
    label, raw_path = value.split("=", 1)
    if not label or not raw_path:
        raise argparse.ArgumentTypeError("checkpoint must use LABEL=/absolute/path")
    return label, Path(raw_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate full Qwen3-VL SFT checkpoints on one fixed frozen "
            "validation sample without executing image actions."
        )
    )
    parser.add_argument("--validation-jsonl", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument(
        "--checkpoint",
        type=_checkpoint,
        action="append",
        required=True,
        help="Repeat as LABEL=/absolute/checkpoint/path; order defines baseline/final.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--samples-per-action", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--template", default="qwen3_vl_nothink")
    parser.add_argument("--flash-attn", default="fa2")
    parser.add_argument("--image-max-pixels", type=int, default=262144)
    args = parser.parse_args()

    checkpoints = args.checkpoint
    labels = [label for label, _ in checkpoints]
    if len(checkpoints) < 2:
        parser.error("provide at least two --checkpoint values for comparison")
    if len(set(labels)) != len(labels):
        parser.error("checkpoint labels must be unique")
    if args.output_root.exists():
        parser.error(f"output root already exists: {args.output_root}")

    all_samples, source = load_frozen_validation_samples(
        args.validation_jsonl,
        provenance_path=args.provenance,
    )
    samples = select_stratified_samples(
        all_samples,
        samples_per_action=args.samples_per_action,
        seed=args.seed,
    )
    args.output_root.mkdir(parents=True)
    sample_manifest = build_sample_manifest(
        samples,
        source=source,
        samples_per_action=args.samples_per_action,
        seed=args.seed,
    )
    (args.output_root / "sample_manifest.json").write_text(
        canonical_json(sample_manifest) + "\n", encoding="utf-8"
    )

    summaries = []
    for label, checkpoint_path in checkpoints:
        print(f"loading checkpoint {label}: {checkpoint_path}", flush=True)
        generator = LlamaFactoryActionGenerator(
            checkpoint_path,
            max_new_tokens=args.max_new_tokens,
            template=args.template,
            flash_attn=args.flash_attn,
            image_max_pixels=args.image_max_pixels,
        )
        try:
            outputs = generate_outputs(
                samples,
                generator,
                progress=lambda index, total, sample_id: print(
                    f"{label}: {index}/{total} {sample_id}", flush=True
                ),
            )
        finally:
            generator.close()
        predictions, summary = evaluate_action_outputs(
            samples,
            outputs,
            checkpoint_label=label,
            checkpoint_path=checkpoint_path,
        )
        write_checkpoint_evaluation(
            output_dir=args.output_root / label,
            predictions=predictions,
            summary=summary,
        )
        summaries.append(summary)

    comparison = compare_checkpoint_summaries(summaries)
    (args.output_root / "comparison.json").write_text(
        canonical_json(comparison) + "\n", encoding="utf-8"
    )
    (args.output_root / "comparison.md").write_text(
        render_comparison_markdown(comparison), encoding="utf-8"
    )
    print(
        "SFT checkpoint action evaluation PASS: "
        f"samples={len(samples)} checkpoints={','.join(labels)} "
        f"report={args.output_root / 'comparison.md'}"
    )


if __name__ == "__main__":
    main()
