# Phase 7 Flow-DPPO 200 Fresh 8-HCU Run

## Frozen Inputs

- Selection:
  `artifacts/phase7/flow_dppo200_official_mix_selected_prompts.json`
- Selection SHA256:
  `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`
- New run root: `runs/phase7_flow_dppo200_fresh8_v1`
- Preparation summary:
  `artifacts/phase7/flow_dppo200_fresh8_v1_prepared_rollouts.json`
- Planner: GPT-5.5, Action Protocol v0.5, PlannerContext v0.6
- Execution profile: `qwen_dual_backend@1`
- Generate backend: local Qwen-Image-2512, 50 steps, 1024 x 1024
- Edit backend: local Qwen-Image-Edit-2511, 40 steps, 1024 x 1024
- Evaluator: local Geneval2 after every image Attempt
- Budget: at most five image Attempts per episode

All 200 episode directories were prepared from empty event state. No image,
Attempt, evaluator result, or submission was imported from an earlier run.
The interrupted root
`runs/phase7_flow_dppo200_official_mix_v07_score_v06` remains untouched as an
archive and is not part of this batch.

## Parallel Schedule

Eight fixed workers run independent episodes, one HCU per worker. Attempts
inside one episode remain sequential because the next PlannerContext depends
on the preceding image and Geneval2 result. The existing model-load lock
serializes only transient pipeline loading; inference can overlap across HCUs.

Range 1-20 uses one logical episode worker per HCU. Beginning at the complete
21-40 boundary, the Sol-approved overlap profile uses two logical episode
workers per HCU and eight cross-process Teacher slots. A physical-HCU lock
allows only one complete Qwen/Geneval2 load-through-unload stage on each card.
This overlaps Teacher planning and local Skill work with another episode's GPU
stage without prefetching across an unevaluated Attempt.

The overlap safety contract includes:

- fixed lock order `physical_device_lock -> global_model_load_lock`;
- one active scheduler per run root and one active executor per episode;
- atomic image save plus decode, dimension, and hash validation before reuse;
- explicit GPU synchronization and cache release before the HCU lock releases;
- scheduler provenance in `scheduler_profiles.jsonl`;
- Teacher concurrency initially capped at eight, prospectively reduced to six
  only if the next checkpoint still shows material timeouts.

Design review:
`docs/reviews/phase7_api_gpu_overlap_sol_review.md`
(`APPROVE_WITH_REQUIRED_CHANGES`, required changes implemented).

The launch ranges are:

- 1-20, 21-40
- 41-50, 51-60
- 61-80
- 81-100
- repeat the same 20-light / 50-deep cadence through 200

Splitting at 50 keeps the deep-review evidence deterministic without requiring
a partially completed 20-episode window.

## Review Cadence

Every 20 completed episodes receives a light checkpoint audit. It checks:

- schema, manifest, lineage, and no-future-leakage invariants;
- submitted Attempt equals reducer best;
- Teacher, PlannerContext, score-policy, and backend version consistency;
- first-to-submitted atom, AM, and GM changes;
- submitted-to-peak GM gap;
- format errors, regressions, rollback/historical-best behavior, and action mix.

Every 50 completed episodes receives a GPT-5.6 Sol deep review. Sol receives
the deterministic checkpoint audit plus a small representative trace set and
answers at most three questions:

1. Is there a protocol, memory, SFT-boundary, or future-leakage blocker?
2. Do outcomes indicate a wrong direction or a major policy, generator, or
   evaluator risk?
3. Should generation continue, continue with a prospective correction, or
   stop?

The next range starts before the review finishes so GPU generation and review
overlap. A blocking Sol verdict stops assignment of further ranges; completed
immutable trajectories are retained rather than rewritten.

## Resume

- Every range has its own tmux session, orchestrator log, and exit-status file.
- Submitted episodes are skipped on an exact-range resume.
- Immutable events, completed images, and evaluator artifacts remain
  authoritative.
- A failed or interrupted range is resumed with the same run root and episode
  IDs; no valid episode is rerun.

## Active Range

- Range: `phase3_ep_001` through `phase3_ep_020`
- tmux session: `gen_retry_fresh8_001_020`
- Workers: 8
- Started: 2026-07-30
- Resume policy: up to five exact-range scheduler retries; completed
  submissions are skipped and incomplete event suffixes resume.
