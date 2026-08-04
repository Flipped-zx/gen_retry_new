# ADR-0008: Meaningful Retry Rollout Policy

- Status: Accepted for prospective rollout pilots
- Action protocol: `0.5` unchanged
- PlannerContext: `0.7`
- Teacher policy: `teacher_system_prompt_v9_meaningful_retry_verb_retention`
- Score policy: `geneval2_pass_count_then_gm@1` unchanged

## Context

Teacher v8 rejected a retry after regression or strict no-progress whenever
`(action, source_attempt_id, target_constraint_ids)` matched the previous
image action. That tuple identifies a route, not the actual visual
intervention. In the completed 200-episode pool, 65 v7 decisions reused the
same route after regression/no-progress; 25 later became productive recovery
actions. The hard rule can therefore reject a legitimate second repair of a
persistent atom.

PlannerContext v0.6 retains the latest image instruction but omits older
instructions from `prior_image_rounds`. A Planner cannot avoid an
episode-wide blind retry when it cannot see the earlier intervention.

The verb study also established a prospective `action_pose_relation@2.1.0`
policy: retrieve it after an evaluated verb failure/uncertainty and preserve
same-count historical verb-pass evidence during non-verb repair.

## Decision

1. New prepared score-policy episodes use PlannerContext v0.7. Historical
   v0.6 episodes remain valid and resumable under their persisted version.
2. V0.7 adds only the original executable `instruction` to each
   `prior_image_rounds` record. The value is rebuilt from past canonical action
   events; no LLM summary or future outcome is added.
3. Runtime no longer rejects an action from tuple equality. Teacher policy
   forbids a blind retry and permits the same action/source/targets only when
   the executable instruction changes a concrete visual intervention.
4. Runtime continues to require constraint-level pass evidence before editing
   from a non-best source.
5. Same-pass historical Attempts with pass evidence absent from reducer-best
   are exposed as labeled historical candidate images. Latest/best duplicates
   are sent only once.
6. Skill guidance replay uses the content captured in the immutable tool
   observation only when its SHA-256 matches the `skill_returned` event.
   Current repository Skill content is used only when it matches the persisted
   hash; otherwise replay falls back to the event summary.
7. `action_pose_relation@2.1.0` and delayed verb retrieval remain part of the
   prospective policy. The rejected forced verb-route closure is not adopted.

## Consequences

- Existing v0.6 contexts and completed trajectory artifacts are not modified.
- The action schema, Qwen routing, Geneval2 inference, reducer comparator,
  budget, and submit semantics do not change.
- PlannerContext v0.6 and v0.7 are both compatible with the same accepted
  primary score policy; the rollout plan locks which version an episode uses.
- The current SFT export remains provisional. This ADR does not approve
  `query_skill` supervision or freeze the final v9 SFT inclusion policy.
- Before bulk rollout, v9 must pass the predeclared paired pilot and a
  prospective held-out verb evaluation.

## Review

GPT-5.6 Sol independently recommended this merge of v8.1 verb behavior with
v9 meaningful retry and PlannerContext v0.7. The recommendation explicitly
keeps final SFT export deferred until rollout quality and equal-budget evidence
are frozen.
