# Actual Normalized Trajectory: `phase3_ep_001`

这份文件只展示我们这条规范后的真实轨迹长什么样。

读法:

- `seen by teacher`: 本轮 Teacher 实际看到的输入形状。
- `assistant output`: 本轮规范后的 canonical assistant action。
- `environment output`: 工具/图像后端/Geneval2 的输出，它会进入下一轮 PlannerView。
- 长内容用代指，例如 `[COMMON_USER_CONTRACT]`、`[TASK_SPEC]`、`[IMG_000_BYTES]`。

Normalized round 对应 live turn:

```text
round_0 -> turn_000  query_skill
round_1 -> turn_002  generate_image -> a_000
round_2 -> turn_003  generate_image -> a_001
round_3 -> turn_008  edit_image     -> a_002
round_4 -> turn_009  edit_image     -> a_003
round_5 -> turn_010  edit_image     -> a_004
round_6 -> turn_011  submit_attempt
```

Rejected raw turns are not shown in this normalized trajectory.

## Common Blocks

### `[SYSTEM_PROMPT_V1]`

```text
You are a verifier-grounded multimodal image retry planner for Gen-Retry v3. Your goal is to maximize the best valid image attempt under the remaining image-attempt budget. Output exactly one canonical action JSON object and no prose or chain-of-thought. Skills provide operational guidance for constructing generation_instruction and edit_instruction text; Skills do not decide whether to generate, edit, branch from best, continue, or submit. Use visible images and Geneval2 atom feedback together. Do not invent unsupported visual observations. Compare latest and best images when they differ before selecting an edit source. Use fixed, regressed, persistent, and stable-pass history. Do not repeat a materially equivalent ineffective instruction unless the new instruction contains a concrete change.
```

### `[COMMON_USER_CONTRACT]`

This is the repeated contract inside `teacher_text_input`.

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:
{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:
Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments.

Allowed actions:
query_skill, generate_image, edit_image, submit_attempt.

query_skill requires:
arguments.skill_ids
arguments.target_constraint_ids

generate_image requires:
arguments.mode
arguments.target_constraint_ids
arguments.preserve_constraint_ids
arguments.strategy_tags
arguments.skill_ids_used
arguments.generation_instruction

edit_image requires:
arguments.source_attempt_id
arguments.target_constraint_ids
arguments.preserve_constraint_ids
arguments.strategy_tags
arguments.skill_ids_used
arguments.edit_instruction

submit_attempt requires:
arguments.selected_attempt_id
arguments.reason_code

Valid templates:
[QUERY_SKILL_TEMPLATE, GENERATE_IMAGE_TEMPLATE, EDIT_IMAGE_TEMPLATE, SUBMIT_TEMPLATE]
```

### `[TASK_SPEC]`

```json
{
  "schema_version": "0.2",
  "episode_id": "phase3_ep_001",
  "max_image_attempts": 5,
  "original_prompt": "six glass lions chasing three red cats behind a brown donut",
  "constraints": [
    {"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","requirement":"Expected answer: six"},
    {"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","requirement":"Expected answer: three"},
    {"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","requirement":"Expected answer: one"},
    {"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","requirement":"Expected answer: Yes"},
    {"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","requirement":"Expected answer: Yes"}
  ]
}
```

### Actual API Message Shape

Every Teacher call is shaped like this:

```json
[
  {
    "role": "system",
    "content": "[SYSTEM_PROMPT_V1]"
  },
  {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "[COMMON_USER_CONTRACT]\n\nTaskSpec:\n[TASK_SPEC]\n\nPlannerView:\n[PLANNER_VIEW_FOR_THIS_ROUND]\n\nVisible image labels:\n[IMAGE_LABELS]\n\nLatest equals best:\n[true_or_false]\n\nActive Skill operators:\n[ACTIVE_SKILL_OPERATORS]\n\nRetrieved skills:\n[RETRIEVED_SKILLS]\n\nExtra observations:\n[EXTRA_OBSERVATIONS]"
      },
      {
        "type": "text",
        "text": "LATEST_IMAGE or BEST_IMAGE label, if any"
      },
      {
        "type": "image_url",
        "image_url": {
          "url": "data:image/png;base64,[IMG_BYTES]"
        }
      }
    ]
  }
]
```

When no image is visible, the image label and image bytes entries are absent.

---

## round_0: `query_skill`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "schema_version": "0.2",
    "task_spec_ref": "task_spec.json",
    "remaining_budget": 5,
    "latest_attempt": null,
    "best_attempt": null,
    "compact_history": [],
    "constraint_state": {
      "c_001": {"status": "not_evaluated", "attempt_ids": []},
      "...": "...",
      "c_011": {"status": "not_evaluated", "attempt_ids": []}
    },
    "visible_images": [],
    "retrieved_experiences": [],
    "skill_manifest": [
      {"skill_id": "counting_and_instance_layout", "version": "1.0.0", "description": "Exact cardinality, instance separation, full visibility, no extras or fused objects."},
      {"skill_id": "spatial_relation_layout", "version": "1.0.0", "description": "Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations."},
      {"skill_id": "attribute_entity_binding", "version": "1.0.0", "description": "Bind color, material, texture, and identity attributes to the correct entity."},
      {"skill_id": "local_edit_preservation", "version": "1.0.0", "description": "Narrow edit scope and preserve already-correct visual evidence."}
    ],
    "tool_manifest": [
      {"tool_id": "query_skill", "action": "query_skill"},
      {"tool_id": "generate_image", "action": "generate_image"},
      {"tool_id": "edit_image", "action": "edit_image"},
      {"tool_id": "submit_attempt", "action": "submit_attempt"}
    ]
  }

  Visible image labels:
  []

  Active Skill operators:
  []

  Retrieved skills:
  []

  Extra observations:
  ["No image attempts exist yet; do not edit or submit."]
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "query_skill",
  "arguments": {
    "skill_ids": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_005",
      "c_008",
      "c_009"
    ]
  }
}
```

### environment output

```text
tool: query_skill

returned:
  [SKILL_MD: counting_and_instance_layout]
  [SKILL_MD: spatial_relation_layout]

next PlannerView will carry:
  full retrieved Skill Markdown in the immediate next live request
  compact active Skill operator summaries in later accepted rounds
```

---

## round_1: `generate_image -> a_000`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "remaining_budget": 5,
    "latest_attempt": null,
    "best_attempt": null,
    "compact_history": [],
    "constraint_state": {
      "c_001": {"status": "not_evaluated", "attempt_ids": []},
      "...": "...",
      "c_011": {"status": "not_evaluated", "attempt_ids": []}
    },
    "visible_images": [],
    "retrieved_experiences": [
      "[ACTIVE_OPERATOR_SUMMARY: counting_and_instance_layout]",
      "[ACTIVE_OPERATOR_SUMMARY: spatial_relation_layout]"
    ]
  }

  Visible image labels:
  []

  Active Skill operators:
  [
    "[ACTIVE_OPERATOR_SUMMARY: counting_and_instance_layout]",
    "[ACTIVE_OPERATOR_SUMMARY: spatial_relation_layout]"
  ]

  Retrieved skills:
  []

  Extra observations:
  ["No image attempts exist yet; do not edit or submit."]
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "generate_image",
  "arguments": {
    "mode": "initial",
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
    "strategy_tags": [
      "fresh_layout",
      "counting",
      "spatial_relation"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "generation_instruction": "Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts."
  }
}
```

### environment output

```text
tool/backend call:
  generate_image

input to Qwen:
  source_image: null
  instruction: assistant.arguments.generation_instruction
  width: 1024
  height: 1024
  num_inference_steps: 40
  true_cfg_scale: 4.0
  guidance_scale: 1.0
  seed: 0

output:
  attempt_id: a_000
  image_artifact_id: img_000
  image_path: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_000.png

Geneval2 normalized atom output:
  pass: [c_003, c_006, c_007, c_009, c_010, c_011]
  fail: [c_001, c_004, c_005, c_008]
  uncertain: [c_002]
  observed:
    c_001: expected six, observed 2
    c_002: expected Yes, observed " no"
    c_004: expected Yes, observed " no"
    c_005: expected three, observed 0
    c_008: expected Yes, observed " no"

state after reducer:
  latest_attempt: a_000
  best_attempt: a_000
  remaining_budget: 4
```

---

## round_2: `generate_image -> a_001`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "remaining_budget": 4,
    "latest_attempt": {
      "attempt_id": "a_000",
      "image_artifact_id": "img_000",
      "passed_constraint_ids": ["c_003","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_001","c_002","c_004","c_005","c_008"]
    },
    "best_attempt": {
      "attempt_id": "a_000",
      "image_artifact_id": "img_000",
      "passed_constraint_ids": ["c_003","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_001","c_002","c_004","c_005","c_008"]
    },
    "compact_history": [
      "[ATTEMPT_SUMMARY: a_000]"
    ],
    "latest_transition": "[TRANSITION_AFTER_A_000]",
    "constraint_state": "[ATOM_STATE_AFTER_A_000]",
    "retrieved_experiences": [
      "[ACTIVE_OPERATOR_SUMMARY: counting_and_instance_layout]",
      "[ACTIVE_OPERATOR_SUMMARY: spatial_relation_layout]"
    ]
  }

  Visible image labels:
  [
    {"label": "LATEST_IMAGE", "attempt_id": "a_000", "artifact_id": "img_000"},
    {"label": "BEST_IMAGE_SAME_AS_LATEST", "attempt_id": "a_000", "artifact_id": "img_000"}
  ]

user multimodal content also includes:
  {"type":"text","text":"LATEST_IMAGE: attempt a_000, artifact img_000"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_000_BYTES]"}}
  {"type":"text","text":"BEST_IMAGE_SAME_AS_LATEST: attempt a_000, artifact img_000"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_000_BYTES]"}}
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "generate_image",
  "arguments": {
    "mode": "initial",
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
    "strategy_tags": [
      "fresh_layout",
      "explicit_counting",
      "spatial_relation"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "generation_instruction": "Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects."
  }
}
```

### environment output

```text
tool/backend call:
  generate_image

input to Qwen:
  source_image: null
  instruction: assistant.arguments.generation_instruction
  width: 1024
  height: 1024
  num_inference_steps: 40
  true_cfg_scale: 4.0
  guidance_scale: 1.0
  seed: 1

output:
  attempt_id: a_001
  image_artifact_id: img_001
  image_path: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_001.png

Geneval2 normalized atom output:
  pass: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  fail: [c_001, c_004, c_008]
  observed:
    c_001: expected six, observed 4
    c_004: expected Yes, observed " no"
    c_008: expected Yes, observed " no"

state after reducer:
  latest_attempt: a_001
  best_attempt: a_001
  remaining_budget: 3
```

---

## round_3: `edit_image a_001 -> a_002`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "remaining_budget": 3,
    "latest_attempt": {
      "attempt_id": "a_001",
      "image_artifact_id": "img_001",
      "passed_constraint_ids": ["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_001","c_004","c_008"]
    },
    "best_attempt": {
      "attempt_id": "a_001",
      "image_artifact_id": "img_001",
      "passed_constraint_ids": ["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_001","c_004","c_008"]
    },
    "compact_history": [
      "[ATTEMPT_SUMMARY: a_000]",
      "[ATTEMPT_SUMMARY: a_001]"
    ],
    "latest_transition": "[TRANSITION_AFTER_A_001]",
    "constraint_state": "[ATOM_STATE_AFTER_A_001]",
    "retrieved_experiences": [
      "[ACTIVE_OPERATOR_SUMMARY: counting_and_instance_layout]",
      "[ACTIVE_OPERATOR_SUMMARY: spatial_relation_layout]"
    ]
  }

  Visible image labels:
  [
    {"label": "LATEST_IMAGE", "attempt_id": "a_001", "artifact_id": "img_001"},
    {"label": "BEST_IMAGE_SAME_AS_LATEST", "attempt_id": "a_001", "artifact_id": "img_001"}
  ]

user multimodal content also includes:
  {"type":"text","text":"LATEST_IMAGE: attempt a_001, artifact img_001"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_001_BYTES]"}}
  {"type":"text","text":"BEST_IMAGE_SAME_AS_LATEST: attempt a_001, artifact img_001"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_001_BYTES]"}}
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_008"
    ],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ],
    "strategy_tags": [
      "localized_repair",
      "add_missing_instances",
      "spatial_relation_repair"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "edit_instruction": "Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene."
  }
}
```

### environment output

```text
tool/backend call:
  edit_image

input to Qwen:
  source_image: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_001.png
  instruction: assistant.arguments.edit_instruction
  width: 1024
  height: 1024
  num_inference_steps: 40
  true_cfg_scale: 4.0
  guidance_scale: 1.0
  seed: 2

output:
  attempt_id: a_002
  image_artifact_id: img_002
  image_path: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_002.png
  parent_attempt_id: a_001

Geneval2 normalized atom output:
  pass: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  fail: [c_004, c_008]
  observed:
    c_004: expected Yes, observed " no"
    c_008: expected Yes, observed " no"

state after reducer:
  latest_attempt: a_002
  best_attempt: a_002
  remaining_budget: 2
```

---

## round_4: `edit_image a_002 -> a_003`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "remaining_budget": 2,
    "latest_attempt": {
      "attempt_id": "a_002",
      "image_artifact_id": "img_002",
      "passed_constraint_ids": ["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_004","c_008"]
    },
    "best_attempt": {
      "attempt_id": "a_002",
      "image_artifact_id": "img_002",
      "passed_constraint_ids": ["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_004","c_008"]
    },
    "compact_history": [
      "[ATTEMPT_SUMMARY: a_000]",
      "[ATTEMPT_SUMMARY: a_001]",
      "[ATTEMPT_SUMMARY: a_002]"
    ],
    "latest_transition": "[TRANSITION_AFTER_A_002]",
    "constraint_state": "[ATOM_STATE_AFTER_A_002]",
    "retrieved_experiences": [
      "[ACTIVE_OPERATOR_SUMMARY: counting_and_instance_layout]",
      "[ACTIVE_OPERATOR_SUMMARY: spatial_relation_layout]"
    ]
  }

  Visible image labels:
  [
    {"label": "LATEST_IMAGE", "attempt_id": "a_002", "artifact_id": "img_002"},
    {"label": "BEST_IMAGE_SAME_AS_LATEST", "attempt_id": "a_002", "artifact_id": "img_002"}
  ]

user multimodal content also includes:
  {"type":"text","text":"LATEST_IMAGE: attempt a_002, artifact img_002"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_002_BYTES]"}}
  {"type":"text","text":"BEST_IMAGE_SAME_AS_LATEST: attempt a_002, artifact img_002"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_002_BYTES]"}}
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": [
      "c_004",
      "c_008"
    ],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ],
    "strategy_tags": [
      "localized_repair",
      "depth_relation_repair",
      "verb_action_cue"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "edit_instruction": "Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects."
  }
}
```

### environment output

```text
tool/backend call:
  edit_image

input to Qwen:
  source_image: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_002.png
  instruction: assistant.arguments.edit_instruction
  width: 1024
  height: 1024
  num_inference_steps: 40
  true_cfg_scale: 4.0
  guidance_scale: 1.0
  seed: 3

output:
  attempt_id: a_003
  image_artifact_id: img_003
  image_path: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_003.png
  parent_attempt_id: a_002

Geneval2 normalized atom output:
  pass: [c_001, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  fail: [c_002, c_004, c_008]
  observed:
    c_002: expected Yes, observed " no"
    c_004: expected Yes, observed " no"
    c_008: expected Yes, observed " no"

state after reducer:
  latest_attempt: a_003
  best_attempt: a_002
  remaining_budget: 1
```

---

## round_5: `edit_image a_002 -> a_004`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "remaining_budget": 1,
    "latest_attempt": {
      "attempt_id": "a_003",
      "image_artifact_id": "img_003",
      "passed_constraint_ids": ["c_001","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_002","c_004","c_008"]
    },
    "best_attempt": {
      "attempt_id": "a_002",
      "image_artifact_id": "img_002",
      "passed_constraint_ids": ["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_004","c_008"]
    },
    "compact_history": [
      "[ATTEMPT_SUMMARY: a_000]",
      "[ATTEMPT_SUMMARY: a_001]",
      "[ATTEMPT_SUMMARY: a_002]",
      "[ATTEMPT_SUMMARY: a_003]"
    ],
    "latest_transition": "[TRANSITION_AFTER_A_003_WITH_C_002_REGRESSION]",
    "constraint_state": "[ATOM_STATE_AFTER_A_003]",
    "retrieved_experiences": [
      "[ACTIVE_OPERATOR_SUMMARY: counting_and_instance_layout]",
      "[ACTIVE_OPERATOR_SUMMARY: spatial_relation_layout]"
    ]
  }

  Visible image labels:
  [
    {"label": "LATEST_IMAGE", "attempt_id": "a_003", "artifact_id": "img_003"},
    {"label": "BEST_IMAGE", "attempt_id": "a_002", "artifact_id": "img_002"}
  ]

user multimodal content also includes:
  {"type":"text","text":"LATEST_IMAGE: attempt a_003, artifact img_003"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_003_BYTES]"}}
  {"type":"text","text":"BEST_IMAGE: attempt a_002, artifact img_002"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_002_BYTES]"}}
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": [
      "c_004",
      "c_008"
    ],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ],
    "strategy_tags": [
      "localized_repair",
      "depth_layering",
      "motion_cue"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "edit_instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap."
  }
}
```

### environment output

```text
tool/backend call:
  edit_image

input to Qwen:
  source_image: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_002.png
  instruction: assistant.arguments.edit_instruction
  width: 1024
  height: 1024
  num_inference_steps: 40
  true_cfg_scale: 4.0
  guidance_scale: 1.0
  seed: 4

output:
  attempt_id: a_004
  image_artifact_id: img_004
  image_path: runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_004.png
  parent_attempt_id: a_002

Geneval2 normalized atom output:
  pass: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  fail: [c_004, c_008]
  observed:
    c_004: expected Yes, observed " no"
    c_008: expected Yes, observed " no"

state after reducer:
  latest_attempt: a_004
  best_attempt: a_002
  remaining_budget: 0
```

---

## round_6: `submit_attempt`

### seen by teacher

```text
system:
  [SYSTEM_PROMPT_V1]

user text:
  [COMMON_USER_CONTRACT]

  TaskSpec:
    [TASK_SPEC]

  PlannerView:
  {
    "episode_id": "phase3_ep_001",
    "remaining_budget": 0,
    "latest_attempt": {
      "attempt_id": "a_004",
      "image_artifact_id": "img_004",
      "passed_constraint_ids": ["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_004","c_008"]
    },
    "best_attempt": {
      "attempt_id": "a_002",
      "image_artifact_id": "img_002",
      "passed_constraint_ids": ["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],
      "failed_constraint_ids": ["c_004","c_008"]
    },
    "compact_history": [
      "[ATTEMPT_SUMMARY: a_000]",
      "[ATTEMPT_SUMMARY: a_001]",
      "[ATTEMPT_SUMMARY: a_002]",
      "[ATTEMPT_SUMMARY: a_003]",
      "[ATTEMPT_SUMMARY: a_004]"
    ],
    "latest_transition": "[TRANSITION_AFTER_A_004]",
    "constraint_state": "[ATOM_STATE_AFTER_A_004]"
  }

  Visible image labels:
  [
    {"label": "LATEST_IMAGE", "attempt_id": "a_004", "artifact_id": "img_004"},
    {"label": "BEST_IMAGE", "attempt_id": "a_002", "artifact_id": "img_002"}
  ]

  Extra observations:
  ["Budget is exhausted; submit the best available attempt with reason_code exactly best_available_under_budget. Do not use budget_exhausted_best_available."]

user multimodal content also includes:
  {"type":"text","text":"LATEST_IMAGE: attempt a_004, artifact img_004"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_004_BYTES]"}}
  {"type":"text","text":"BEST_IMAGE: attempt a_002, artifact img_002"}
  {"type":"image_url","image_url":{"url":"data:image/png;base64,[IMG_002_BYTES]"}}
```

### assistant output

```json
{
  "schema_version": "0.2",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_002",
    "reason_code": "best_available_under_budget"
  }
}
```

### environment output

```json
{
  "schema_version": "0.2",
  "episode_id": "phase3_ep_001",
  "attempt_order": [
    "a_000",
    "a_001",
    "a_002",
    "a_003",
    "a_004"
  ],
  "submitted_attempt_id": "a_002",
  "best_attempt_id": "a_002",
  "reason_code": "best_available_under_budget"
}
```
