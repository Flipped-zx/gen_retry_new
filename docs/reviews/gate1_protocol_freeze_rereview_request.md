# SOL_REVIEW_REQUEST

## Gate

`Protocol Freeze`

## Decision to review

Freeze v0.2 as a minimal executable retry protocol after addressing Gate 1
Review 1: the assistant emits exactly one action JSON, while artifacts,
evaluator observations, transitions, best-so-far, lineage, paths, budgets, skill
tool responses, and invalid-action observations remain environment-owned facts.

## Current evidence

- Relevant schema/ADR:
  - `schemas/action_protocol_v0_2.schema.json`
  - `schemas/task_spec_v0_2.schema.json`
  - `schemas/episode_event_v0_2.schema.json`
  - `schemas/planner_view_v0_2.schema.json`
  - `schemas/artifact_manifest_v0_2.schema.json`
  - `docs/decisions/ADR-0001-qianwen-image-edit-backend.md`
  - `docs/decisions/ADR-0002-event-sourced-memory.md`
  - `docs/decisions/ADR-0003-no-separate-refine-action.md`
- Minimal implementation:
  - `src/gen_retry/protocol/action_parser.py`
  - `src/gen_retry/protocol/reference_validator.py`
  - `src/gen_retry/protocol/task_spec_builder.py`
  - `src/gen_retry/protocol/trajectory_validator.py`
  - `src/gen_retry/cli/validate_schemas.py`
  - `src/gen_retry/cli/validate_fixtures.py`
- Changes since Review 1:
  - `action_validated.action` now references the canonical action schema.
  - `task_created.task_spec` now references the TaskSpec schema.
  - image start and completion payload schemas are separate.
  - completed image executions require request ID, attempt ID, parent ID, backend,
    operation, image artifact ID, artifact manifest ref, and artifact hash.
  - generate execution payloads reject `source_attempt_id`; edit execution
    payloads require it.
  - `skill_returned` requires `query_action_event_id`, non-empty target
    constraints, and trajectory validation checks that it matches an earlier
    `query_skill` action in the same turn.
  - trajectory validation rejects duplicate event IDs, attempt IDs, TaskSpec
    constraint IDs, artifact IDs, and duplicate per-attempt Geneval2 observations.
- Canonical fixtures:
  - `tests/fixtures/events/query_skill_events.jsonl`
  - `tests/fixtures/events/one_attempt_events.jsonl`
  - `examples/one_episode_trajectory.jsonl`
- Test summary:
  - `python -m gen_retry.cli.validate_schemas` passed, 5 schemas
  - `python -m gen_retry.cli.validate_fixtures` passed, 38 fixture records
  - `pytest tests/contract -q` passed, 37 tests
- Conflicting evidence, if any:
  - None after Review 1 changes.

## Questions

1. Do the revised event schema and trajectory validator now make canonical histories replayable enough for Phase 2 reducer implementation?
2. Is the `query_skill -> skill_returned` invariant explicit enough after adding `query_action_event_id`, input refs, and semantic matching?
3. Are the remaining risks, especially best-attempt tie-breaking and artifact URI portability, acceptable to defer to Phase 2 implementation tests?

## Explicit non-goals

- Do not review live Qianwen-Image-Edit, Geneval2, GPT teacher, SFT exporter, or runtime concurrency implementation.
- Do not request broad external repository archaeology; Phase 0 evidence is already recorded in `docs/SOURCE_LEDGER.md`.
- Do not redesign the action set beyond blocking issues for Gate 1.

## Expected response

- Return exactly one verdict: `APPROVE`, `REQUEST_CHANGES`, or `BLOCKED`.
- Include blocking issues only.
- Include recommended decision, residual risks, and one minimal validation experiment if useful.
- Do not implement code.
