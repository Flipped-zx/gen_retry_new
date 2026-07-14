# SOL_REVIEW_REQUEST

## Gate

`Protocol Freeze`

## Decision to review

Approve v0.2 Protocol Freeze after the user-authorized extra final correction
cycle. Scope is strictly limited to the four blocking findings recorded in
`docs/reviews/gate1_protocol_freeze_review_3_blocked.md`.

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
  - `src/gen_retry/protocol/trajectory_validator.py`
  - `src/gen_retry/cli/validate_fixtures.py`
  - `tests/contract/test_event_schema.py`
  - `examples/one_episode_trajectory.jsonl`
- Resolved blockers from `gate1_protocol_freeze_review_3_blocked.md`:
  1. Deterministic attempt lineage: `image_execution_started` no longer permits
     `attempt_id` or `parent_attempt_id`; completion events are the source of
     attempt lineage and must match the prior start by request/operation/backend/source.
  2. One skill response per query: trajectory validation tracks consumed
     `query_skill` action IDs and rejects duplicate `skill_returned` events.
  3. Evaluator completeness: each `geneval2_completed` event must cover every
     TaskSpec constraint, with duplicate and unknown constraint observations
     rejected.
  4. Submission causality: each `attempt_submitted` event must reference a
     validated `submit_attempt` action and match selected attempt and reason
     code. The canonical example now includes this action before submission.
- Focused negative tests:
  - image start cannot declare attempt lineage;
  - duplicate skill response for one query is rejected;
  - incomplete Geneval2 result is rejected;
  - submission without a linked validated submit action is rejected;
  - submission payload/action mismatch is rejected.
- Test summary:
  - `python -m gen_retry.cli.validate_schemas` passed, 5 schemas
  - `python -m gen_retry.cli.validate_fixtures` passed, 39 fixture records
  - `pytest tests/contract -q` passed, 48 tests

## Questions

1. Are the four recorded Gate 1 blockers resolved without adding actions or
   expanding the roadmap?
2. Is the protocol now replayable enough to begin Phase 2 event-store/reducer
   implementation?
3. Are residual items in `docs/followups/phase2_replay_followups.md` acceptable
   as Phase 2 follow-ups rather than Gate 1 blockers?

## Explicit non-goals

- Do not review live Qianwen-Image-Edit, Geneval2, GPT teacher, SFT exporter, or
  runtime concurrency implementation.
- Do not introduce new blocking requirements unless there is a concrete
  correctness, replayability, or train/inference consistency defect.
- Do not redesign the action set or expand the roadmap.

## Expected response

- Return exactly one verdict: `APPROVE`, `REQUEST_CHANGES`, or `BLOCKED`.
- If the four recorded blockers are resolved, expected verdict is `APPROVE`.
- Documentation-only or optional improvements should be follow-ups, not blockers.
- Do not implement code.
