# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 5 | `phase3_ep_041`, `phase3_ep_043`, `phase3_ep_044`, `phase3_ep_045`, `phase3_ep_049` |
| `regeneration_used` | 3 | `phase3_ep_042`, `phase3_ep_047`, `phase3_ep_048` |
| `local_edit_used` | 5 | `phase3_ep_042`, `phase3_ep_046`, `phase3_ep_047`, `phase3_ep_048`, `phase3_ep_050` |
| `target_constraint_fixed` | 4 | `phase3_ep_046`, `phase3_ep_047`, `phase3_ep_048`, `phase3_ep_050` |
| `constraint_regression` | 2 | `phase3_ep_046`, `phase3_ep_048` |
| `persistent_failure` | 2 | `phase3_ep_042`, `phase3_ep_047` |
| `repeated_ineffective_strategy` | 2 | `phase3_ep_042`, `phase3_ep_046` |
| `historical_branch` | 2 | `phase3_ep_042`, `phase3_ep_046` |
| `best_so_far_recovery` | 2 | `phase3_ep_042`, `phase3_ep_046` |
| `historical_best_submission` | 1 | `phase3_ep_042` |
| `all_constraints_passed` | 8 | `phase3_ep_041`, `phase3_ep_043`, `phase3_ep_044`, `phase3_ep_045`, `phase3_ep_046`, `phase3_ep_048`, `phase3_ep_049`, `phase3_ep_050` |
| `budget_exhausted` | 4 | `phase3_ep_042`, `phase3_ep_046`, `phase3_ep_047`, `phase3_ep_048` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 8 trajectories reached all atom constraints.
