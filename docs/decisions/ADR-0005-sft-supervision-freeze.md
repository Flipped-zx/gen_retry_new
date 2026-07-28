# ADR-0005: SFT Supervision Freeze

## Status

Accepted; amended for Planner I/O v0.5 on 2026-07-26.

## Context

Gate 2 approved the Phase 3 trajectories as sufficient evidence for an SFT
supervision freeze. Subsequent Planner I/O reviews found two unresolved
problems:

1. v0.4 required free-text `decision_summary` and `diagnosis_summary` fields.
   The available v0.4 display trace was projected from v0.3 rather than
   produced by a native live rollout, so its empty summaries were neither
   positive nor negative evidence and could not be used as SFT labels.
2. Skill retrieval mechanics were valid, but Skill utility had not demonstrated
   target repair without preserved-atom regression.

The field was reconsidered with a native GPT-5.5 teacher-only A/B pilot over
five fixed pre-outcome PlannerContexts. Both protocols produced 10/10 valid and
decision-correct actions, but two candidate summaries for broad-failure
regeneration merely restated target/preserve intent and did not explain why
fresh generation was chosen over localized editing. Because the predeclared
acceptance criterion required 10/10 summaries to add genuine
state-to-decision supervision, the final Sol verdict was `FAIL_KEEP_V05`.

A required inference field must be trained, so required-but-zero-loss remains
invalid. The native pilot did not justify making the free-text field a
trainable requirement; the coherent current choice is to exclude it.

## Decision

For new rollout and SFT-facing records, the canonical protocol is:

- `schemas/action_protocol_v0_5.schema.json`
- `schemas/planner_context_v0_5.schema.json`

Older v0.2, v0.3, and v0.4 actions remain immutable historical records and
continue to validate inside the event envelope. They are not silently rewritten
or treated as native v0.5 targets.

The v0.5 assistant action target contains only:

- `query_skill`: `skill_ids`, `target_constraint_ids`;
- `generate_image`: `target_constraint_ids`,
  `preserve_constraint_ids`, `instruction`;
- `edit_image`: `source_attempt_id`, `target_constraint_ids`,
  `preserve_constraint_ids`, `instruction`;
- `submit_attempt`: `selected_attempt_id`, `reason_code`.

The canonical v0.5 action excludes `decision_summary`, `diagnosis_summary`,
`mode`, `strategy_tags`, `skill_ids_used`, `diagnostic_hypotheses`,
`interventions`, `repair_plan`, and environment-owned facts.

Training and inference use the same message contract:

1. `system`: fixed Gen-Retry v0.5 planner contract;
2. `user`: canonical PlannerContext, visible image bindings, and response
   contract;
3. `assistant`: exactly one canonical v0.5 action when selected as a target.

Loss mask:

- `system`: 0;
- `user`: 0;
- `query_skill` assistant action: 0;
- `skill_returned` and all tool/environment observations: 0;
- raw teacher output: 0;
- selected canonical `generate_image`, `edit_image`, or `submit_attempt`: 1.

Positive target selection:

- Include only canonical v0.5 `generate_image`, `edit_image`, and
  `submit_attempt` actions labeled `trainable_positive` or
  `recovery_positive`.
- Keep `query_skill` as a real Planner Action in canonical history, but do not
  optimize it until Skill utility validation is accepted.
- Keep harmful, ineffective, ambiguous, invalid, and format-error actions as
  context/audit evidence only.
- Keep harmful or ineffective actions in history when needed to supervise a
  later recovery action.

`query_skill` may become trainable only after capability-isolated evidence
shows that the query is relevant, the returned version/hash is used by the next
image action, at least one target atom improves, and no preserve atom regresses.

Splits remain stable SHA-256 prompt-group splits. Context audit retains the 24k
context-token and 1.4k target-token budgets. Truncation drops oldest prior image
rounds first while preserving TaskSpec, latest attempt, best attempt, and
visible image bindings.

## Consequences

- Planner supervision is expressed by action choice, source selection,
  target/preserve sets, executable instruction, and submit selection rather
  than free-text rationale.
- Required inference fields and trained target fields remain aligned.
- Skill retrieval remains visible and replayable without prematurely making it
  positive SFT behavior.
- Existing Phase 4 exports produced under older policies are audit artifacts,
  not final v0.5 training records.
