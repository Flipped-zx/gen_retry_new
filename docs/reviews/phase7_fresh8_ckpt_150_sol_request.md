# Phase 7 Fresh-8 Checkpoint 150 Sol Review Request

## Gate

`50-trajectory deep review at cumulative checkpoint 150`

## Scope

Review the frozen completed-quality increment, fixed admission-status cohort,
cumulative SFT reconciliation, resource evidence, and the prospective v8
retry-closure policy required at checkpoint 140. The continuous queue remains
active. Do not edit files, invoke Teacher/Qwen/Geneval2, inspect credentials,
or treat rejected raw turns as canonical actions.

## Frozen Contracts

- PlannerContext `0.6`
- Action protocol `0.5`
- Score policy `geneval2_pass_count_then_gm@1`
- Execution profile `qwen_dual_backend@1`
- At most five image attempts
- Skill responses and evaluator outcomes are context-only for SFT

Accepted dual-backend routing is defined by
`docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`:
source-free `generate_image` uses Qwen-Image-2512 and source-conditioned
`edit_image` uses Qwen-Image-Edit-2511.

## Cohort Semantics

- Predeclaration:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_150_predeclared_cohorts.json`
- Completed-quality increment:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_150_completed_quality_increment.json`
- Fixed admission-status denominator:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_150_admission_status.md`
- Teacher-policy boundary:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_150_teacher_policy_boundary.md`

Quality metrics are completion-conditioned. Operational status uses all fixed
IDs 141-150. The checkpoint-150 quality increment and cumulative cohort are
entirely v7 and serve as the final pre-v8 baseline.

## Evidence

- 10-trajectory increment audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_150_quality_increment_audit.md`
- 150-trajectory cumulative audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_150_cumulative_audit.md`
- Increment behavior labels:
  `docs/phase7/checkpoints/ckpt_150_analysis/sft_candidate_action_report.md`
- Cumulative behavior labels:
  `docs/phase7/checkpoints/ckpt_150_cumulative_analysis/sft_candidate_action_report.md`
- Cumulative SFT reconciliation:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_150_sft_reconciliation.md`
- Resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_150_resource_profile.md`
- Required prospective policy:
  `docs/phase7/planner_retry_closure_policy_v8.md`
- Checkpoint-140 review:
  `docs/reviews/phase7_fresh8_ckpt_140_sol_review.md`
- Accepted routing decision:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`
- Current module contracts:
  `docs/architecture/MODULE_CONTRACTS.md`

Checkpoint-150 increment:

- 10/10 valid submissions and 38 evaluated images.
- Atom pass improved from 51/66 to 61/66.
- Soft-TIFA AM improved from 78.02 to 90.21.
- Soft-TIFA GM improved from 32.50 to 76.17.
- Peak GM is 76.37; submitted-to-peak gap is 0.20.
- 6/10 reached all atoms.
- Six regressive actions and five strictly ineffective actions.
- All ten trajectories persisted Teacher policy v7.

Cumulative checkpoint 150:

- 150 valid trajectories and 489 evaluated images.
- Atom pass improved from 877/1063 to 985/1063.
- Soft-TIFA AM improved from 82.77 to 91.69.
- Soft-TIFA GM improved from 45.58 to 75.55.
- 91/150 reached all atoms.
- 96 regressive actions, 70 strictly ineffective actions, and 37
  historical-best submissions.

Fixed admission status:

- 9/10 completed.
- 0/10 failed unsubmitted.
- 1/10 active: `phase3_ep_149`.
- 0/10 not yet admitted.

SFT reconciliation:

- 847 labeled records.
- 490 canonical targets.
- 357 context-only records.
- 77 harmful, 72 ineffective, 144 query-Skill, and 64 rejected raw records
  remain excluded from target loss.
- All mask, canonical-target, execution-profile, context/score-contract, and
  prompt-split invariants passed.

Infrastructure:

- Mean 5.92/8 active HCUs, median six, zero all-idle samples.
- No continuous-queue OOM, API timeout, connection error, rate-limit error,
  evaluator gap, invalid lineage, future leakage, credential text, or backend
  mismatch.

Prospective v8 validation:

- Teacher system prompt version:
  `teacher_system_prompt_v8_retry_closure_policy`.
- Runtime rejects identical action/source/target retries after regression or
  strict no-progress.
- Edit defaults to reducer-best; another historical source needs relevant
  passed-constraint evidence absent from best.
- Action protocol, PlannerContext, score policy, routing, completed history,
  and SFT ownership are unchanged.
- 79 contract tests, 133 unit tests, 12 schemas, 104 fixtures, and historical
  replay pass.
- The first valid v8 submission is outside the frozen checkpoint-150 cohort;
  no v8 outcome claim is made here.

## Questions

1. Is there any remaining data-validity, protocol, memory, SFT-boundary,
   evaluator, routing, cohort, or future-leakage blocker at checkpoint 150?
2. Do the final v7 baseline and cumulative SFT results indicate a wrong
   direction or major risk, and is the v7/v8 policy boundary handled
   correctly?
3. Should the queue continue under v8 unchanged, continue with a specific
   prospective correction, or stop?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Answer the three questions directly. Distinguish data-validity blockers from
optional planner-quality, SFT, or throughput improvements.
