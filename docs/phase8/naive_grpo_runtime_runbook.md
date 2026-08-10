# Naive Geneval2 GRPO Runtime Runbook

## Frozen Baseline

- Policy: `flow1000_v9_selective_skill_full_s42`
- Method: terminal-only `naive_geneval2_grpo@0.1`
- Reward: `passed_atom_count + 0.25 * Geneval2_GM`
- Rollouts per exact prompt: 4
- Image-attempt budget: 5
- Sampling: temperature 0.7, top-p 0.95, top-k -1
- Token limits: 1,400 per assistant Action; 16,000 cumulative assistant-action
  tokens per complete episode
- Optimizer: LR `1e-6`, one PPO epoch, one train epoch, BF16 FSDP 8
- PPO clip: low 0.20, high 0.28
- Active reference KL: 0.02
- Trainable tokens: canonical assistant actions only

The existing 1,000 GPT-5.5 Teacher trajectories are replay/calibration data,
not GRPO samples. Live policy updates use only fresh on-policy candidates from
the frozen Phase 8 train manifest.

## Eight-Device Topology

Rollout stage:

```text
2 devices  Qwen3-VL policy rollout, SGLang TP=2
2 devices  Qwen-Image-2512 replicas for generate_image
2 devices  Qwen-Image-Edit-2511 replicas for edit_image
2 devices  Geneval2 replicas
```

The environment owns routing. `generate_image` never carries a source and
routes only to Qwen-Image-2512. `edit_image` requires a historical source and
routes only to Qwen-Image-Edit-2511. If measured edit share exceeds 0.60, one
generate replica may be rebalanced to edit at a declared stage boundary.

After artifact-backed rollouts close, stop and release all rollout services.
The optimizer stage then uses all eight devices for actor FSDP. Do not attempt
to keep the local image/evaluator services resident while claiming FSDP 8.

## W&B

The committed default is offline:

```bash
GEN_RETRY_WANDB_MODE=offline \
python -m gen_retry.cli.rl_preflight --strict --target smoke
```

After the 32-group smoke passes, online tracking is enabled without editing
the frozen YAML:

```bash
export GEN_RETRY_WANDB_MODE=online
export WANDB_API_KEY='<environment-only>'
export WANDB_ENTITY='Gen_retry'
python -m gen_retry.cli.rl_preflight --strict --target smoke
```

Never place a key in YAML, a launcher argument, an event, or a report. Model
weight upload remains disabled. Log config/artifact hashes, reward mean/std,
valid and zero-variance group fractions, effective candidates, KL, clip
fraction, entropy, invalid actions, action distribution, image calls, backend
queue utilization, resume counts, and HCU time.

## Admission Ladder

| Stage | Prompt groups | Full trajectories | Expected image calls | Decision |
| --- | ---: | ---: | ---: | --- |
| Smoke | 32 | 128 | about 441 | runtime/resume only |
| Mechanism | 128 | 512 | about 1,763 | optimizer signal |
| Minimum curve | 250 | 1,000 | about 3,443 | exploratory learning curve |
| First efficacy | 500 | 2,000 | about 6,886 | recommended first result |
| Conditional | 1,000 | 4,000 | about 13,772 | only after declared review |

The call estimates use the observed 3.443 image calls per completed Teacher
trajectory. They are budgeting proxies; Student behavior may use a different
number of attempts.

With four concurrent image replicas, the planning range is roughly 7-16 hours
for the 32-group smoke, 28-64 hours for 128 groups, and 5-10 days for 500
groups. The range combines the earlier eight-device batch throughput proxy and
the slower recent single-HCU five-attempt observation. Measure the smoke's
per-backend service time and replace these estimates before approving 128 or
500. Optimizer time should be reported separately; image execution is expected
to dominate.

Start with four rollouts. Increase to six only when the admitted 32/128 evidence
shows more than 35% zero-variance prompt groups. Compare arms at equal image
calls, not merely equal prompt counts.

Stage admission is fail-closed: valid groups must be at least 95%,
policy-invalid candidates at most 5%, and zero-variance groups at most 35%.
Infrastructure failures are retried under the same semantic request ID and,
if exhausted, are listed as excluded groups with a failure artifact. They are
never silently dropped or converted to zero reward.

## Launch Gate

```bash
source /opt/dtk-26.04/env.sh
PYTHONPATH=src python -m gen_retry.cli.rl_preflight --strict
```

The launch gate requires real W&B/rLLM/verl/SGLang packages in an isolated,
vendor-compatible environment, eight visible HCUs, valid model/evaluator
paths, the checkpoint fingerprint, and all frozen data hashes. Do not install
generic PyPI Torch over the vendor build.

The command has two explicit targets:

```bash
# Dependencies + 8 HCUs + custom adapter evidence; permits only collection.
PYTHONPATH=src python -m gen_retry.cli.rl_preflight --strict --target smoke

# Additionally requires the passing hash-bound 32-group report.
PYTHONPATH=src python -m gen_retry.cli.rl_preflight --strict --target optimization
```

`CONTROL_PLANE_READY` is not permission to collect images.
`READY_FOR_SMOKE` permits only the 32-group artifact-backed smoke.
`READY_FOR_OPTIMIZATION` is the first state that permits an optimizer update.
Adapter and smoke checks are typed test-report artifacts, not booleans. Every
ref is repository-root-contained. The optimization gate reloads the referenced
rollout and advantage batches, reruns admission and optimizer preparation, and
requires all report counts to equal the recomputed result.

Stock Gen-Searcher rLLM is not an executable Gen-Retry trainer: its image call
is terminal-only, its parser is XML-oriented, its released KL is inactive, and
it recomputes log-probs. The custom workflow must preserve Qwen3-VL image
tokens/grids and feed only `prepare_optimizer_batch` output into verl. A
32-group artifact-backed resume/replay smoke is mandatory before any policy
checkpoint is promoted.

The frozen fresh pool is intentionally hard-skewed. Train has 10 easy / 542
medium / 448 hard prompts; development has only 2 easy prompts and
confirmation only 5. A 500-group result therefore estimates performance on
this hard-skewed retry pool, not broad easy-case retention or the official
Geneval2 distribution. Keep the official 800 untouched.
