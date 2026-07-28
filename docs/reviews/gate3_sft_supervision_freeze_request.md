# SOL_REVIEW_REQUEST

## Gate

`SFT Supervision Freeze`

## Decision to review

Approve the Phase 4 supervision policy as the frozen basis for the first SFT dataset build.

## Current evidence

- Relevant schema/ADR:
  - `schemas/action_protocol_v0_2.schema.json`
  - `schemas/planner_view_v0_2.schema.json`
  - `docs/decisions/ADR-0005-sft-supervision-freeze.md`
  - `docs/phase4/sft_supervision_freeze.md`
- Minimal test/pilot summary:
  - Gate 2 approved in `docs/reviews/gate2_five_trajectory_pilot_review.md`.
  - Phase 3 labels: `artifacts/phase3/action_supervision_labels.jsonl`.
  - Phase 4 dry run: `python -m gen_retry.cli.phase4_sft_dry_run` passed.
  - Dry-run audit: 78 input labels, 28 final target records, 50 context-only records, 0 loss-mask violations, 0 noncanonical targets, 0 prompt split violations.
  - Targeted actions are 16 `generate_image`, 2 `edit_image`, and 10 `submit_attempt`.
  - `query_skill` is context-only until skill content is accepted, addressing the Gate 2 reviewer risk.
- Conflicting evidence, if any:
  - Phase 3 labels marked real `query_skill` interactions as positive candidates, but Phase 4 excludes them from final targets because the skill documents are placeholder-level.
  - Edit target count is low because most edits in the fresh trajectories regressed constraints and are history-only.

## Questions（最多 3 个）

1. Is the action-only target and loss-mask policy sufficient to freeze SFT supervision?
2. Is excluding `query_skill` from final positive targets, despite positive Phase 3 candidate labels, the correct conservative choice for this freeze?
3. Are the split, context rendering, and dry-run audit strong enough to proceed to Phase 5 dataset build without changing protocol semantics?

## Explicit non-goals

- Do not request more live rollouts merely to improve action balance.
- Do not implement Phase 5 dataset build.
- Do not revisit Gate 1 protocol semantics unless this freeze violates them.
- Do not inspect credentials or raw provider headers.

## Expected response

- blocking issues only;
- recommended decision;
- risks and one minimal validation experiment;
- no code implementation.
