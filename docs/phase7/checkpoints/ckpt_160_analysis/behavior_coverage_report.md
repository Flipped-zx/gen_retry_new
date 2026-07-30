# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 2 | `phase3_ep_166`, `phase3_ep_169` |
| `regeneration_used` | 4 | `phase3_ep_147`, `phase3_ep_151`, `phase3_ep_154`, `phase3_ep_157` |
| `local_edit_used` | 8 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154`, `phase3_ep_155`, `phase3_ep_157`, `phase3_ep_165` |
| `target_constraint_fixed` | 7 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_154`, `phase3_ep_155`, `phase3_ep_157`, `phase3_ep_165` |
| `constraint_regression` | 5 | `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154`, `phase3_ep_155` |
| `persistent_failure` | 6 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154`, `phase3_ep_155` |
| `repeated_ineffective_strategy` | 6 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154`, `phase3_ep_157` |
| `historical_branch` | 4 | `phase3_ep_149`, `phase3_ep_152`, `phase3_ep_154`, `phase3_ep_157` |
| `best_so_far_recovery` | 5 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154` |
| `historical_best_submission` | 5 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154` |
| `all_constraints_passed` | 4 | `phase3_ep_157`, `phase3_ep_165`, `phase3_ep_166`, `phase3_ep_169` |
| `budget_exhausted` | 6 | `phase3_ep_147`, `phase3_ep_149`, `phase3_ep_151`, `phase3_ep_152`, `phase3_ep_154`, `phase3_ep_155` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 4 trajectories reached all atom constraints.
