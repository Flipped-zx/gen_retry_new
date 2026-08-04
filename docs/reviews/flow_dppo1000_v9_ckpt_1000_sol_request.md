# Flow-DPPO 1000 v9 Final Sol Review Request

## Gate

`Flow-DPPO 1000 v9 final batch review`

## Decision To Review

Decide whether the completed 1000-trajectory batch is a valid, useful
trajectory pool that may proceed to the separate Gate-3 supervision audit, or
whether a data-integrity, policy-direction, or claim-validity issue blocks its
use. This review does not freeze an SFT export.

## Current Evidence

- Deterministic audit: `PASS`, 1000 submitted episodes and 3443 image
  Attempts; start/completion/image/Geneval2 counts all equal 3443.
- Resume scheduler exit: `0`; no active rollout worker, no orphan image or
  half-written Attempt, and no `STOP_ADMISSION` file.
- Frozen mix: 375 easy, 375 medium, 250 hard; 6937 atom slots.
- Atom pass rate: `79.86% -> 90.85%`, net `+762` passed atoms.
- Geneval2 Soft-TIFA AM: `80.60 -> 90.25`.
- Submitted Geneval2 Soft-TIFA GM: `40.32 -> 71.14`; post-hoc per-episode
  GM peak is `72.30`, so the submitted-to-peak gap is `1.16` points.
- All-pass: `552/1000`; 260 were direct first-attempt successes and 292
  reached all-pass after retry.
- Difficulty submitted GM: easy `83.29`, medium `70.36`, hard `54.08`.
- Submitted atom pass by type: object `99.37%`, attribute `93.54%`, position
  `89.57%`, count `83.41%`, verb `40.74%`.
- Actions: 1174 generate, 2269 edit, 1051 query-Skill, 1000 submit.
- Retry exposure: 2443 post-initial image actions; 749 contain regression,
  547 are strict no-progress under the deterministic audit rule, and 1293
  become reducer-best.
- Source/submission containment: 2168/2269 edits use reducer-best; 657
  historical edit branches; 316 episodes submit historical best rather than
  latest.
- Uniform provenance: Action Protocol `0.5`, PlannerContext `0.7`, Teacher
  prompt `teacher_system_prompt_v9_meaningful_retry_verb_retention`, Teacher
  `gpt-5.5`, execution profile `qwen_dual_backend@1`, score policy
  `geneval2_pass_count_then_gm@1` for all 1000 episodes.
- Linter is advisory: among canonical image Actions with metadata, verdicts
  are 2998 pass, 91 warn, 290 reject. At least 169 reject-verdict Actions are
  initial/new-best outcomes, so verdict alone cannot define positive SFT
  inclusion. The 13 historical hard rejections occur only in episodes 001-020;
  episodes 021-1000 created zero `instruction_quality_rejected` repair turns.
- Audit verifies point-in-time PlannerContext snapshots, legal source lineage,
  reducer-best submission, closed manifests, and zero credential-like output.
- The v9 SFT compatibility/outcome audit and Gate-3 export freeze remain open;
  harmful/ineffective Actions, raw errors, evaluator/tool observations, and
  query-Skill remain context-only by current policy.

Primary evidence:

- `artifacts/phase7/checkpoints/flow_dppo1000_v9_ckpt_1000_audit.json`
- `docs/phase7/checkpoints/flow_dppo1000_v9_ckpt_1000_audit.md`
- `docs/phase7/meaningful_retry_sft_v9_design.md`
- `docs/decisions/ADR-0008-meaningful-retry-rollout-policy.md`
- `docs/decisions/ADR-0009-advisory-instruction-quality-linter.md`

## Questions (Max 3)

1. Do the aggregate, difficulty-stratified, and constraint-type results support
   accepting this as a useful trajectory pool, while keeping submitted GM
   separate from the post-hoc peak and from official leaderboard claims?
2. Do the regression/no-progress, source-selection, linter, query-Skill, and
   resume findings expose any blocking protocol or data-integrity issue, or are
   they non-blocking inputs to post-hoc supervision filtering?
3. What exact boundary should be stated between accepting the canonical 1k
   trajectories and declaring them ready for positive SFT export under v9?

## Explicit Non-Goals

- Do not modify or rerun completed trajectories.
- Do not redesign the action schema, reducer, score policy, generator, or
  evaluator in this review.
- Do not treat the synthetic Flow-DPPO train-prompt batch as an official
  Geneval2 leaderboard evaluation.
- Do not freeze Gate 3 merely because the rollout audit passed.

## Expected Response

- `PASS_TRAJECTORY_POOL`, `PASS_WITH_BLOCKED_SFT_EXPORT`, or
  `FAIL_DATASET_BLOCKER`;
- direct answers to all three questions;
- blocking issues separated from required pre-SFT work and optional analysis.
