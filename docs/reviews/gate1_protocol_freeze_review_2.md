# Gate 1 Review 2

Verdict: `REQUEST_CHANGES`

Reviewer: sol reviewer subagent

## Blocking Issues

1. Episode identity was not fully enforced: mixed `episode_id` values, mismatched
   task envelope/TaskSpec episode IDs, and actions before `task_created` could
   pass trajectory validation.
2. Attempt identity and causality were still ambiguous: image completions could
   appear without matching starts/actions, image artifact IDs could be reused
   across attempts, and multiple Geneval2 results could be recorded for one
   attempt.

## Resolution Summary

- `validate_trajectory_events` now requires non-empty trajectories with
  `task_created` first.
- All events must share one `episode_id`.
- `task_created.episode_id` must match nested `TaskSpec.episode_id`.
- `action_validated` before `task_created` is rejected.
- `image_execution_started` must reference exactly one validated
  `generate_image` or `edit_image` action and must match operation/source.
- `image_execution_completed` must match a prior start by `request_id`, must
  reference the start event, and must match operation/backend/source.
- Image artifact IDs are unique.
- Each request can start and complete only once.
- Each attempt can have only one Geneval2 result.

## Verification

- `python -m gen_retry.cli.validate_schemas` — passed, 5 schemas
- `python -m gen_retry.cli.validate_fixtures` — passed, 38 fixture records
- `pytest tests/contract -q` — passed, 43 tests
