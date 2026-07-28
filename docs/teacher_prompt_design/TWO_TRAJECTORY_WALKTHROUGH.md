# Two Trajectory Walkthrough

Purpose: 只展示两条轨迹如何一步步走下来。这里不做额外分析。

## Trajectory A: GenEvolve-Style

### Step 0

```text
seen by model:
  system prompt:
    output exactly one of:
      <think>...</think><tool_call>{...}</tool_call>
      <think>...</think><answer>{...}</answer>
    available tools:
      search
      image_search
      query_knowledge

  user prompt:
    create an image prompt for the requested scene/object/person

assistant target:
  <think>
  I need visual grounding, so I will search for reference images.
  </think>
  <tool_call>
  {"name":"image_search","arguments":{"query":"..."}}
  </tool_call>
```

### Step 1

```text
seen by model:
  previous user prompt
  previous assistant tool call
  tool response:
    IMG_001: image result ...
    IMG_004: image result ...

assistant target:
  <think>
  I need prompt-writing guidance for layout / text / counting / attributes.
  </think>
  <tool_call>
  {"name":"query_knowledge","arguments":{"skill_name":"spatial_layout"}}
  </tool_call>
```

### Step 2

```text
seen by model:
  previous prompt
  image_search results with IMG ids
  previous query_knowledge call
  tool response:
    Markdown skill content for spatial_layout

assistant target:
  <think>
  I will use the reference image for identity/layout and apply the skill guidance.
  </think>
  <answer>
  {
    "gen_prompt": "... use the first reference image for identity/layout ...",
    "reference_images": [
      {
        "img_id": "IMG_001",
        "note": "identity or shape reference"
      }
    ]
  }
  </answer>
```

## Trajectory B: Gen-Retry `phase3_ep_001`

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

### Step 0

```text
seen by model:
  system prompt:
    output exactly one canonical action JSON
    allowed actions:
      query_skill
      generate_image
      edit_image
      submit_attempt

  user / PlannerView:
    TaskSpec atoms: c_001 ... c_011
    budget: 5
    history: []
    visible images: []
    available skill summaries

assistant target:
  query_skill(
    skill_ids=[counting_and_instance_layout, spatial_relation_layout],
    target_constraint_ids=[c_001,c_004,c_005,c_008,c_009]
  )

observation:
  returned full Skill Markdown:
    counting_and_instance_layout
    spatial_relation_layout
```

### Step 1

```text
seen by model:
  TaskSpec atoms: c_001 ... c_011
  budget: 5
  history: []
  visible images: []
  active Skills:
    counting_and_instance_layout
    spatial_relation_layout

assistant target:
  generate_image(
    target=all atoms,
    preserve=[],
    skill_ids_used=[counting_and_instance_layout, spatial_relation_layout],
    strategy_tags=[fresh_layout,counting,spatial_relation],
    generation_instruction="exactly one brown donut foreground; exactly three red cats behind it; exactly six glass lions chasing cats; all visible/separated; no extras/fusion/cropping/reflections"
  )

observation:
  Qwen -> img_000
  Geneval2 -> 6/11 pass
  failed=[c_001,c_002,c_004,c_005,c_008]
  state:
    latest=a_000
    best=a_000
    budget=4
```

### Step 2

```text
seen by model:
  latest=a_000
  best=a_000
  visible images=[img_000]
  history=[a_000]
  budget=4
  failed=[c_001,c_002,c_004,c_005,c_008]

assistant target:
  generate_image(
    target=all atoms,
    preserve=[],
    skill_ids_used=[counting_and_instance_layout, spatial_relation_layout],
    strategy_tags=[fresh_layout,explicit_counting,spatial_relation],
    generation_instruction="clean white studio; large brown donut foreground; three red cats behind donut; six translucent glass lions in separated arc behind cats; no extras/duplicates/reflections"
  )

observation:
  Qwen -> img_001
  Geneval2 -> 8/11 pass
  fixed=[c_002,c_005]
  failed=[c_001,c_004,c_008]
  state:
    latest=a_001
    best=a_001
    budget=3
```

### Step 3

```text
seen by model:
  latest=a_001
  best=a_001
  visible images=[img_001]
  history=[a_000,a_001]
  budget=3
  failed=[c_001,c_004,c_008]
  stable_passes=[c_002,c_003,c_005,c_006,c_007,c_009,c_010,c_011]

assistant target:
  edit_image(
    source_attempt_id=a_001,
    target=[c_001,c_004,c_008],
    preserve=[c_002,c_003,c_005,c_006,c_007,c_009,c_010,c_011],
    skill_ids_used=[counting_and_instance_layout, spatial_relation_layout],
    strategy_tags=[localized_repair,counting,spatial_relation],
    edit_instruction="add exactly two transparent glass lions so final count is six; make lions chase cats; keep cats behind donut; preserve stable passes; forbid extras/cropping/fusion/unrelated redraw"
  )

observation:
  Qwen edit -> img_002
  Geneval2 -> 9/11 pass
  fixed=[c_001]
  failed=[c_004,c_008]
  state:
    latest=a_002
    best=a_002
    budget=2
```

### Step 4

```text
seen by model:
  latest=a_002
  best=a_002
  visible images=[img_002]
  history=[a_000,a_001,a_002]
  budget=2
  failed=[c_004,c_008]
  stable_passes=9 atoms

assistant target:
  edit_image(
    source_attempt_id=a_002,
    target=[c_004,c_008],
    preserve=[nine passing atoms],
    strategy_tags=[localized_repair,depth_relation,motion_relation],
    edit_instruction="adjust only depth and motion cues; keep counts/material/colors; make cats behind donut and lions chasing cats clearer"
  )

observation:
  Qwen edit -> img_003
  Geneval2 -> 8/11 pass
  regressed=[c_002]
  failed=[c_002,c_004,c_008]
  state:
    latest=a_003
    best=a_002
    budget=1
```

### Step 5

```text
seen by model:
  latest=a_003
  best=a_002
  visible images=[latest img_003, best img_002]
  history=[a_000,a_001,a_002,a_003]
  budget=1
  latest_regressed=[c_002]
  best_failed=[c_004,c_008]

assistant target:
  edit_image(
    source_attempt_id=a_002,
    target=[c_004,c_008],
    preserve=[nine passing atoms from best],
    strategy_tags=[best_branch,localized_repair,spatial_relation],
    edit_instruction="revise a_002, not a_003; preserve six glass lions, three red cats, one brown donut; repair chasing/depth relation"
  )

observation:
  Qwen edit -> img_004
  Geneval2 -> 9/11 pass
  failed=[c_004,c_008]
  state:
    latest=a_004
    best=a_002
    budget=0
```

### Step 6

```text
seen by model:
  latest=a_004
  best=a_002
  visible images=[latest img_004, best img_002]
  budget=0

assistant target:
  submit_attempt(
    selected_attempt_id=a_002,
    reason_code=best_available_under_budget
  )

observation:
  submitted=a_002
```
