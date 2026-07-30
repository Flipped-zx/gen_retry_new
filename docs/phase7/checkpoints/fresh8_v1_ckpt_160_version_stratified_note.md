# Checkpoint 160 Version-Stratified Note

## Frozen Increment

The checkpoint-160 completed-quality increment contains:

- v7: seven trajectories, 34 image attempts, 42/51 submitted atoms, GM 42.72,
  one all-pass submission, 11 regressive actions, and seven strictly
  ineffective actions.
- v8: three trajectories, four image attempts, 19/19 submitted atoms, GM
  98.47, three all-pass submissions, zero regressive actions, and zero
  strictly ineffective actions.

## Interpretation Boundary

This is not a causal v7/v8 comparison. The v8 subgroup is only three
trajectories, contains one easy and two medium prompts, and needed only four
images. The result is early compatibility evidence: v8 did not break direct
submission or a single successful reducer-best edit.

The three v8 behaviors were:

- `phase3_ep_166`: first generation passed all eight atoms; submit `a_000`.
- `phase3_ep_169`: first generation passed all four atoms; submit `a_000`.
- `phase3_ep_165`: first generation missed one attribute-binding atom; edit
  reducer-best `a_000`, preserve count/layout/donuts, then submit all-pass
  `a_001`.

No frozen v8 trajectory triggered a retry-closure rejection. Benefit against
repeated regressive/no-progress routes remains untested at this boundary.
