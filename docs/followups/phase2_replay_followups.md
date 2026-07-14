# Phase 2 Replay Follow-ups

These items are not Gate 1 blockers. They should be resolved through Phase 2
event-store, reducer, and replay tests.

## Follow-ups

- [x] Define deterministic best-attempt tie-breaking when attempts have equal pass
  counts or equivalent evaluator status.
- [x] Define portable artifact URI rules for local paths versus run-relative refs.
- [x] Add content-hash manifest closure checks for persisted fake image and
  evaluator report artifacts.
- [ ] Extend artifact-manifest closure to planner view, raw output, and event log
  refs when the runner materializes those artifacts.
- [ ] Finalize raw-output retention and redaction policy for artifact-backed raw
  assistant outputs.
