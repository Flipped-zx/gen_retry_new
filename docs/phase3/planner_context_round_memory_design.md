# PlannerContext, Planning Round, and Episode Memory Design

Date: 2026-07-16

## Current Audit

Current live rollouts use `PlannerView` as the full teacher input state. The object is built by `src/gen_retry/runtime/planner_view.py`.

Current `compact_history` is deterministic but too thin:

```python
{
  "attempt_id": ...,
  "parent_attempt_id": ...,
  "image_artifact_id": ...,
  "action_type": ...,
  "passed_constraint_ids": ...,
  "failed_constraint_ids": ...
}
```

It does not include the image action's decision summary, diagnostic hypotheses, interventions, `generation_instruction` / `edit_instruction`, or per-attempt transition. The teacher can infer some facts from `latest_transition`, `constraint_state`, visible images, and active Skill summaries, but it cannot directly see how each historical action attempted to solve the problem.

Current transition computation already uses the real edit source:

- for `edit_image`, transition source is `attempt.parent_attempt_id`, which is copied from `source_attempt_id`;
- for non-initial `generate_image`, transition source is the previous latest attempt;
- for the first generation, there is no source and no fixed/regressed atoms are fabricated.

Current action protocol still requires `strategy_tags`, and the teacher prompt requires the same. These tags duplicate the intended role of `interventions[].operation` and should be removed for new trajectories.

## Design Choice

Keep the event-sourced runtime, Qwen adapter, Geneval2 adapter, budget semantics, and best-attempt ranking unchanged. Add a deterministic PlannerContext and RoundRecord layer built from canonical events.

The old `PlannerView` module may remain as a compatibility import, but the public serialized object for new rollouts is `PlannerContext`.

## PlannerContext

Top-level shape:

```json
{
  "schema_version": "0.3",
  "episode_id": "phase3_ep_001",
  "task_context": {},
  "latest_observation": {},
  "active_round": {},
  "episode_memory": {},
  "control": {}
}
```

### task_context

Contains the original prompt, max image attempts, and canonical Geneval2 constraints.

### latest_observation

Represents the latest evaluated image state before the next planner action.

It is `null` before any image attempt. It does not change after `query_skill`; it updates only after `generate_image` / `edit_image` is executed and evaluated.

### active_round

Represents the current unfinished Planning Round:

```json
{
  "round_id": "r_000",
  "start_attempt_id": null,
  "planning_actions": [
    {
      "step_id": "s_000",
      "turn_id": "turn_000",
      "action_event_id": "evt_0004",
      "action": "query_skill",
      "requested_skill_ids": ["counting_and_instance_layout"],
      "target_constraint_ids": ["c_001"],
      "tool_response_ref": {"event_id": "evt_0005"}
    }
  ],
  "tool_responses": [
    {
      "event_id": "evt_0005",
      "query_action_event_id": "evt_0004",
      "returned_skill_ids": ["counting_and_instance_layout"],
      "skills": [
        {
          "skill_id": "counting_and_instance_layout",
          "version": "1.0.0",
          "content_sha256": "...",
          "summary": "..."
        }
      ]
    }
  ],
  "active_capability_skills": [
    {
      "skill_id": "counting_and_instance_layout",
      "summary": "..."
    }
  ]
}
```

`query_skill` is a real planner action and belongs to this active round. It does not create an attempt, image transition, or budget decrement.

`planning_actions[]` stores assistant-owned canonical actions only, plus a stable link to the tool response event. `tool_responses[]` stores environment-owned Skill results. SFT masking treats the query action as assistant target when selected, and the linked tool response as context only.

### episode_memory

Stores completed rounds, not raw attempt rows.

```json
{
  "recent_round": {},
  "earlier_rounds": [],
  "best_attempt": {}
}
```

`recent_round` keeps the full most recent completed RoundRecord. `earlier_rounds` keep compact deterministic summaries. `best_attempt` keeps the best image state and the source round/action summary that produced it.

### control

Contains step/round counters, budget, latest/best IDs, legal actions, and submit eligibility.

## RoundRecord

A completed image-producing round records:

```json
{
  "round_id": "r_002",
  "start_observation_ref": {"attempt_id": "a_001"},
  "planning_actions": [],
  "tool_responses": [],
  "image_action": {
    "step_id": "s_005",
    "action_event_id": "evt_0037",
    "action": "edit_image",
    "source_attempt_id": "a_001",
    "decision_summary": "...",
    "diagnostic_hypotheses": [],
    "interventions": [],
    "target_constraint_ids": [],
    "preserve_constraint_ids": [],
    "skill_ids_used": [],
    "execution_instruction": "..."
  },
  "result_attempt_id": "a_002",
  "outcome_comparison_ref": {
    "attempt_id": "a_001",
    "reason": "edit_source"
  },
  "observed_outcome": {
    "fixed_constraint_ids": [],
    "regressed_constraint_ids": [],
    "persistent_failed_constraint_ids": [],
    "preserved_constraint_ids": [],
    "initial_passed_constraint_ids": [],
    "initial_failed_constraint_ids": [],
    "initial_uncertain_constraint_ids": [],
    "new_uncertain_constraint_ids": [],
    "resolved_uncertain_constraint_ids": []
  },
  "value": {
    "score_delta": 0,
    "net_atom_gain": 0,
    "became_best": false
  }
}
```

`outcome_comparison_ref` is the source of truth for the transition calculation. For `edit_image`, it is always the action's `source_attempt_id`; for non-initial `generate_image`, it is the latest attempt before generation; for the first generation, it is `null` with reason `initial_generation`. `observed_outcome` and `value.score_delta` are computed against this reference, not against `start_observation_ref` when those differ.

The outcome is environment-owned and is never copied into the image action target.

For live runs, each completed RoundRecord is written as `round_records/round_record_XXX.json`,
recorded in `manifest.json` as artifact type `round_record`, and linked by a
`round_record_persisted` event before the next PlannerContext is built. Older
completed runs can regenerate the same artifacts post-hoc from immutable events
without changing the canonical action history.

## Action Protocol v0.3

The action names remain:

- `query_skill`
- `generate_image`
- `edit_image`
- `submit_attempt`

`generate_image.arguments`:

```json
{
  "mode": "initial",
  "decision_summary": "...",
  "diagnostic_hypotheses": [
    {
      "constraint_ids": ["c_001"],
      "visual_targets": ["red cat group"],
      "hypothesis": "The count may fail if cats are fused, cropped, or duplicated as reflections."
    }
  ],
  "interventions": [
    {
      "operation": "instance_count_layout",
      "target_constraint_ids": ["c_001"],
      "visual_targets": ["red cat group"],
      "change": "Render exactly two separated, fully visible cats with no reflected duplicates."
    }
  ],
  "target_constraint_ids": [],
  "preserve_constraint_ids": [],
  "skill_ids_used": [],
  "generation_instruction": "..."
}
```

`edit_image.arguments`:

```json
{
  "source_attempt_id": "a_001",
  "decision_summary": "...",
  "diagnostic_hypotheses": [],
  "interventions": [],
  "target_constraint_ids": [],
  "preserve_constraint_ids": [],
  "skill_ids_used": [],
  "edit_instruction": "..."
}
```

`strategy_tags` is removed. There is no legacy projection from `interventions[].operation` back to tags.

`mode` is retained for `generate_image` because current code and prior supervision use it to distinguish first generation from regeneration; the actual action choice is still `generate_image`, and the reason belongs in `decision_summary`.

`submit_attempt.arguments` adds a required `decision_summary` in v0.3 so the final action target states why submitting is better than spending more budget or why the budget forces submission.

`diagnostic_hypotheses[]` item schema:

- `constraint_ids`: 1 to 4 known target constraint IDs;
- `visual_targets`: 1 to 6 short entity or group names from the prompt/rubric;
- `hypothesis`: 12 to 360 characters, an actionable visual failure hypothesis rather than a restatement of fail/pass.

`interventions[]` item schema:

- `operation`: one value from the minimal registry below;
- `target_constraint_ids`: 1 to 6 known target constraint IDs;
- `visual_targets`: 1 to 6 short entity or group names;
- `change`: 12 to 480 characters describing the concrete visual change.

An image action may contain up to 12 interventions so complex Geneval2 prompts can map separate atom groups to separate operation labels without forcing ambiguous combined labels.

Runtime validation enforces that diagnostic and intervention constraint IDs are legal and are subsets of the image action's `target_constraint_ids`. Initial `generate_image` may omit diagnostic hypotheses because there is no failed observation yet; `edit_image` and `generate_image(mode="regenerate")` require at least one diagnostic hypothesis. All image actions require at least one intervention.

## Operation Registry

Minimal registry, grounded in current Skills and actual trajectory instructions. The registry names visual intervention families, not hidden intent labels:

| Operation | Evidence | Meaning |
|---|---|---|
| `instance_count_layout` | `counting_and_instance_layout` operators; actual count repair/generation instructions | Control exact cardinality, separated visible instances, and no extras/fused/reflected duplicates. |
| `spatial_relation_layout` | `spatial_relation_layout` relation/depth/frame operators; actual donut/cat prompts | Arrange static relative position, depth layer, occlusion, and frame anchors for position atoms. It does not cover pose, gaze, or motion evidence. |
| `action_pose_cue` | `spatial_relation_layout` chasing/following/facing operators; actual lion pursuit edits | Add verb/action evidence such as body pose, gaze direction, limb position, speed marks, or pursuit cues. It does not cover static relative placement, depth, or count. |
| `attribute_binding` | `attribute_entity_binding` color/material/entity operators; actual glass/red/brown prompts | Bind color, material, texture, or identity to the correct entity without leakage. |

No `other` / `custom_operation` is included initially. If the teacher needs a new operation, the runtime should reject it and force a schema/policy update rather than silently accept an ungrounded taxonomy expansion.

If a single image action needs both spatial placement and action evidence, the teacher should emit two intervention items, one `spatial_relation_layout` and one `action_pose_cue`, rather than stretching either operation label.

Known unavailable evidence: local shallow search found NEWTON and GenEvolve materials, but did not find local GEMS or CODESKILL source/PDF artifacts under `/root/private_data/agentic_image` at max depth 6. Existing `docs/SOURCE_LEDGER.md` contains prior broad GEMS notes only.

## Source Evidence Used

- Local Capability Skills under `skills/*/SKILL.md`.
- Existing `phase3_ep_001` canonical action instructions.
- GenEvolve appendix and runtime evidence in `docs/SOURCE_LEDGER.md`.
- NEWTON README and planner skills: video generation is one tool inside the planner toolbox; memory records tools called plus generated prompt; `img_create` distinguishes generate vs edit via reference images while preserving prompt-as-tool-argument semantics.

## Future-Leakage Rules

PlannerContext for action step `s_k` is built only from events before the planner output for `s_k`.

Allowed context:

- task spec;
- latest evaluated observation;
- active round query_skill actions that already completed;
- completed earlier rounds;
- current best state;
- visible latest/best images;
- budget/control state.

Forbidden context:

- the outcome of the action being requested;
- generated image artifacts that do not exist yet;
- Geneval2 results from future attempts;
- post-hoc labels or human analysis;
- raw teacher output.

## Provider Schema Strategy

Provider-level JSON schema should use action-specific schemas where possible. It must avoid unsupported constructs already observed in the GPT-5.5 endpoint, such as top-level `oneOf` and `uniqueItems` in provider-facing schema. Runtime validation remains authoritative and uses the full local JSON Schema plus reference/runtime checks.

## Implementation Plan

1. Add action protocol v0.3 and PlannerContext v0.3 schemas.
2. Update fixtures and parser to target v0.3 for new runs.
3. Build deterministic RoundRecord/PlannerContext from event history.
4. Write PlannerContext and RoundRecord artifacts for new runs; keep compatibility aliases for code paths that still say `planner_view`.
5. Update teacher prompt to ask for decision summaries, hypotheses, interventions, and no `strategy_tags`.
6. Update validators to require legal operations and valid constraint binding.
7. Update instruction quality, trace export, SFT renderer, and analysis code to read v0.3 fields.
8. Add golden replay and focused invariant tests.
9. Attempt one new live trajectory with the same prompt/config as `phase3_ep_001`.
