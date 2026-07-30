# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 8 | `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_006`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_018` |
| `regeneration_used` | 1 | `phase3_ep_011` |
| `local_edit_used` | 12 | `phase3_ep_001`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_007`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_014`, `phase3_ep_017`, `phase3_ep_019`, `phase3_ep_020` |
| `target_constraint_fixed` | 12 | `phase3_ep_001`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_007`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_014`, `phase3_ep_017`, `phase3_ep_019`, `phase3_ep_020` |
| `constraint_regression` | 3 | `phase3_ep_005`, `phase3_ep_011`, `phase3_ep_013` |
| `persistent_failure` | 3 | `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_014` |
| `repeated_ineffective_strategy` | 0 | - |
| `historical_branch` | 5 | `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_010`, `phase3_ep_014`, `phase3_ep_019` |
| `best_so_far_recovery` | 5 | `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_010`, `phase3_ep_014`, `phase3_ep_019` |
| `historical_best_submission` | 0 | - |
| `all_constraints_passed` | 17 | `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`, `phase3_ep_004`, `phase3_ep_005`, `phase3_ep_006`, `phase3_ep_007`, `phase3_ep_008`, `phase3_ep_009`, `phase3_ep_012`, `phase3_ep_013`, `phase3_ep_015`, `phase3_ep_016`, `phase3_ep_017`, `phase3_ep_018`, `phase3_ep_019`, `phase3_ep_020` |
| `budget_exhausted` | 5 | `phase3_ep_004`, `phase3_ep_010`, `phase3_ep_011`, `phase3_ep_014`, `phase3_ep_020` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. No historical-best submission occurred in this checkpoint, although historical-source recovery branches were exercised. Constraint regression and repeated ineffective strategy supply negative history-only examples. 17 trajectories reached all atom constraints.
