# Phase 3 20-Trajectory Comparison

All 20 rows below are fresh-start live trajectories. Smoke outputs and archived invalid infrastructure runs are not counted.

| Episode | Attempts | Best | Submitted | Reason | Best Pass | Raw Errors | Behaviors |
| --- | ---: | --- | --- | --- | ---: | ---: | --- |
| `phase3_ep_159` | 5 | `a_002` | `a_002` | `best_available_under_budget` | 7/9 | 0 | `best_so_far_recovery`, `budget_exhausted`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_160` | 5 | `a_000` | `a_000` | `best_available_under_budget` | 9/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy` |
| `phase3_ep_161` | 5 | `a_000` | `a_000` | `best_available_under_budget` | 3/4 | 1 | `best_so_far_recovery`, `budget_exhausted`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy` |
| `phase3_ep_162` | 5 | `a_003` | `a_003` | `best_available_under_budget` | 3/4 | 0 | `best_so_far_recovery`, `budget_exhausted`, `historical_best_submission`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy` |
| `phase3_ep_163` | 5 | `a_001` | `a_001` | `best_available_under_budget` | 4/5 | 0 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy` |
| `phase3_ep_164` | 4 | `a_003` | `a_003` | `all_constraints_passed` | 6/6 | 0 | `all_constraints_passed`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_167` | 3 | `a_002` | `a_002` | `all_constraints_passed` | 9/9 | 0 | `all_constraints_passed`, `best_so_far_recovery`, `constraint_regression`, `historical_branch`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_168` | 5 | `a_003` | `a_003` | `best_available_under_budget` | 9/10 | 0 | `best_so_far_recovery`, `budget_exhausted`, `historical_best_submission`, `local_edit_used`, `persistent_failure`, `target_constraint_fixed` |
| `phase3_ep_170` | 4 | `a_003` | `a_003` | `all_constraints_passed` | 4/4 | 0 | `all_constraints_passed`, `local_edit_used`, `regeneration_used`, `target_constraint_fixed` |
| `phase3_ep_171` | 5 | `a_003` | `a_003` | `best_available_under_budget` | 5/6 | 1 | `best_so_far_recovery`, `budget_exhausted`, `constraint_regression`, `historical_best_submission`, `historical_branch`, `local_edit_used`, `persistent_failure`, `regeneration_used`, `repeated_ineffective_strategy`, `target_constraint_fixed` |
| `phase3_ep_172` | 1 | `a_000` | `a_000` | `all_constraints_passed` | 8/8 | 0 | `all_constraints_passed`, `direct_success` |
| `phase3_ep_173` | 4 | `a_003` | `a_003` | `all_constraints_passed` | 7/7 | 0 | `all_constraints_passed`, `constraint_regression`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_175` | 2 | `a_001` | `a_001` | `all_constraints_passed` | 10/10 | 0 | `all_constraints_passed`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_176` | 3 | `a_002` | `a_002` | `all_constraints_passed` | 10/10 | 2 | `all_constraints_passed`, `local_edit_used`, `regeneration_used`, `target_constraint_fixed` |
| `phase3_ep_177` | 1 | `a_000` | `a_000` | `all_constraints_passed` | 4/4 | 0 | `all_constraints_passed`, `direct_success` |
| `phase3_ep_179` | 2 | `a_001` | `a_001` | `all_constraints_passed` | 6/6 | 0 | `all_constraints_passed`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_185` | 1 | `a_000` | `a_000` | `all_constraints_passed` | 4/4 | 0 | `all_constraints_passed`, `direct_success` |
| `phase3_ep_186` | 1 | `a_000` | `a_000` | `all_constraints_passed` | 4/4 | 0 | `all_constraints_passed`, `direct_success` |
| `phase3_ep_187` | 2 | `a_001` | `a_001` | `all_constraints_passed` | 6/6 | 0 | `all_constraints_passed`, `local_edit_used`, `target_constraint_fixed` |
| `phase3_ep_193` | 1 | `a_000` | `a_000` | `all_constraints_passed` | 4/4 | 1 | `all_constraints_passed`, `direct_success` |

## Excluded Invalid Runs

| Run | Latest Event | Counted |
| --- | --- | --- |
| `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` | `image_execution_started` | no |
