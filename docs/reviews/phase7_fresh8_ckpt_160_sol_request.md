# Phase 7 Fresh-8 Checkpoint 160 Sol Review Request

## Gate

`20-trajectory light review at cumulative checkpoint 160`

## Scope

Review only for an early blocker after Teacher policy v8 began producing valid
submissions. The continuous queue remains active. Do not edit files, invoke
Teacher/Qwen/Geneval2, inspect credentials, or infer a causal v8 improvement
from three trajectories.

## Frozen Contracts

- PlannerContext `0.6`
- Action protocol `0.5`
- Score policy `geneval2_pass_count_then_gm@1`
- Execution profile `qwen_dual_backend@1`
- At most five image attempts
- Accepted routing:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`

## Evidence

- Predeclared cohort:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_160_predeclared_cohorts.json`
- Frozen increment:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_160_completed_quality_increment.json`
- Full increment audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_160_quality_increment_audit.md`
- v7 audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_160_v7_increment_audit.md`
- v8 audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_160_v8_increment_audit.md`
- Version interpretation:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_160_version_stratified_note.md`
- Fixed admission status:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_160_admission_status.md`
- Resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_160_resource_profile.md`
- v8 policy:
  `docs/phase7/planner_retry_closure_policy_v8.md`
- Checkpoint-150 deep verdict:
  `docs/reviews/phase7_fresh8_ckpt_150_sol_review.md`

Full increment:

- 10 valid trajectories and 38 evaluated images.
- Atom pass improved from 55/70 to 61/70.
- Soft-TIFA GM improved from 34.18 to 59.44.
- 4/10 reached all atoms.
- 11 regressive and seven strictly ineffective actions.

Version split:

- v7: seven trajectories, 34 attempts, 42/51 submitted atoms, GM 42.72, and
  all 11 regressive actions.
- v8: three trajectories, four attempts, 19/19 submitted atoms, GM 98.47,
  zero regression, and zero ineffective actions.
- The v8 subgroup is small and easier; no performance claim is permitted.
- v8 exercised two first-image submissions and one successful reducer-best
  edit, but no closure rejection.

Fixed status and resources:

- IDs 151-160: eight completed, two active, zero failed.
- Mean 5.92/8 active HCUs, median six, zero all-idle samples, and no continuous
  queue infrastructure error.

## Questions

1. Is there any early data-validity, routing, memory, SFT-boundary,
   cohort/version, or future-leakage blocker?
2. Is the v8 interpretation sufficiently conservative, especially given
   three easier trajectories and no closure-rejection example?
3. Should admission continue unchanged to the predeclared checkpoint 180, or
   is a specific prospective correction required now?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Answer the three questions directly and do not treat the small v8 subgroup as
evidence of aggregate performance improvement.
