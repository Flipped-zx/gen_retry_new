# Phase 4 SFT Export Dry Run

- Policy: `phase4_sft_supervision_freeze_v0.6`
- Input labeled records: 847
- Canonical labeled actions: 783
- Raw rejected turns kept context-only: 64
- Target records emitted: 490
- Context-only records: 357
- Gate 2 validation experiment: PASS

## Target Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 171 |
| `generate_image` | 169 |
| `submit_attempt` | 150 |

## Exclusion Reasons

| Reason | Count |
| --- | ---: |
| `label_history_only_harmful_context_only` | 77 |
| `label_history_only_ineffective_context_only` | 72 |
| `positive_or_recovery_canonical_action` | 490 |
| `query_skill_context_only_until_utility_validated` | 144 |
| `raw_teacher_output_excluded` | 64 |

## Split Counts

| Split | Prompt Groups |
| --- | ---: |
| `test` | 20 |
| `train` | 160 |
| `validation` | 20 |

## Token Estimate Percentiles

| Segment | p50 | p90 | p95 | max |
| --- | ---: | ---: | ---: | ---: |
| context | 1868 | 2177 | 2241 | 3089 |
| target | 256 | 414 | 452 | 590 |

## Mask Invariants

- System and user messages have loss weight 0.
- Assistant messages have loss weight 1 only for selected canonical action targets.
- `query_skill` assistant actions and linked tool responses have loss weight 0 until Skill utility is validated.
- Raw teacher output, format errors, Geneval2 observations, harmful actions, and ineffective actions are context-only.
