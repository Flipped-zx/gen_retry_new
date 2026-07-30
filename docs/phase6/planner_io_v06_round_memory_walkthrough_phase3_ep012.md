# Planner I/O v0.6 Real Walkthrough: `phase3_ep_012`

## 1. What Is Passed To The Agent

The Teacher is the Planner Agent. Every Planner call receives:

```json
{
  "system": "<teacher system prompt; identical across turns>",
  "user": {
    "task_spec": "<original prompt plus the 11 frozen Geneval2 atoms>",
    "planner_context": {
      "task_context": {},
      "latest_attempt": null,
      "skill_context": {},
      "episode_memory": {},
      "runtime_state": {}
    },
    "visible_images": []
  }
}
```

Only `planner_context`, `visible_images`, and runtime observations change
between calls. The original prompt and atom rubric are not repeated below.

The Agent returns exactly one canonical v0.5 action:

```json
{
  "schema_version": "0.5",
  "action": "query_skill | generate_image | edit_image | submit_attempt",
  "arguments": {}
}
```

Image backend selection is environment-owned:

- source-free `generate_image` -> Qwen-Image-2512;
- source-conditioned `edit_image` -> Qwen-Image-Edit-2511.

Backend/model fields are not part of the Agent output or SFT target.

## 2. Task And Final Result

Prompt:

> a checkered toy in front of five sparkling checkered chairs on top of seven candles

Result:

| Attempt | Action | Source | Pass | GM | Best after outcome |
| --- | --- | --- | ---: | ---: | --- |
| `a_000` | generate | none | 9/11 | 8.00 | `a_000` |
| `a_001` | edit | `a_000` | 9/11 | 5.94 | `a_000` |
| `a_002` | generate | none | 9/11 | 19.01 | `a_002` |
| `a_003` | edit | `a_002` | 10/11 | 42.69 | `a_003` |
| `a_004` | edit | `a_003` | 9/11 | 24.59 | `a_003` |

Submitted: `a_003`, not latest `a_004`.

## 3. Round 0: Skill Query And First Generation

### Planner Call 0 Input

Artifact:
`planner_contexts/planner_context_000.json`

```json
{
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
    "remaining_image_budget": 5
  },
  "visible_images": []
}
```

### Planner Call 0 Output

```json
{
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
      "c_007",
      "c_009",
      "c_010"
    ]
  }
}
```

Environment output: the three referenced Skill Markdown contents are loaded
and inserted into `skill_context.active_skills`. No image Attempt is created
and image budget remains 5.

### Planner Call 1 Input Change

Artifact:
`planner_contexts/planner_context_001.json`

```json
{
  "latest_attempt": null,
  "skill_context": {
    "active_skills": [
      "attribute_entity_binding",
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ]
  },
  "episode_memory": {
    "last_completed_image_round": null,
    "prior_image_rounds": [],
    "best_attempt": null
  },
  "runtime_state": {
    "remaining_image_budget": 5
  }
}
```

Each list entry is actually an object containing `skill_id`, target atom IDs,
guidance level, and the retrieved guidance text. The list above abbreviates
only the unchanged Markdown bodies.

### Planner Call 1 Output

```json
{
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
      "c_010",
      "c_011"
    ],
    "preserve_constraint_ids": [],
    "instruction": "<full source-free scene instruction>"
  }
}
```

Execution and observation:

```text
Planner action
-> Qwen-Image-2512
-> a_000
-> Geneval2
-> 9/11, GM 0.079976
-> failed: c_009 chair-on-candle relation, c_010 candle count
```

### Context Update For Next Round

Artifact:
`planner_contexts/planner_context_002.json`

```json
{
  "latest_attempt": {
    "attempt_id": "a_000",
    "passed_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_011"
    ],
    "failed_constraint_ids": ["c_009", "c_010"],
    "primary_score": 0.079976
  },
  "episode_memory": {
    "last_completed_image_round": "r_000 -> a_000",
    "prior_image_rounds": [],
    "best_attempt": "a_000"
  },
  "runtime_state": {
    "remaining_image_budget": 4
  },
  "visible_images": ["a_000"]
}
```

## 4. Round 1: An Ineffective Local Edit

### Planner Input

The Agent sees the `a_000` image, its complete atom state, Round 0's
generate instruction and outcome, and `a_000` as current best.

### Planner Output

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "target_constraint_ids": ["c_009", "c_010"],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_011"
    ],
    "instruction": "<add two candles, establish support contact, preserve passed evidence>"
  }
}
```

Execution and observation:

```text
a_000
-> Qwen-Image-Edit-2511
-> a_001
-> 9/11, GM 0.059364
-> fixed: none
-> persistent failed: c_009, c_010
-> regressed: none
-> became_best: false
```

### Context Update

Artifact:
`planner_contexts/planner_context_003.json`

```json
{
  "latest_attempt": {
    "attempt_id": "a_001",
    "failed_constraint_ids": ["c_009", "c_010"],
    "primary_score": 0.059364
  },
  "episode_memory": {
    "last_completed_image_round": "r_001: edit a_000 -> a_001",
    "prior_image_rounds": ["r_000"],
    "best_attempt": "a_000"
  },
  "runtime_state": {
    "remaining_image_budget": 3
  },
  "visible_images": ["a_001", "a_000"]
}
```

`latest_attempt` answers what the newest image currently satisfies.
`last_completed_image_round` answers what action produced it and what changed.
`best_attempt` remains a separate reference because latest is now worse.

## 5. Round 2: Abandon The Edit Path And Regenerate

### Planner Input

The Agent sees that the local edit preserved all passing atoms but fixed
nothing and lowered GM. It also sees both latest `a_001` and best `a_000`.

### Planner Output

```json
{
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
      "c_010",
      "c_011"
    ],
    "preserve_constraint_ids": [],
    "instruction": "<new full composition with seven candle supports>"
  }
}
```

This is a normal Planner Action with no source. The environment therefore
routes it to Qwen-Image-2512.

Execution and observation:

```text
source-free regenerate
-> a_002
-> 9/11, GM 0.190072
-> same pass count as a_000
-> higher GM than a_000
-> became_best: true by GM tie-break
```

### Context Update

Artifact:
`planner_contexts/planner_context_004.json`

```json
{
  "latest_attempt": {
    "attempt_id": "a_002",
    "failed_constraint_ids": ["c_009", "c_010"],
    "primary_score": 0.190072
  },
  "episode_memory": {
    "last_completed_image_round": "r_002: generate -> a_002",
    "prior_image_rounds": ["r_000", "r_001"],
    "best_attempt": "a_002"
  },
  "runtime_state": {
    "remaining_image_budget": 2
  }
}
```

## 6. Round 3: Productive Edit From The New Best

### Planner Output

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": ["c_009", "c_010"],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_011"
    ],
    "instruction": "<remove one extra candle and make candles support chairs>"
  }
}
```

Execution and observation:

```text
a_002
-> Qwen-Image-Edit-2511
-> a_003
-> 10/11, GM 0.426870
-> fixed: c_010 candle count
-> persistent failed: c_009 chair-on-candle relation
-> regressed: none
-> became_best: true
```

### Context Update

Artifact:
`planner_contexts/planner_context_005.json`

```json
{
  "latest_attempt": {
    "attempt_id": "a_003",
    "failed_constraint_ids": ["c_009"],
    "primary_score": 0.426870
  },
  "episode_memory": {
    "last_completed_image_round": "r_003: edit a_002 -> a_003",
    "prior_image_rounds": ["r_000", "r_001", "r_002"],
    "best_attempt": "a_003"
  },
  "runtime_state": {
    "remaining_image_budget": 1
  }
}
```

## 7. Round 4: Final Edit Regresses

### Planner Output

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_003",
    "target_constraint_ids": ["c_009"],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_010",
      "c_011"
    ],
    "instruction": "<strengthen visible chair/candle support contact>"
  }
}
```

Execution and observation:

```text
a_003
-> Qwen-Image-Edit-2511
-> a_004
-> 9/11, GM 0.245931
-> fixed: none
-> persistent failed: c_009
-> regressed: c_010 candle count
-> became_best: false
```

### Final PlannerContext

Artifact:
`planner_contexts/planner_context_006.json`

```json
{
  "latest_attempt": {
    "attempt_id": "a_004",
    "failed_constraint_ids": ["c_009", "c_010"],
    "primary_score": 0.245931
  },
  "episode_memory": {
    "last_completed_image_round": "r_004: edit a_003 -> a_004",
    "prior_image_rounds": ["r_000", "r_001", "r_002", "r_003"],
    "best_attempt": "a_003"
  },
  "runtime_state": {
    "remaining_image_budget": 0
  },
  "visible_images": ["a_004", "a_003"]
}
```

## 8. Submit Action

```json
{
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_003",
    "reason_code": "best_available_under_budget"
  }
}
```

`submit_attempt` is learned as a Planner Action. The environment validates that
`a_003` is the reducer best, records submission, and creates no new image
Attempt.

## 9. What This Trajectory Demonstrates

- Skill retrieval is a real Action and its Markdown content enters the next
  PlannerContext.
- A Planning Round may include Skill query actions plus one terminal image
  action.
- Generate and edit remain semantic Agent choices; backend routing happens
  only after the action is accepted.
- The Agent saw an ineffective edit and switched to source-free regeneration.
- GM affected best selection only when pass count tied.
- `latest_attempt`, the action/outcome record, and `best_attempt` have distinct
  jobs and do not collapse into one ambiguous history object.
- A final regression remained in history, while submission correctly selected
  the earlier best image.

The exact canonical actions, full instructions, PlannerContext snapshots,
images, Geneval2 records, and RoundRecords remain under:

`runs/phase6_v07_dual_backend5_score_v06/phase3_ep_012/`
