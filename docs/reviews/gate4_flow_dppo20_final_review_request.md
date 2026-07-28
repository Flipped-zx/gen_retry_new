# SOL_REVIEW_REQUEST

## Gate

`Phase 5 Flow-DPPO 20-Trajectory Final Quality / SFT Boundary`

## Decision To Review

Decide whether the completed 20-trajectory batch is valid evidence for the
native Planner I/O v0.5 data pipeline and whether its selected positive actions
may proceed to later SFT dataset assembly under the frozen loss mask.

## Current Evidence

- Frozen protocol and supervision:
  - `schemas/action_protocol_v0_5.schema.json`
  - `schemas/planner_context_v0_5.schema.json`
  - `docs/decisions/ADR-0005-sft-supervision-freeze.md`
- Selection and execution:
  - 12 hard / 5 medium / 3 easy Flow-DPPO training prompts;
  - official 800 test rows and deterministic semantic-family overlaps excluded;
  - 20/20 fresh episodes, 92 evaluated 1024 x 1024/40-step images;
  - two fixed GPU workers, one child per physical device;
  - interrupted image/evaluator suffixes recovered without regenerating valid
    completed attempts.
- Deterministic audit:
  - `docs/phase5/flow_dppo20_validation_report.md`
  - `artifacts/phase5/flow_dppo20_validation_summary.json`
  - 20/20 schema/manifest/lineage/Geneval2/RoundRecord/point-in-time
    PlannerContext/submission/credential checks pass.
- Outcome:
  - first-attempt aggregate 137/200 atoms (68.5%);
  - best aggregate 171/200 atoms (85.5%), +34;
  - 13/20 improve; 4/20 reach all atoms;
  - verb remains weakest at 7/15 best-pass atoms.
- SFT boundary:
  - 59 candidate native v0.5 image/submit actions;
  - 24 `query_skill` actions retained at loss 0;
  - 53 harmful/ineffective image actions and 28 rejected raw turns remain
    context/audit only;
  - no outcome is injected into the action that precedes it.
- Mixed rollout-only Teacher prompt versions:
  - some requests use v4 and later requests use v5 with the static Skill
    catalog;
  - every request records its exact prompt version;
  - every canonical action uses v0.5;
  - the frozen SFT renderer supplies one normalized v0.5 training system
    contract, rather than copying the rollout-only Teacher system prompt.
- Representative complete success:
  - `docs/phase5/flow_dppo20_analysis/trajectory_trace_phase3_ep_011.md`
  - query -> fresh 10/11 -> ineffective edit -> branch from historical best ->
    targeted edit 11/11 -> submit.

## Questions

1. Do the point-in-time audit, source-based lineage, complete evaluator suffix,
   best submission, and representative trace establish that these are valid
   native v0.5 trajectories with no blocking future leakage or resume defect?
2. Is the supervision boundary correct: target only the 59 positive/recovery
   native v0.5 generate/edit/submit actions, while masking `query_skill`,
   rejected raw turns, and harmful/ineffective actions?
3. Does the mixed rollout-only Teacher prompt v4/v5 provenance block use of
   otherwise valid canonical v0.5 targets when the later SFT renderer uses one
   frozen v0.5 system contract? If yes, state the minimum required exclusion;
   do not request rerunning valid trajectories merely for prompt uniformity.

## Explicit Non-Goals

- Do not claim overall model improvement from 20 trajectories.
- Do not activate `query_skill` as an SFT target.
- Do not redesign Qwen-Image-Edit, Geneval2, reward, RL, or the v0.5 schema.
- Do not require rerunning a valid trajectory only to obtain preferred
  behavior.
- Do not invoke live Teacher, Qwen, or Geneval2.

## Expected Response

Return exactly one of:

- `PASS`, with any non-blocking risks; or
- `FAIL`, followed only by concrete blocking issues and the minimum fix.
