# Phase 2 Replay Follow-ups

These items are not Gate 1 blockers. They should be resolved through Phase 2
event-store, reducer, and replay tests.

## Follow-ups

- Define deterministic best-attempt tie-breaking when attempts have equal pass
  counts or equivalent evaluator status.
- Check artifact-manifest closure: every planner view, raw output, image,
  evaluator report, and event log ref should resolve through the episode
  artifact manifest.
- Define portable artifact URI rules for local paths versus run-relative refs.
- Finalize raw-output retention and redaction policy for artifact-backed raw
  assistant outputs.
