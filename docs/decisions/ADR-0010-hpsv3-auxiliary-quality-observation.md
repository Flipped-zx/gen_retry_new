# ADR-0010: HPSv3 Auxiliary Quality Observation

- Status: Accepted for the GPT-5.5 Teacher paired pilot on
  `research/hpsv3-quality-guard`; not accepted for SFT or promotion
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
| provenance | `evaluator_id/version`, `checkpoint_ref/sha256`, `preprocess_version`, `report_ref/sha256` |
| identity | immutable original `prompt_sha256`, `prompt_hash_policy_id`, `attempt_id`, `image_artifact_id/sha256` |
| baselines | `source_attempt_id`, `quality_anchor_attempt_id`, `quality_anchor_policy_id` |
| score | `status`, `mu`, optional `sigma`, `delta_from_source`, `delta_from_anchor` |
| reproducibility | `delta_policy_id`, canonical `risk_policy`, `risk_policy_sha256` |
| decision view | derived `quality_risk` (`low`, `watch`, `high`, `unknown`) |

The event must occur after the same Attempt's `geneval2_completed` event, so
the existing reducer has already materialized the Attempt. The immutable
prompt hash is exactly `sha256(original_prompt.encode("utf-8"))`; an edit
instruction never replaces it.

`source_attempt_id` is the direct parent. Under `lineage_root_v1`, a root has
no quality anchor and every edit descendant is anchored to its deterministic
lineage root. Self, future, sibling, and other non-ancestor anchors are
invalid. Deltas are recomputed as `child_mu - baseline_mu` from prior
successful observations. A delta is null if its baseline lacks a successful
score.

`failed` and `missing` require null `mu`, `sigma`, and deltas plus
`quality_risk=unknown` and a non-empty `error_code`. `success` requires a
score, report artifact, and null error. The risk policy embeds its calibration
reference and exact high/watch thresholds; its hash is over canonical JSON.
All evaluator and policy fingerprints are locked within an episode.

PlannerContext v0.8 exposes only compact score fields and a chronological
`quality_history`; full checkpoint/report provenance stays in the event and
artifact. In a v0.8 episode, the next PlannerContext cannot be built until the
environment has emitted exactly one `success`, `failed`, or `missing` quality
event for every already-evaluated Attempt. Existing v0.7 contexts and
completed trajectories are not rewritten.

## Decision Policy

1. Keep the frozen Geneval2 ordering exactly as `higher pass-count`, then
   `higher Geneval2 GM`, then earlier Attempt. HPSv3 never changes
   `best_attempt_id`, submission, or SFT target selection by itself.
2. `G+H` is exactly PlannerContext v0.8 plus the versioned
   `planner_context_only_hpsv3_advisory_v1` Teacher instruction. No environment
   middleware filters a source or rewrites an action. The context exposes this
   fact as `hidden_source_filter=false`.
3. Use the existing `local_edit_preservation` skill for a watch/high-risk next
   edit: minimal localized operation, explicit spatial anchor, preserve passed
   evidence, and forbid a full-scene redraw. No new overlapping Skill is added.
4. If a child is `high` risk and has no Geneval2 improvement, the next decision
   may branch from `quality_anchor_attempt_id` or choose source-free
   regeneration. The risky child remains in canonical history and is still
   evaluated.
5. If a child is semantically better but HPSv3 regresses, retain it as a valid
   Geneval2 candidate; HPSv3 may trigger a later comparison or shallow branch,
   never a veto. `watch`/`unknown` status cannot block an action.

For a submitted root Attempt, quality decisions use absolute `mu`; its null
anchor delta is not silently converted to zero. Failed/missing submitted HPS
is an inconclusive endpoint for admission, while failed/missing intermediate
observations remain non-blocking planner context.

Threshold values are not chosen in this ADR. The 18-episode edit-stress set is
calibration/feasibility only. It freezes thresholds against blind human
degradation labels, then persists the resulting policy and fingerprint before
confirmation. HPSv3-only non-regression is not a claim of perceptual
non-regression.

## Required Evidence Before Promotion

The frozen 60-episode confirmation manifest is disjoint from calibration and
was selected without HPS results. Offline HPS annotation of existing images
only diagnoses historical quality loss; it does not test mitigation. The
mitigation test reruns each confirmation prompt as paired `G` and `G+H` arms
with the GPT-5.5 Teacher v9 planner (the frozen SFT planner remains v0.7-only),
prompt, TaskSpec, planner/model settings, execution profile, seeds, budget, and
image-call count held fixed. Geneval2 non-inferiority is tested before any
quality improvement claim; submitted HPS coverage, absolute-`mu` improvement,
high-risk reduction, and blind human preference are conjunctive quality gates.
Statistics resample episode IDs, never Attempts.

This protocol and any source-selection rule require GPT-5.6 Sol review before
being used in live rollouts or SFT export.
