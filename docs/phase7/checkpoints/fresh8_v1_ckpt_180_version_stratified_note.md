# Checkpoint 180 Version-Stratified Note

## Frozen Increment

The checkpoint-180 completed-quality increment contains:

- v7: five trajectories, 25 image attempts, 26/32 submitted atoms, GM 35.86,
  zero all-pass submissions, seven regressive actions, and nine strictly
  ineffective actions.
- v8: 15 trajectories, 39 image attempts, 96/98 submitted atoms, GM 95.26,
  13 all-pass submissions, four regressive actions, and four strictly
  ineffective actions.

The full 20-trajectory increment improves atom pass from 109/130 to 122/130
and GM from 49.10 to 80.41. The selected submission equals per-trajectory peak
GM for every episode in this increment.

## Retry-Closure Opportunities

Using canonical attempt actions and reducer outcomes:

- v7: 11 decisions followed a regression or strict no-progress result; two
  repeated the same `(action, source_attempt_id, target_constraint_ids)`.
- v8: six decisions followed a regression or strict no-progress result; zero
  repeated that tuple.
- v8 runtime closure rejections: zero. The Teacher changed strategy without
  requiring runtime repair.

## Interpretation Boundary

This is descriptive mechanism evidence, not a causal v7/v8 ablation. The
policy boundary is nonrandom, the v7 group has only five completion-tail
episodes, and difficulty/completion-order distributions differ. The supported
claim is narrower: v8 exercised the intended closure condition and all six
observed opportunities complied without breaking canonical execution.
