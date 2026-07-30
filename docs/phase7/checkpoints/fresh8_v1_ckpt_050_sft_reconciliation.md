# Phase 4 SFT Export Dry Run

- Policy: `phase4_sft_supervision_freeze_v0.6`
- Input labeled records: 281
- Canonical labeled actions: 245
- Raw rejected turns kept context-only: 36
- Target records emitted: 164
- Context-only records: 117
- Gate 2 validation experiment: PASS

## Target Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 58 |
| `generate_image` | 56 |
| `submit_attempt` | 50 |

## Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `label_history_only_harmful_context_only` | 10 |
| `label_history_only_ineffective_context_only` | 24 |
| `positive_or_recovery_canonical_action` | 164 |
| `query_skill_context_only_until_utility_validated` | 47 |
| `raw_teacher_output_excluded` | 36 |

## Split Counts

| Split | Prompt Groups |
| --- | ---: |
| `test` | 20 |
| `train` | 160 |
| `validation` | 20 |

## Token Estimate Percentiles

| Segment | p50 | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| context | 1860 | 2170 | 2231 | 3030 |
| target | 262 | 413 | 456 | 518 |

## Mask Invariants

- System and user messages have loss weight 0.
- Assistant messages have loss weight 1 only for selected canonical action targets.
- `query_skill` assistant actions and linked tool responses have loss weight 0 until Skill utility is validated.
- Raw teacher output, format errors, Geneval2 observations, harmful actions, and ineffective actions are context-only.
