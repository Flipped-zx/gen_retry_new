# Meaningful-Retry SFT v9 Sol Review

## Initial Verdict

`PASS_WITH_REQUIRED_CHANGES`

The initial review required:

1. PlannerContext v0.7 to retain all prior image instructions.
2. Outcome-blind semantic comparison against all relevant history, including
   non-adjacent `A -> B -> A` routes.
3. Independent outcome tiering against `best_before`.
4. Explicit atom-gain, GM-only, preserve, and equal-pass atom-swap rules.
5. Source-selection rules consistent with which images are actually visible.
6. A new versioned SFT export and a fixed paired pilot before Gate 3 freeze.

## Final Verdict

`PASS`

The revised design is internally executable and leakage-safe:

- PlannerContext v0.7 restores only pre-action instructions and preserves
  separate original-v0.6 and rebuilt-v0.7 hashes.
- Compatibility review is isolated from candidate outcomes and covers
  non-adjacent semantic repetition.
- Equivalent or unidentifiable resampling retries remain context-only.
- Atom-gain and GM-only rules use deterministic comparisons with
  `best_before`.
- Independent recomputation retained 124/129 atom-gain and 73/130 GM-only
  provisional retries before semantic compatibility review.
- Non-best source rules match actual latest/best image visibility.
- Existing v7/v8 trajectories remain reusable through per-action
  compatibility review.
- The paired pilot fixes coverage and equal-budget comparison.

This verdict approves the design only. Gate 3 remains open until
PlannerContext v0.7, the two-pass audit, the revised SFT export, and the
20-trajectory paired pilot are implemented and validated.

