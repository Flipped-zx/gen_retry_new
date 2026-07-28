# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 0 | - |
| `regeneration_used` | 0 | - |
| `local_edit_used` | 1 | `phase3_ep_001` |
| `target_constraint_fixed` | 0 | - |
| `constraint_regression` | 1 | `phase3_ep_001` |
| `persistent_failure` | 1 | `phase3_ep_001` |
| `repeated_ineffective_strategy` | 1 | `phase3_ep_001` |
| `historical_branch` | 1 | `phase3_ep_001` |
| `best_so_far_recovery` | 1 | `phase3_ep_001` |
| `historical_best_submission` | 1 | `phase3_ep_001` |
| `all_constraints_passed` | 0 | - |
| `budget_exhausted` | 1 | `phase3_ep_001` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission appears when the policy submits an earlier best attempt after later edits or regenerations regress. Constraint regression and repeated ineffective strategy are common enough to supply negative history-only examples, while one trajectory reached all atom constraints before budget exhaustion.
