# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 1 | `phase3_ep_153` |
| `regeneration_used` | 2 | `phase3_ep_138`, `phase3_ep_158` |
| `local_edit_used` | 9 | `phase3_ep_138`, `phase3_ep_140`, `phase3_ep_142`, `phase3_ep_143`, `phase3_ep_144`, `phase3_ep_146`, `phase3_ep_148`, `phase3_ep_156`, `phase3_ep_158` |
| `target_constraint_fixed` | 7 | `phase3_ep_140`, `phase3_ep_142`, `phase3_ep_144`, `phase3_ep_146`, `phase3_ep_148`, `phase3_ep_156`, `phase3_ep_158` |
| `constraint_regression` | 3 | `phase3_ep_140`, `phase3_ep_142`, `phase3_ep_144` |
| `persistent_failure` | 4 | `phase3_ep_138`, `phase3_ep_142`, `phase3_ep_143`, `phase3_ep_144` |
| `repeated_ineffective_strategy` | 4 | `phase3_ep_138`, `phase3_ep_142`, `phase3_ep_143`, `phase3_ep_144` |
| `historical_branch` | 4 | `phase3_ep_138`, `phase3_ep_142`, `phase3_ep_143`, `phase3_ep_144` |
| `best_so_far_recovery` | 4 | `phase3_ep_138`, `phase3_ep_142`, `phase3_ep_143`, `phase3_ep_144` |
| `historical_best_submission` | 3 | `phase3_ep_138`, `phase3_ep_143`, `phase3_ep_144` |
| `all_constraints_passed` | 6 | `phase3_ep_140`, `phase3_ep_146`, `phase3_ep_148`, `phase3_ep_153`, `phase3_ep_156`, `phase3_ep_158` |
| `budget_exhausted` | 6 | `phase3_ep_138`, `phase3_ep_140`, `phase3_ep_142`, `phase3_ep_143`, `phase3_ep_144`, `phase3_ep_146` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 6 trajectories reached all atom constraints.
