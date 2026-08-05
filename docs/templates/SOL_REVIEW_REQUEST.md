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
- HPS events must follow the same Attempt's Geneval2 event. The reducer and
  validator now agree on Attempt materialization order.
- `failed`/`missing` observations require null score/delta fields,
  `quality_risk=unknown`, and a non-empty error. Successful observations require
  a score/report and null error.
- Prompt hashing is exact UTF-8 original-prompt SHA-256. Edit source is the
  direct parent; anchor is the deterministic lineage root. Self, future,
  sibling, and other non-ancestor anchors are rejected.
- `delta = child_mu - baseline_mu` is replay-checked. Risk thresholds,
  calibration provenance, and canonical policy fingerprint are persisted and
  locked within an episode.
- HPS `image_sha256` is cross-checked against the exact
  `image_execution_completed.payload.artifact_sha256`, in addition to the
  artifact ID check.
- `G+H` is explicitly PlannerContext v0.8 plus
  `planner_context_only_hpsv3_advisory_v1`; no environment middleware filters
  sources. Watch/high risk can motivate an explicit
  `local_edit_preservation` query, shallow branch, or regeneration Action.
- Before each v0.8 context, the environment must emit exactly one explicit
  HPS `success`, `failed`, or `missing` event for every evaluated Attempt, so a
  late/hidden quality omission is rejected while evaluator failure remains
  non-blocking.
- Validation passes: 79 contract tests, 196 unit tests, 15 schemas, 106 fixture
  records, and canonical episode replay.
- The completed 1k pool has 623 episodes with at least two edits. A frozen,
  stratified 18-episode D2/D3+ x difficulty x semantic U/D/N cohort is listed
  in `docs/phase7/edit_stress_cohort_report.md`. It has no HPS sidecar yet;
  current GM directions are explicitly not called HPS quality drops.
- A deterministic 60-episode confirmation manifest is disjoint from those 18
  calibration episodes and was selected without HPS results. All 60 primary
  pairs are direct edits with resolvable images and Geneval2 artifacts.
- Offline HPS annotation is now explicitly diagnostic only. Mitigation requires
  a fresh paired `G`/`G+H` rollout. Admission first requires a submitted
  Geneval2 atom-pass non-inferiority lower bound above `-0.02`, then evaluates
  HPS submitted-`mu` improvement, high-risk edit-rate reduction, and blind
  human preference. All quality gates are conjunctive; failed/missing submitted
  HPS is inconclusive, and root `delta_from_anchor=null` is not imputed.
- Stage 2 explicitly uses GPT-5.5 Teacher v9 for both arms. The frozen SFT
  planner remains v0.7-only; no unrecorded v0.8 SFT compatibility is assumed.

## Questions (max 3)

1. Do the post-Geneval event order, strict missing semantics, lineage-root
   anchor, exact delta and image-digest checks, and versioned hash/risk
   policies close the first review's protocol/replay blockers?
2. Is the operational boundary now identifiable and safe: `G` is v0.7,
   `G+H` is v0.8 plus its recorded Planner instruction, all interventions are
   explicit Actions, and HPS never changes reducer best or vetoes semantic gain?
3. Are the disjoint 18 calibration / 60 confirmation design, episode-cluster
   analysis, `-0.02` semantic non-inferiority guard, held-out HPS endpoints, and
   blind human audit sufficient to begin the paired intervention pilot?

## Explicit non-goals

- No weighted Geneval2+HPS score or HPS-only veto.
- No modification or rerun of the completed 1k trajectories.
- No claim that HPSv3 alone proves perceptual non-regression.
- No SFT export or live policy promotion in this branch.

## Expected response

Return `PASS`, `PASS_WITH_REQUIRED_CHANGES`, or `FAIL_STOP_PILOT`; answer each
question directly, identify concrete blockers, and separate required pilot
changes from optional later analysis.

## Review Result

GPT-5.6 Sol returned `PASS`. The versioned verdict and scope are recorded in
`docs/reviews/hpsv3_aux_quality_guard_sol_review.md`.
