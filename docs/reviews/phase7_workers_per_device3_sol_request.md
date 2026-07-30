# Phase 7 Three-Workers-Per-Device Sol Review Request

## Decision

Whether to change only the prospective scheduler profile from two to three
logical episode workers per physical HCU, beginning at the next complete range
boundary after episodes 21-40.

## Frozen Semantics

- Eight physical HCUs.
- One complete local GPU stage at a time per physical HCU.
- Eight cross-process Teacher slots; this cap would not change.
- One active executor per episode.
- Fixed lock order: physical HCU, then global model-load lock.
- No Teacher call while holding a GPU lock and no GPU lock while holding a
  Teacher slot.
- All Planner, Action, Skill, Qwen, Geneval2, score, seed, and resume contracts
  remain unchanged.

## Evidence

- Existing implementation review:
  `docs/reviews/phase7_api_gpu_overlap_sol_review.md`
- Checkpoint 20 validity review:
  `docs/reviews/phase7_fresh8_ckpt_020_sol_review.md`
- The 21-40 range has no OOM, API timeout, connection error, or execution
  traceback so far.
- One 30-second steady-state sample during 21-40 observed a mean 5.13 active
  HCUs, with a range of 4-6. Idle HCUs coincided with active episodes waiting
  on causally legal Teacher calls.
- Physical-HCU locks remain the hard GPU concurrency limit. Raising logical
  workers would add waiting/planning processes, not concurrent model residency.

## Questions

1. Is three logical workers per HCU safe under the existing hard locks and
   unchanged eight-slot Teacher cap?
2. Does enabling it only at a complete range boundary preserve trajectory and
   SFT comparability?
3. Should it begin at the next boundary, or should the scheduler remain at two
   workers until a longer utilization sample is available?

## Expected Response

Return `APPROVE_NEXT_BOUNDARY`, `HOLD_TWO_WORKERS`, or `STOP_BLOCKING`, followed
by concise conditions or blockers. Do not edit files or invoke live services.
