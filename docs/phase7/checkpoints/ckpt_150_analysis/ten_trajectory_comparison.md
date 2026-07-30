# Phase 3 10-Trajectory Comparison

All 10 rows below are fresh-start live trajectories. Smoke outputs and archived invalid infrastructure runs are not counted.

| Episode | Attempts | Best | Submitted | Reason | Best Pass | Raw Errors | Behaviors |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| `phase3_ep_138` | 5 | `a_001` | `a_001` | `best_available_under_budget` | 2/4 | 0 | `best_so_far_recovery`, `budget_exhausted`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy` |
| `phase3_ep_140` | 5 | `a_004` | `a_004` | `best_available_under_budget` | 6/6 | 2 | `all_constraints_passed`, `budget_exhausted`, `constraint_regression`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_142` | 5 | `a_004` | `a_004` | `best_available_under_budget` | 7/8 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_branch`, `local_edit_used`, `persistent_failure`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_143` | 5 | `a_003` | `a_003` | `best_available_under_budget` | 9/10 | 1 | `best_so_far_recovery`, `budget_exhausted`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `repeated_ineffective_strategy` |
| `phase3_ep_144` | 5 | `a_003` | `a_003` | `best_available_under_budget` | 9/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_146` | 5 | `a_004` | `a_004` | `best_available_under_budget` | 4/4 | 0 | `all_constraints_passed`, `budget_exhausted`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_148` | 2 | `a_001` | `a_001` | `all_constraints_passed` | 6/6 | 0 | `all_constraints_passed`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_153` | 1 | `a_000` | `a_000` | `all_constraints_passed` | 4/4 | 0 | `all_constraints_passed`, `direct_success` |
| `phase3_ep_156` | 2 | `a_001` | `a_001` | `all_constraints_passed` | 6/6 | 0 | `all_constraints_passed`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_158` | 3 | `a_002` | `a_002` | `all_constraints_passed` | 8/8 | 0 | `all_constraints_passed`, `local_edit_used`, `regeneration_used`, `target_constraint_fixed` |

## Excluded Invalid Runs

| Run | Latest Event | Counted |
| --- | --- | --- |
| `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` | `image_execution_started` | no |
