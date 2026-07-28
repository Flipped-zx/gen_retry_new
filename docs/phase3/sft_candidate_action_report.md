# Phase 3 SFT Candidate Action Report

- Episodes analyzed: 10
- Canonical actions labeled: 69
- Raw rejected turns labeled excluded: 9
- SFT candidate actions: 38

## Label Counts

| Label | Count |
| --- | ---: |
| `trainable_positive` | 29 |
| `recovery_positive` | 9 |
| `history_only_harmful` | 28 |
| `history_only_ineffective` | 3 |
| `excluded_ambiguous` | 0 |
| `excluded_invalid` | 9 |

## Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 25 |
| `generate_image` | 24 |
| `invalid_raw_output` | 9 |
| `query_skill` | 10 |
| `submit_attempt` | 10 |

## SFT Policy

Use `trainable_positive` and `recovery_positive` canonical assistant actions as candidate targets. Keep `history_only_harmful`, `history_only_ineffective`, `excluded_ambiguous`, `excluded_invalid`, tool responses, Geneval2 observations, and raw teacher outputs as context or audit evidence only.
