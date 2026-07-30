# Phase 3 SFT Candidate Action Report

- Episodes analyzed: 150
- Canonical actions labeled: 783
- Raw rejected turns labeled excluded: 64
- SFT candidate actions: 490
- Valid query_skill actions retained with loss 0: 144

## Label Counts

| Label | Count |
| --- | ---: |
| `trainable_positive` | 567 |
| `recovery_positive` | 67 |
| `history_only_harmful` | 77 |
| `history_only_ineffective` | 72 |
| `excluded_ambiguous` | 0 |
| `excluded_invalid` | 64 |

## Action Counts

| Action | Count |
| --- | ---: |
| `edit_image` | 307 |
| `generate_image` | 182 |
| `invalid_raw_output` | 64 |
| `query_skill` | 144 |
| `submit_attempt` | 150 |

## SFT Policy

Use only native v0.5 `generate_image`, `edit_image`, and `submit_attempt` actions labeled `trainable_positive` or `recovery_positive` as candidate targets. Keep `query_skill` actions and linked tool responses at loss 0 until Skill utility validation is accepted. Harmful, ineffective, ambiguous, invalid, Geneval2, and raw teacher records remain context or audit evidence only.

`history_only_ineffective` is an action-level supervision label evaluated with the episode's frozen pass-count/primary-GM ordering. The rollout audit's `ineffective image actions` is a narrower operational count: no fixed atom, no regressed atom, and no reducer-best update. The two counts therefore need not match.
