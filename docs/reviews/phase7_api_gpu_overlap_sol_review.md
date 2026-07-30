# Phase 7 Teacher/GPU Overlap Sol Review

## Verdict

`APPROVE_WITH_REQUIRED_CHANGES`

## Required Changes

1. Two logical workers per HCU may be enabled only after adding a lock keyed
   by the real physical HCU ID. The fixed lock order is:
   `physical_device_lock -> global_model_load_lock`.
2. The physical-device lock must cover model load, inference, artifact save,
   output/model deletion, synchronization, garbage collection, cache release,
   and unload for both Qwen and Geneval2.
3. A run-root scheduler lock and per-episode execution lock must prevent two
   schedulers or orphan executors from writing one episode concurrently.
4. Images must use temporary-file plus atomic rename. Cache reuse must verify
   decode, dimensions, and hash computation.
5. Teacher calls need a cross-process hard limit. Start with eight slots; if
   the next checkpoint still shows material 180-second timeouts, lower the
   prospective cap to six.
6. No worker may hold a Teacher slot while waiting for a GPU lock, and no
   worker may call Teacher while holding a GPU lock.
7. Enable the new scheduler only at the 21-40 range boundary. Record logical
   workers, workers per device, Teacher cap, and lock version as environment
   provenance.

## Comparability Decision

A new run root is not required. The change is scheduling-only and may start at
a complete range boundary if Teacher prompt/model, PlannerContext, Action
Protocol, Skill content, Qwen/Geneval2 parameters, seed, and score policy stay
fixed. One episode must remain causally sequential: no Teacher action may be
prefetched across an image Attempt that has not completed Geneval2.

## Approved Minimum Profile

- 16 logical episode workers
- 8 Teacher slots
- 8 physical HCU execution slots
- 1 complete local GPU stage at a time per physical HCU
- 1 active executor per episode

## Implementation Verification

`PASS`

GPT-5.6 Sol verified the implementation diff and validation summary after all
required changes were applied:

- 7/7 required changes satisfied;
- no blocking issue;
- safe to enable at the 21-40 boundary after 1-20 exits successfully;
- no new run root required;
- trajectory semantics and SFT comparability remain unchanged.
