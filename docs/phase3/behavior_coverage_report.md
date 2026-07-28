# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 0 | - |
| `regeneration_used` | 8 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_004`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010` |
| `local_edit_used` | 10 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010` |
| `target_constraint_fixed` | 10 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010` |
| `constraint_regression` | 10 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010` |
| `persistent_failure` | 9 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009` |
| `repeated_ineffective_strategy` | 10 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010` |
| `historical_branch` | 9 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010` |
| `best_so_far_recovery` | 9 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009` |
| `historical_best_submission` | 9 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009` |
| `all_constraints_passed` | 1 | `phase3_ep_010` |
| `budget_exhausted` | 9 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission appears when the policy submits an earlier best attempt after later edits or regenerations regress. Constraint regression and repeated ineffective strategy are common enough to supply negative history-only examples, while one trajectory reached all atom constraints before budget exhaustion.
