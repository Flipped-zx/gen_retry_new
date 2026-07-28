# SOL_REVIEW_REQUEST

## Gate

`Phase 5 Dataset Build / concurrency and data-source design`

## Decision to review

Approve the hard-heavy Flow-DPPO 20-prompt selection policy and the minimum
two-GPU scheduler/resume changes required before launching 20 native v0.5
trajectories.

## Current evidence

- Canonical protocol:
  - `schemas/action_protocol_v0_5.schema.json`
  - `schemas/planner_context_v0_5.schema.json`
  - `docs/decisions/ADR-0005-sft-supervision-freeze.md`
- Flow-DPPO / UniRL source:
  - repository: `https://github.com/Tencent-Hunyuan/UniRL`
  - commit: `e1a814ff9de6de644b093c6ed0106869c1881e53`
  - license: Apache-2.0
  - train path: `datasets/geneval2/synthetic/train.jsonl`
  - 20,000 rows with `prompt`, `atom_count`, `vqa_list`, `skills`
  - atom-count bins 3-10; actual VQA counts 3-12
  - 1,593 prompts contain `verb`; 12,570 contain `position`
  - official 800-row Geneval2 data remains held-out and is not sampled
- Proposed deterministic selection:
  - 12 hard: `atom_count` 9-10, high VQA count, relation/entity/count burden;
  - 5 medium: `atom_count` 6-8;
  - 3 easy: `atom_count` 3-5;
  - rank within tiers using actual VQA count, distinct skill types,
    verb/position relations, attribute bindings, high object counts, and entity
    count;
  - greedily reward uncovered verb/position operators and penalize reused
    entity families;
  - require exact source line, row hash, tier, score components, and original
    VQA list in the selected artifact.
- Current machine:
  - two visible GPUs, both at 0% reported VRAM before launch;
  - one image/evaluator model workload per GPU is the safe assumption.
- Current runner findings:
  - episode actions are sequential and preserve canonical history;
  - current shared `ThreadPoolExecutor` preassigns devices by episode index,
    which can schedule two concurrent jobs onto one GPU when completion order
    differs;
  - Qwen and Geneval2 models are loaded per attempt, so current workers are not
    persistent model workers;
  - Qwen then Geneval2 execute synchronously on the same episode/device;
  - current resume handles `image_execution_started` without completion but
    not image-completed/evaluator-pending or evaluator-completed/reducer-pending
    crash windows;
  - rollout preparation can overwrite an existing run directory.
- Proposed minimum runtime design:
  - one fixed device-bound worker loop per GPU consuming a shared episode queue;
  - each child process exposes exactly one physical GPU through
    `CUDA_VISIBLE_DEVICES`, `HIP_VISIBLE_DEVICES`, and
    `ROCR_VISIBLE_DEVICES`;
  - no simultaneous Qwen/Geneval2 execution on the same GPU;
  - preserve episode-local sequential execution;
  - continue other episodes after one episode fails and report failures;
  - add no-overwrite preparation guard;
  - add deterministic recovery for image-completed/evaluator-pending and
    evaluator-completed/reducer-pending states;
  - retain per-attempt model loading for this batch unless persistent residency
    is proven safe, because alternating Qwen and VQA models may exceed VRAM.

## Questions

1. Is the 12 hard / 5 medium / 3 easy Flow-DPPO selection policy sufficiently
   grounded, diverse, and fair for this 20-trajectory batch while keeping the
   official 800 rows held out?
2. Is the fixed two-device worker queue plus crash-window recovery the correct
   minimum safe concurrency design, or is persistent model residency a
   blocking requirement before launch?
3. Are these launch gates sufficient: all 20 fresh directories validate as
   native v0.5; scheduler tests prove at most one child per GPU; resume replay
   tests cover both crash windows; 40 steps at 1024x1024; no legacy image reuse;
   and final Sol review checks all submitted trajectories and SFT boundaries?

## Explicit non-goals

- Do not change the v0.5 action or PlannerContext schema.
- Do not make `query_skill` a positive SFT target.
- Do not use official Geneval2 test prompts as training trajectories.
- Do not require simultaneous Qwen and Geneval2 residency on one GPU without
  explicit memory evidence.
- Do not run live Teacher, Qwen, or Geneval2 calls during this review.
- Do not implement code.

## Expected response

- `APPROVE` or `REQUEST_CHANGES`;
- blocking issues only;
- one final selection/concurrency recommendation;
- no implementation.
