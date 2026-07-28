# Planner I/O v0.5 Field/SFT Sol Review

Date: 2026-07-26

Reviewer: GPT-5.6 Sol

Scope: read-only review of Planner I/O field clarity, SFT target boundaries, and the smallest v0.5 design change needed before SFT-facing freeze.

Superseded decision note (2026-07-26): the subsequent v0.5 schema/Skill Sol
review rejected canonical `decision_summary` and rejected required-but-zero-loss
masking. The implemented v0.5 schema removes both `decision_summary` and
`diagnosis_summary`; `ADR-0005` is authoritative.

## Verdict

`REQUEST_CHANGES`

v0.4 is a reasonable base for v0.5, but the current display artifacts must not be treated as training data or final SFT fixtures.

## Blocking Issues

1. `ADR-0005` is stale relative to v0.4.

   The ADR still describes v0.3 targets such as `diagnostic_hypotheses`, `interventions`, `skill_ids_used`, and submit `decision_summary`, while `schemas/action_protocol_v0_4.schema.json` uses the smaller v0.4 target shape. Before any v0.5 SFT freeze, the ADR and schema must agree.

2. The current SFT display JSON is not trainable data.

   `docs/phase3/planner_io_v04_sft_message_view_phase3_ep001.json` contains `_note` in assistant content, empty `decision_summary` values from the old normalized trajectory, and non-schema display fields. It is useful as a human-readable view only.

3. The query-skill observation boundary still needs one clean transcript proof.

   The final SFT message layout must show:

   ```text
   assistant(query_skill action)
   -> tool_response(skill content, loss 0)
   -> assistant(next planner action)
   ```

   Skill returns may enter later planner context as observation, but they are not assistant targets.

## Recommended v0.5 Direction

Keep the v0.4 action-only target principle. Improve field names so the planner input separates image state from action history:

| v0.4 | v0.5 recommendation | Meaning |
|---|---|---|
| `latest_observation` | `latest_attempt` | The newest generated image state and Geneval2 atom snapshot. |
| `episode_memory.recent_round` | `episode_memory.last_completed_image_round` | The previous image-producing round, including action, source, result, and transition. |
| `episode_memory.earlier_rounds` | `episode_memory.prior_image_rounds` | Older compressed image rounds. |
| `episode_memory.best_attempt` | `episode_memory.best_attempt` | Historical best attempt, which may differ from latest. |
| outside PlannerContext | `visible_images` | Multimodal latest/best image bindings, kept outside JSON context. |

Reviewer preference:

- Rename `comparison_attempt_id` to `baseline_attempt_id`.
- Do not duplicate best constraint results when best is the same as latest.
- Do not fill initial generation outcome with many empty transition arrays.
- Keep generated images, Geneval2 outcomes, best/latest, and budget as environment-owned facts.

## Action Output Guidance

Sol recommended shrinking action targets further:

- keep the four actions;
- unify `generation_instruction` and `edit_instruction` to `instruction`;
- keep `source_attempt_id`, `target_constraint_ids`, `preserve_constraint_ids`, and submit `reason_code`;
- delete free-text `diagnosis_summary`;
- consider deleting or zero-loss masking `decision_summary` if it proves noisy.

Main-thread design decision:

- Keep a short bounded `decision_summary` in v0.5 generate/edit actions because Gen-Retry is training a planner, not only a prompt writer. The field records why the planner chose generate/edit/source/rollback under the visible state.
- Remove `diagnosis_summary` from the canonical target. The final `instruction` plus target/preserve IDs should carry the executable repair content.

## Minimal Validation Before Freeze

Run an offline v0.4-to-v0.5 renderer comparison over existing event streams:

1. cover initial generation, query skill, monotonic improvement, regression, rollback, and submit;
2. validate action schema, context schema, reference validity, and loss masks;
3. prove no `_note`, raw teacher output, tool response, image result, Geneval2 result, best/latest update, or budget update has target loss;
4. compare token counts and action-valid rate against v0.4.

No live API or image generation is required for this review.
