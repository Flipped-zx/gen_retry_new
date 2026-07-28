# SOL_REVIEW_REQUEST

## Gate

`SFT Supervision Freeze`

## Decision to review

Reconsider whether native future Gen-Retry planner actions should include a
short trainable `decision_summary`, after correcting the provenance of the
v0.4 evidence used in the previous review.

## Current evidence

- Relevant schema/ADR:
  - `schemas/action_protocol_v0_3.schema.json`
  - `schemas/action_protocol_v0_4.schema.json`
  - `schemas/action_protocol_v0_5.schema.json`
  - `schemas/planner_context_v0_5.schema.json`
  - `docs/decisions/ADR-0005-sft-supervision-freeze.md`
  - `docs/phase3/planner_io_v05_field_design_packet.md`
  - `docs/phase3/planner_io_v05_round_memory_walkthrough_phase3_ep001.md`
  - `docs/reviews/planner_io_v05_field_sft_review.md`
  - `docs/teacher_prompt_design/TRAINING_TRAJECTORY_FORMAT_COMPARISON.md`
- Corrected trajectory provenance:
  - v0.4 was not exercised by a native live trajectory.
  - The v0.4 display trajectory was a deterministic projection of a completed
    v0.3 trajectory for field review.
  - Therefore its empty `decision_summary` values are conversion artifacts,
    not evidence that a native teacher cannot produce the field, that the field
    is noisy, or that it lacks planning value.
  - Post-hoc summaries must still not be used as SFT labels.
- Current v0.5 state:
  - `decision_summary` is excluded.
  - Planner supervision is represented by action choice, source selection,
    target/preserve constraint sets, executable `instruction`, and submit
    `reason_code`.
  - Offline v0.5 contract/unit/schema/fixture/replay validation passed.
- Conflicting evidence:
  - A free-text rationale can duplicate structured fields, consume target
    tokens, and become stylistic noise in a small SFT dataset.
  - Gen-Retry is a planner, so a native bounded statement of why it chose
    generate vs edit, latest vs historical best, or continue vs submit may
    expose a useful state-to-decision bridge that the existing fields encode
    only implicitly.
  - GenEvolve uses concise `<think>` planning before tool calls, but its ReAct
    objective and tool/search setting are not identical to Gen-Retry.

## Questions

1. Given the corrected provenance, should the next native Gen-Retry protocol
   keep v0.5 without `decision_summary`, or require a short trainable
   `decision_summary` for generate/edit/submit actions? Give one final
   recommendation, not both.
2. If the field should be included, define its exact semantic boundary,
   length/format constraints, loss treatment, and anti-leakage rules. If it
   should remain excluded, explain how the current structured target adequately
   supervises action/source/rollback decisions.
3. Is a native controlled pilot needed before the SFT freeze can be considered
   final? If yes, specify the smallest experiment and an explicit acceptance
   criterion without requiring Qwen/Geneval2 outcome improvement.

## Explicit non-goals

- Do not change code, schemas, ADRs, or completed trajectory artifacts.
- Do not review Skill content or Skill utility.
- Do not run live teacher, Qwen-Image-Edit, or Geneval2 calls.
- Do not reopen unrelated PlannerContext field decisions.
- Do not treat the projected v0.4 trace as native training evidence.

## Expected response

- `KEEP_EXCLUDED` or `REINTRODUCE_REQUIRED_TRAINABLE`;
- concise reasoning grounded in corrected evidence;
- exact field contract if reintroduced;
- one minimal validation experiment and acceptance criterion;
- no code implementation.
