# Phase 3 SFT Candidate Action Report

- Episodes analyzed: 20
- Canonical actions labeled: 102
- Raw rejected turns labeled excluded: 4
- SFT candidate actions: 57
- Valid query_skill actions retained with loss 0: 17

## Label Counts

| Label | Count |
| --- | ---: |
| `trainable_positive` | 66 |
| `recovery_positive` | 8 |
| `history_only_harmful` | 14 |
| `history_only_ineffective` | 14 |
| `excluded_ambiguous` | 0 |
| `excluded_invalid` | 4 |

## Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 37 |
| `generate_image` | 28 |
| `invalid_raw_output` | 4 |
| `query_skill` | 17 |
| `submit_attempt` | 20 |

## SFT Policy

Use only native v0.5 `generate_image`, `edit_image`, and `submit_attempt` actions labeled `trainable_positive` or `recovery_positive` as candidate targets. Keep `query_skill` actions and linked tool responses at loss 0 until Skill utility validation is accepted. Harmful, ineffective, ambiguous, invalid, Geneval2, and raw teacher records remain context or audit evidence only.

`history_only_ineffective` is an action-level supervision label evaluated with the episode's frozen pass-count/primary-GM ordering. The rollout audit's `ineffective image actions` is a narrower operational count: no fixed atom, no regressed atom, and no reducer-best update. The two counts therefore need not match.
