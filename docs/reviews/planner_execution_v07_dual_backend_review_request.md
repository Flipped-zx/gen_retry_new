# SOL_REVIEW_REQUEST

## Gate

`Planner execution backend semantics amendment`

## Decision to review

Review the proposed v0.7 execution profile before changing ADR-0001 or live
runtime code:

```text
generate_image -> local Qwen-Image-2512, no source image
edit_image     -> local Qwen-Image-Edit-2511, declared source Attempt
```

The canonical action space and action arguments remain unchanged. Backend and
model selection remain deterministic environment-owned facts.

## Current evidence

- Current implemented protocol is v0.5:
  `schemas/action_protocol_v0_5.schema.json` and
  `schemas/planner_context_v0_5.schema.json`.
- There is no implemented v0.6 schema. The v0.6 label only appears in an
  unexecuted review template concerning PlannerContext score/selection
  semantics.
- ADR-0001 currently fixes both logical image actions to one
  Qwen-Image-Edit backend.
- Current source-free `generate_image` creates a white 1024 x 1024 canvas and
  passes it to `QwenImageEditPlusPipeline`.
- Local model paths exist for both `Qwen-Image-2512` and
  `Qwen-Image-Edit-2511`.
- Qwen-Image-2512 is a source-free `QwenImagePipeline`; Qwen-Image-Edit-2511 is
  source-conditioned.
- Gen-Searcher uses the Qwen text-to-image model for pure text and the edit
  model when references are present, but this is a final-renderer route rather
  than a sequential retry trajectory.
- Gen-Retry has a genuinely sequential image state:
  generate/evaluate/edit-or-regenerate/evaluate/submit.
- Candidate design:
  `docs/architecture/planner_execution_v0_7_dual_backend.md`.

## Questions

1. Should this change be represented as an execution-profile/ADR revision
   while retaining the existing canonical action schema, or does the changed
   executable meaning require a new action schema version for SFT clarity?
2. Is deterministic routing by logical action sufficient, with no
   Planner-predicted `backend`, `mode`, or `regenerate_image` field? Identify
   any missing provenance or invariant required to prevent ambiguous training
   examples.
3. Is the proposed first diagnostic comparison adequate: frozen previously
   difficult prompts, equal image-attempt budget, legacy edit-only versus
   dual-backend end-to-end runs, plus a separate fixed-action matched replay
   before attributing gains to either renderer?

## Explicit non-goals

- Do not run Teacher, Qwen, or Geneval2.
- Do not change PlannerContext score/selection semantics.
- Do not change reducer best/submission policy.
- Do not activate or retrain Skills.
- Do not rewrite completed trajectories.
- Do not implement code in this review.

## Expected response

- `APPROVE` or `REQUEST_CHANGES`;
- blocking issues only;
- exact recommendation on versioning and provenance;
- exact minimum comparison needed before rollout expansion.
