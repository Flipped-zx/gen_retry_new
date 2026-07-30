# Phase 7 Fresh-8 Checkpoint 180 Sol Review Request

## Gate

`20-trajectory light review at cumulative checkpoint 180`

## Scope

Review the frozen completed-quality increment for validity and early v8
mechanism evidence. The continuous queue remains active. Do not edit files,
invoke Teacher/Qwen/Geneval2, inspect credentials, or interpret the nonrandom
v7/v8 boundary as a causal performance ablation.

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
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_180_predeclared_cohorts.json`
- Frozen increment:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_180_completed_quality_increment.json`
- Full increment audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_180_quality_increment_audit.md`
- v7 audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_180_v7_increment_audit.md`
- v8 audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_180_v8_increment_audit.md`
- Version/closure interpretation:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_180_version_stratified_note.md`
- Fixed admission status:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_180_admission_status.md`
- Resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_180_resource_profile.md`
- v8 policy:
  `docs/phase7/planner_retry_closure_policy_v8.md`
- Checkpoint-160 verdict:
  `docs/reviews/phase7_fresh8_ckpt_160_sol_review.md`

Full increment:

- 20 valid trajectories and 64 evaluated images.
- Atom pass improved from 109/130 to 122/130.
- Soft-TIFA AM improved from 84.41 to 92.65.
- Soft-TIFA GM improved from 49.10 to 80.41.
- 13/20 reached all atoms.
- Submitted-to-peak GM gap is zero.
- 11 regressive and 13 strictly ineffective actions.

Version split:

- v7: five trajectories, 25 attempts, 26/32 submitted atoms, GM 35.86, zero
  all-pass submissions, and seven regressive actions.
- v8: 15 trajectories, 39 attempts, 96/98 submitted atoms, GM 95.26, 13
  all-pass submissions, and four regressive actions.
- v8 had six post-regression/strict-no-progress decisions and zero equivalent
  action/source/target repeats; v7 had two repeats across 11 opportunities.
- No v8 runtime closure rejection occurred.
- Version assignment is nonrandom, so only mechanism consistency is claimed.

Fixed status and resources:

- IDs 161-180: 17 completed, three active, zero failed.
- Mean 5.91/8 active HCUs, median six, zero all-idle samples, and no continuous
  queue infrastructure error.

## Questions

1. Is there any data-validity, routing, memory, SFT-boundary, cohort/version,
   or future-leakage blocker?
2. Is the supported v8 claim correctly limited to observed retry-closure
   compliance rather than causal performance improvement?
3. Should admission continue unchanged to the final all-ID checkpoint 200, or
   is a specific prospective correction required now?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Answer the three questions directly and separate validity blockers from
optional monitoring.
