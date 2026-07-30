# Planner Score Semantics v0.6

Status: accepted by ADR-0007 after GPT-5.6 Sol `APPROVE`

## Version boundary

- Action Protocol remains `0.5`.
- PlannerContext advances from `0.5` to `0.6`.
- Image execution remains independently versioned; current new-run profile is
  `qwen_dual_backend@1`.
- Score ownership remains entirely in the environment.

## Problem

The reducer currently ranks attempts by thresholded passed-atom count and keeps
the earlier attempt on a tie. Geneval2 already persists the correct-answer
probability for each atom as `constraint_results[].confidence`. Flow-DPPO's
prompt-level Soft-TIFA GM can therefore be computed deterministically:

```text
GM = exp(mean(log(max(correct_answer_probability, 1e-300))))
```

The 20 completed Flow-DPPO trajectories contain 18 episodes with a pass-count
tie. A deterministic `(pass_count, GM, earlier_attempt)` ordering would change
the selected best in eight episodes and raise mean submitted GM from 0.4725 to
0.5333 without lowering any selected pass count. In this batch, it also selects
the same attempt as GM-only ranking, although that is not guaranteed generally.

## Proposed score policy

New episodes explicitly lock:

```json
{
  "policy_id": "geneval2_pass_count_then_gm",
  "policy_version": "1",
  "primary_metric": {
    "metric_id": "geneval2_soft_tifa_gm",
    "metric_version": "flow_dppo_v1"
  },
  "best_selection_rule": "higher_pass_count_then_higher_primary_score_then_earlier"
}
```

The complete policy tuple is persisted in the initial environment event and
the prepared rollout plan:

```text
PlannerContext version
score-policy ID + version
primary-metric ID + version
```

Historical episodes without the initial-event lock retain
`pass_count_only_then_earlier@1` replay semantics. Policy is never inferred from
the current runtime configuration, the presence of confidence fields, or an
aggregate score.

“Atom-level equal” means equal passed-atom count under the current unweighted
reducer. It does not require the exact same set of passing atoms. All current
Geneval2 constraints have equal priority in the reducer; when the discrete
objective is tied, GM is more principled than creation order. A future weighted
or priority-aware atom objective would require a separate policy.

## Canonical `flow_dppo_v1` numeric contract

`geneval2_soft_tifa_gm@flow_dppo_v1` is frozen as follows:

1. Sort atom observations by `constraint_id` ascending.
2. Read each persisted correct-answer probability as an IEEE-754 binary64
   value and reject missing, non-finite, or out-of-range values.
3. Clamp each probability with the exact binary64 value `1e-300`.
4. Compute logs with Python `math.log`, aggregate with `math.fsum`, divide by
   the integer atom count, and apply Python `math.exp`.
5. Serialize the resulting binary64 JSON number through the repository's
   canonical JSON writer. JSON parse round-trips that value.
6. Event validation recomputes the value with the same metric implementation
   and requires exact binary64 equality.
7. Best ranking compares validated persisted values with exact `>` / `<`.
   There is no epsilon. Exact equality falls through to canonical attempt
   ordinal, where the earlier attempt wins.

The shared metric implementation is used by the Geneval2 adapter, event
validator, reducer, PlannerContext builder, and Phase 5 audit. No module carries
an independent copy of the formula.

## Environment records

Each new `geneval2_completed` event persists:

```json
{
  "primary_score": {
    "metric_id": "geneval2_soft_tifa_gm",
    "metric_version": "flow_dppo_v1",
    "value": 0.25700426807793075
  }
}
```

The event validator recomputes GM from atom probabilities and rejects a
mismatched persisted aggregate. The reducer ranks only the canonical validated
aggregate. New score-policy episodes require a complete probability for every
atom and a primary score in every `geneval2_completed` event. Historical events
without probabilities or aggregate scores remain replayable under the legacy
policy.

AM remains a reporting-only atom-level continuous statistic. It is not exposed
as a second Planner optimization scalar because the atom statuses already
provide localized evidence and two primary scalars would make stop/source
selection ambiguous.

## PlannerContext v0.6

The next Planner call explicitly identifies its schema:

```text
planner_context_schema_version: "0.6"
```

It sees only already-observed scores:

- `latest_attempt.primary_score`
- `episode_memory.best_attempt.primary_score` when best differs from latest;
  when they are the same, the existing reference avoids duplication
- last and prior round outcomes retain:
  - `baseline_attempt_id`
  - `primary_score_delta`
- `runtime_state.score_policy` contains the complete policy/metric tuple and
  selection rule

Delta is exactly `result GM - baseline GM`. For edit, baseline is the declared
source attempt. For a later source-free generation, baseline is the previous
latest attempt. For the initial generation, baseline and delta are `null`.
Both fields live inside the round's `observed_outcome` or compressed
`outcome_summary`; they are not Planner-authored action fields.

The current action target never contains the result score produced after that
action. Geneval2 scores are context-only environment observations with SFT loss
zero. Every `became_best` field is derived through the reducer's single shared
policy comparator; PlannerContext does not independently reimplement ranking.

## Best and submission semantics

For score-policy v1:

1. higher passed-atom count wins;
2. on equal pass count, higher Soft-TIFA GM wins;
3. on an exact GM tie, the earlier attempt remains best.

`best_attempt` uses this ordering. `submit_attempt` remains a Planner Action and
may technically name any historical attempt, but normal budget-exhaustion and
best-available behavior should submit the environment-designated best.

This is intentionally not GM-primary selection. A lower-pass-count attempt may
have higher GM, but it does not displace a higher-pass-count attempt under v1.
Reports must continue to disclose both submitted GM and post-hoc GM-only peak
so any remaining metric-alignment gap is visible.

## Compatibility and preparation

- Completed trajectories and artifacts are never rewritten.
- Event replay chooses score policy only from the episode's initial event.
- Resume rejects disagreement between the prepared rollout plan and the full
  initial-event context/policy/metric tuple.
- Existing unexecuted comparison scaffolds must be migrated deterministically
  or replaced before live calls so they opt into the new policy explicitly.
- SFT exports record and group by the full context/policy/metric tuple and must
  not silently mix contexts with different best-selection semantics.
- For each SFT sample, export validation locates the referenced
  `planner_context_built` event, rebuilds PlannerContext from that exact event
  prefix, compares it to the persisted input artifact, and verifies that the
  target action event occurs later. This rejects any score or atom outcome from
  the target action or a future round.

## Non-goals

- No change to Geneval2 model inference.
- No change to thresholds or atom normalization.
- No AM optimization target.
- No score field in canonical Planner Actions.
- No automatic rewriting of historical submissions.
