# ADR-0010: HPSv3 Auxiliary Quality Observation

- Status: Proposed on `research/hpsv3-quality-guard`
- Action protocol: `0.5` (unchanged)
- PlannerContext: `0.8` research extension; `0.7` replay remains unchanged
- Primary selector: `geneval2_pass_count_then_gm` (unchanged)
- Auxiliary evaluator: `hpsv3` observation only

## Context

Repeated Qwen image edits can repair a Geneval2 atom while making the image
less faithful or less aesthetically coherent. HPSv3 gives a useful same-prompt
signal: the score of a child can be compared with its direct source and with a
stable quality anchor. That signal is not a semantic verifier and is not enough
to establish that quality did not drop.

## Observation Contract

Each evaluated image may append one `auxiliary_quality_completed` event. Its
payload is validated by
`schemas/auxiliary_quality_observation_v0_1.schema.json` and records:

| Group | Fields |
| --- | --- |
| provenance | `evaluator_id/version`, `checkpoint_ref/sha256`, optional `preprocess_version`, `report_ref/sha256` |
| identity | immutable original `prompt_sha256`, `attempt_id`, `image_artifact_id/sha256` |
| baselines | `source_attempt_id`, `quality_anchor_attempt_id` |
| score | `status`, `mu`, optional `sigma`, `delta_from_source`, `delta_from_anchor` |
| decision view | `quality_risk` (`low`, `watch`, `high`, `unknown`) |

The original prompt is never replaced by an edit instruction. A delta is null
when its baseline ID is null. Failed or missing evaluations carry no score.
The event is environment-owned and must not contain an Action or a planner
prediction.

PlannerContext v0.8 exposes only compact score fields and a chronological
`quality_history`; full checkpoint/report provenance stays in the event and
artifact. Existing v0.7 contexts and completed trajectories are not rewritten.

## Decision Policy

1. Keep the frozen Geneval2 ordering exactly as `higher pass-count`, then
   `higher Geneval2 GM`, then earlier Attempt. HPSv3 never changes
   `best_attempt_id`, submission, or SFT target selection by itself.
2. Use the existing `local_edit_preservation` skill for any edit that has a
   quality warning: minimal localized operation, explicit spatial anchor,
   preserve passed evidence, and forbidden full-scene redraw.
3. If a child is `high` risk and has no Geneval2 improvement, the next decision
   may branch from `quality_anchor_attempt_id` or choose source-free
   regeneration. The risky child remains in canonical history and is still
   evaluated.
4. If a child is semantically better but HPSv3 regresses, retain it as a valid
   Geneval2 candidate; HPSv3 may trigger a later comparison or shallow branch,
   never a veto. `watch`/`unknown` status cannot block an action.

Thresholds for `quality_risk` are not frozen by this ADR. They must be chosen
on an edit-stress calibration cohort and then held fixed for confirmation.
HPSv3-only non-regression is not a claim of perceptual non-regression.

## Required Evidence Before Promotion

Select typical episodes from the 1k rollout with at least two edits, stratified
by edit depth, difficulty, and failure type. A paired pilot must keep prompt,
TaskSpec, planner, execution profile, seeds, and budget fixed. Report semantic
Geneval2 endpoints and HPS/source-anchor deltas per prompt group; add blind
human review for a small calibration subset. Do not treat Attempts inside one
episode as independent samples.

This protocol and any source-selection rule require GPT-5.6 Sol review before
being used in live rollouts or SFT export.
