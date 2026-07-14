# Phase 1 File Plan

Phase 1 is Gate 1: Protocol Freeze. It should stay schema-first and avoid live
Qianwen, Geneval2, or teacher calls.

## Edit Order

1. Validate existing schemas against the Phase 0 findings.
   - `schemas/task_spec_v0_2.schema.json`
   - `schemas/action_protocol_v0_2.schema.json`
   - `schemas/episode_event_v0_2.schema.json`
   - `schemas/planner_view_v0_2.schema.json`

2. Add canonical fixtures.
   - `tests/fixtures/task_spec/geneval2_minimal.json`
   - `tests/fixtures/actions/query_skill.json`
   - `tests/fixtures/actions/generate_image.json`
   - `tests/fixtures/actions/edit_image.json`
   - `tests/fixtures/actions/submit_attempt.json`
   - `tests/fixtures/events/one_attempt_events.jsonl`
   - `tests/fixtures/planner_views/after_failed_attempt.json`

3. Add validation and parser code.
   - `src/gen_retry/protocol/schema_loader.py`
   - `src/gen_retry/protocol/action_parser.py`
   - `src/gen_retry/protocol/reference_validator.py`
   - `src/gen_retry/cli/validate_schemas.py`
   - `src/gen_retry/cli/validate_fixtures.py`

4. Add contract tests.
   - `tests/contract/test_action_protocol.py`
   - `tests/contract/test_task_spec_schema.py`
   - `tests/contract/test_event_schema.py`
   - `tests/contract/test_planner_view_schema.py`
   - `tests/contract/test_no_environment_facts_in_actions.py`

5. Add architecture notes if schemas change.
   - `docs/decisions/ADR-0001-qianwen-image-edit-backend.md`
   - `docs/decisions/ADR-0002-event-sourced-memory.md`
   - `docs/decisions/ADR-0003-no-separate-refine-action.md`
   - `docs/status.md`

## Required Phase 1 Checks

```bash
python -m gen_retry.cli.validate_schemas
python -m gen_retry.cli.validate_fixtures
pytest tests/contract -q
```

## Gate 1 Review Trigger

Use `sol_reviewer` only if Phase 1 changes:

- the action set;
- memory ownership;
- transition/best-so-far semantics;
- SFT masking semantics;
- backend generate/edit semantics.
