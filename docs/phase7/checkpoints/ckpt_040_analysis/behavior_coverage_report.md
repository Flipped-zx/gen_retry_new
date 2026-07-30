# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 4 | `phase3_ep_027`, `phase3_ep_033`, `phase3_ep_034`, `phase3_ep_039` |
| `regeneration_used` | 3 | `phase3_ep_024`, `phase3_ep_031`, `phase3_ep_038` |
| `local_edit_used` | 16 | `phase3_ep_021`, `phase3_ep_022`, `phase3_ep_023`, `phase3_ep_024`, `phase3_ep_025`, `phase3_ep_026`, `phase3_ep_028`, `phase3_ep_029`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_032`, `phase3_ep_035`, `phase3_ep_036`, `phase3_ep_037`, `phase3_ep_038`, `phase3_ep_040` |
| `target_constraint_fixed` | 12 | `phase3_ep_021`, `phase3_ep_022`, `phase3_ep_023`, `phase3_ep_025`, `phase3_ep_026`, `phase3_ep_028`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_035`, `phase3_ep_037`, `phase3_ep_038`, `phase3_ep_040` |
| `constraint_regression` | 6 | `phase3_ep_022`, `phase3_ep_028`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_038`, `phase3_ep_040` |
| `persistent_failure` | 10 | `phase3_ep_022`, `phase3_ep_024`, `phase3_ep_028`, `phase3_ep_029`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_032`, `phase3_ep_036`, `phase3_ep_038`, `phase3_ep_040` |
| `repeated_ineffective_strategy` | 6 | `phase3_ep_022`, `phase3_ep_024`, `phase3_ep_028`, `phase3_ep_030`, `phase3_ep_036`, `phase3_ep_040` |
| `historical_branch` | 8 | `phase3_ep_022`, `phase3_ep_024`, `phase3_ep_028`, `phase3_ep_029`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_036`, `phase3_ep_040` |
| `best_so_far_recovery` | 9 | `phase3_ep_022`, `phase3_ep_024`, `phase3_ep_028`, `phase3_ep_029`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_032`, `phase3_ep_036`, `phase3_ep_040` |
| `historical_best_submission` | 6 | `phase3_ep_024`, `phase3_ep_028`, `phase3_ep_030`, `phase3_ep_032`, `phase3_ep_036`, `phase3_ep_040` |
| `all_constraints_passed` | 10 | `phase3_ep_021`, `phase3_ep_023`, `phase3_ep_025`, `phase3_ep_026`, `phase3_ep_027`, `phase3_ep_033`, `phase3_ep_034`, `phase3_ep_035`, `phase3_ep_037`, `phase3_ep_039` |
| `budget_exhausted` | 10 | `phase3_ep_022`, `phase3_ep_024`, `phase3_ep_028`, `phase3_ep_029`, `phase3_ep_030`, `phase3_ep_031`, `phase3_ep_032`, `phase3_ep_036`, `phase3_ep_038`, `phase3_ep_040` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 10 trajectories reached all atom constraints.
