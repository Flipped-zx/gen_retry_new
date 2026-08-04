# Meaningful-Retry SFT v9 Sol Review Request

## Gate

`Gate 3 candidate: meaningful-retry SFT policy`

## Decision

Review `docs/phase7/meaningful_retry_sft_v9_design.md`.

The proposal:

- removes the v8 tuple-equality hard rejection;
- keeps Action Protocol v0.5;
- introduces PlannerContext v0.7 only to retain past image instructions;
- separates runtime validity, Planner policy, outcome-blind compatibility, and
  outcome-based supervision tiering;
- reuses v7/v8 trajectories only after per-action v9 compatibility review.

## Evidence

- 200 trajectories, 684 Attempts, 663 provisional SFT targets.
- 484 post-initial retries: 263 positive, 106 harmful, 115 ineffective.
- 65 v7 same-route retries after regression/no-progress: 25 positive, 16
  ineffective, 24 harmful.
- Four positive labels improve only a non-best source.
- 130 positive retries are GM-only; 23 swap passed atom identities, three do
  not improve a declared target confidence, and 17 regress a preserve atom.
- PlannerContext v0.6 omits instructions from `prior_image_rounds`.
- Restoring all prior instructions produces a maximum estimated context size
  of roughly 3,940 tokens under the existing estimator.

## Questions

1. Is the runtime/policy/offline-supervision separation plus PlannerContext
   v0.7 sufficient?
2. Are the global-best atom and target-relevant GM-only rules sound?
3. Can v7/v8 trajectories be reused safely, and is the proposed paired pilot
   sufficient before Gate 3 freeze?

## Non-goals

- No Action schema change.
- No completed-trajectory mutation.
- No image or evaluator call during review.
- No causal claim from outcome-filtered actions.

