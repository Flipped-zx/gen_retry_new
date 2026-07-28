# Phase 4 SFT Export Dry Run

- Policy: `phase4_sft_supervision_freeze_v0.2`
- Input labeled records: 78
- Canonical labeled actions: 69
- Raw rejected turns kept context-only: 9
- Target records emitted: 28
- Context-only records: 50
- Gate 2 validation experiment: PASS

## Target Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 2 |
| `generate_image` | 16 |
| `submit_attempt` | 10 |

## Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `label_history_only_harmful_context_only` | 28 |
| `label_history_only_ineffective_context_only` | 3 |
| `positive_or_recovery_canonical_action` | 28 |
| `query_skill_placeholder_catalog_context_only` | 10 |
| `raw_teacher_output_excluded` | 9 |

## Split Counts

| Split | Prompt Groups |
| --- | ---: |
| `test` | 1 |
| `train` | 8 |
| `validation` | 1 |

## Token Estimate Percentiles

| Segment | p50 | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| context | 1341 | 1676 | 1677 | 1680 |
| target | 162 | 195 | 213 | 250 |

## Mask Invariants

- System and user messages have loss weight 0.
- Assistant messages have loss weight 1 only for selected canonical action targets.
- `query_skill`, raw teacher output, format-error, tool response, Geneval2, harmful, and ineffective records are context-only in this dry run.
