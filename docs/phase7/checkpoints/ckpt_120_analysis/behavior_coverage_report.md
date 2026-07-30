# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 7 | `phase3_ep_113`, `phase3_ep_114`, `phase3_ep_115`, `phase3_ep_122`, `phase3_ep_124`, `phase3_ep_128`, `phase3_ep_129` |
| `regeneration_used` | 7 | `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_103`, `phase3_ep_107`, `phase3_ep_108`, `phase3_ep_109`, `phase3_ep_111` |
| `local_edit_used` | 13 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_102`, `phase3_ep_103`, `phase3_ep_104`, `phase3_ep_107`, `phase3_ep_108`, `phase3_ep_109`, `phase3_ep_111`, `phase3_ep_112`, `phase3_ep_120`, `phase3_ep_121` |
| `target_constraint_fixed` | 10 | `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_102`, `phase3_ep_103`, `phase3_ep_108`, `phase3_ep_109`, `phase3_ep_111`, `phase3_ep_112`, `phase3_ep_120`, `phase3_ep_121` |
| `constraint_regression` | 6 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_104`, `phase3_ep_109`, `phase3_ep_111` |
| `persistent_failure` | 9 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_102`, `phase3_ep_103`, `phase3_ep_104`, `phase3_ep_107`, `phase3_ep_109`, `phase3_ep_111` |
| `repeated_ineffective_strategy` | 9 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_102`, `phase3_ep_103`, `phase3_ep_104`, `phase3_ep_107`, `phase3_ep_109`, `phase3_ep_111` |
| `historical_branch` | 7 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_103`, `phase3_ep_104`, `phase3_ep_109`, `phase3_ep_111` |
| `best_so_far_recovery` | 7 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_104`, `phase3_ep_107`, `phase3_ep_109`, `phase3_ep_111` |
| `historical_best_submission` | 6 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_104`, `phase3_ep_107`, `phase3_ep_111` |
| `all_constraints_passed` | 11 | `phase3_ep_108`, `phase3_ep_112`, `phase3_ep_113`, `phase3_ep_114`, `phase3_ep_115`, `phase3_ep_120`, `phase3_ep_121`, `phase3_ep_122`, `phase3_ep_124`, `phase3_ep_128`, `phase3_ep_129` |
| `budget_exhausted` | 10 | `phase3_ep_095`, `phase3_ep_098`, `phase3_ep_100`, `phase3_ep_102`, `phase3_ep_103`, `phase3_ep_104`, `phase3_ep_107`, `phase3_ep_109`, `phase3_ep_111`, `phase3_ep_112` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 11 trajectories reached all atom constraints.
