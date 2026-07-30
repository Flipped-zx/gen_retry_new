# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 3 | `phase3_ep_137`, `phase3_ep_139`, `phase3_ep_150` |
| `regeneration_used` | 5 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_125`, `phase3_ep_130`, `phase3_ep_134` |
| `local_edit_used` | 17 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_119`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_126`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_131`, `phase3_ep_132`, `phase3_ep_133`, `phase3_ep_134`, `phase3_ep_135`, `phase3_ep_136`, `phase3_ep_141`, `phase3_ep_145` |
| `target_constraint_fixed` | 13 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_119`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_131`, `phase3_ep_132`, `phase3_ep_134`, `phase3_ep_135`, `phase3_ep_141`, `phase3_ep_145` |
| `constraint_regression` | 10 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_119`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_132`, `phase3_ep_133`, `phase3_ep_135` |
| `persistent_failure` | 13 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_119`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_126`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_132`, `phase3_ep_133`, `phase3_ep_135`, `phase3_ep_136` |
| `repeated_ineffective_strategy` | 10 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_126`, `phase3_ep_130`, `phase3_ep_133`, `phase3_ep_135`, `phase3_ep_136` |
| `historical_branch` | 10 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_123`, `phase3_ep_126`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_133`, `phase3_ep_135`, `phase3_ep_136` |
| `best_so_far_recovery` | 11 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_126`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_133`, `phase3_ep_135`, `phase3_ep_136` |
| `historical_best_submission` | 9 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_126`, `phase3_ep_130`, `phase3_ep_135`, `phase3_ep_136` |
| `all_constraints_passed` | 7 | `phase3_ep_131`, `phase3_ep_134`, `phase3_ep_137`, `phase3_ep_139`, `phase3_ep_141`, `phase3_ep_145`, `phase3_ep_150` |
| `budget_exhausted` | 13 | `phase3_ep_116`, `phase3_ep_117`, `phase3_ep_118`, `phase3_ep_119`, `phase3_ep_123`, `phase3_ep_125`, `phase3_ep_126`, `phase3_ep_127`, `phase3_ep_130`, `phase3_ep_132`, `phase3_ep_133`, `phase3_ep_135`, `phase3_ep_136` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 7 trajectories reached all atom constraints.
