# Checkpoint 200 Teacher-Policy Stratification

## Episode Groups

The final 200 trajectories group by persisted Planner-request version:

- v7-only: 162 trajectories.
- v8-only: 37 trajectories.
- mixed resume: one trajectory, `phase3_ep_069`.

`phase3_ep_069` produced its first two attempts under v7, then resumed under
v8. It is included once in the 200-trajectory aggregate and excluded from both
pure-version descriptive groups.

## Descriptive Metrics

| Group | Episodes | Attempts | Initial atoms | Submitted atoms | Initial GM | Submitted GM | All pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v7-only | 162 | 548 | 939/1146 | 1053/1146 | 43.70 | 72.90 | 92 |
| v8-only | 37 | 131 | 213/265 | 241/265 | 38.65 | 75.82 | 19 |
| mixed resume | 1 | 5 | 7/8 | 7/8 | 7.10 | 85.14 | 0 |

These groups are not a randomized ablation. Prompt difficulty, completion
order, and the policy switch boundary differ.

## Retry-Closure Mechanism

Using canonical actions and reducer outcomes:

- v7-only: 148 post-regression or strict-no-progress decisions; 65 next
  actions repeated the same `(action, source_attempt_id,
  target_constraint_ids)`.
- v8-only: 32 such decisions; zero next actions repeated that tuple.
- Runtime `repeated_failed_retry_strategy` rejections: zero.
- Runtime `historical_source_without_constraint_evidence` rejections: zero.

The supported claim is behavioral: v8 changed Planner outputs so observed
closure opportunities did not repeat the same failed route. This evidence
does not isolate a causal GM or all-pass improvement.
