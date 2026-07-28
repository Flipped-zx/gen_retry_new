# SOL_REVIEW_REQUEST

## Gate

`Protocol Freeze`

## Decision to review

Migrate Planner I/O from the current v0.3 PlannerContext/action schema to `gen_retry_planner_io_v04_codex_reference.md` as the single source of truth, removing v0.3-only planner-visible fields and compatibility layers.

## Current evidence

- Relevant schema/ADR:
  - `gen_retry_planner_io_v04_codex_reference.md`
  - `schemas/action_protocol_v0_3.schema.json`
  - `schemas/planner_context_v0_3.schema.json`
  - `docs/phase3/trajectory_trace_planner_context_v0_3_ep_001.md`
- Minimal test/pilot summary:
  - Existing v0.3 implementation passed contract/unit/schema/fixture/replay validation before this migration.
  - Existing v0.3 live trajectory exists at `runs/planner_context_v0_3/phase3_ep_001`.
  - v0.4 requires golden replay of the real `phase3_ep_001` branch sequence: query -> generate -> generate -> edit -> regressive edit -> rollback edit from historical best -> submit historical best.
- Conflicting evidence, if any:
  - Repository status and older docs still describe v0.3 as current.
  - v0.3 exposes `active_round`, `control`, `mode`, `skill_ids_used`, `diagnostic_hypotheses`, and `interventions`; v0.4 explicitly removes or merges these.

## Questions

1. Is adopting v0.4 exactly as specified a reasonable improvement over the current v0.3 trajectory structure for clear SFT-style planner input/output?
2. Are there blocking semantic risks in removing `active_round`, `mode`, `skill_ids_used`, `diagnostic_hypotheses[]`, and `interventions[]` from the planner-visible protocol?
3. Is the v0.4 golden replay requirement sufficient to validate source-relative edit transitions, latest/best separation, rollback from historical best, and submit of non-latest best?

## Explicit non-goals

- Do not review Qwen-Image-Edit image quality.
- Do not run or request live trajectories.
- Do not propose new fields, actions, memory layers, or compatibility structures outside v0.4.
- Do not implement code.

## Expected response

- blocking issues only;
- recommended decision;
- risks and one minimal validation experiment;
- no code implementation.
