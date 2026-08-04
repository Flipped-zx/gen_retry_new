# Sol Review Request: High-Quality Rollout V9 Implementation

## Scope

Review only the prospective rollout implementation. Do not review or freeze a
final SFT exporter.

Changed semantics:

- PlannerContext v0.7 adds prior image-action `instruction` fields.
- Teacher v9 replaces tuple rejection with meaningful intervention change.
- Runtime keeps non-best source evidence validation but removes tuple equality
  rejection.
- Retrieval-time Skill content is restored from hash-verified immutable tool
  observations.
- Same-count historical Attempts with unique pass evidence are exposed as
  visible image candidates.
- Existing v0.6 episodes retain their persisted version and artifacts.

Unchanged:

- Action Protocol v0.5;
- Qwen generate/edit routing;
- Geneval2;
- pass-count then GM reducer;
- attempt budget and submission;
- final SFT eligibility/masking.

Primary files:

- `docs/decisions/ADR-0008-meaningful-retry-rollout-policy.md`
- `schemas/planner_context_v0_7.schema.json`
- `src/gen_retry/runtime/planner_context.py`
- `src/gen_retry/agent/teacher_client.py`
- `src/gen_retry/phase3/live_runner.py`
- `src/gen_retry/domain/score_policy.py`
- `docs/phase7/high_quality_trajectory_policy_and_evidence_plan.md`

Validation:

- contract tests: 79 passed;
- unit tests: 149 passed;
- schema validation: 13 passed;
- fixture validation: 105 records passed;
- historical example replay: passed;
- old `verb_multiround_teacher_v2`: 13/13 persisted PlannerContexts rebuild
  exactly after Skill upgrade;
- failed-12 verb batch audit: 12 episodes / 60 attempts, PASS.

## Questions

1. Does v0.7 expose enough past-only information to support meaningful retry
   without changing Action Protocol or leaking future outcomes?
2. Are hash-stable Skill replay and historical source image visibility now
   consistent with the Teacher's executable source choice?
3. Is there any blocking correctness or claim issue before the fixed paired
   v8.1/v9 pilot?

Return exactly `PASS` or `FAIL` with blocking issues only.
