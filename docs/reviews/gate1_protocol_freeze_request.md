# SOL_REVIEW_REQUEST

## Gate

`Protocol Freeze`

## Decision to review

Freeze v0.2 as a minimal executable retry protocol: the assistant emits exactly
one action JSON, while artifacts, evaluator observations, transitions,
best-so-far, lineage, paths, budgets, and invalid-action observations remain
environment-owned event facts.

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
  - `src/gen_retry/cli/validate_schemas.py`
  - `src/gen_retry/cli/validate_fixtures.py`
- Canonical fixtures:
  - `tests/fixtures/task_spec/geneval2_minimal.json`
  - `tests/fixtures/actions/*.json`
  - `tests/fixtures/events/one_attempt_events.jsonl`
  - `tests/fixtures/planner_views/after_failed_attempt.json`
  - `tests/fixtures/artifacts/demo_manifest.json`
  - `examples/one_episode_trajectory.jsonl`
- Test summary:
  - `python -m gen_retry.cli.validate_schemas` passed, 5 schemas
  - `python -m gen_retry.cli.validate_fixtures` passed, 35 fixture records
  - `pytest tests/contract -q` passed, 29 tests
- Source ledger references:
  - Legacy Gen-Retry: Geneval2 normalization, transition sets, best-so-far, masking evidence.
  - Gen-Searcher: assistant target vs observation separation and artifact-path provenance.
  - GenEvolve: real skill retrieval and stable image references.
  - Geneval2: atom-level VQA metadata fields.
- Conflicting evidence, if any:
  - Legacy prompt-rewrite and mutable trajectory JSON conflict with v3 invariants and were intentionally retired.

## Questions

1. Does the v0.2 action protocol keep the assistant target minimal enough for SFT, with no separate `refine_prompt` action and no environment-owned fields?
2. Are event payloads and artifact manifests sufficient for Phase 2 deterministic replay without introducing runtime dependencies on external repositories?
3. Is the `query_skill -> skill_returned` interaction explicit enough to satisfy the skill-selection invariant before live pilots?

## Explicit non-goals

- Do not review live Qianwen-Image-Edit, Geneval2, GPT teacher, SFT exporter, or runtime concurrency implementation.
- Do not request broad external repository archaeology; Phase 0 evidence is already recorded in `docs/SOURCE_LEDGER.md`.
- Do not redesign the action set beyond blocking issues for Gate 1.

## Expected response

- Return exactly one verdict: `APPROVE`, `REQUEST_CHANGES`, or `BLOCKED`.
- Include blocking issues only.
- Include recommended decision, residual risks, and one minimal validation experiment if needed.
- Do not implement code.
