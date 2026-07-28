# Planner I/O v0.4: Real Fields Per Round for `phase3_ep_001`

Source events: `runs/teacher_prompt_v1_validation/phase3_ep_001/events.jsonl`

This is the real branch-recovery trajectory normalized into Planner I/O v0.4. It is not a new live rollout. The source actions were produced before v0.4, so `decision_summary` is empty in this replay. New v0.4 live actions must fill it.

## Global Input Shape

Every planner call receives:

```yaml
system_prompt: fixed v0.4 planner protocol
planner_context:
  task_context:
    original_prompt
    max_image_attempts
    atom_constraints:
      - constraint_id
        constraint_type
        requirement
        evaluator_question
  latest_observation:
    attempt_id
    constraint_results:
      passed_constraint_ids
      failed_constraint_ids
      uncertain_constraint_ids
      observations:
        - constraint_id
          observed_value
  skill_context:
    active_skills:
      - skill_id
        target_constraint_ids
        guidance
        guidance_level
  episode_memory:
    recent_round:
      skill_queries
      image_action
      result_attempt_id
      observed_outcome
    earlier_rounds
    best_attempt
  runtime_state:
    remaining_image_budget
    available_actions
visible_images:
  - role
    attempt_id
    artifact_id
```

The assistant output is always:

```yaml
schema_version: "0.4"
action: query_skill | generate_image | edit_image | submit_attempt
arguments: {}
```

## Task Fields

These fields stay fixed across the episode:

```yaml
planner_context.task_context.original_prompt:
  six glass lions chasing three red cats behind a brown donut

planner_context.task_context.max_image_attempts: 5

planner_context.task_context.atom_constraints:
  - c_001 count: lion count = six
  - c_002 attribute: lions are glass
  - c_003 object: lions exist
  - c_004 verb: lions are chasing cats
  - c_005 count: cat count = three
  - c_006 attribute: cats are red
  - c_007 object: cats exist
  - c_008 position: cats are behind donut
  - c_009 count: donut count = one
  - c_010 attribute: donut is brown
  - c_011 object: donut exists
```

## Round 1A: `query_skill`

### Planner Input

```yaml
planner_context.latest_observation: null

planner_context.skill_context.active_skills: []

planner_context.episode_memory.recent_round: null
planner_context.episode_memory.earlier_rounds: []
planner_context.episode_memory.best_attempt: null

planner_context.runtime_state.remaining_image_budget: 5
planner_context.runtime_state.available_actions:
  - query_skill
  - generate_image

visible_images: []
```

### Planner Output

```json
{
  "schema_version": "0.4",
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

### Environment Update Into Next Planner Input

```yaml
planner_context.skill_context.active_skills:
  - skill_id: counting_and_instance_layout
    target_constraint_ids: [c_001, c_005, c_009]
    guidance: [full Skill text]
    guidance_level: full

  - skill_id: spatial_relation_layout
    target_constraint_ids: [c_004, c_008]
    guidance: [full Skill text]
    guidance_level: full
```

No image attempt is created. `planner_context.runtime_state.remaining_image_budget` stays `5`.

## Round 1B: `generate_image -> a_000`

### Planner Input Delta

```yaml
planner_context.latest_observation: null
planner_context.skill_context.active_skills:
  - counting_and_instance_layout
  - spatial_relation_layout
planner_context.episode_memory.recent_round: null
planner_context.episode_memory.earlier_rounds: []
planner_context.episode_memory.best_attempt: null
planner_context.runtime_state.remaining_image_budget: 5
visible_images: []
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "",
    "diagnosis_summary": null,
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
    "generation_instruction": "Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts."
  }
}
```

### Environment Update Into Round 2 Input

```yaml
planner_context.latest_observation:
  attempt_id: a_000
  constraint_results:
    passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_001, c_004, c_005, c_008]
    uncertain_constraint_ids: [c_002]
    observations: [{constraint_id, observed_value}, ...]

planner_context.episode_memory.recent_round:
  skill_queries:
    - skill_id: counting_and_instance_layout
      target_constraint_ids: [c_001, c_005, c_009]
    - skill_id: spatial_relation_layout
      target_constraint_ids: [c_004, c_008]
  image_action:
    action: generate_image
    source_attempt_id: null
    decision_summary: ""
    diagnosis_summary: null
    target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
    preserve_constraint_ids: []
    instruction: [same generation_instruction]
  result_attempt_id: a_000
  observed_outcome:
    comparison_attempt_id: null
    initial_passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
    initial_failed_constraint_ids: [c_001, c_004, c_005, c_008]
    initial_uncertain_constraint_ids: [c_002]
    fixed_constraint_ids: []
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: []
    preserved_constraint_ids: []
    new_uncertain_constraint_ids: []
    became_best: true

planner_context.episode_memory.earlier_rounds: []

planner_context.episode_memory.best_attempt:
  attempt_id: a_000
  same_as_latest: true
  constraint_results:
    passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_001, c_004, c_005, c_008]
    uncertain_constraint_ids: [c_002]
    observations: [{constraint_id, observed_value}, ...]

planner_context.runtime_state.remaining_image_budget: 4
planner_context.runtime_state.available_actions:
  - query_skill
  - generate_image
  - edit_image
  - submit_attempt

visible_images:
  - role: latest
    attempt_id: a_000
    artifact_id: [a_000 image artifact id]
```

## Round 2: `generate_image -> a_001`

### Planner Input

```yaml
planner_context.latest_observation.attempt_id: a_000
planner_context.latest_observation.constraint_results:
  passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_001, c_004, c_005, c_008]
  uncertain_constraint_ids: [c_002]

planner_context.skill_context.active_skills:
  - counting_and_instance_layout
  - spatial_relation_layout

planner_context.episode_memory.recent_round.result_attempt_id: a_000
planner_context.episode_memory.earlier_rounds: []
planner_context.episode_memory.best_attempt.attempt_id: a_000
planner_context.episode_memory.best_attempt.same_as_latest: true

planner_context.runtime_state.remaining_image_budget: 4
planner_context.runtime_state.available_actions:
  - query_skill
  - generate_image
  - edit_image
  - submit_attempt

visible_images:
  - role: latest
    attempt_id: a_000
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "",
    "diagnosis_summary": null,
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
    "generation_instruction": "Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects."
  }
}
```

### Environment Update Into Round 3 Input

```yaml
planner_context.latest_observation:
  attempt_id: a_001
  constraint_results:
    passed_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_001, c_004, c_008]
    uncertain_constraint_ids: []
    observations: [{constraint_id, observed_value}, ...]

planner_context.episode_memory.recent_round:
  skill_queries: []
  image_action:
    action: generate_image
    source_attempt_id: null
    decision_summary: ""
    diagnosis_summary: null
    target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
    preserve_constraint_ids: []
    instruction: [Round 2 generation_instruction]
  result_attempt_id: a_001
  observed_outcome:
    comparison_attempt_id: a_000
    initial_passed_constraint_ids: []
    initial_failed_constraint_ids: []
    initial_uncertain_constraint_ids: []
    fixed_constraint_ids: [c_002, c_005]
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_001, c_004, c_008]
    preserved_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
    new_uncertain_constraint_ids: []
    became_best: true

planner_context.episode_memory.earlier_rounds:
  - action: generate_image
    source_attempt_id: null
    result_attempt_id: a_000
    decision_summary: ""
    target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
    preserve_constraint_ids: []
    outcome_summary:
      fixed_constraint_ids: []
      regressed_constraint_ids: []
      persistent_failed_constraint_ids: []
      became_best: true

planner_context.episode_memory.best_attempt:
  attempt_id: a_001
  same_as_latest: true

planner_context.runtime_state.remaining_image_budget: 3

visible_images:
  - role: latest
    attempt_id: a_001
```

## Round 3: `edit_image(source_attempt_id=a_001) -> a_002`

### Planner Input

```yaml
planner_context.latest_observation.attempt_id: a_001
planner_context.latest_observation.constraint_results:
  failed_constraint_ids: [c_001, c_004, c_008]

planner_context.episode_memory.recent_round.result_attempt_id: a_001
planner_context.episode_memory.recent_round.observed_outcome:
  comparison_attempt_id: a_000
  fixed_constraint_ids: [c_002, c_005]
  persistent_failed_constraint_ids: [c_001, c_004, c_008]
  became_best: true

planner_context.episode_memory.earlier_rounds:
  - result_attempt_id: a_000

planner_context.episode_memory.best_attempt:
  attempt_id: a_001
  same_as_latest: true

planner_context.runtime_state.remaining_image_budget: 3

visible_images:
  - role: latest
    attempt_id: a_001
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",
    "decision_summary": "",
    "diagnosis_summary": null,
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
    "edit_instruction": "Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene."
  }
}
```

### Environment Update Into Round 4 Input

```yaml
planner_context.latest_observation:
  attempt_id: a_002
  constraint_results:
    passed_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_004, c_008]
    uncertain_constraint_ids: []

planner_context.episode_memory.recent_round:
  skill_queries: []
  image_action:
    action: edit_image
    source_attempt_id: a_001
    decision_summary: ""
    diagnosis_summary: null
    target_constraint_ids: [c_001, c_004, c_008]
    preserve_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    instruction: [Round 3 edit_instruction]
  result_attempt_id: a_002
  observed_outcome:
    comparison_attempt_id: a_001
    initial_passed_constraint_ids: []
    initial_failed_constraint_ids: []
    initial_uncertain_constraint_ids: []
    fixed_constraint_ids: [c_001]
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_004, c_008]
    preserved_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    new_uncertain_constraint_ids: []
    became_best: true

planner_context.episode_memory.earlier_rounds:
  - result_attempt_id: a_000
  - result_attempt_id: a_001

planner_context.episode_memory.best_attempt:
  attempt_id: a_002
  same_as_latest: true

planner_context.runtime_state.remaining_image_budget: 2

visible_images:
  - role: latest
    attempt_id: a_002
```

## Round 4: `edit_image(source_attempt_id=a_002) -> a_003`

### Planner Input

```yaml
planner_context.latest_observation.attempt_id: a_002
planner_context.latest_observation.constraint_results:
  passed_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_004, c_008]

planner_context.episode_memory.recent_round.result_attempt_id: a_002
planner_context.episode_memory.recent_round.observed_outcome:
  comparison_attempt_id: a_001
  fixed_constraint_ids: [c_001]
  persistent_failed_constraint_ids: [c_004, c_008]
  became_best: true

planner_context.episode_memory.best_attempt:
  attempt_id: a_002
  same_as_latest: true

planner_context.runtime_state.remaining_image_budget: 2

visible_images:
  - role: latest
    attempt_id: a_002
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "decision_summary": "",
    "diagnosis_summary": null,
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
    "edit_instruction": "Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects."
  }
}
```

### Environment Update Into Round 5 Input

```yaml
planner_context.latest_observation:
  attempt_id: a_003
  constraint_results:
    failed_constraint_ids: [c_002, c_004, c_008]

planner_context.episode_memory.recent_round:
  image_action:
    action: edit_image
    source_attempt_id: a_002
    target_constraint_ids: [c_004, c_008]
    preserve_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    instruction: [Round 4 edit_instruction]
  result_attempt_id: a_003
  observed_outcome:
    comparison_attempt_id: a_002
    fixed_constraint_ids: []
    regressed_constraint_ids: [c_002]
    persistent_failed_constraint_ids: [c_004, c_008]
    preserved_constraint_ids: [c_001, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    new_uncertain_constraint_ids: []
    became_best: false

planner_context.episode_memory.earlier_rounds:
  - result_attempt_id: a_000
  - result_attempt_id: a_001
  - result_attempt_id: a_002

planner_context.episode_memory.best_attempt:
  attempt_id: a_002
  same_as_latest: false
  constraint_results:
    failed_constraint_ids: [c_004, c_008]

planner_context.runtime_state.remaining_image_budget: 1

visible_images:
  - role: latest
    attempt_id: a_003
  - role: best
    attempt_id: a_002
```

## Round 5: `edit_image(source_attempt_id=a_002) -> a_004`

### Planner Input

```yaml
planner_context.latest_observation.attempt_id: a_003
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_002, c_004, c_008]

planner_context.episode_memory.recent_round.result_attempt_id: a_003
planner_context.episode_memory.recent_round.observed_outcome:
  comparison_attempt_id: a_002
  regressed_constraint_ids: [c_002]
  persistent_failed_constraint_ids: [c_004, c_008]
  became_best: false

planner_context.episode_memory.best_attempt:
  attempt_id: a_002
  same_as_latest: false
  constraint_results.failed_constraint_ids: [c_004, c_008]

planner_context.runtime_state.remaining_image_budget: 1

visible_images:
  - role: latest
    attempt_id: a_003
  - role: best
    attempt_id: a_002
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "decision_summary": "",
    "diagnosis_summary": null,
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
    "edit_instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap."
  }
}
```

### Environment Update Into Final Submit Input

```yaml
planner_context.latest_observation:
  attempt_id: a_004
  constraint_results:
    failed_constraint_ids: [c_004, c_008]

planner_context.episode_memory.recent_round:
  image_action:
    action: edit_image
    source_attempt_id: a_002
    target_constraint_ids: [c_004, c_008]
    preserve_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    instruction: [Round 5 edit_instruction]
  result_attempt_id: a_004
  observed_outcome:
    comparison_attempt_id: a_002
    fixed_constraint_ids: []
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_004, c_008]
    preserved_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    new_uncertain_constraint_ids: []
    became_best: false

planner_context.episode_memory.best_attempt:
  attempt_id: a_002
  same_as_latest: false

planner_context.runtime_state.remaining_image_budget: 0
planner_context.runtime_state.available_actions:
  - submit_attempt

visible_images:
  - role: latest
    attempt_id: a_004
  - role: best
    attempt_id: a_002
```

## Final Planner Call: `submit_attempt`

### Planner Input

```yaml
planner_context.latest_observation.attempt_id: a_004
planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: false
planner_context.runtime_state.remaining_image_budget: 0
planner_context.runtime_state.available_actions: [submit_attempt]
visible_images:
  - role: latest
    attempt_id: a_004
  - role: best
    attempt_id: a_002
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_002",
    "reason_code": "best_available_under_budget"
  }
}
```

## Short Summary

| Step | Planner input changed by previous step | Planner output | Environment writes into next input |
|---|---|---|---|
| Round 1A | initial `task_context`, empty observation/memory/skills | `query_skill` | `skill_context.active_skills` |
| Round 1B | active skills now present | `generate_image` | `latest_observation=a_000`, `recent_round`, `best_attempt=a_000`, budget 4 |
| Round 2 | sees `a_000` failures and Round 1 memory | `generate_image` | `latest_observation=a_001`, Round 1 compacted, `best_attempt=a_001`, budget 3 |
| Round 3 | sees `a_001` failures and best=`a_001` | `edit_image(source_attempt_id=a_001)` | `latest_observation=a_002`, `best_attempt=a_002`, budget 2 |
| Round 4 | sees only `c_004/c_008` still failed | `edit_image(source_attempt_id=a_002)` | `latest_observation=a_003`, regression `[c_002]`, best remains `a_002`, budget 1 |
| Round 5 | sees latest `a_003`, best `a_002`, and two visible images | `edit_image(source_attempt_id=a_002)` | `latest_observation=a_004`, best remains `a_002`, budget 0 |
| Final | budget 0, only submit legal | `submit_attempt(selected_attempt_id=a_002)` | episode ends |
