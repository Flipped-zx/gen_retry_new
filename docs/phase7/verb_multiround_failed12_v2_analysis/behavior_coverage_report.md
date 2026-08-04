# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 0 | - |
| `regeneration_used` | 6 | `phase3_ep_032`, `phase3_ep_107`, `phase3_ep_135`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `local_edit_used` | 10 | `phase3_ep_032`, `phase3_ep_042`, `phase3_ep_051`, `phase3_ep_107`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_154`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `target_constraint_fixed` | 5 | `phase3_ep_032`, `phase3_ep_042`, `phase3_ep_051`, `phase3_ep_116`, `phase3_ep_135` |
| `constraint_regression` | 8 | `phase3_ep_032`, `phase3_ep_051`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_154`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `persistent_failure` | 10 | `phase3_ep_032`, `phase3_ep_042`, `phase3_ep_051`, `phase3_ep_107`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_154`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `repeated_ineffective_strategy` | 6 | `phase3_ep_107`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `historical_branch` | 7 | `phase3_ep_107`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_154`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `best_so_far_recovery` | 8 | `phase3_ep_051`, `phase3_ep_107`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_154`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `historical_best_submission` | 6 | `phase3_ep_051`, `phase3_ep_107`, `phase3_ep_135`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `all_constraints_passed` | 0 | - |
| `budget_exhausted` | 10 | `phase3_ep_032`, `phase3_ep_042`, `phase3_ep_051`, `phase3_ep_107`, `phase3_ep_116`, `phase3_ep_135`, `phase3_ep_154`, `phase3_ep_163`, `phase3_ep_181`, `phase3_ep_200` |
| `invalid_infrastructure_run` | 0 | - |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 0 trajectories reached all atom constraints.
