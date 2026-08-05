# SOL_REVIEW_REQUEST

## Gate

`HPSv3 auxiliary quality guard and edit-stress pilot`

## Decision to review

This branch proposes an additive HPSv3 observation contract and a research
PlannerContext v0.8. It does not change Action protocol v0.5, Geneval2 best
selection, reducer state ordering, or SFT targets. Review whether the field
semantics and the proposed source-selection guard are safe to pilot.

## Current evidence

- `main` and `research/hpsv3-aux-quality` remain at `84cb2c7`; this branch is
  `research/hpsv3-quality-guard`.
- HPSv3 produces a same-prompt score (`mu`, optional `sigma`) and is available
  for offline scoring outside the repository.
- Added `auxiliary_quality_observation_v0_1.schema.json`, an
  `auxiliary_quality_completed` event, and PlannerContext v0.8 compact fields.
- Geneval2 ordering remains `pass-count -> Geneval2 GM -> earlier Attempt`.
- Focused tests pass; schema/fixture validation passes.
- The completed 1k pool has 623 episodes with at least two edits. A frozen,
  stratified 18-episode D2/D3+ x difficulty x semantic U/D/N cohort is listed
  in `docs/phase7/edit_stress_cohort_report.md`. It has no HPS sidecar yet;
  current GM directions are explicitly not called HPS quality drops.

## Questions (max 3)

1. Are the proposed provenance, original-prompt hash, source/quality-anchor,
   `mu/sigma`, delta, status, and risk fields sufficient and unambiguous for
   same-prompt edit comparisons? Is the additive v0.8 context boundary correct
   for preserving v0.7 replay and environment/model ownership?
2. Is the policy boundary sound: use `local_edit_preservation` for a risky
   edit; on high HPS risk without Geneval2 gain, rebranch from the quality
   anchor or regenerate; never let HPS veto a semantic gain or alter reducer
   best/submission? What missing guard or failure mode blocks a pilot?
3. Is the frozen 18-episode cohort and the proposed paired HPS re-score / G vs
   G+H pilot sufficient as an admission design, or must the cohort/endpoint,
   calibration, or human audit change before any intervention is run?

## Explicit non-goals

- No weighted Geneval2+HPS score or HPS-only veto.
- No modification or rerun of the completed 1k trajectories.
- No claim that HPSv3 alone proves perceptual non-regression.
- No SFT export or live policy promotion in this branch.

## Expected response

Return `PASS`, `PASS_WITH_REQUIRED_CHANGES`, or `FAIL_STOP_PILOT`; answer each
question directly, identify concrete blockers, and separate required pilot
changes from optional later analysis.
