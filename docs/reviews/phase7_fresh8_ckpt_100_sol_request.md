# Phase 7 Fresh-8 Checkpoint 100 Sol Review Request

## Gate

`50-trajectory deep review at cumulative checkpoint 100`

## Scope

Review the completed-quality cohort, the prospectively fixed admission-status
cohort, cumulative SFT reconciliation, and resource evidence. The continuous
queue remains active. Do not edit files, invoke Teacher/Qwen/Geneval2, inspect
credentials, or treat rejected raw turns as canonical actions.

## Frozen Contracts

- PlannerContext `0.6`
- Action protocol `0.5`
- Score policy `geneval2_pass_count_then_gm@1`
- Execution profile `qwen_dual_backend@1`
- At most five image attempts
- Skill responses and evaluator outcomes are context-only for SFT

## Cohort Semantics

The checkpoint-80 review required separating quality from admitted-work
status. That prospective change is implemented:

- predeclaration:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_100_predeclared_cohorts.json`
- completed-quality cohort:
  `artifacts/phase7/checkpoints/fresh8_v1_ckpt_100_completed_quality_cohort.json`
- fixed admission-status denominator:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_100_admission_status.md`

Quality metrics are explicitly completion-conditioned. Operational status uses
the complete fixed ID range 61-100 and includes incomplete work.

## Evidence

- 40-trajectory completed quality audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_100_quality_cohort_audit.md`
- 100-trajectory completed quality audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_100_cumulative_audit.md`
- Fixed admission-status denominator:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_100_admission_status.md`
- Behavior labels:
  `docs/phase7/checkpoints/ckpt_100_analysis/sft_candidate_action_report.md`
- Trajectory comparison:
  `docs/phase7/checkpoints/ckpt_100_analysis/trajectory_comparison.md`
- Cumulative SFT labels:
  `docs/phase7/checkpoints/ckpt_100_cumulative_analysis/sft_candidate_action_report.md`
- SFT dry-run reconciliation:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_100_sft_reconciliation.md`
- Resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_100_resource_profile.md`
- Prior review:
  `docs/reviews/phase7_fresh8_ckpt_080_sol_review.md`
- Accepted dual-backend decision:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`
- Current module contracts:
  `docs/architecture/MODULE_CONTRACTS.md`

Completed-quality results:

- 100/100 valid submissions; 307 complete image/evaluator attempts.
- Atom pass improved from 591/713 to 666/713.
- Soft-TIFA AM improved from 83.59 to 92.71.
- Soft-TIFA GM improved from 48.38 to 78.71.
- Per-trajectory peak GM is 79.20; submitted-to-peak gap is 0.49.
- 67/100 reached all atoms.
- 19 historical-best submissions, 44 historical edit branches, 52 regressive
  actions, and 40 strictly ineffective actions.
- 50 rejected raw Teacher turns, all instruction-quality-invalid and excluded
  from canonical/SFT targets.

Fixed admission-status results at the snapshot:

- 36/40 completed.
- 1/40 failed unsubmitted: `phase3_ep_069`, preserved for pending-only resume.
- 3/40 active: `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`.
- 0/40 not yet admitted.

SFT reconciliation:

- 554 labeled records.
- 328 canonical targets.
- 226 context-only records.
- 40 harmful, 39 ineffective, 97 query-Skill, and 50 rejected raw records
  remain excluded from target loss.
- All mask, profile, score-contract, and split invariants passed.

Infrastructure:

- Mean 5.94/8 active HCUs, median 6, zero all-idle samples.
- No OOM, API timeout, connection error, rate limit, evaluator gap, invalid
  lineage, future leakage, credential text, or backend mismatch.

## Questions

1. Does the completed-quality/admission-status split now resolve the
   checkpoint-80 selection-bias concern, and is there any remaining protocol,
   memory, SFT-boundary, evaluator, routing, or future-leakage blocker?
2. Do the 100-trajectory quality, behavior, rejection, recovery, and SFT
   results indicate a wrong direction or a major risk requiring prospective
   policy change?
3. Should new admission continue unchanged, continue with a prospective
   non-destructive correction, or stop?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Answer the three questions directly. Distinguish data-validity blockers from
optional planner-quality, SFT, or throughput improvements.
