# Planner I/O v0.4 Sol Review

## Verdict

Adopt v0.4 as the planner I/O source of truth. The migration is architecturally reasonable because it removes duplicated self-reported fields while preserving the execution-critical decisions: action type, edit source, target/preserve constraints, final executable instruction, latest/best separation, and source-relative outcomes.

## Blocking Work Identified

1. Replace action and PlannerContext schemas with v0.4.
2. Rewrite PlannerContext rendering to expose only `task_context`, `latest_observation`, `skill_context`, `episode_memory`, and `runtime_state`.
3. Keep round/timeline processing internal so query_skill can still be aligned with the terminal image action.
4. Consolidate Skill guidance into `skill_context.active_skills`.
5. Rewrite teacher prompting, provider schema, parser, and reference validation to remove v0.3-only fields.
6. Move legal actions and budget to `runtime_state`; visible images must be multimodal bindings outside PlannerContext.

## Risks

- The old v0.3 live trajectory does not match the v0.4 golden branch sequence; use the real `teacher_prompt_v1_validation/phase3_ep_001` event sequence for golden replay.
- Existing query_skill events provide a shared target constraint list. The implementation needs a deterministic per-skill target mapping.
- Skill guidance needs deterministic full/summary behavior because `skill_ids_used` is removed.

## Minimal Validation

Use the real `phase3_ep_001` branch sequence to verify:

```text
query_skill -> generate_image -> generate_image -> edit_image(a_001)
-> edit_image(a_002) with regression -> edit_image(a_002) rollback
-> submit_attempt(a_002)
```

The replay must prove source-relative edit comparison, latest/best separation, rollback from historical best, and submit of non-latest best.
