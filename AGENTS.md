# AGENTS.md — Gen-Retry v3（clean-room repository）

## Mission

Build a verifier-grounded, image-aware, history-aware retry agent for rubric-based image generation. The agent must emit exactly one strict executable action per assistant turn and must use canonical attempt history.

Read, in order:

1. `README_START_HERE.md`
2. `DEVELOPMENT_BLUEPRINT.md`
3. `docs/architecture/MODULE_CONTRACTS.md`
4. the current task under `tasks/`

## Repository boundary

- This repository is the only writable implementation root.
- Legacy Gen-Retry, Gen-Searcher, GenEvolve, and Geneval2 roots are external evidence sources configured in `configs/paths/local.yaml`.
- Treat all external roots as read-only, even when operating-system permissions would allow writes.
- Never create production imports, editable installs, symlinks, or runtime dependencies that reach into the legacy Gen-Retry repository.
- Code may be copied only after path/commit/license evidence is recorded and the copy is adapted behind a v3 module contract.
- All generated reports, fixtures, patches, and notes must be written inside this repository.

## Source-of-truth order

1. Versioned JSON Schemas under `schemas/`.
2. Accepted ADRs under `docs/decisions/`.
3. `docs/architecture/MODULE_CONTRACTS.md`.
4. `DEVELOPMENT_BLUEPRINT.md`.
5. Repository code and tests.
6. `docs/SOURCE_LEDGER.md`.

When these conflict, stop and report the conflict. Do not silently invent a protocol.

## Fixed backend semantics

- The only image execution backend in v0.2 is **Qianwen-Image-Edit**.
- `generate_image` and `edit_image` remain separate logical actions.
- Both actions are executed through one adapter: `QianwenImageEditAdapter`.
- `generate_image` uses generation/regeneration mode without a source attempt.
- `edit_image` requires a valid `source_attempt_id` and source image artifact.
- Never reintroduce a separate Qwen-Image generator unless an ADR explicitly changes this decision.

## Core invariants

- Planner outputs exactly one action: `query_skill`, `generate_image`, `edit_image`, or `submit_attempt`.
- A generation/edit instruction is an action argument; do not add a separate `refine_prompt` action.
- Geneval2 results, scores, transitions, best-so-far, lineage, budget, and paths are environment-owned facts.
- Raw assistant output never enters persistent memory.
- Persistent memory is derived from immutable events by deterministic reducers.
- Skill selection must be a real `query_skill -> tool_response` interaction.
- Tool responses and image/evaluator observations are context only, not SFT targets.
- Harmful actions can remain in canonical history but are not positive SFT targets by default.
- Never store secrets in code, events, artifacts, fixtures, reports, or prompts.

## Development behavior

- Work depth-first in small testable increments.
- Prefer schema, fixtures, parsers, reducers, and replay tests before live APIs.
- All expensive calls must be idempotent, resumable, artifact-backed, and cacheable.
- Do not refactor unrelated code.
- A schema change must update schema, fixture, parser, tests, changelog, and affected ADR together.
- Every completed phase updates `docs/status.md`.

## Grounding policy

When borrowing from Gen-Searcher, GenEvolve, or papers:

1. Use the read-only `source_researcher` subagent.
2. Record exact repository paths, commit hashes when available, or paper sections in `docs/SOURCE_LEDGER.md`.
3. Label evidence as `repository-grounded`, `paper-grounded`, or `local-design`.
4. Check licenses before copying code.
5. Prefer interface and workflow ideas over blind code copying.
6. Do not repeat broad searches already captured in the ledger unless the source changed.

## Delegation and review

### Ordinary work

Use the main Codex 5.5 High/XHigh thread for implementation, tests, debugging, adapters, CLI, docs, and focused reviews.

### Read-only source research

Use `source_researcher` for external repository archaeology and API/document verification. It must read source roots from `configs/paths/local.yaml` and must not modify them.

### High-level reviewer

Use `sol_reviewer` only when:

1. action/message schema semantics change;
2. memory ownership, transition, branching, or best-so-far semantics change;
3. SFT masking or productive/harmful/recovery supervision changes;
4. the experiment may not prove the claimed contribution;
5. a difficult-to-reverse concurrency/resume design changes;
6. five-pilot evidence exposes conflicting requirements.

Before spawning it, fill `docs/templates/SOL_REVIEW_REQUEST.md`. Ask at most three questions and attach only the minimum schema/diff/test summary.

### Mandatory gates

- Gate 1: Protocol Freeze.
- Gate 2: Five-Trajectory Pilot Review.
- Gate 3: SFT Supervision Freeze.

No repeated broad audits outside these gates.

## Required validation

Use the narrowest relevant tests. Once available, protocol/trajectory changes must run:

```bash
pytest tests/contract -q
pytest tests/unit -q
python -m gen_retry.cli.validate_schemas
python -m gen_retry.cli.validate_fixtures
python -m gen_retry.cli.replay_episode examples/one_episode_trajectory.jsonl
```

## Task completion report

Report:

1. files changed;
2. behavior implemented;
3. commands/tests and results;
4. assumptions;
5. remaining risks;
6. whether a review gate was triggered.
