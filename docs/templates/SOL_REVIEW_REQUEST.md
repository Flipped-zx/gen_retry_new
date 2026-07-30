# SOL_REVIEW_REQUEST

## Gate

`PlannerContext / best-attempt semantics amendment review`

## Decision to review

Review the concrete PlannerContext v0.6 score-semantics proposal in
`docs/architecture/planner_score_semantics_v0_6.md`. Action Protocol remains
v0.5. New episodes would rank best by passed-atom count, then Geneval2
Soft-TIFA GM, then earlier attempt.

## Current evidence

- Geneval2 atom results already persist correct-answer probabilities.
- GM is deterministically recomputable from immutable events.
- In the completed 20-trajectory batch, pass-count-then-GM changes eight best
  attempts and raises mean selected GM from 0.4725 to 0.5333 without lowering
  selected pass count.
- Six changed cases have identical atom-status vectors; two have equal pass
  count but different passing atom identities.
- Historical episodes must retain pass-count-only replay semantics.

## Questions（最多 3 个）

1. Should atom-level equality mean equal pass count, exact atom-status vector,
   or should GM become primary?
2. Is one GM scalar on latest/best plus score delta in round memory sufficient,
   with AM reporting-only?
3. Are score-policy locking, aggregate recomputation, legacy fallback, resume
   rejection, and SFT grouping sufficient?

## Explicit non-goals

- No schema or reducer implementation in this review.
- No new rollout, Qwen-Image-Edit, Teacher, or Geneval2 calls.
- No redesign of the Geneval2 evaluator.
- No claim that the 20 synthetic training prompts are an official leaderboard
  evaluation.

## Expected response

- direct recommendation for each question;
- blocking ambiguity or SFT risk only;
- one minimal v0.6 candidate field/selection policy if change is recommended;
- distinguish required change from optional token optimization.
