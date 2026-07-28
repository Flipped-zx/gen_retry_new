# Skill Lifecycle Policy v1

Date: 2026-07-15

## Boundary

Foundational Skills teach how to operationalize count, spatial, attribute, and preservation constraints inside generation/edit instructions.

Foundational Skills do not decide:

- whether to generate or edit;
- whether to branch from best or continue latest;
- whether to continue or submit;
- which retry strategy is globally optimal.

## Lifecycle

1. The planner initially sees only Skill IDs, versions, and summaries.
2. A `query_skill` action returns full Skill Markdown, version, content hash, and summary.
3. Full Markdown is injected into the immediately following Teacher request.
4. A compact deterministic operator summary remains active in later PlannerViews.
5. The same Skill identity `(skill_id, version, content_sha256)` may be retrieved at most once per episode by default.
6. At most two Skills may be requested in one query.
7. Consecutive query-only actions are forbidden.
8. A repeated failure of the same capability is not sufficient reason to retrieve the same Skill again.
9. A new query is allowed only for a new capability, an inactive Skill, a changed version/hash, or demonstrated absence of a required operator.
10. If an old event lacks `content_sha256`, the runtime treats the same `skill_id/version` as already active to avoid unsafe duplicate retrieval.

## Active Operator Retention

Active operator summaries are stored in PlannerView `retrieved_experiences` using deterministic entries:

- `experience_id`: `skill:<skill_id>@<version>:<hash-prefix>`;
- `failure_signature`: `active_skill_operator:<skill_id>`;
- `summary`: compact operators extracted from every bullet in the Skill Markdown `### Operators` section, bounded to a deterministic length.

They intentionally do not set `preferred_action`, because foundational Skills must not recommend `generate_image` versus `edit_image`.

This preserves useful prompt-construction guidance without re-injecting full Markdown every turn. The summary is built from hash-verified retrieval-time Skill content in `tool_observations.jsonl`; the mutable current Skill store is not used to reconstruct old identities. If retrieval-time content is unavailable, the runtime falls back only to hash-verified `content_ref` content or marks the content unavailable.

When a Skill is superseded by a changed version/hash, the latest retrieved identity for that `skill_id` replaces the older active summary. The full event log still keeps both retrieval identities.

## Runtime Enforcement

Implemented outside the frozen action schema in `src/gen_retry/phase3/live_runner.py`:

- rejects more than two queried Skills;
- rejects duplicate Skill IDs in one query;
- rejects same Skill identity retrieval once already active;
- permits a changed Skill version/hash as a new identity;
- retains a meaningful representation of every available operator bullet in the compact active summary, within the deterministic length bound;
- rejects consecutive query-only loops;
- allows `skill_ids_used` if grounded by either the immediately retrieved full Skill or an active retained operator summary.

Focused tests:

- `tests/unit/test_skill_v1_runtime_policy.py`

## Logging Requirements

Each Skill retrieval must log:

- Skill ID;
- version;
- content hash;
- retrieval turn;
- active operators;
- downstream action ID when used.

Existing `skill_returned`, `tool_observations.jsonl`, and PlannerView active summaries cover this without storing secrets.
