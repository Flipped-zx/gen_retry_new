# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 1 | `phase3_ep_019` |
| `regeneration_used` | 8 | `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_015`, `phase3_ep_018` |
| `local_edit_used` | 19 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_014`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_018`, `phase3_ep_020` |
| `target_constraint_fixed` | 16 | `phase3_ep_001`, `phase3_ep_003`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_014`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_018`, `phase3_ep_020` |
| `constraint_regression` | 11 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_005`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_020` |
| `persistent_failure` | 16 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_020` |
| `repeated_ineffective_strategy` | 17 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_014`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_020` |
| `historical_branch` | 10 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_007`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_012`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_020` |
| `best_so_far_recovery` | 14 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_004`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_020` |
| `historical_best_submission` | 13 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_004`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_020` |
| `all_constraints_passed` | 4 | `phase3_ep_011`, `phase3_ep_014`, `phase3_ep_018`, `phase3_ep_019` |
| `budget_exhausted` | 17 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_010`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_014`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_020` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission appears when the policy submits an earlier best attempt after later edits or regenerations regress. Constraint regression and repeated ineffective strategy supply negative history-only examples. 4 trajectories reached all atom constraints.
