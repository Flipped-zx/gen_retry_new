# Phase 3 SFT Candidate Action Report

- Episodes analyzed: 20
- Canonical actions labeled: 136
- Raw rejected turns labeled excluded: 28
- SFT candidate actions: 59
- Valid query_skill actions retained with loss 0: 24

## Label Counts

| Label | Count |
| --- | ---: |
| `trainable_positive` | 68 |
| `recovery_positive` | 15 |
| `history_only_harmful` | 24 |
| `history_only_ineffective` | 29 |
| `excluded_ambiguous` | 0 |
| `excluded_invalid` | 28 |

## Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 63 |
| `generate_image` | 29 |
| `invalid_raw_output` | 28 |
| `query_skill` | 24 |
| `submit_attempt` | 20 |

## SFT Policy

Use only native v0.5 `generate_image`, `edit_image`, and `submit_attempt` actions labeled `trainable_positive` or `recovery_positive` as candidate targets. Keep `query_skill` actions and linked tool responses at loss 0 until Skill utility validation is accepted. Harmful, ineffective, ambiguous, invalid, Geneval2, and raw teacher records remain context or audit evidence only.
