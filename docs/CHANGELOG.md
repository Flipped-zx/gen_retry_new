# Changelog

## 2026-07-14

- Added the v0.2 artifact manifest schema for environment-owned artifact refs.
- Tightened the v0.2 episode event schema with payload contracts for canonical
  actions, skill returns, image execution, Geneval2 observations, reducer output,
  submission, and invalid-action observations.
- Tightened the v0.2 planner view schema so planner-visible image references,
  attempts, transitions, tool manifests, and skill manifests are structured and
  exclude raw model output text.
- Addressed Gate 1 requested changes:
  - `action_validated` and `task_created` event payloads now reference the
    canonical action and TaskSpec schemas directly.
  - image execution start/completion payloads are separated, with completed
    events requiring replayable attempt and artifact identity fields.
  - generate execution payloads cannot carry source attempts; edit payloads must
    carry source attempts.
  - `skill_returned` payloads require a query action reference.
  - semantic trajectory validation rejects duplicate constraint IDs, duplicate
    artifact IDs, duplicate per-attempt Geneval2 observations, unknown edit
    sources, and mismatched or unlinked skill returns.
- Addressed Gate 1 second-cycle requested changes:
  - trajectory validation now requires a single episode identity, a first
    `task_created` event, and matching envelope/TaskSpec episode IDs.
  - actions before `task_created` are rejected.
  - image starts must reference exactly one validated image action.
  - image completions must match a prior start by request ID and reference that
    start event.
  - image artifact IDs and Geneval2 results are unique per trajectory/attempt.
- Addressed the user-authorized extra Gate 1 correction cycle:
  - image execution start events can no longer declare attempt lineage fields,
    so completion events are the single source for attempt/parent IDs.
  - each `query_skill` action can have at most one `skill_returned` event.
  - each `geneval2_completed` event must cover every TaskSpec constraint exactly
    once.
  - each `attempt_submitted` event must link to a validated `submit_attempt`
    action with matching selected attempt and reason code.
