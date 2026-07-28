# Gate 3 Review — SFT Supervision Freeze

## Verdict

`APPROVE`

## Blocking Issues

None.

## Reviewer Summary

Phase 5 may proceed. The freeze keeps the SFT target action-only: canonical assistant JSON, loss only on selected assistant actions, and no training target for raw teacher output, tool/evaluator observations, environment facts, or rejected turns.

Dry-run evidence:

- 78 input labels
- 28 targets
- 50 context-only records
- 0 loss-mask violations
- 0 noncanonical targets
- 0 split violations
- 28 emitted assistant targets validated against `schemas/action_protocol_v0_2.schema.json`

The `query_skill` decision is conservative and accepted: all ten `query_skill` records are context-only because the skill catalog is placeholder-level.

## Risks To Carry Into Phase 5

- Edit supervision is thin: 2 `edit_image` targets versus 16 `generate_image` and 10 `submit_attempt`.
- `query_skill` remains non-trainable unless a separate skill-catalog review accepts non-placeholder skill content.
- Truncation policy is documented but unexercised because no dry-run record required truncation.
- Phase 5 must use the same renderer and policy shape documented in `docs/phase4/sft_supervision_freeze.md`.

## Minimal Validation Experiment

Before writing the Phase 5 dataset, run one export invariant test over the produced dataset: assert each training sample has exactly one schema-valid assistant canonical action with loss `1`, every system/user/context/tool/evaluator/raw record has loss `0`, no `query_skill` or raw rejected output is targeted, and every sample split matches `artifacts/phase4/sft_split_manifest.json`.
