# Planner Retry Closure Policy v8

## Trigger

Checkpoint 140 showed 23 regressive image actions across 79 attempts, compared
with 67 across the preceding 372 attempts. Sol returned
`PASS_WITH_PROSPECTIVE_CHANGE`.

## Forward-Only Rules

Teacher system prompt version:
`teacher_system_prompt_v8_retry_closure_policy`.

1. After the latest image result regresses any atom, the next image action may
   not repeat the same `(action, source_attempt_id, target_constraint_ids)`
   tuple.
2. The same prohibition applies after strict no-progress: no fixed atom, no
   regressed atom, and the result did not become reducer-best.
3. `edit_image` defaults to the reducer-best source.
4. A non-best source is valid only if it passes at least one target or preserve
   constraint that reducer-best does not pass.

These are runtime action-policy checks, not new action fields. Rejected turns
remain raw context-only records and never become canonical actions or positive
SFT targets.

## Compatibility

- Action Protocol remains `0.5`.
- PlannerContext remains `0.6`.
- Score policy remains `geneval2_pass_count_then_gm@1`.
- Execution profile remains `qwen_dual_backend@1`.
- Completed v7 trajectories are immutable.
- Already-running child processes finish with the prompt version loaded at
  process start.
- Newly started child processes load v8 and persist its version/hash in each
  sanitized Planner request.

## Evaluation

Post-change behavior must be reported separately by persisted
`system_prompt_version`. The next reviews compare regression concentration,
strict no-progress repetition, all-pass rate, atom gain, and GM without
rerunning any v7 trajectory.
