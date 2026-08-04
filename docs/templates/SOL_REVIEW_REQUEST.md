# SOL_REVIEW_REQUEST

## Gate

`Flow-DPPO 1000 v9 checkpoint 200 deep review`

## Decision to review

Decide whether the active 1000-trajectory queue should continue unchanged,
continue with a non-blocking monitoring requirement, or create
`STOP_ADMISSION` because checkpoint-200 evidence shows a major protocol,
quality, or SFT risk.

## Current evidence

- Deterministic audit: PASS, fixed IDs 001-200, 665 image Attempts.
- Difficulty mix: 75 easy, 75 medium, 50 hard.
- Atom pass rate: initial 80.46%, reducer-best 91.55%; net +155 atoms over
  1397 constraint slots.
- Geneval2 Soft-TIFA GM: initial 38.86, submitted 72.40; +33.54 points.
- Submitted-to-oracle-peak GM gap: 1.47 points.
- All-pass episodes: 120/200.
- 66 episodes contain regression, with 128 regressive image Actions.
- 107 image Actions are strict ineffective/no-progress under the audit rule.
- 123 historical branches; 55 episodes submit a historical best rather than
  latest, indicating reducer-best rollback is active.
- Actions: 231 generate, 434 edit, 214 query_skill, 200 submit.
- The 13 historical instruction-linter format errors all pass the current hard
  runtime contract and carry advisory flags only.
- Prospective advisory metadata observed so far: 654 pass, 21 warn, 56 reject;
  linter verdict is environment metadata and does not determine SFT inclusion.
- Current queue remains active with no `STOP_ADMISSION`.

Primary evidence:

- `docs/phase7/checkpoints/flow_dppo1000_v9_ckpt_0200_audit.md`
- `artifacts/phase7/checkpoints/flow_dppo1000_v9_ckpt_0200_audit.json`
- `docs/decisions/ADR-0008-meaningful-retry-rollout-policy.md`
- `docs/decisions/ADR-0009-advisory-instruction-quality-linter.md`

## Questions (max 3)

1. Do the atom/GM/all-pass gains and small submit-to-peak gap justify
   continuing admission despite the observed regression and ineffective-action
   counts, or is either count evidence of a blocking direction error?
2. Does the current advisory-linter and post-hoc SFT filtering boundary remain
   coherent at this scale, and must any additional metric be collected before
   checkpoint 400?
3. Is there any protocol, leakage, source-selection, Skill-use, or supervision
   risk in the checkpoint evidence that requires `STOP_ADMISSION` now?

## Explicit non-goals

- No schema or runtime-policy redesign during this review.
- No modification or rerun of completed trajectories.
- No claim that 200 synthetic-train prompts are an official leaderboard score.

## Expected response

- `PASS_CONTINUE`, `PASS_CONTINUE_WITH_MONITORING`, or `FAIL_STOP_ADMISSION`;
- direct answer to each question;
- required monitoring separated from optional later analysis;
- only concrete blocking evidence may stop the queue.
