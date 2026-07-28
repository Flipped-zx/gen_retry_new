# SOL_REVIEW_REQUEST

## Gate

`SFT Supervision Freeze`

## Decision to review

Whether Gen-Retry should freeze a v0.5 Planner I/O protocol that keeps the v0.4 action-only target shape but renames and clarifies dynamic PlannerContext fields to reduce SFT ambiguity.

## Current evidence

- Relevant schema/ADR:
  - `schemas/action_protocol_v0_4.schema.json`
  - `schemas/planner_context_v0_4.schema.json`
  - `docs/phase3/planner_io_v04_field_confirmation_short.md`
  - `docs/phase3/planner_io_v04_round_io_phase3_ep001.json`
  - `docs/phase3/planner_io_v04_sft_message_view_phase3_ep001.json`
  - `docs/SOURCE_LEDGER.md`
- Minimal test/pilot summary:
  - Current v0.4 replay validation previously passed contract/unit/schema/fixture replay checks.
  - Real normalized trajectory uses prompt `six glass lions chasing three red cats behind a brown donut`.
  - The old trajectory was normalized into v0.4 fields; `decision_summary` is empty in old source actions and should be populated only in future v0.5 live calls.
- Conflicting evidence, if any:
  - User finds `latest_observation` vs `episode_memory.recent_round` semantically blurry.
  - The current names can make reviewers think the same "latest/previous result" is stored twice.
  - GenEvolve/Gen-Searcher style trajectories are easier to read because each assistant action and following environment observation are visually separated.

## Questions

1. For SFT, are the v0.4 fields `latest_observation`, `episode_memory.recent_round`, and `episode_memory.best_attempt` semantically clear enough, or should v0.5 rename them to `current_image_state`, `last_completed_round`, and `best_image_state`?
2. Does v0.4/v0.5 keep the correct boundary between assistant target fields and environment-owned observation fields, especially for Geneval2 outcome, best/latest, budget, visible images, and skill tool responses?
3. What is the smallest v0.5 field design that improves clarity without adding noisy fields that would harm SFT?

## Explicit Non-Goals

- Do not review Qwen-Image-Edit rendering quality.
- Do not propose a new action space beyond `query_skill`, `generate_image`, `edit_image`, `submit_attempt`.
- Do not require a live rollout.
- Do not implement code.

## Expected Response

- blocking issues only;
- recommended decision;
- risks and one minimal validation experiment;
- no code implementation.
