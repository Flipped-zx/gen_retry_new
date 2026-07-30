# Phase 7 Teacher/GPU Overlap Review Request

## Gate

`Prospective rollout concurrency and resume-safety review`

## Decision To Review

For ranges after the active 1-20 checkpoint, allow two logical episode workers
per physical HCU while retaining exactly one local GPU execution slot per HCU.
Teacher calls, action validation, and local Skill retrieval may overlap another
episode's Qwen/Geneval2 execution. Every Qwen or Geneval2 load-through-unload
section must hold a physical-device file lock.

No same-episode action may be prefetched across an unevaluated image Attempt.

## Current Evidence

- The active scheduler has eight episode workers for eight HCUs.
- Qwen/Geneval2 use most of one HCU during execution, but the assigned HCU is
  idle while its episode waits for GPT-5.5 or performs CPU event reduction.
- One worker per HCU therefore leaves visible idle gaps.
- The current global model-load lock controls transient loading peaks but does
  not prevent two processes assigned to one physical HCU from loading or
  executing concurrently.
- The proposed implementation adds a physical-HCU execution lock acquired
  before model load and held through inference, artifact save, model deletion,
  and cache release.
- A scheduler option would duplicate each physical HCU into two logical
  episode workers. Default behavior remains one worker per HCU.
- Teacher API calls need a separate bounded cross-process concurrency limit;
  the active eight-worker range has already observed transient 180-second
  Teacher timeouts, recovered at the range level without consuming images.
- Sampling parameters, seeds, backends, PlannerContext, action schema,
  evaluator, and per-episode sequential dependencies remain unchanged.

## Questions

1. Is two logical workers per HCU plus a load-through-unload physical-device
   lock a sound way to overlap Teacher work with GPU execution without OOM,
   duplicate execution, or trajectory-semantic changes?
2. Should Teacher concurrency remain capped at eight (or lower) while
   scheduler-level exact-range resume handles transient timeouts?
3. Can this be enabled prospectively from the next range without invalidating
   comparison across the 200 trajectories, or is a new run root required?

## Non-Goals

- Do not precompute an action that depends on an image/Geneval2 result that
  does not yet exist.
- Do not change generator/evaluator parameters or model IDs.
- Do not allow two GPU stages on the same physical HCU.
- Do not modify completed trajectory artifacts.
- Do not run Teacher, Qwen, or Geneval2 during review.

## Expected Response

`APPROVE`, `APPROVE_WITH_REQUIRED_CHANGES`, or `REJECT`, with only blocking
concurrency, resume, comparability, or SFT risks and the minimum safe policy.
