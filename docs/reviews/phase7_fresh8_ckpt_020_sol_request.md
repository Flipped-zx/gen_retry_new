# Phase 7 Fresh-8 Checkpoint 20 Sol Review Request

## Gate

`20-trajectory light review during the fresh 200-trajectory rollout`

## Scope

Review only the first 20 submitted episodes in:

`runs/phase7_flow_dppo200_fresh8_v1/phase3_ep_001` through
`phase3_ep_020`.

The next range is already running concurrently. Do not edit files, invoke
Teacher/Qwen/Geneval2, or inspect credentials.

## Frozen Contracts

- PlannerContext: `0.6`
- Action protocol: `0.5`
- Score policy: `geneval2_pass_count_then_gm@1`
- Execution profile: `qwen_dual_backend@1`
- `generate_image` uses local Qwen-Image without a source.
- `edit_image` uses local Qwen-Image-Edit with an explicit source.
- Maximum image attempts: 5.
- Query-Skill records remain context-only for SFT.

## Evidence

- Deterministic audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_020_audit.md`
- Behavior coverage:
  `docs/phase7/checkpoints/ckpt_020_analysis/behavior_coverage_report.md`
- SFT labels:
  `docs/phase7/checkpoints/ckpt_020_analysis/sft_candidate_action_report.md`
- Per-episode comparison:
  `docs/phase7/checkpoints/ckpt_020_analysis/trajectory_comparison.md`

Headline results:

- 20/20 submitted; 52 image attempts; 52 complete Geneval2 evaluations.
- Submitted atom pass rate: 141/144 (97.9%), up 16 atoms from first attempts.
- Submitted Soft-TIFA AM: 96.05, up 10.72.
- Submitted Soft-TIFA GM: 89.89, up 35.93.
- Submitted-to-per-trajectory-peak GM gap: 0.00.
- 17/20 episodes reached all atoms.
- Three regressive and five ineffective image actions remain in history.
- Five historical branches and four best-recovery behaviors were observed.
- Thirteen raw Teacher turns were rejected for instruction quality before
  execution; none were protocol/reference-invalid under the corrected
  validator, and none are eligible SFT targets.
- No OOM, incomplete evaluator result, invalid lineage, future-state
  PlannerContext, credential text, or backend-routing mismatch was found.

## Questions

1. Does this checkpoint expose any blocking protocol, memory, SFT-boundary, or
   future-leakage issue?
2. Do the gains, residual failures, regressions, ineffective actions, and
   rejected Teacher turns indicate a wrong direction or a major
   planner/generator/evaluator risk?
3. Should generation continue unchanged through episode 40, or is a
   prospective correction required at the next complete range boundary?

## Expected Response

Return one of:

- `PASS_CONTINUE`
- `PASS_WITH_PROSPECTIVE_CHANGE`
- `STOP_BLOCKING`

Give direct answers to the three questions. Distinguish a data-validity blocker
from an optional efficiency or policy-quality improvement.
