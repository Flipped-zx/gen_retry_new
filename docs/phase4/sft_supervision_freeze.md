# Phase 4 SFT Supervision Freeze

## Scope

This freeze is derived from the ten fresh Phase 3 live trajectories, Gate 2
approval, and the v0.5 Sol amendment. It defines the training message shape,
target selection, loss mask, split policy, and dry-run validation for new native
v0.5 records.

## Message Format

Training and inference use the same renderer:

| Role | Content | Loss |
| --- | --- | ---: |
| `system` | Fixed Gen-Retry v0.5 planner contract | 0 |
| `user` | Canonical PlannerContext, visible image references, and response contract | 0 |
| `assistant` | Canonical action JSON, only for selected targets | 1 |

The renderer is implemented in `gen_retry.sft.supervision.render_messages`.

Raw teacher output, raw tool payloads, Geneval2 observations, and
environment-owned facts are never assistant targets. Environment facts are
exposed only through canonical PlannerContext.

## Assistant Target

The exact target text is deterministic canonical JSON for one native action
matching `action_protocol_v0.5`.

Allowed final target actions in this freeze:

- `generate_image`
- `edit_image`
- `submit_attempt`

`query_skill` remains a real Planner Action but has loss 0 until
capability-isolated Skill utility is accepted.

## Label Policy

| Phase 3 label | Phase 4 handling |
| --- | --- |
| `trainable_positive` | target only if action is targetable |
| `recovery_positive` | target only if action is targetable |
| `history_only_harmful` | context/audit only |
| `history_only_ineffective` | context/audit only |
| `excluded_ambiguous` | context/audit only |
| `excluded_invalid` | audit only |

Harmful and ineffective actions may appear in history to explain a later recovery target, but they are not positive targets.

## Image And History Context

Visible image references are carried from the planner request and point to
run-relative image artifacts. The renderer keeps latest and best image
references when present.

Attempt history is the canonical compact history from PlannerContext.
Best-so-far, transition, remaining budget, and atom status are
environment-owned context, not model targets.

## Split

Prompt groups are split by stable SHA-256 of the original prompt:

- train: 8 prompt groups
- validation: 1 prompt group
- test: 1 prompt group

The split manifest is `artifacts/phase4/sft_split_manifest.json`. No prompt group crosses splits.

## Budget And Truncation

Dry-run token estimates use `ceil(characters/4)`.

- max context budget: 24,000 estimated tokens
- max target budget: 1,400 estimated tokens
- truncation order for future larger datasets: drop oldest non-visible history first; keep TaskSpec, latest attempt, best attempt, and visible images.

No Phase 4 dry-run record required truncation.

## Historical Dry-Run Result

The following result was produced under the older Phase 4 policy and is retained
for audit. It is not a native v0.5 dataset export; old canonical actions are
context-only under the v0.5 renderer.

Command:

```bash
python -m gen_retry.cli.phase4_sft_dry_run
```

Result:

- input labeled records: 78
- final target records: 28
- context-only records: 50
- target actions: 16 `generate_image`, 2 `edit_image`, 10 `submit_attempt`
- raw rejected turns targeted: 0
- query-skill actions targeted: 0
- loss-mask violations: 0
- prompt split violations: 0

Detailed artifacts:

- `artifacts/phase4/sft_supervision_policy.json`
- `artifacts/phase4/sft_dry_run_decisions.jsonl`
- `artifacts/phase4/sft_dry_run_records.jsonl`
- `artifacts/phase4/sft_dry_run_audit.json`
- `docs/phase4/sft_export_dry_run_report.md`
