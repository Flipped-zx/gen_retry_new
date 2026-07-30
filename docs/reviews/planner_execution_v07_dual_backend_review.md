# Planner Execution Dual-Backend Review

Reviewer: GPT-5.6 Sol

Initial verdict: `REQUEST_CHANGES`

## Blocking changes

1. Keep Action Protocol and PlannerContext at v0.5. Version the execution
   profile independently as `qwen_dual_backend@1`; do not serialize the
   informal v0.7 label as a schema version.
2. Add a new ADR that explicitly supersedes ADR-0001 when accepted.
3. Do not silently add heuristic action-instruction hard validation under the
   unchanged v0.5 protocol.
4. Persist complete per-execution profile, backend, model, pipeline, sampling,
   source, result, and digest provenance. Lock one profile per episode and
   reject profile mismatches on resume.
5. Filter or group SFT records by execution profile. Legacy white-canvas
   generation instructions and native T2I instructions must not be silently
   mixed.
6. Run five prompts under both adaptive profiles. Renderer attribution also
   requires five paired first-generation calls using identical canonical
   instruction and seed, plus one edit-route consistency check.

## Amendments

The blocking changes are incorporated in:

- `docs/architecture/planner_execution_v0_7_dual_backend.md`
- `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`

## Final review

Verdict: `APPROVE`

The reviewer confirmed that:

- independent execution-profile versioning preserves v0.5 Action and
  PlannerContext SFT semantics;
- the amended provenance, episode lock, resume rejection, and SFT grouping
  requirements remove ambiguous backend ownership;
- the ten adaptive trajectories, five paired first generations, and one fixed
  edit-route check establish the minimum attribution boundary.

The design is approved for implementation and invariant tests. ADR-0006 remains
Proposed until those tests pass and must become Accepted before any live
dual-backend trajectory starts.
