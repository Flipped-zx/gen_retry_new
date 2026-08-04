# Gate 3 SFT Supervision Freeze Review Request

## Gate

`Gate 3: Flow-DPPO 1000 v9 selective-skill SFT supervision freeze`

## Decision to review

Review the final 1000-trajectory SFT target policy before the formal Full SFT
launch. The export contains positive and recovery `generate_image`, `edit_image`,
and `submit_attempt` targets. `query_skill` is targetable only when its returned
skill is followed by a positive/recovery image action that overlaps a preserved
or improved constraint; other skill calls remain context-only.

## Evidence

- Source: `runs/phase7_flow_dppo1000_v9_fresh8_v1`, 1000 submitted trajectories.
- Prior deterministic audit: PASS; 5507 labeled actions.
- Candidate labels before the selective-skill pass: 3785 trainable-positive,
  569 recovery-positive, 601 harmful history-only, 539 ineffective history-only,
  and 13 invalid raw outputs.
- Required target invariant: exactly one canonical assistant action, with system
  and user context masked from loss; no evaluator result after the target is
  visible.
- Relevant implementation: `src/gen_retry/sft/supervision.py`,
  `src/gen_retry/sft/llamafactory.py`, and focused tests (25 passed).

## Questions (max 3)

1. Is the utility-linked `query_skill` rule sufficiently conservative and useful
   for cold-start SFT, or should any additional skill targets be admitted?
2. Are positive/recovery image and submit targets, harmful/ineffective history,
   and the loss-mask/context contract coherent for the 1000-trajectory Full SFT?
3. Is there any leakage, split, source-image, or protocol issue that blocks
   freezing this policy for training?

## Explicit non-goals

- No new rollout, evaluator, or image call.
- No redesign of the Action Protocol or runtime policy.
- No LoRA run before the Full SFT has a usable checkpoint.

## Expected response

Return `PASS_FREEZE`, `PASS_FREEZE_WITH_MONITORING`, or `FAIL_HOLD`, answer each
question directly, and list only concrete launch-blocking issues separately from
optional monitoring.
