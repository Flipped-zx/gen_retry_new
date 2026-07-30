# Phase 3 Behavior Coverage

| Behavior | Count | Evidence |
| --- | ---: | --- |
| `direct_success` | 13 | `phase3_ep_065`, `phase3_ep_074`, `phase3_ep_081`, `phase3_ep_082`, `phase3_ep_084`, `phase3_ep_089`, `phase3_ep_090`, `phase3_ep_091`, `phase3_ep_097`, `phase3_ep_101`, `phase3_ep_105`, `phase3_ep_106`, `phase3_ep_110` |
| `regeneration_used` | 6 | `phase3_ep_061`, `phase3_ep_076`, `phase3_ep_078`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_092` |
| `local_edit_used` | 27 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_066`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_070`, `phase3_ep_071`, `phase3_ep_072`, `phase3_ep_073`, `phase3_ep_075`, `phase3_ep_076`, `phase3_ep_077`, `phase3_ep_078`, `phase3_ep_079`, `phase3_ep_080`, `phase3_ep_083`, `phase3_ep_085`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_088`, `phase3_ep_092`, `phase3_ep_093`, `phase3_ep_094`, `phase3_ep_096`, `phase3_ep_099` |
| `target_constraint_fixed` | 26 | `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_066`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_070`, `phase3_ep_071`, `phase3_ep_072`, `phase3_ep_073`, `phase3_ep_075`, `phase3_ep_076`, `phase3_ep_077`, `phase3_ep_078`, `phase3_ep_079`, `phase3_ep_080`, `phase3_ep_083`, `phase3_ep_085`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_088`, `phase3_ep_092`, `phase3_ep_093`, `phase3_ep_094`, `phase3_ep_096`, `phase3_ep_099` |
| `constraint_regression` | 13 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_068`, `phase3_ep_072`, `phase3_ep_075`, `phase3_ep_076`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_083`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_088`, `phase3_ep_092` |
| `persistent_failure` | 14 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_068`, `phase3_ep_072`, `phase3_ep_075`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_088`, `phase3_ep_092`, `phase3_ep_093` |
| `repeated_ineffective_strategy` | 8 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_068`, `phase3_ep_075`, `phase3_ep_076`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_086` |
| `historical_branch` | 14 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_064`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_072`, `phase3_ep_075`, `phase3_ep_076`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_083`, `phase3_ep_085`, `phase3_ep_086`, `phase3_ep_087` |
| `best_so_far_recovery` | 17 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_067`, `phase3_ep_068`, `phase3_ep_072`, `phase3_ep_075`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_083`, `phase3_ep_085`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_088`, `phase3_ep_092`, `phase3_ep_093` |
| `historical_best_submission` | 9 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_068`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_088`, `phase3_ep_092`, `phase3_ep_093` |
| `all_constraints_passed` | 26 | `phase3_ep_065`, `phase3_ep_066`, `phase3_ep_067`, `phase3_ep_070`, `phase3_ep_071`, `phase3_ep_073`, `phase3_ep_074`, `phase3_ep_076`, `phase3_ep_077`, `phase3_ep_079`, `phase3_ep_081`, `phase3_ep_082`, `phase3_ep_083`, `phase3_ep_084`, `phase3_ep_085`, `phase3_ep_089`, `phase3_ep_090`, `phase3_ep_091`, `phase3_ep_094`, `phase3_ep_096`, `phase3_ep_097`, `phase3_ep_099`, `phase3_ep_101`, `phase3_ep_105`, `phase3_ep_106`, `phase3_ep_110` |
| `budget_exhausted` | 15 | `phase3_ep_061`, `phase3_ep_062`, `phase3_ep_063`, `phase3_ep_064`, `phase3_ep_068`, `phase3_ep_070`, `phase3_ep_072`, `phase3_ep_075`, `phase3_ep_078`, `phase3_ep_080`, `phase3_ep_086`, `phase3_ep_087`, `phase3_ep_088`, `phase3_ep_092`, `phase3_ep_093` |
| `invalid_infrastructure_run` | 1 | `runs/phase3_invalid/phase3_ep_001_ungrounded_skill_use_20260714T1447Z` |

## Interpretation

The fresh rollouts exercise both productive and non-productive history use. Historical-best submission occurred when the policy submitted an earlier best after a later regression. Constraint regression and repeated ineffective strategy supply negative history-only examples. 26 trajectories reached all atom constraints.
