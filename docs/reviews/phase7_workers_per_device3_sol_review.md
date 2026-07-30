# Phase 7 Three-Workers-Per-Device Sol Review

## Verdict

`HOLD_TWO_WORKERS`

## Findings

1. Existing hard locks prevent extra GPU residency and the unchanged
   eight-slot Teacher cap bounds API concurrency. However, 24 logical workers
   add unmeasured host-memory, process, lock-wait, and queueing pressure.
2. A complete range boundary would preserve trajectory and SFT comparability
   if all frozen semantics and scheduler provenance remain unchanged.
3. One 30-second utilization sample is insufficient evidence. Complete
   episodes 21-40 and inspect sustained HCU utilization, GPU-lock waits,
   Teacher waits/timeouts, rejected-turn concentration, host-resource
   pressure, and execution failures before reconsidering three workers.

No protocol or SFT blocker was identified. The active and next scheduler ranges
remain at two logical workers per physical HCU.
