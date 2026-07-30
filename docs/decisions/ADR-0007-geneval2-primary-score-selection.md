# ADR-0007: Geneval2 Primary Score Selection

- Status: Accepted
- Action protocol: `0.5`
- PlannerContext: `0.6`
- Score policy: `geneval2_pass_count_then_gm@1`
- Primary metric: `geneval2_soft_tifa_gm@flow_dppo_v1`

## Context

PlannerContext v0.5 exposes thresholded atom states, and the reducer selects
best by passed-atom count with the earlier Attempt winning ties. Geneval2
already persists each atom's correct-answer probability. The prompt-level
Soft-TIFA geometric mean is therefore deterministic environment state, not a
Planner prediction.

In the completed Flow-DPPO 20-trajectory batch, the old tie rule selected a
mean GM of 0.4725. Replacing creation order with GM only when pass counts tie
changes eight selected Attempts and raises mean GM to 0.5333 without reducing
the selected pass count in any episode.

## Decision

New episodes use this total ordering:

1. higher passed-atom count;
2. on equal pass count, higher canonical Soft-TIFA GM;
3. on exact GM equality, earlier canonical Attempt ordinal.

Equal atom-level utility means equal pass count under the current unweighted
rubric. It does not require the same atom identity vector. GM is not primary:
an Attempt with fewer passed atoms cannot displace one with more passed atoms.
AM remains reporting-only.

## Numeric contract

For `geneval2_soft_tifa_gm@flow_dppo_v1`:

1. sort observations by `constraint_id`;
2. require one finite binary64 `confidence` in `[0, 1]` per atom;
3. compute `exp(fsum(log(max(p, 1e-300))) / N)`;
4. persist the canonical JSON number;
5. recompute and require exact equality during event validation;
6. compare with exact `>` and retain the earlier Attempt on equality.

The adapter, validator, reducer, PlannerContext builder, and audit use one
shared implementation.

## Ownership and context

- `task_created` and `rollout_plan.json` lock the complete score policy.
- Every new `geneval2_completed` event persists the canonical aggregate.
- PlannerContext v0.6 exposes observed latest/best GM and source-aware round GM
  deltas.
- The score is environment/context-only and never appears in a Planner Action.
- Every `became_best` value uses the reducer's shared comparator.
- SFT exports rebuild each input from its exact event prefix and reject mixed
  PlannerContext/score-policy tuples.

For edit, delta is result GM minus declared source GM. For later source-free
generation, it is result GM minus the previous latest GM. Initial generation
has no baseline or delta.

## Compatibility

Historical episodes without a score-policy lock replay with
`pass_count_only_then_earlier@1` and PlannerContext v0.5. Completed events,
submissions, and artifacts are not rewritten. Resume rejects disagreement
between the rollout plan and initial event policy.

## Review and evidence

- Design: `docs/architecture/planner_score_semantics_v0_6.md`
- GPT-5.6 Sol final verdict: `APPROVE`
- Contract, unit, schema, fixture, and historical replay validation passed.
- No Teacher, Qwen, or Geneval2 live call was made for this protocol change.
