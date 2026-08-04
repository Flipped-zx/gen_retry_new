# Flow-DPPO 1000 v9 API Prefetch Review

## Verdict

`KEEP_CURRENT_CROSS_EPISODE_OVERLAP`

The current 16 logical workers and eight cross-process Teacher slots already
allow later episodes to complete their first Teacher call while another
episode owns a Qwen/Geneval2 GPU stage. This captures the useful API/GPU
overlap without adding a central prefetch protocol.

Do not prefetch the next action inside one episode past an unevaluated image.
After `query_skill`, the second Teacher request must wait for the local Skill
response and rebuilt PlannerContext. After an image action, the next request
must wait for Qwen, Geneval2, reducer, RoundRecord, and the next
PlannerContext.

## Why Not Deeper Prefetch

A deeper first-action queue would require durable Teacher-output caching,
episode ownership, stop-admission semantics, duplicate request handling, and
resume reconciliation. A crash after the Teacher response but before raw
output/event persistence can currently repeat that API request without
corrupting the trajectory; deeper speculative prefetch would increase this
surface.

Only revisit this decision if a fixed 20- or 100-ID resource profile shows
pending work is abundant while active HCUs stay below 5/8 primarily because
of first-Teacher latency.

## Monitoring

- active HCU count and pending episode count;
- PlannerContext-built to planner-output-recorded latency;
- Teacher timeout, rate-limit, and connection errors;
- first-action and post-query Skill Teacher latency;
- repeated request IDs after resume;
- per-attempt Qwen and Geneval2 latency;
- valid submitted episodes accidentally admitted again;
- no-future-leakage, submitted-best, and source-attempt invariants.

This was a read-only GPT-5.5 XHigh review. It did not call an API/GPU or modify
the repository.
