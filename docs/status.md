# Status

## Current Phase

Phase 2 — Mock Replay Runtime in progress.

## Gate State

- Gate 1 Protocol Freeze: APPROVED after user-authorized extra final correction cycle
- Gate 2 Five-Trajectory Pilot Review: not started
- Gate 3 SFT Supervision Freeze: not started

## Protocol

- Current version: draft v0.2
- Live APIs run: no
- External roots configured: yes

## Completed Deliverables

- Phase 0 repository archaeology complete.
- Phase 1 protocol implementation complete pending Gate 1 review.
- Phase 0 reports:
  - `docs/architecture/external_repo_inventory.md`
  - `docs/architecture/legacy_to_v3_field_map.md`
  - `docs/architecture/reuse_adapt_rewrite_retire_matrix.md`
  - `docs/architecture/implementation_gap_report.md`
  - `docs/architecture/phase1_file_plan.md`
- Source provenance updated in `docs/SOURCE_LEDGER.md`.
- Local config files are ignored by `.gitignore`.
- Versioned v0.2 schemas are present for TaskSpec, planner actions, episode
  events, planner views, and artifact manifests.
- Strict action parser, reference validator, TaskSpec builder, and validation CLIs
  are implemented under `src/gen_retry/`.
- Canonical fixtures and contract tests are implemented under `tests/`.
- Gate 1 requested changes addressed:
  - completed image execution events require replayable IDs and artifact refs;
  - nested canonical actions and TaskSpecs are cross-schema validated;
  - `query_skill -> skill_returned` is causally checked by trajectory validation;
  - duplicate constraint/artifact/observation IDs are rejected by semantic
    validators.
- Gate 1 second-cycle requested changes addressed:
  - one episode identity per trajectory is enforced;
  - `task_created` must be first and match nested TaskSpec episode ID;
  - image starts must reference one validated image action;
  - image completions must match a prior start/request and cannot reuse image
    artifact IDs;
  - each attempt can have only one Geneval2 result.
- User-authorized extra Gate 1 correction cycle completed:
  - image start events cannot declare attempt lineage fields;
  - one `skill_returned` event is allowed per `query_skill` action;
  - Geneval2 results must include every TaskSpec constraint;
  - submission events must link to a validated `submit_attempt` action.
- Phase 2 replay runtime slice implemented:
  - append-only JSONL event store;
  - deterministic event loading and trajectory validation;
  - reducer reconstructing attempts, transitions, best-so-far, remaining budget,
    and submission;
  - planner-view builder;
  - replay CLI;
  - fake Qianwen-Image-Edit and fake Geneval2 adapters;
  - five mock episode fixture directories.

## Tests And Results

- Phase 0: documentation/provenance verification only; no live API calls.
- External roots were inspected read-only; their working trees remain dirty as recorded in Phase 0 evidence.
- Phase 1:
  - `python -m gen_retry.cli.validate_schemas` — passed, 5 schemas
  - `python -m gen_retry.cli.validate_fixtures` — passed, 139 fixture records
  - `pytest tests/contract -q` — passed, 48 tests
- Phase 2:
  - `pytest tests/unit -q` — passed, 8 tests
  - `python -m gen_retry.cli.replay_episode examples/one_episode_trajectory.jsonl` — passed
  - `python -m gen_retry.cli.replay_episode examples/one_episode_trajectory.jsonl --planner-view` — passed

## Active Risks

- External source roots have pre-existing dirty working trees; reuse decisions must rely on recorded commit/path/license evidence.
- Legacy Gen-Retry has no root license found, so copying code remains disallowed until file-level license evidence is recorded.
- Geneval2 is CC BY-NC 4.0 and should remain an external evaluator/runtime unless licensing is explicitly reviewed.
- Best-attempt tie-breaking, artifact URI portability, artifact-manifest closure,
  and raw-output retention are recorded as Phase 2 follow-ups, not Gate 1
  blockers.
- The five mock episode fixtures currently share the same validated canonical
  trajectory shape; Phase 2 still needs distinct case-specific trajectories
  before exit criteria are fully satisfied.

## Unresolved Decisions

- None currently blocking Phase 2.

## Last Reviewer Verdict

Gate 1 first verdict: `REQUEST_CHANGES`.

Gate 1 second verdict: `REQUEST_CHANGES`.

Gate 1 final allowed re-review verdict: `REQUEST_CHANGES`.

User authorized one additional and final correction cycle. The four recorded
blocking issues were addressed in the current diff.

Extra final Gate 1 Sol review verdict: `APPROVE`.

## Next Autonomous Action

Continue Phase 2 by making the five mock fixtures case-specific and broadening
deterministic replay/provenance tests around branch recovery.
