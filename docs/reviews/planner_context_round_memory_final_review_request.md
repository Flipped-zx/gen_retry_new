# SOL_REVIEW_REQUEST

## Gate

PlannerContext / Planning Round / Episode Memory final implementation review.

## Decision to review

Gen-Retry v3 now uses PlannerContext v0.3 and completed RoundRecords to make `query_skill`, `generate_image`, `edit_image`, and `submit_attempt` explicit Planner Actions with round-scoped memory and source-based transition semantics.

## Current evidence

Relevant schema/ADR/design:

- `schemas/action_protocol_v0_3.schema.json`
- `schemas/planner_context_v0_3.schema.json`
- `schemas/episode_event_v0_2.schema.json`
- `schemas/artifact_manifest_v0_2.schema.json`
- `docs/phase3/planner_context_round_memory_design.md`
- `docs/decisions/ADR-0005-sft-supervision-freeze.md`
- `docs/phase3/planner_context_round_memory_comparison.md`

Implementation files:

- `src/gen_retry/runtime/planner_context.py`
- `src/gen_retry/phase3/live_runner.py`
- `src/gen_retry/protocol/action_parser.py`
- `src/gen_retry/protocol/reference_validator.py`
- `src/gen_retry/protocol/provider_schemas.py`
- `src/gen_retry/agent/teacher_client.py`
- `src/gen_retry/sft/supervision.py`
- `src/gen_retry/cli/export_trajectory_trace.py`

Minimal test/pilot summary:

- `pytest tests/contract -q` — 58 passed.
- `pytest tests/unit -q` — 43 passed.
- `python -m gen_retry.cli.validate_schemas` — 7 schemas validated.
- `python -m gen_retry.cli.validate_fixtures` — 104 fixture records validated.
- `python -m gen_retry.cli.replay_episode examples/one_episode_trajectory.jsonl --planner-context` — passed.
- Live trajectory: `runs/planner_context_v0_3/phase3_ep_001`
  - 5 image attempts.
  - 5 Geneval2 evaluations.
  - 5 persisted RoundRecord artifacts.
  - submitted `a_004`.
  - final Geneval2: 10 pass, 1 fail (`c_004`).
  - rollback/source case: latest `a_003`, best `a_000`, final edit `a_000 -> a_004`, submit best `a_004`.

Known caveats:

- This is a single live architecture-validation trajectory, not a performance proof.
- The live run includes recoverable `format_error` events from rejected teacher outputs; only validated canonical actions are SFT targets.
- Existing v0.2 schema remains available only for old fixtures/replay compatibility. New live actions use v0.3 and do not emit `strategy_tags`.

## Questions

1. Do the implemented Planner Action, Action Step, Planning Round, Attempt, and RoundRecord semantics satisfy the goal, especially that `query_skill` belongs to the current round while tool/evaluator outputs remain environment observations?
2. Are edit transitions, rollback, latest/best/source separation, initial-generation outcome, and future-leakage boundaries implemented correctly enough for the new live trajectory and golden replay evidence?
3. Are action schema v0.3, provider schema/runtime validator split, removal of `strategy_tags`, operation registry, and SFT target/context boundaries acceptable, or is there any blocking ambiguity before treating this as the new trajectory format?

## Explicit Non-Goals

- Do not review Qwen image quality or Geneval2 model accuracy.
- Do not require broader multi-trajectory performance evidence.
- Do not require RL or dataset-build changes beyond the SFT target/context boundary already touched.

## Expected Response

Return exactly:

- `PASS`

or:

- `FAIL`
- blocking issue 1
- blocking issue 2

Only list blocking issues. Do not propose broad future enhancements as blockers.
