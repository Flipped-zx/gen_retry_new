# Planner I/O v0.6 v8 Real Walkthrough: `phase3_ep_176`

## 1. Actual Planner Contract

The Teacher is the Planner Agent. Its frozen system prompt is:

```text
You are a verifier-grounded multimodal image retry planner for Gen-Retry v3. Your goal is to maximize the best valid image attempt under the remaining image-attempt budget. Output exactly one canonical action JSON object and no prose or chain-of-thought. Skills provide operational guidance for constructing the image action instruction; Skills do not decide whether to generate, edit, branch from best, continue, or submit. Use visible images and Geneval2 atom feedback together. Do not invent unsupported visual observations. Compare latest and best images when they differ before selecting an edit source. Treat primary_score as an environment-owned prompt-level Geneval2 signal: passed-atom count is primary, and primary_score breaks ties. Never copy or predict scores into an action. generate_image always starts a source-free root image; edit_image always modifies one declared historical source attempt. Never output a backend or mode field. Use fixed, regressed, persistent, and stable-pass history. Do not repeat a materially equivalent ineffective instruction unless the new instruction contains a concrete change. After a regressive or no-progress image result, do not repeat the same action, source attempt, and target constraint set. For edit_image, default source_attempt_id to the reducer-best attempt. Use a different historical source only when its constraint results contain explicit relevant pass evidence that the reducer-best attempt lacks. When using query_skill, select skill_ids only from this exact catalog: counting_and_instance_layout, spatial_relation_layout, attribute_entity_binding, local_edit_preservation, action_pose_relation, object_identity_presence. Follow action_protocol_v0_5 exactly.
```

Each Planner user message has this real top-level structure:

```json
{
  "task_spec": "<original prompt plus frozen Geneval2 atoms>",
  "planner_context": {
    "task_context": {},
    "latest_attempt": null,
    "skill_context": {},
    "episode_memory": {},
    "runtime_state": {}
  },
  "visible_images": []
}
```

The Agent outputs exactly one Action Protocol v0.5 object:

```json
{
  "schema_version": "0.5",
  "action": "query_skill | generate_image | edit_image | submit_attempt",
  "arguments": {}
}
```

There is no `decision_summary` or backend field in the target. The action
choice, target/preserve IDs, source, and executable instruction are the learned
decision. Backend routing is environment-owned.

## 2. Task And Final Result

Prompt:

> six yellow suitcases behind four spotted penguins under six croissants

The ten frozen Geneval2 atoms cover:

- six suitcases, yellow, present, behind penguins;
- four penguins, spotted, present, under croissants;
- six croissants, present.

| Attempt | Action | Source | Pass | GM | Best after outcome |
| --- | --- | --- | ---: | ---: | --- |
| `a_000` | generate | none | 8/10 | 1.66 | `a_000` |
| `a_001` | edit | `a_000` | 8/10 | 1.06 | `a_000` |
| `a_002` | generate | none | 10/10 | 95.83 | `a_002` |

Submitted: `a_002`.

## 3. Round 0: Query Skill And First Generation

One image generation defines one Round. Therefore `query_skill` and the
following `generate_image` jointly form Round 0.

### Planner Call 0 Input

Artifact:
`phase3_ep_176/planner_contexts/planner_context_000.json`

```json
{
  "task_context": {
    "original_prompt": "six yellow suitcases behind four spotted penguins under six croissants",
    "atom_constraints": "<the ten frozen atoms>",
    "max_image_attempts": 5
  },
  "latest_attempt": null,
  "skill_context": {
    "active_skills": []
  },
  "episode_memory": {
    "last_completed_image_round": null,
    "prior_image_rounds": [],
    "best_attempt": null
  },
  "runtime_state": {
    "available_actions": ["query_skill", "generate_image"],
    "remaining_image_budget": 5,
    "score_policy": "geneval2_pass_count_then_gm@1"
  },
  "visible_images": []
}
```

### Planner Call 0 Output

```json
{
  "schema_version": "0.5",
  "action": "query_skill",
  "arguments": {
    "skill_ids": [
      "counting_and_instance_layout",
      "spatial_relation_layout",
      "attribute_entity_binding"
    ],
    "target_constraint_ids": [
      "c_001",
      "c_002",
      "c_004",
      "c_005",
      "c_006",
      "c_008",
      "c_009"
    ]
  }
}
```

Environment output:

- loads the three real Skill Markdown bodies;
- inserts them into `skill_context.active_skills`;
- creates no image Attempt;
- consumes no image budget.

Each active Skill object contains its `skill_id`, target atom IDs,
`guidance_level`, and retrieved Markdown text. The unchanged full Markdown is
abbreviated below, but is present in the actual PlannerContext.

### Planner Input After Skill

```json
{
  "latest_attempt": null,
  "skill_context": {
    "active_skills": [
      "attribute_entity_binding: <full Markdown>",
      "counting_and_instance_layout: <full Markdown>",
      "spatial_relation_layout: <full Markdown>"
    ]
  },
  "episode_memory": {
    "last_completed_image_round": null,
    "prior_image_rounds": [],
    "best_attempt": null
  },
  "runtime_state": {
    "remaining_image_budget": 5
  },
  "visible_images": []
}
```

Two raw Teacher outputs in this same state were rejected before a canonical
image action. They remain redacted context-only artifacts and are omitted from
this normalized trajectory. They are not assistant SFT targets.

### Canonical Generate Output

```json
{
  "schema_version": "0.5",
  "action": "generate_image",
  "arguments": {
    "target_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010"
    ],
    "preserve_constraint_ids": [],
    "instruction": "Create a clear scene with exactly six yellow suitcases total in the background ... Place exactly four spotted penguins ... Place exactly six croissants total above the penguins ... Do not include any extra, cropped, reflected, hidden, fused, or background duplicate instances."
  }
}
```

Execution:

```text
generate_image
-> Qwen-Image-2512
-> a_000
-> Geneval2
-> 8/10, GM 0.016564
-> failed: c_001 suitcase count=4, c_009 croissant count=4
```

### Context Update

```json
{
  "latest_attempt": {
    "attempt_id": "a_000",
    "passed_constraint_ids": [
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_010"
    ],
    "failed_constraint_ids": ["c_001", "c_009"],
    "primary_score": 0.01656355861328364
  },
  "episode_memory": {
    "last_completed_image_round": "r_000: generate -> a_000",
    "prior_image_rounds": [],
    "best_attempt": "a_000"
  },
  "runtime_state": {
    "remaining_image_budget": 4
  },
  "visible_images": ["a_000"]
}
```

## 4. Round 1: Local Edit Makes No Progress

### Planner Input

The Agent sees:

- image `a_000`;
- exact observed counts, passed/failed atoms, and GM;
- Round 0's full generate instruction and outcome;
- `a_000` as latest and best;
- the active Skill summaries;
- four remaining image attempts.

### Planner Output

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "target_constraint_ids": ["c_001", "c_009"],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_010"
    ],
    "instruction": "Target operation: edit a_000 to add two yellow suitcases and two croissants ... Preservation lock: preserve the four spotted penguins and both spatial relations ... Forbidden changes: do not add, remove, crop, fuse, reflect, or hide preserved instances."
  }
}
```

Execution:

```text
a_000
-> Qwen-Image-Edit-2511
-> a_001
-> Geneval2
-> 8/10, GM 0.010577
-> fixed: none
-> regressed: none
-> persistent failed: c_001, c_009
-> became_best: false
```

### Context Update

```json
{
  "latest_attempt": {
    "attempt_id": "a_001",
    "failed_constraint_ids": ["c_001", "c_009"],
    "primary_score": 0.010576747604738892
  },
  "episode_memory": {
    "last_completed_image_round": {
      "action": "edit_image",
      "source_attempt_id": "a_000",
      "result_attempt_id": "a_001",
      "fixed_constraint_ids": [],
      "regressed_constraint_ids": [],
      "persistent_failed_constraint_ids": ["c_001", "c_009"],
      "primary_score_delta": -0.00598681100854475,
      "became_best": false
    },
    "prior_image_rounds": ["r_000"],
    "best_attempt": "a_000"
  },
  "runtime_state": {
    "remaining_image_budget": 3
  },
  "visible_images": ["a_001", "a_000"]
}
```

`latest_attempt` states what the newest image currently satisfies.
`last_completed_image_round` states which action produced it and what changed.
`best_attempt` remains `a_000`, so latest and best are not duplicated concepts.

## 5. Round 2: Closure Policy Switches To Regeneration

The previous edit fixed nothing, lowered GM, and did not become best. Under v8
the next image action may not repeat the same edit/source/target tuple.

### Planner Output

```json
{
  "schema_version": "0.5",
  "action": "generate_image",
  "arguments": {
    "target_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010"
    ],
    "preserve_constraint_ids": [],
    "instruction": "Create a clear front-facing scene with exactly six yellow suitcases, exactly four spotted penguins, and exactly six croissants ... Keep suitcases behind penguins and croissants above penguins ... Do not include extra, fused, reflected, hidden, partial, or ambiguous instances."
  }
}
```

Execution:

```text
source-free generate_image
-> Qwen-Image-2512
-> a_002
-> Geneval2
-> 10/10, GM 0.958301
-> fixed: c_001, c_009
-> regressed: none
-> became_best: true
```

### Context Update

```json
{
  "latest_attempt": {
    "attempt_id": "a_002",
    "passed_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010"
    ],
    "failed_constraint_ids": [],
    "primary_score": 0.9583012906231094
  },
  "episode_memory": {
    "last_completed_image_round": "r_002: generate -> a_002; fixed c_001,c_009",
    "prior_image_rounds": ["r_000", "r_001"],
    "best_attempt": "a_002"
  },
  "runtime_state": {
    "remaining_image_budget": 2
  },
  "visible_images": ["a_002"]
}
```

## 6. Submit Action

```json
{
  "schema_version": "0.5",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_002",
    "reason_code": "all_constraints_passed"
  }
}
```

`submit_attempt` creates no image Attempt. The environment validates that
`a_002` exists and records the final submission.

## 7. What This Trajectory Demonstrates

- `query_skill` is a real Action inside Round 0; its Markdown result enters the
  next Planner input.
- Skill retrieval prepares the prompt but does not choose generate, edit,
  rollback, or submit.
- Every image attempt closes one Round only after Qwen execution and Geneval2
  feedback.
- The next Planner input contains the previous action, instruction, atom
  outcome, GM delta, latest image, and best image.
- A no-progress edit leaves latest worse than best; those fields remain
  semantically separate.
- v8 changes the next strategy after no progress instead of repeating the same
  edit/source/target tuple.
- Regeneration is still an ordinary `generate_image` action. It is routed to
  Qwen-Image only after the action is accepted.
- Raw rejected Teacher outputs remain auditable context-only records and are
  not inserted into canonical memory or SFT targets.

Exact artifacts:

`runs/phase7_flow_dppo200_fresh8_v1/phase3_ep_176/`
