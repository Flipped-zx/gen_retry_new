# SOL_REVIEW_REQUEST

## Gate

`PlannerContext / best-attempt semantics amendment review`

## Decision to review

Review the proposed environment-owned Geneval2 prompt score and best-selection
policy in:

`docs/architecture/planner_score_semantics_v0_6.md`.

The candidate keeps Action Protocol v0.5 and introduces PlannerContext v0.6:

```text
best = max(attempts, key=(passed_atom_count, Soft-TIFA GM, earlier attempt))
```

## Evidence

- Each live Geneval2 atom already persists its correct-answer probability as
  `constraint_results[].confidence`.
- Soft-TIFA GM is deterministically recomputable from immutable events.
- Current best selection is pass count only, with earlier-attempt tie-break.
- In the completed 20-trajectory batch:
  - 18/20 episodes contain a pass-count tie;
  - pass-count-then-GM changes eight selected best attempts;
  - mean selected GM rises from 0.4725 to 0.5333;
  - selected pass count never decreases;
  - GM-only and pass-count-then-GM happen to select the same attempt in this
    batch, but this is not assumed as a general property.
- Six of the eight changed cases have exactly the same per-atom status vector;
  two have the same pass count but different passing atom identities.
- Historical event logs must keep their old pass-count-only replay semantics.

## Questions

1. Should v1 define atom-level equality as equal pass count, exact atom-status
   vector equality, or make GM primary? Evaluate metric alignment, semantic
   regressions, and the evidence above.
2. Is the proposed PlannerContext exposure minimal and clear: one primary GM
   scalar for latest/best plus score delta in round memory, while AM remains
   reporting-only and all scores stay environment/context-only?
3. Are episode-level score-policy locking, deterministic aggregate
   recomputation, legacy fallback, resume rejection, and SFT policy/version
   grouping sufficient to prevent future leakage and historical replay drift?

## Explicit non-goals

- Do not run Teacher, Qwen, or Geneval2.
- Do not change Action Protocol v0.5.
- Do not change image execution routing.
- Do not modify completed trajectory artifacts.

## Expected response

- `APPROVE` or `REQUEST_CHANGES`;
- blocking issues only;
- exact recommended ordering and minimum persisted/context fields.

## First review result

`REQUEST_CHANGES`

Required amendments:

1. freeze numeric GM recomputation and comparison;
2. make score delta baseline-aware and use one shared best comparator;
3. lock/group the full PlannerContext/policy/metric tuple and add temporal
   prefix reconstruction to SFT audit.

All three amendments are now specified in
`docs/architecture/planner_score_semantics_v0_6.md`.

## Final review result

`APPROVE`

The amended design freezes the numeric contract, uses one comparator for all
best updates, defines source-aware score deltas, locks the complete policy
tuple, and requires temporal-prefix reconstruction for SFT inputs.
