# Frozen-Test-20 Qwen Raw-Prompt Baseline

## Scope

- Cohort: the exact 20 TaskSpecs in `runs/phase7_sft_frozen_test20_v2`.
- Prompt input: exact `task_spec.original_prompt`, without SFT/Teacher rewriting.
- Generate backend: existing `qwen_dual_backend@1` Qwen-Image route.
- Render: 50 steps, 1024 x 1024, seeds 0 through 4.
- Evaluator: existing local Geneval2 adapter and thresholds.
- Single-image arm: variant 0, seed 0.
- Best-of-5 arms: highest GM and pass-count-first selectors are both reported.
- Fresh root: `runs/phase7_sft_frozen_test20_qwen_raw_b5_v1`.
- Frozen plan: `artifacts/phase7/sft_frozen_test20_qwen_raw_b5_v1_plan.json`.

Preparation copied TaskSpecs only. It imported no SFT actions, events, images, or
Geneval2 results. At freeze time the root contained 100 TaskSpec copies and no
image, Geneval2, or result artifacts.

## Launch

```bash
GEN_RETRY_MODEL_LOAD_CONCURRENCY=4 \
python -m gen_retry.cli.run_qwen_raw_prompt_baseline_parallel \
  --run-root runs/phase7_sft_frozen_test20_qwen_raw_b5_v1 \
  --device-id 0 --device-id 1 --device-id 2 --device-id 3 \
  --device-id 4 --device-id 5 --device-id 6 --device-id 7
```

The scheduler skips completed `result.json` files. Interrupted image or
Geneval2 artifacts remain resumable within this new root through the existing
adapter cache; no artifact outside the root is used.

## Report

```bash
python -m gen_retry.cli.analyze_qwen_raw_prompt_baseline \
  --run-root runs/phase7_sft_frozen_test20_qwen_raw_b5_v1 \
  --artifact artifacts/phase7/sft_frozen_test20_qwen_raw_b5_v1_report.json \
  --report docs/phase7/sft_frozen_test20_qwen_raw_b5_v1_report.md
```

The analyzer requires all 100 results and reports exact-prompt single-image,
highest-GM Best-of-5, and pass-count-first Best-of-5 metrics.
