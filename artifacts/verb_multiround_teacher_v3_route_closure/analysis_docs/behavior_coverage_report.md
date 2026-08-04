# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 0 | - |
| `regeneration_used` | 2 | `phase3_ep_014`, `phase3_ep_098` |
| `local_edit_used` | 2 | `phase3_ep_014`, `phase3_ep_098` |
| `target_constraint_fixed` | 1 | `phase3_ep_098` |
| `constraint_regression` | 0 | - |
| `persistent_failure` | 1 | `phase3_ep_014` |
| `repeated_ineffective_strategy` | 1 | `phase3_ep_014` |
| `historical_branch` | 1 | `phase3_ep_014` |
| `best_so_far_recovery` | 1 | `phase3_ep_014` |
| `historical_best_submission` | 0 | - |
| `all_constraints_passed` | 1 | `phase3_ep_098` |
| `budget_exhausted` | 1 | `phase3_ep_014` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. No historical-best submission occurred in this checkpoint, although historical-source recovery branches were exercised. Constraint regression and repeated ineffective strategy supply negative history-only examples. 1 trajectories reached all atom constraints.
