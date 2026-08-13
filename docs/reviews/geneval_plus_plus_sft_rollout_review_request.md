# SOL Review Request: Geneval++ SFT Rollout Adapter

## Gate

Bounded benchmark/evaluation adaptation review; no numbered protocol gate.

## Decision To Review

Add `geneval_plus_plus_metadata_aware_agent@1`. Deterministically convert all
280 Echo-4o Geneval++ metadata rows into exact-count, color, image-region, and
relative-size TaskSpec atoms. Reuse the current Geneval2-compatible VQA path
only as online proxy feedback. Export exactly the canonical submitted Attempt
as one-based JPEGs for the unchanged Echo-4o GPT-4.1 evaluator.

## Minimum Evidence

- Echo-4o commit `28f36d76558e5f53b9deceda78bf025ef0d0ea24` publishes
  280 balanced rows across seven tags.
- The JSONL has 591 include clauses, 290 colors, 240 regions, 80 size labels,
  and 40 counting upper bounds.
- The upstream evaluator consumes `1.jpg` through `280.jpg`, prompt, and a
  metadata-derived checklist; it returns whole-image correct/reason and tag
  macro accuracy using GPT-4.1.
- The implementation fails closed, binds dataset/raw-row/semantic-row/TaskSpec
  hashes, and verifies the canonical submitted artifact and manifest digest.
- Action Protocol v0.5, PlannerContext v0.7, reducer comparator,
  `qwen_dual_backend@1`, and checkpoint are unchanged.

## Questions

1. Does the deterministic atomization preserve the published checklist semantics without overweighting matching exact-count bounds or inverse size labels?
2. Is VQA acceptable as explicitly proxy-only online control when the unchanged GPT-4.1 evaluator alone supplies the formal score?
3. Are one canonical submitted image per prompt, strict 280/280 coverage, and disclosed multi-attempt budget sufficient for a metadata-aware Agent evaluation claim?

## Explicit Non-Goals

- No claim of prompt-only protocol equivalence.
- No canonical schema, reducer, backend, checkpoint, or formal evaluator change.
- No modification or production import from the Echo-4o checkout.

## Expected Response

Return `PASS_IMPLEMENT`, `PASS_WITH_REQUIRED_CHANGES`, or `FAIL_STOP`.
