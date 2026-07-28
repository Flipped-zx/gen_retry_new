# Phase 3 HQ5 Parallel Rollout Plan

Date: 2026-07-15

## Objective

Collect five additional fresh-start live trajectories with production-quality Qwen-Image-Edit rendering:

- no standalone image smoke by default;
- no legacy image reuse;
- GPT-5.5 teacher policy;
- local Qwen-Image-Edit-2511 direct runtime;
- Geneval2 evaluation after every image attempt;
- `max_image_attempts=5`;
- `num_inference_steps=40`;
- `height=1024`, `width=1024`.

## Resource Policy

Current live resource check with `hy-smi` sees one HCU device with `VRAM=0%` and `HCU=0%`. The compact `hy-smi` table does not expose total VRAM, so the safe default is one local Qwen image worker per visible GPU.

The runner therefore uses episode-level parallelism only when resources allow:

- one worker per eligible GPU by default;
- no more than one local Qwen worker per GPU unless explicitly overridden;
- refuse to start when teacher environment is missing;
- refuse to start when no GPU is visible unless `--allow-cpu` is explicitly passed;
- refuse low-quality rollout params unless explicitly marked diagnostic with `--allow-low-quality`.

Within an episode, actions remain sequential to preserve canonical history. Across episodes, the scheduler can run in parallel on independent devices.

## Commands

Prepare five fresh directories from the already-selected prompts:

```bash
python -m gen_retry.cli.prepare_phase3_rollouts \
  --selected-prompts artifacts/phase3/selected_ten_prompts.json \
  --output-root runs/phase3_hq5 \
  --summary-output artifacts/phase3_hq5/prepared_rollouts.json \
  --limit 5 \
  --max-image-attempts 5 \
  --created-at 2026-07-15T00:00:00Z
```

Run the high-quality five-trajectory batch:

```bash
python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root runs/phase3_hq5 \
  --image-steps 40 \
  --image-height 1024 \
  --image-width 1024
```

The command inherits `TEACHER_API_KEY` and `TEACHER_BASE_URL` from the environment and reports only `SET` or `MISSING`.

## Outputs

- Episode directories: `runs/phase3_hq5/phase3_ep_001` through `runs/phase3_hq5/phase3_ep_005`
- Preparation summary: `artifacts/phase3_hq5/prepared_rollouts.json`
- Per-episode runner logs: `runs/phase3_hq5/parallel_logs/*.log`
- Canonical records inside each episode:
  - `planner_requests.jsonl`
  - `raw_teacher_outputs.jsonl`
  - `canonical_actions.jsonl`
  - `tool_observations.jsonl`
  - `geneval2_results.jsonl`
  - `events.jsonl`
  - `episode_state.json`
  - `submission.json`
