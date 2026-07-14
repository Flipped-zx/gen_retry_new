# Gate 1 Review 1

Verdict: `REQUEST_CHANGES`

Reviewer: sol reviewer subagent

## Blocking Issues

1. Canonical events permitted unreplayable image execution histories, including
   completed edits without attempt/source/artifact identity fields and weakly
   typed nested actions.
2. `query_skill -> skill_returned` was not causally enforced.
3. Deterministic identity resolution was underspecified for constraint IDs,
   artifact IDs, and per-attempt Geneval2 observations.

## Resolution Summary

- Split image execution event payload schemas into started and completed
  contracts.
- Required completed execution payloads to include attempt identity, operation,
  backend, image artifact ID, artifact manifest ref, and artifact hash.
- Required edit execution payloads to include source attempt identity; generate
  execution payloads reject source attempts.
- Cross-referenced nested `TaskSpec` and action payloads from the event schema.
- Added semantic trajectory validation for skill causality, known edit sources,
  duplicate attempt IDs, duplicate constraint IDs, duplicate artifact IDs, and
  duplicate Geneval2 observations.
- Added positive `query_skill -> skill_returned` fixture and negative contract
  tests for the reviewer probes.

## Verification

- `python -m gen_retry.cli.validate_schemas` — passed, 5 schemas
- `python -m gen_retry.cli.validate_fixtures` — passed, 38 fixture records
- `pytest tests/contract -q` — passed, 37 tests
