# Original GenEval Metadata-Aware SFT Agent Evaluation

## Scope

Protocol ID: `original_geneval_metadata_aware_agent@1`.

The frozen SFT Planner sees a deterministic rubric derived from original
GenEval metadata before its first action. This is a metadata-aware Agent test,
not the standard prompt-only GenEval generation protocol. The online
Geneval2-compatible VQA result is selection feedback only. The formal result is
computed after submission by the unmodified original GenEval detector.

## Inputs

- Original GenEval metadata:
  `geneval/prompts/evaluation_metadata.jsonl` (exactly 553 rows).
- Upstream checkout: `https://github.com/djghosh13/geneval.git` at
  `af4902f24d3ca90ebbb446dd9891a59e0f82725f`.
- Frozen SFT checkpoint.
- `Qwen-Image-2512`, `Qwen-Image-Edit-2511`, and the configured online VQA model.

## Prepare

```bash
export PYTHONPATH=src

python -m gen_retry.cli.prepare_official_geneval_rollouts \
  --benchmark-data /absolute/path/to/geneval/prompts/evaluation_metadata.jsonl \
  --output-root runs/original_geneval_metadata_aware_agent_v1 \
  --summary-output artifacts/original_geneval_metadata_aware_agent_v1_prepared.json \
  --max-image-attempts 5
```

Preparation fails unless the complete 553-row benchmark and all six official
tags validate. `--limit` is available only for smoke runs; the full file is
still validated before selection.

## Run The SFT Planner And Dual Backend

```bash
python -m gen_retry.cli.serve_sft_planner \
  --checkpoint /absolute/path/to/sft-checkpoint \
  --host 127.0.0.1 \
  --port 8765

python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root runs/original_geneval_metadata_aware_agent_v1 \
  --planner-provider sft \
  --sft-planner-url http://127.0.0.1:8765 \
  --sft-checkpoint /absolute/path/to/sft-checkpoint \
  --execution-profile-id qwen_dual_backend \
  --generate-image-steps 50 \
  --edit-image-steps 40 \
  --image-height 1024 \
  --image-width 1024 \
  --workers-per-device 1 \
  --device-id 1
```

Use `--dry-run` first. The existing score policy is explicitly an online VQA
proxy. It is not an original GenEval or official GenEval2 result.

## Export Canonical Submissions

```bash
python -m gen_retry.cli.export_official_geneval_submission \
  --preparation-summary artifacts/original_geneval_metadata_aware_agent_v1_prepared.json \
  --benchmark-data /absolute/path/to/geneval/prompts/evaluation_metadata.jsonl \
  --output-root artifacts/original_geneval_metadata_aware_agent_v1_submission \
  --audit-output artifacts/original_geneval_metadata_aware_agent_v1_export_audit.json
```

Formal export requires 553/553 canonical submissions. It exports only the
reducer-submitted Attempt, verifies its manifest digest, and writes the
semantically unchanged source metadata beside one PNG. `--allow-partial` is for
smoke/debug only and must not be scored as a formal result.

## Run The Pristine Detector

From the read-only original GenEval checkout/environment:

```bash
python evaluation/evaluate_images.py \
  /absolute/path/to/artifacts/original_geneval_metadata_aware_agent_v1_submission \
  --outfile /absolute/path/to/artifacts/original_geneval_metadata_aware_agent_v1_results.jsonl \
  --model-path /absolute/path/to/geneval/model/mask2former2

python evaluation/summary_scores.py \
  /absolute/path/to/artifacts/original_geneval_metadata_aware_agent_v1_results.jsonl
```

Report the task-macro detector score as one submitted image per prompt. Do not
interpret `% correct prompts` as upstream best-of-four; with one image it is
identical to image correctness.

## Required Report Fields

Record checkpoint digest, execution profile, max attempts, actual generate/edit
and total image-call counts, online VQA model/thresholds, proxy score policy,
one-image submission policy, GenEval commit, detector options, 553/553 coverage,
and export audit digest. Keep proxy and detector metrics in separate sections.
