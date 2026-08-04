# SFT Checkpoint Action Evaluation

The checkpoint evaluator compares full-SFT checkpoints on the same small,
deterministic subset of the frozen validation split. It performs planner
inference only: it does not execute `generate_image` / `edit_image`, call
Geneval2, or mutate trajectory memory.

The default sample contains four records per gold action (16 total). Selection
is SHA-256 ranked by `seed + sample_id`, so checkpoint-100 and the final model
receive identical examples. The evaluator removes the gold assistant message
before inference and uses LLaMA-Factory's own `qwen3_vl_nothink` multimodal
chat path with greedy decoding.

Run after training has finished and both full checkpoints are complete:

```bash
source /opt/dtk-26.04/env.sh
source runs/sft_runtime_v2/venv/bin/activate
export PYTHONPATH=src
export HIP_VISIBLE_DEVICES=0
export CUDA_VISIBLE_DEVICES=0

python -m gen_retry.cli.evaluate_sft_checkpoints \
  --validation-jsonl artifacts/sft/flow_dppo1000_v9_selective_skill_frozen/validation.jsonl \
  --checkpoint checkpoint-100=runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42/checkpoint-100 \
  --checkpoint final=runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42 \
  --output-root artifacts/sft/checkpoint_eval/flow1000_v9_full_s42
```

The command serially loads and releases checkpoints on one visible HCU. It
writes the frozen sample manifest, raw predictions with per-row scores, one
summary per checkpoint, and `comparison.json` / `comparison.md`.

Reported metrics are strict v0.5 schema validity, invalid rate, valid action
distribution, `query_skill` rate, action-type and exact-action accuracy,
target-constraint Jaccard/recall, preserve-constraint Jaccard, and historical
attempt-reference accuracy. These are action-imitation diagnostics, not an
end-to-end image quality claim.
