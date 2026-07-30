# Checkpoint 150 Teacher-Policy Boundary

The completed-quality increment and cumulative checkpoint-150 cohort contain
only:

`teacher_system_prompt_v7_planner_context_v0_6_primary_score`

Teacher policy v8 was committed after the checkpoint-140 review. Child
processes that had already loaded v7 were allowed to finish. The first valid
v8 submission observed after the frozen checkpoint-150 boundary is
`phase3_ep_166`; it is not included in checkpoint-150 metrics.

Future checkpoint reports group evidence by the persisted
`system_prompt_version` in sanitized Planner requests. They do not infer
policy version from wall-clock time, source-tree state, or episode ID.
