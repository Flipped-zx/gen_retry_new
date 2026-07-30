# Phase 7 Fresh-8 Checkpoint 50 Sol Review Request

## Gate

`50-trajectory deep review during the fresh 200-trajectory rollout`

## Scope

Review only the 50 submitted episodes in:

`runs/phase7_flow_dppo200_fresh8_v1/phase3_ep_001` through
`phase3_ep_050`.

Episodes 51-200 are running concurrently in one continuous queue. Do not edit
files, invoke Teacher/Qwen/Geneval2, inspect credentials, or reinterpret
rejected raw turns as valid actions.

## Frozen Contracts

- PlannerContext: `0.6`
- Action protocol: `0.5`
- Score policy: `geneval2_pass_count_then_gm@1`
- Execution profile: `qwen_dual_backend@1`
- `generate_image` uses local Qwen-Image without a source.
- `edit_image` uses local Qwen-Image-Edit with an explicit source.
- Maximum image attempts: 5.
- Skill tool responses and evaluator outcomes are context-only, not SFT
  assistant targets.
- Canonical submitted episodes are immutable; a blocking verdict stops only
  new admission.

## Evidence

- Cumulative deterministic audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_050_cumulative_audit.md`
- New range audit:
  `docs/phase7/checkpoints/fresh8_v1_range_041_050_audit.md`
- Behavior coverage:
  `docs/phase7/checkpoints/ckpt_050_analysis/behavior_coverage_report.md`
- SFT labels:
  `docs/phase7/checkpoints/ckpt_050_analysis/sft_candidate_action_report.md`
- Per-episode comparison:
  `docs/phase7/checkpoints/ckpt_050_analysis/ten_trajectory_comparison.md`
- Resource evidence:
  `docs/phase7/checkpoints/fresh8_v1_range_041_050_resource_profile.md`
- Accepted dual-backend semantics:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`

Headline cumulative results:

- 50/50 submitted; 148 image attempts with complete Geneval2 outcomes.
- Submitted atom pass rate: 339/361 (93.9%), up 33 atoms from first attempts.
- Submitted Soft-TIFA AM: 93.23, up 8.94.
- Submitted Soft-TIFA GM: 82.02, up 32.18.
- Per-trajectory peak GM: 82.65; submitted-to-peak gap: 0.63.
- 35/50 episodes reached all atoms.
- Seven historical-best submissions, 20 historical edit branches, and 16
  regressive image actions were preserved in canonical history.
- Twenty-six image actions were strictly ineffective under atom/GM outcome
  labeling.
- Thirty-six raw Teacher turns were rejected for instruction quality before
  image execution; none remain protocol/reference-invalid and none are
  positive SFT candidates.
- No OOM, evaluator incompleteness, invalid lineage, future-state
  PlannerContext, credential text, or backend-routing mismatch was found.

Representative new-range evidence:

- `phase3_ep_046` first had 7/8 atoms. An edit regressed elephant count, the
  Planner rolled back to historical best, then a final local edit fixed toy
  count and submitted 8/8 with GM 99.39.
- `phase3_ep_048` improved from 8/10 and GM 18.19 to 10/10 and GM 97.74 on the
  fifth attempt.
- `phase3_ep_042` remained 3/5 after both historical-source editing and
  source-free regeneration; the history therefore retains useful negative
  action evidence without labeling it positive by default.

## Questions

1. Does the 50-episode evidence expose any blocking protocol, memory,
   SFT-boundary, evaluator, backend-routing, or future-leakage issue?
2. Do the observed recovery paths, regressions, ineffective actions, residual
   failures, and instruction-quality rejections indicate a wrong direction or
   a major risk for the planned SFT data?
3. Should the continuous queue proceed unchanged, proceed with a prospective
   non-destructive correction, or stop new admission?

## Expected Response

Return one of:

- `PASS_CONTINUE_QUEUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Give direct answers to the three questions. Distinguish a data-validity blocker
from an optional planner-quality or throughput improvement.
