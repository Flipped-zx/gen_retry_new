# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 2 | `phase3_ep_057`, `phase3_ep_060` |
| `regeneration_used` | 2 | `phase3_ep_051`, `phase3_ep_058` |
| `local_edit_used` | 8 | `phase3_ep_051`, `phase3_ep_052`, `phase3_ep_053`, `phase3_ep_054`, `phase3_ep_055`, `phase3_ep_056`, `phase3_ep_058`, `phase3_ep_059` |
| `target_constraint_fixed` | 8 | `phase3_ep_051`, `phase3_ep_052`, `phase3_ep_053`, `phase3_ep_054`, `phase3_ep_055`, `phase3_ep_056`, `phase3_ep_058`, `phase3_ep_059` |
| `constraint_regression` | 4 | `phase3_ep_051`, `phase3_ep_053`, `phase3_ep_055`, `phase3_ep_059` |
| `persistent_failure` | 4 | `phase3_ep_051`, `phase3_ep_053`, `phase3_ep_055`, `phase3_ep_059` |
| `repeated_ineffective_strategy` | 5 | `phase3_ep_051`, `phase3_ep_053`, `phase3_ep_055`, `phase3_ep_058`, `phase3_ep_059` |
| `historical_branch` | 4 | `phase3_ep_053`, `phase3_ep_055`, `phase3_ep_058`, `phase3_ep_059` |
| `best_so_far_recovery` | 5 | `phase3_ep_051`, `phase3_ep_053`, `phase3_ep_055`, `phase3_ep_058`, `phase3_ep_059` |
| `historical_best_submission` | 3 | `phase3_ep_051`, `phase3_ep_053`, `phase3_ep_059` |
| `all_constraints_passed` | 6 | `phase3_ep_052`, `phase3_ep_054`, `phase3_ep_056`, `phase3_ep_057`, `phase3_ep_058`, `phase3_ep_060` |
| `budget_exhausted` | 5 | `phase3_ep_051`, `phase3_ep_053`, `phase3_ep_055`, `phase3_ep_056`, `phase3_ep_059` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 6 trajectories reached all atom constraints.
