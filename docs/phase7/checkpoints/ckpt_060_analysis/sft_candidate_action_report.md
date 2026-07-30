# Phase 3 SFT Candidate Action Report

- Episodes analyzed: 10
- Canonical actions labeled: 56
- Raw rejected turns labeled excluded: 1
- SFT candidate actions: 33
- Valid query_skill actions retained with loss 0: 10

## Label Counts

| Label | Count |
| --- | ---: |
| `trainable_positive` | 38 |
| `recovery_positive` | 5 |
| `history_only_harmful` | 10 |
| `history_only_ineffective` | 3 |
| `excluded_ambiguous` | 0 |
| `excluded_invalid` | 1 |

## Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 23 |
| `generate_image` | 13 |
| `invalid_raw_output` | 1 |
| `query_skill` | 10 |
| `submit_attempt` | 10 |

## SFT Policy

Use only native v0.5 `generate_image`, `edit_image`, and `submit_attempt` actions labeled `trainable_positive` or `recovery_positive` as candidate targets. Keep `query_skill` actions and linked tool responses at loss 0 until Skill utility validation is accepted. Harmful, ineffective, ambiguous, invalid, Geneval2, and raw teacher records remain context or audit evidence only.

`history_only_ineffective` is an action-level supervision label evaluated with the episode's frozen pass-count/primary-GM ordering. The rollout audit's `ineffective image actions` is a narrower operational count: no fixed atom, no regressed atom, and no reducer-best update. The two counts therefore need not match.
