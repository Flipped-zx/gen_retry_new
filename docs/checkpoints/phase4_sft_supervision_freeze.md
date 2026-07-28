# Phase 4 Checkpoint — SFT Supervision Freeze

Date: 2026-07-14

Amended: 2026-07-26 for Planner I/O v0.5. The original dry-run counts below are
historical audit results, not native v0.5 target counts.

## Inputs

- Gate 2 review: `docs/reviews/gate2_five_trajectory_pilot_review.md`
- Phase 3 action labels: `artifacts/phase3/action_supervision_labels.jsonl`
- Phase 3 trajectory index: `artifacts/phase3/trajectory_index.json`
- Phase 4 ADR: `docs/decisions/ADR-0005-sft-supervision-freeze.md`

## Frozen Decisions

- Principal target: canonical assistant action JSON.
- Message format: fixed v0.5 `system`, canonical PlannerContext `user`, selected canonical v0.5 action `assistant`.
- Loss mask: assistant target only; all context roles and observations masked.
- Final targetable actions: `generate_image`, `edit_image`, `submit_attempt`.
- `query_skill`: real Planner Action, context-only/loss 0 until Skill utility is accepted.
- Harmful/ineffective/invalid records: context or audit only.
- Split: stable prompt-group SHA-256, with no prompt group crossing splits.

## Dry-Run Result

`python -m gen_retry.cli.phase4_sft_dry_run` passed.

- Input labeled records: 78
- Target records emitted: 28
- Context-only records: 50
- Loss-mask violations: 0
- Noncanonical target violations: 0
- Prompt split violations: 0

## Artifacts

- `artifacts/phase4/sft_supervision_policy.json`
- `artifacts/phase4/sft_dry_run_decisions.jsonl`
- `artifacts/phase4/sft_dry_run_records.jsonl`
- `artifacts/phase4/sft_split_manifest.json`
- `artifacts/phase4/sft_dry_run_audit.json`
- `docs/phase4/sft_export_dry_run_report.md`

## Review Gate

Gate 3 SFT Supervision Freeze is ready for Sol review.
