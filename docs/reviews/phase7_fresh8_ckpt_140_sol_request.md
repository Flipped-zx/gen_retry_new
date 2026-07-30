# Phase 7 Fresh-8 Checkpoint 140 Sol Review Request

## Gate

`20-trajectory cadence light review at cumulative checkpoint 140`

## Scope

Review the weaker 20-trajectory completed-quality increment, cumulative
140-trajectory quality, and the fixed ID 121-140 admission-status denominator.
The queue remains active. Do not edit files, invoke Teacher/Qwen/Geneval2,
inspect credentials, or treat rejected raw turns as canonical actions.

## Frozen Contracts

- PlannerContext `0.6`
- Action protocol `0.5`
- Score policy `geneval2_pass_count_then_gm@1`
- Execution profile `qwen_dual_backend@1`, accepted by ADR-0006
- At most five image attempts
- Skill responses and evaluator outcomes are context-only for SFT

## Evidence

- Predeclaration:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_140_predeclared_cohorts.json`
- Completed-quality increment:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_140_completed_quality_increment.json`
- Increment audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_140_quality_increment_audit.md`
- Cumulative audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_140_cumulative_audit.md`
- Fixed admission status:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_140_admission_status.md`
- Behavior labels:
  `docs/phase7/checkpoints/ckpt_140_analysis/sft_candidate_action_report.md`
- Trajectory comparison:
  `docs/phase7/checkpoints/ckpt_140_analysis/trajectory_comparison.md`
- Resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_140_resource_profile.md`
- Accepted routing decision:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`
- Prior review:
  `docs/reviews/phase7_fresh8_ckpt_120_sol_review.md`

Increment results:

- 20/20 valid submissions; 79 complete image/evaluator attempts.
- Difficulty mix: 6 easy, 10 medium, 4 hard.
- Atom pass improved from 124/148 to 135/148.
- Soft-TIFA AM improved from 82.75 to 89.18.
- Soft-TIFA GM improved from 30.63 to 58.59.
- Per-trajectory peak GM is 60.60; submitted-to-peak gap is 2.01.
- 7/20 reached all atoms.
- Nine historical-best submissions, 16 historical edit branches, 23
  regressive actions, and 12 strictly ineffective image actions.
- Seven raw Teacher turns were rejected for instruction quality; none remain
  protocol/reference-invalid.

Cumulative results:

- 140/140 valid submissions; 451 attempts.
- Submitted atoms 924/997 (92.7%), up 98 from first attempts.
- Submitted GM 75.50, up 28.98; submitted-to-peak gap 0.64.
- 85/140 all-pass episodes.

Fixed admission status:

- 18/20 completed.
- 0/20 failed unsubmitted.
- 2/20 active: episodes 138 and 140.
- 0/20 not yet admitted.

Infrastructure:

- Mean 5.89/8 active HCUs, median 6, zero all-idle samples.
- No OOM, API timeout, connection error, rate limit, evaluator gap, invalid
  lineage, future leakage, credential text, or backend mismatch.

## Questions

1. Is there any new protocol, memory, SFT-boundary, routing, evaluator,
   cohort-scope, or future-leakage blocker?
2. Does the drop to 7/20 all-pass, 2.01 GM selection gap, and higher regression
   concentration indicate a wrong direction or require a prospective policy
   correction before more admissions?
3. Should the queue proceed unchanged to checkpoint 150/160, proceed with a
   prospective non-destructive correction, or stop?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Answer all three questions directly and distinguish data-validity blockers
from optional or required planner-quality corrections.
