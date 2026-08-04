# Phase 4 SFT Export Dry Run

- Policy: `flow_dppo1000_v9_selective_skill_v1`
- Input labeled records: 5507
- Canonical labeled actions: 5494
- Raw rejected turns kept context-only: 13
- Target records emitted: 4302
- Context-only records: 1205
- Gate 2 validation experiment: PASS

## Target Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 1191 |
| `generate_image` | 1112 |
| `query_skill` | 999 |
| `submit_attempt` | 1000 |

## Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `label_history_only_harmful_context_only` | 601 |
| `label_history_only_ineffective_context_only` | 539 |
| `positive_or_recovery_canonical_action` | 3303 |
| `query_skill_context_only_until_utility_validated` | 52 |
| `query_skill_utility_validated` | 999 |
| `raw_teacher_output_excluded` | 13 |

## Split Counts

| Split | Prompt Groups |
| --- | ---: |
| `test` | 100 |
| `train` | 800 |
| `validation` | 100 |

## Token Estimate Percentiles

| Segment | p50 | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| context | 1869 | 3275 | 3586 | 4626 |
| target | 180 | 427 | 475 | 694 |

## Mask Invariants

- System and user messages have loss weight 0.
- Assistant messages have loss weight 1 only for selected canonical action targets.
- `query_skill` assistant actions and linked tool responses have loss weight 0 until Skill utility is validated.
- Raw teacher output, format errors, Geneval2 observations, harmful actions, and ineffective actions are context-only.
