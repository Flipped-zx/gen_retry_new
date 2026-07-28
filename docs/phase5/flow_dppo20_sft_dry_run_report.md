# Phase 4 SFT Export Dry Run

- Policy: `phase4_sft_supervision_freeze_v0.5`
- Input labeled records: 164
- Canonical labeled actions: 136
- Raw rejected turns kept context-only: 28
- Target records emitted: 59
- Context-only records: 105
- Gate 2 validation experiment: PASS

## Target Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 16 |
| `generate_image` | 23 |
| `submit_attempt` | 20 |

## Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `label_history_only_harmful_context_only` | 24 |
| `label_history_only_ineffective_context_only` | 29 |
| `positive_or_recovery_canonical_action` | 59 |
| `query_skill_context_only_until_utility_validated` | 24 |
| `raw_teacher_output_excluded` | 28 |

## Split Counts

| Split | Prompt Groups |
| --- | ---: |
| `test` | 2 |
| `train` | 16 |
| `validation` | 2 |

## Token Estimate Percentiles

| Segment | p50 | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| context | 1996 | 2418 | 2507 | 2896 |
| target | 261 | 459 | 470 | 542 |

## Mask Invariants

- System and user messages have loss weight 0.
- Assistant messages have loss weight 1 only for selected canonical action targets.
- `query_skill` assistant actions and linked tool responses have loss weight 0 until Skill utility is validated.
- Raw teacher output, format errors, Geneval2 observations, harmful actions, and ineffective actions are context-only.
