# SFT Checkpoint Action Evaluation

Fixed sample count: 16.

| Metric | checkpoint-100 | final | Final delta |
| --- | ---: | ---: | ---: |
| schema_valid_rate | 1.0000 | 1.0000 | 0.0000 |
| invalid_rate | 0.0000 | 0.0000 | 0.0000 |
| action_type_accuracy | 0.9375 | 1.0000 | 0.0625 |
| exact_action_accuracy | 0.5000 | 0.5000 | 0.0000 |
| query_skill_rate | 0.2500 | 0.2500 | 0.0000 |
| target_constraint_jaccard | 0.9479 | 1.0000 | 0.0521 |
| target_constraint_recall | 0.9479 | 1.0000 | 0.0521 |
| preserve_constraint_jaccard | 0.8750 | 1.0000 | 0.1250 |
| attempt_reference_accuracy | 1.0000 | 1.0000 | 0.0000 |

`invalid_rate` is expected to decrease; all other deltas are descriptive. The action metrics do not execute images or rerun Geneval2.
