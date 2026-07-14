# SOL_REVIEW_REQUEST

## Gate

`Protocol Freeze`

## Decision to review

Freeze v0.2 after the second requested-change cycle. The protocol now combines
schema validation with normative trajectory validation so replay can associate
each canonical action, tool response, image execution, artifact, evaluator
result, transition, and submission with one episode and deterministic IDs.

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
- Changes since Review 2:
  - one `episode_id` per trajectory is enforced;
  - `task_created` must be first;
  - task envelope and nested TaskSpec episode IDs must match;
  - actions before `task_created` are rejected;
  - image starts must reference exactly one validated image action and match
    operation/source;
  - image completions must match a prior start by request ID, reference that
    start event, and match operation/backend/source;
  - request starts/completions, attempt IDs, image artifact IDs, and Geneval2
    results are unique where deterministic replay requires uniqueness.
- Reviewer-probe negative tests now exist for:
  - cross-episode skill response;
  - mismatched task envelope/TaskSpec episode;
  - action before task;
  - duplicate Geneval2 result for one attempt;
  - orphan completion reusing an image artifact;
  - image start without a validated action.
- Test summary:
  - `python -m gen_retry.cli.validate_schemas` passed, 5 schemas
  - `python -m gen_retry.cli.validate_fixtures` passed, 38 fixture records
  - `pytest tests/contract -q` passed, 43 tests
- Conflicting evidence, if any:
  - None after Review 2 changes.

## Questions

1. Are the replay identity and causality invariants now strong enough to freeze
   Gate 1 and begin Phase 2 reducer/event-store implementation?
2. Are remaining policies such as best-attempt tie-breaking and artifact URI
   portability acceptable to finalize through Phase 2 deterministic replay tests?
3. Is there any remaining blocking issue in action minimality, backend
   semantics, or `query_skill -> skill_returned` ownership?

## Explicit non-goals

- Do not review live Qianwen-Image-Edit, Geneval2, GPT teacher, SFT exporter, or
  runtime concurrency implementation.
- Do not request broad external repository archaeology.
- Do not redesign the action set beyond blocking issues for Gate 1.

## Expected response

- Return exactly one verdict: `APPROVE`, `REQUEST_CHANGES`, or `BLOCKED`.
- Include blocking issues only.
- Include recommended decision, residual risks, and one minimal validation
  experiment if useful.
- Do not implement code.
