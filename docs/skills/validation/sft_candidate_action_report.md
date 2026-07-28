# Phase 3 SFT Candidate Action Report

- Episodes analyzed: 1
- Canonical actions labeled: 10
- Raw rejected turns labeled excluded: 0
- SFT candidate actions: 6

## Label Counts

| Label | Count |
| --- | ---: |
| `trainable_positive` | 5 |
| `recovery_positive` | 1 |
| `history_only_harmful` | 1 |
| `history_only_ineffective` | 3 |
| `excluded_ambiguous` | 0 |
| `excluded_invalid` | 0 |

## Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 4 |
| `generate_image` | 1 |
| `query_skill` | 4 |
| `submit_attempt` | 1 |

## SFT Policy

Use `trainable_positive` and `recovery_positive` canonical assistant actions as candidate targets. Keep `history_only_harmful`, `history_only_ineffective`, `excluded_ambiguous`, `excluded_invalid`, tool responses, Geneval2 observations, and raw teacher outputs as context or audit evidence only.
