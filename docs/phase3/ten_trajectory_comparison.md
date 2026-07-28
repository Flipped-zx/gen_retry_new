# Phase 3 Ten-Trajectory Comparison

All ten rows below are fresh-start live trajectories. Smoke outputs and archived invalid infrastructure runs are not counted as Phase 3 episodes.

| Episode | Attempts | Best | Submitted | Reason | Best Pass | Raw Errors | Behaviors |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| `phase3_ep_001` | 5 | `a_001` | `a_001` | `best_available_under_budget` | 6/11 | 5 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_002` | 5 | `a_000` | `a_000` | `best_available_under_budget` | 5/11 | 4 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_003` | 5 | `a_001` | `a_001` | `best_available_under_budget` | 8/11 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_004` | 5 | `a_001` | `a_001` | `best_available_under_budget` | 3/11 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_005` | 5 | `a_001` | `a_001` | `best_available_under_budget` | 6/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_006` | 5 | `a_002` | `a_002` | `best_available_under_budget` | 4/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_007` | 5 | `a_002` | `a_002` | `best_available_under_budget` | 7/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_008` | 5 | `a_000` | `a_000` | `best_available_under_budget` | 7/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_009` | 5 | `a_000` | `a_000` | `best_available_under_budget` | 6/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_010` | 4 | `a_003` | `a_003` | `all_constraints_passed` | 10/10 | 0 | `all_constraints_passed`, `constraint_regression`, `historical_branch`, `local_edit_used`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |

## Excluded Invalid Runs

| Run | Latest Event | Counted |
| --- | --- | --- |
| `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` | `image_execution_started` | no |
