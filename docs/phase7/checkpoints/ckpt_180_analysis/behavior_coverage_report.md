# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 5 | `phase3_ep_172`, `phase3_ep_177`, `phase3_ep_185`, `phase3_ep_186`, `phase3_ep_193` |
| `regeneration_used` | 7 | `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_170`, `phase3_ep_171`, `phase3_ep_176` |
| `local_edit_used` | 15 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_164`, `phase3_ep_167`, `phase3_ep_168`, `phase3_ep_170`, `phase3_ep_171`, `phase3_ep_173`, `phase3_ep_175`, `phase3_ep_176`, `phase3_ep_179`, `phase3_ep_187` |
| `target_constraint_fixed` | 11 | `phase3_ep_159`, `phase3_ep_164`, `phase3_ep_167`, `phase3_ep_168`, `phase3_ep_170`, `phase3_ep_171`, `phase3_ep_173`, `phase3_ep_175`, `phase3_ep_176`, `phase3_ep_179`, `phase3_ep_187` |
| `constraint_regression` | 5 | `phase3_ep_160`, `phase3_ep_163`, `phase3_ep_167`, `phase3_ep_171`, `phase3_ep_173` |
| `persistent_failure` | 7 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_168`, `phase3_ep_171` |
| `repeated_ineffective_strategy` | 6 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_171` |
| `historical_branch` | 6 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_163`, `phase3_ep_167`, `phase3_ep_171` |
| `best_so_far_recovery` | 8 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_167`, `phase3_ep_168`, `phase3_ep_171` |
| `historical_best_submission` | 7 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_168`, `phase3_ep_171` |
| `all_constraints_passed` | 13 | `phase3_ep_164`, `phase3_ep_167`, `phase3_ep_170`, `phase3_ep_172`, `phase3_ep_173`, `phase3_ep_175`, `phase3_ep_176`, `phase3_ep_177`, `phase3_ep_179`, `phase3_ep_185`, `phase3_ep_186`, `phase3_ep_187`, `phase3_ep_193` |
| `budget_exhausted` | 7 | `phase3_ep_159`, `phase3_ep_160`, `phase3_ep_161`, `phase3_ep_162`, `phase3_ep_163`, `phase3_ep_168`, `phase3_ep_171` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 13 trajectories reached all atom constraints.
