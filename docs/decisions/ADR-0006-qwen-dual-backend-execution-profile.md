# ADR-0006: Qwen Dual-Backend Execution Profile

- Status: Accepted
- Execution profile: `qwen_dual_backend@1`
- Action protocol: `0.5`
- PlannerContext: `0.5`
- Supersedes: ADR-0001

## Context

ADR-0001 routed both logical image actions through Qwen-Image-Edit. A
source-free `generate_image` was implemented by giving the edit pipeline a
white canvas. The local environment now contains a native text-to-image model,
`Qwen-Image-2512`, in addition to `Qwen-Image-Edit-2511`.

Gen-Retry models a human retry workflow in which a fresh generation and an
edit of an existing image are genuinely different operations. The canonical
v0.5 Action already expresses that distinction without a backend field.

## Decision

Introduce an independently versioned environment execution profile:

```text
execution_profile_id: qwen_dual_backend
execution_profile_version: 1

generate_image -> Qwen-Image-2512
edit_image     -> Qwen-Image-Edit-2511
```

`generate_image` never has a source and creates a root Attempt. `edit_image`
requires a historical source Attempt and artifact and creates a child Attempt.

The Planner does not predict backend, model ID, mode, paths, or sampling
metadata. These remain environment-owned provenance.

## Protocol consequences

- Keep `action_protocol_version=0.5`.
- Keep `planner_context_version=0.5`.
- Do not add `regenerate_image`, `mode`, or `backend` fields.
- A later `generate_image` is a source-free restart under the same logical
  action as the initial generation.
- No new action-specific instruction heuristic becomes a hard protocol
  validator in this change.

## Provenance invariants

- One episode is locked to one execution profile.
- Every image execution records profile ID/version, logical action, backend ID,
  model ID and revision/fingerprint, pipeline ID, adapter version, complete
  sampling parameters, source/result Attempt IDs, source digest when
  applicable, and output digest.
- Resume must reject a profile mismatch.
- Legacy `qwen_image_edit` edit-only trajectories are not rewritten.
- SFT export must filter or group by execution profile so white-canvas
  generation instructions are not silently mixed with native T2I generation
  instructions.

## Experiment boundary

Acceptance requires the five-prompt diagnostic specified in
`docs/architecture/planner_execution_v0_7_dual_backend.md`:

- ten adaptive trajectories, five per profile;
- five paired first-generation renderer comparisons with frozen instruction
  and seed;
- at least one edit-route consistency check;
- no aggregate benchmark claim from this selected diagnostic set.

## Acceptance evidence

- GPT-5.6 Sol amended-design review: `APPROVE`, recorded in
  `docs/reviews/planner_execution_v07_dual_backend_review.md`.
- Focused dual-route, provenance, resume-lock, event-schema, trajectory, and
  SFT-profile invariant tests pass.
- No dual-backend live trajectory was launched before acceptance.
