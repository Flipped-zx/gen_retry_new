# SOL Review Request: Consecutive `query_skill` Live Blocker

## Gate

`v0.7 five-trajectory live diagnostic / action-semantics blocker`

## Decision To Review

Determine whether the live runtime's unconditional rejection of consecutive
`query_skill` actions is inconsistent with the accepted Planning Round
semantics, which allow zero to N Skill queries before one terminal image
action.

No schema field change is proposed. The candidate runtime-only correction
would allow another `query_skill` in the same active round only when it
requests at least one not-yet-active Skill and remains below a small finite
per-round query cap. Repeated equivalent queries would still be rejected.

## Current Evidence

- `docs/phase3/trajectory_trace_planner_context_v0_3_ep_001.md` defines one
  Planning Round as zero to N `query_skill` actions followed by one
  `generate_image` or `edit_image` action.
- `query_skill.arguments.skill_ids` already accepts multiple Skill IDs, and
  each successful tool response is persisted in the current round's
  `skill_context.active_skills`.
- In
  `runs/phase6_v07_dual_backend5_score_v06/phase3_ep_001`, GPT-5.5 first
  queried three Skills successfully, then requested two different,
  not-yet-active Skills before any image action.
- `src/gen_retry/phase3/live_runner.py` rejected that second query and three
  repair attempts with `consecutive_query_skill`, so the episode stopped with
  zero image attempts. No completed trajectory artifact was changed.
- Four other episodes in the same batch use one Skill query before generation
  and are unaffected.

## Questions

1. Is the unconditional consecutive-query rejection a blocking
   implementation mismatch with the accepted zero-to-N Planning Round
   semantics?
2. If yes, is the minimal safe policy to allow only novel Skill IDs with a
   finite per-round query cap, while rejecting equivalent/redundant queries?
3. May the failed episode resume from its immutable event prefix after that
   runtime correction, while the four unaffected completed/in-progress
   episodes remain valid members of the same diagnostic batch?

## Explicit Non-Goals

- No Action Protocol or PlannerContext schema change.
- No promotion of `query_skill` to a positive SFT target.
- No modification or rerun of valid submitted trajectories.
- No change to generator, evaluator, score, budget, or submission semantics.

## Expected Response

Return `PASS` with a precise bounded policy, or `FAIL` with the blocking reason
and the alternative recovery rule. Distinguish protocol correctness from
optional Teacher-prompt optimization.
