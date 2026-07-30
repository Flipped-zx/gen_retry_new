# Phase 4 SFT Export Dry Run

- Policy: `phase4_sft_supervision_freeze_v0.6`
- Input labeled records: 554
- Canonical labeled actions: 504
- Raw rejected turns kept context-only: 50
- Target records emitted: 328
- Context-only records: 226
- Gate 2 validation experiment: PASS

## Target Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 116 |
| `generate_image` | 112 |
| `submit_attempt` | 100 |

## Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `label_history_only_harmful_context_only` | 40 |
| `label_history_only_ineffective_context_only` | 39 |
| `positive_or_recovery_canonical_action` | 328 |
| `query_skill_context_only_until_utility_validated` | 97 |
| `raw_teacher_output_excluded` | 50 |

## Split Counts

| Split | Prompt Groups |
| --- | ---: |
| `test` | 20 |
| `train` | 160 |
| `validation` | 20 |

## Token Estimate Percentiles

| Segment | p50 | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| context | 1862 | 2174 | 2241 | 3089 |
| target | 258 | 413 | 446 | 590 |

## Mask Invariants

- System and user messages have loss weight 0.
- Assistant messages have loss weight 1 only for selected canonical action targets.
- `query_skill` assistant actions and linked tool responses have loss weight 0 until Skill utility is validated.
- Raw teacher output, format errors, Geneval2 observations, harmful actions, and ineffective actions are context-only.
