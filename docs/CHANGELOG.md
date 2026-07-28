# Changelog

## 2026-07-27

- Added optional loading of Git-ignored `.env.teacher.local` credentials while
  preserving shell-export precedence.
- Added a resumable, sanitized GPT-5.5 teacher-only A/B pilot for bounded
  `decision_summary` supervision across five fixed PlannerContext cases.
- Recorded the final Sol verdict `FAIL_KEEP_V05`: two broad-failure
  regeneration summaries did not justify generate-over-edit selection, so the
  canonical v0.5 action schema remains unchanged.
- Added deterministic hard-heavy selection of 20 Flow-DPPO Geneval2 synthetic
  training prompts while excluding the official 800-row test set and
  overlapping semantic families.
- Added a two-device rollout scheduler with one child per physical HCU,
  serialized local model loading, failure isolation, and resumable
  image/evaluator/memory/RoundRecord/context suffix recovery.
- Completed 20 native PlannerContext v0.5 trajectories with 92 local
  1024 x 1024, 40-step Qwen-Image-Edit attempts and complete Geneval2 atom
  evaluation.
- Added batch closure/future-leakage auditing, cross-trajectory analysis, and a
  readable complete-success trace for `phase3_ep_011`.
- Corrected SFT candidate reporting so `query_skill` remains loss 0 and only
  positive/recovery native v0.5 generate/edit/submit actions are candidates.
- Made SFT request indexing deduplicate only identical interrupted retries and
  reject conflicting duplicate request IDs.
- Completed a v0.5 SFT export dry run with 59 loss-bearing targets and 105
  context-only records.
- Recorded the final GPT-5.6 Sol Gate 4 verdict `PASS`.
- Added a consolidated Planner I/O v0.5 architecture document separating Agent
  input/action fields from environment-owned updates and records.
- Added a native v0.5 round-by-round walkthrough for Flow-DPPO
  `phase3_ep_011`, including Skill retrieval, an ineffective edit, a branch
  from historical best, and the all-pass submission.
- Extended the 20-trajectory validation report with deterministic difficulty
  rules, five real strategy case studies, and Flow-DPPO-compatible Geneval2
  Soft-TIFA GM for first, submitted, and peak attempts.
- Added Geneval2 Soft-TIFA AM as the reproducible atom-level continuous metric;
  the 20-trajectory first-to-submitted result is 69.38 to 84.70 (+15.32).

## 2026-07-26

- Added Planner Action Protocol v0.5 with one strict action and a shared
  `instruction` field for generate/edit actions.
- Removed `decision_summary`, `diagnosis_summary`, and legacy planning fields
  from canonical v0.5 image actions.
- Added PlannerContext v0.5 with `latest_attempt`,
  `last_completed_image_round`, `prior_image_rounds`, and deduplicated
  `best_attempt` state.
- Kept nested v0.2-v0.4 actions valid in historical event envelopes while
  making v0.5 the default parser/runtime protocol.
- Changed v0.5 SFT supervision so `query_skill` remains a real action with loss
  0 until Skill utility is validated.
- Upgraded count-edit and local-preservation Skills, added action-pose and
  object-identity Skills, and deprecated overlapping placeholder IDs.

## 2026-07-14

- Added the v0.2 artifact manifest schema for environment-owned artifact refs.
- Tightened the v0.2 episode event schema with payload contracts for canonical
  actions, skill returns, image execution, Geneval2 observations, reducer output,
  submission, and invalid-action observations.
- Tightened the v0.2 planner view schema so planner-visible image references,
  attempts, transitions, tool manifests, and skill manifests are structured and
  exclude raw model output text.
- Addressed Gate 1 requested changes:
  - `action_validated` and `task_created` event payloads now reference the
    canonical action and TaskSpec schemas directly.
  - image execution start/completion payloads are separated, with completed
    events requiring replayable attempt and artifact identity fields.
  - generate execution payloads cannot carry source attempts; edit payloads must
    carry source attempts.
  - `skill_returned` payloads require a query action reference.
  - semantic trajectory validation rejects duplicate constraint IDs, duplicate
    artifact IDs, duplicate per-attempt Geneval2 observations, unknown edit
    sources, and mismatched or unlinked skill returns.
- Addressed Gate 1 second-cycle requested changes:
  - trajectory validation now requires a single episode identity, a first
    `task_created` event, and matching envelope/TaskSpec episode IDs.
  - actions before `task_created` are rejected.
  - image starts must reference exactly one validated image action.
  - image completions must match a prior start by request ID and reference that
    start event.
  - image artifact IDs and Geneval2 results are unique per trajectory/attempt.
- Addressed the user-authorized extra Gate 1 correction cycle:
  - image execution start events can no longer declare attempt lineage fields,
    so completion events are the single source for attempt/parent IDs.
  - each `query_skill` action can have at most one `skill_returned` event.
  - each `geneval2_completed` event must cover every TaskSpec constraint exactly
    once.
  - each `attempt_submitted` event must link to a validated `submit_attempt`
    action with matching selected attempt and reason code.
