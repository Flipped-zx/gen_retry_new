# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 0 | - |
| `regeneration_used` | 0 | - |
| `local_edit_used` | 2 | `phase3_ep_014`, `phase3_ep_098` |
| `target_constraint_fixed` | 2 | `phase3_ep_014`, `phase3_ep_098` |
| `constraint_regression` | 1 | `phase3_ep_014` |
| `persistent_failure` | 1 | `phase3_ep_014` |
| `repeated_ineffective_strategy` | 0 | - |
| `historical_branch` | 0 | - |
| `best_so_far_recovery` | 1 | `phase3_ep_014` |
| `historical_best_submission` | 1 | `phase3_ep_014` |
| `all_constraints_passed` | 1 | `phase3_ep_098` |
| `budget_exhausted` | 1 | `phase3_ep_014` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 1 trajectories reached all atom constraints.
