# Phase 7 Fresh-8 Checkpoint 120 Sol Review Request

## Gate

`20-trajectory cadence light review at cumulative checkpoint 120`

## Scope

Review the 20-trajectory completed-quality increment, the cumulative
120-trajectory quality audit, and the fixed ID 101-120 admission-status
denominator. The continuous queue remains active. Do not edit files, invoke
Teacher/Qwen/Geneval2, inspect credentials, or treat rejected raw turns as
canonical actions.

## Frozen Contracts

- PlannerContext `0.6`
- Action protocol `0.5`
- Score policy `geneval2_pass_count_then_gm@1`
- Execution profile `qwen_dual_backend@1`, accepted by ADR-0006
- At most five image attempts
- Skill responses and evaluator outcomes are context-only for SFT

## Evidence

- Predeclaration:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_120_predeclared_cohorts.json`
- Completed-quality increment:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_120_completed_quality_increment.json`
- Increment audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_120_quality_increment_audit.md`
- Cumulative audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_120_cumulative_audit.md`
- Fixed admission-status denominator:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_120_admission_status.md`
- Behavior labels:
  `docs/phase7/checkpoints/ckpt_120_analysis/sft_candidate_action_report.md`
- Trajectory comparison:
  `docs/phase7/checkpoints/ckpt_120_analysis/trajectory_comparison.md`
- Resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_120_resource_profile.md`
- Accepted routing decision:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`
- Prior deep review:
  `docs/reviews/phase7_fresh8_ckpt_100_sol_review.md`

Increment results:

- 20/20 valid submissions; 65 complete image/evaluator attempts.
- Atom pass improved from 111/136 to 123/136.
- Soft-TIFA AM improved from 81.07 to 89.84.
- Soft-TIFA GM improved from 53.10 to 76.37.
- Submitted-to-peak GM gap is 0.00.
- 11/20 reached all atoms.
- Six historical-best submissions, ten historical edit branches, 15
  regressive actions, and 13 strictly ineffective image actions.
- Four raw Teacher turns were rejected for instruction quality; none remain
  protocol/reference-invalid.

Cumulative results:

- 120/120 valid submissions; 372 attempts.
- Submitted atoms 789/849 (92.9%), up 87 from first attempts.
- Submitted GM 78.32, up 29.15; submitted-to-peak gap 0.41.
- 78/120 all-pass episodes.

Fixed admission-status results:

- 16/20 completed.
- 0/20 failed unsubmitted.
- 4/20 active: episodes 116-119.
- 0/20 not yet admitted.

Infrastructure:

- Mean 5.84/8 active HCUs, median 6, zero all-idle samples.
- No OOM, API timeout, connection error, rate limit, evaluator gap, invalid
  lineage, future leakage, credential text, or backend mismatch.

## Questions

1. Is the quality/status split still correctly scoped, and is there any new
   protocol, memory, SFT-boundary, routing, evaluator, or future-leakage
   blocker?
2. Do the increment's lower all-pass rate, regressions, ineffective actions,
   or residual failures indicate a wrong direction or a major risk?
3. Should the queue proceed unchanged to checkpoint 140, proceed with a
   prospective correction, or stop new admission?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Answer all three questions directly and distinguish blockers from optional
quality or throughput improvements.
