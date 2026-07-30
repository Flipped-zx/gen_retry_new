# v0.7 Live Consecutive `query_skill` Blocker Review

## Verdict

`PASS`

## Required Runtime Policy

- The unconditional rejection of consecutive `query_skill` actions is an
  implementation mismatch with the accepted zero-to-N Planning Round
  semantics.
- Permit at most two successful `query_skill -> skill_returned` interactions
  per active image-producing round.
- Keep the existing one-to-three unique Skill IDs per query.
- Every resolved Skill identity must be novel for the episode; reject the
  whole action if any requested identity was already returned.
- Reject a third query with `round_skill_query_limit`.
- If a validated query lacks `skill_returned`, resume that interaction
  idempotently before accepting another Planner action.
- Rejected outputs and format errors do not consume the two-query allowance.

## Recovery Decision

Resume only `phase3_ep_001` from its immutable event prefix after the bounded
runtime correction. Preserve the historical `consecutive_query_skill` error
events for audit, but do not surface the now-obsolete final error as a new
Teacher repair instruction.

The other four trajectories remain valid because all of their accepted actions
are invariant under the corrected rule. Image attempts, scores, and
submissions remain comparable. Planner call count, repair count, latency, and
cost for the resumed episode are not directly comparable because its prefix
contains blocker-induced retries.

## Scope

This is a runtime legality correction. It does not change the Action Protocol,
PlannerContext schema, SFT treatment of `query_skill`, generator, evaluator,
score policy, image budget, or submission semantics.
