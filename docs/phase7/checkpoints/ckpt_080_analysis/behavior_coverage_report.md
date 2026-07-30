# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 8 | `phase3_ep_065`, `phase3_ep_074`, `phase3_ep_081`, `phase3_ep_082`, `phase3_ep_084`, `phase3_ep_089`, `phase3_ep_090`, `phase3_ep_091` |
| `regeneration_used` | 1 | `phase3_ep_061` |
| `local_edit_used` | 12 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_066`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_070`, `phase3_ep_071`, `phase3_ep_073`, `phase3_ep_077`, `phase3_ep_083` |
| `target_constraint_fixed` | 11 | `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_066`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_070`, `phase3_ep_071`, `phase3_ep_073`, `phase3_ep_077`, `phase3_ep_083` |
| `constraint_regression` | 4 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_068`, `phase3_ep_083` |
| `persistent_failure` | 5 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_068` |
| `repeated_ineffective_strategy` | 3 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_068` |
| `historical_branch` | 6 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_064`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_083` |
| `best_so_far_recovery` | 7 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_083` |
| `historical_best_submission` | 4 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_068` |
| `all_constraints_passed` | 15 | `phase3_ep_065`, `phase3_ep_066`, `phase3_ep_067`, `phase3_ep_070`, `phase3_ep_071`, `phase3_ep_073`, `phase3_ep_074`, `phase3_ep_077`, `phase3_ep_081`, `phase3_ep_082`, `phase3_ep_083`, `phase3_ep_084`, `phase3_ep_089`, `phase3_ep_090`, `phase3_ep_091` |
| `budget_exhausted` | 6 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_068`, `phase3_ep_070` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 15 trajectories reached all atom constraints.
