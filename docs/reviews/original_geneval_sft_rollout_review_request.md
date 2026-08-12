# SOL Review Request: Original GenEval SFT Rollout Adapter

## Decision

Add deterministic original GenEval metadata-to-TaskSpec preparation and a
post-submission exporter. Use the existing Geneval2-compatible VQA path only as
online proxy feedback. Evaluate the one submitted image per prompt afterward
with the pristine original GenEval detector checkout.

## Questions

1. Is this adaptation valid if the Planner-visible rubric and proxy role are disclosed?
2. May the existing canonical VQA observation remain unchanged when it is never called an official score?
3. Is one submitted image per prompt a valid Agent-level protocol when separated from the upstream four-sample recipe?

## Non-Goals

No Action, PlannerContext, event, reducer, backend, checkpoint, or official
detector change. No detector result is fed back into canonical history.
