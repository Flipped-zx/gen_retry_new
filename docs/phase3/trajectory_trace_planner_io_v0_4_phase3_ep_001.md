# Normalized Trajectory: Planner I/O v0.4 `phase3_ep_001`

Source events: `runs/teacher_prompt_v1_validation/phase3_ep_001/events.jsonl`

This is a v0.4 replay/normalization of the real branch-recovery trajectory. It is not a new live rollout. The original teacher actions were v0.2, so fields that did not exist then, such as `decision_summary`, normalize to an empty string in replay artifacts. New v0.4 live actions must populate them.

## System Protocol

The planner receives a fixed system protocol defining:

- action space: `query_skill`, `generate_image`, `edit_image`, `submit_attempt`;
- output envelope: one JSON object with `schema_version: "0.4"`, `action`, and `arguments`;
- `generate_image` has no source attempt;
- `edit_image` requires `source_attempt_id`;
- visible images are provided outside PlannerContext as labeled multimodal inputs;
- budget zero allows only `submit_attempt`.

## Task Context

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

Atom constraints: `c_001` to `c_011`, covering lion count/material/existence, chasing relation, cat count/color/existence, cats-behind-donut relation, and donut count/color/existence.

## Action Sequence

```text
s_000 query_skill
s_001 generate_image              -> a_000
s_002 generate_image              -> a_001
s_003 edit_image(source=a_001)    -> a_002
s_004 edit_image(source=a_002)    -> a_003
s_005 edit_image(source=a_002)    -> a_004
s_006 submit_attempt(a_002)
```

## Round 0

### Planner Input Before `query_skill`

```yaml
planner_context:
  task_context: original prompt + atom constraints + max_image_attempts=5
  latest_observation: null
  skill_context:
    active_skills: []
  episode_memory:
    recent_round: null
    earlier_rounds: []
    best_attempt: null
  runtime_state:
    remaining_image_budget: 5
    available_actions: [query_skill, generate_image]
visible_images: []
```

### Assistant Action

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

### Tool Result In Next Planner Input

```yaml
skill_context:
  active_skills:
    - skill_id: counting_and_instance_layout
      target_constraint_ids: [c_001, c_005, c_009]
      guidance_level: full
    - skill_id: spatial_relation_layout
      target_constraint_ids: [c_004, c_008]
      guidance_level: full
```

No attempt is created and no image budget is consumed.

### Assistant Image Action

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "",
    "diagnosis_summary": null,
    "target_constraint_ids": ["c_001", "c_002", "c_003", "c_004", "c_005", "c_006", "c_007", "c_008", "c_009", "c_010", "c_011"],
    "preserve_constraint_ids": [],
    "generation_instruction": "Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts."
  }
}
```

### Environment Output

```yaml
result_attempt_id: a_000
comparison_attempt_id: null
initial_passed: [c_003, c_006, c_007, c_009, c_010, c_011]
initial_failed: [c_001, c_004, c_005, c_008]
initial_uncertain: [c_002]
became_best: true
```

## Round 1

### Planner Input Delta

```yaml
latest_observation: a_000
episode_memory:
  recent_round: Round 0 full memory
  earlier_rounds: []
  best_attempt: a_000, same_as_latest=true
runtime_state:
  remaining_image_budget: 4
  available_actions: [query_skill, generate_image, edit_image, submit_attempt]
visible_images:
  - LATEST_IMAGE: attempt a_000
```

### Assistant Action

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "",
    "diagnosis_summary": null,
    "target_constraint_ids": ["c_001", "c_002", "c_003", "c_004", "c_005", "c_006", "c_007", "c_008", "c_009", "c_010", "c_011"],
    "preserve_constraint_ids": [],
    "generation_instruction": "Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects."
  }
}
```

### Environment Output

```yaml
result_attempt_id: a_001
comparison_attempt_id: a_000
fixed: [c_002, c_005]
regressed: []
persistent_failed: [c_001, c_004, c_008]
became_best: true
```

## Round 2

### Planner Input Delta

```yaml
latest_observation: a_001
episode_memory:
  recent_round: Round 1 full memory
  earlier_rounds: [Round 0 compact]
  best_attempt: a_001, same_as_latest=true
runtime_state.remaining_image_budget: 3
visible_images:
  - LATEST_IMAGE: attempt a_001
```

### Assistant Action

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",
    "decision_summary": "",
    "diagnosis_summary": null,
    "target_constraint_ids": ["c_001", "c_004", "c_008"],
    "preserve_constraint_ids": ["c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "edit_instruction": "Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene."
  }
}
```

### Environment Output

```yaml
result_attempt_id: a_002
comparison_attempt_id: a_001
fixed: [c_001]
regressed: []
persistent_failed: [c_004, c_008]
became_best: true
```

## Round 3

### Planner Input Delta

```yaml
latest_observation: a_002
episode_memory:
  recent_round: Round 2 full memory
  earlier_rounds: [Round 0 compact, Round 1 compact]
  best_attempt: a_002, same_as_latest=true
runtime_state.remaining_image_budget: 2
visible_images:
  - LATEST_IMAGE: attempt a_002
```

### Assistant Action

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "decision_summary": "",
    "diagnosis_summary": null,
    "target_constraint_ids": ["c_004", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "edit_instruction": "Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects."
  }
}
```

### Environment Output

```yaml
result_attempt_id: a_003
comparison_attempt_id: a_002
fixed: []
regressed: [c_002]
persistent_failed: [c_004, c_008]
became_best: false
```

## Round 4

### Planner Input Delta

```yaml
latest_observation: a_003
episode_memory:
  recent_round: Round 3 full memory showing c_002 regression
  earlier_rounds: [Round 0 compact, Round 1 compact, Round 2 compact]
  best_attempt: a_002, same_as_latest=false
runtime_state.remaining_image_budget: 1
visible_images:
  - LATEST_IMAGE: attempt a_003
  - BEST_IMAGE: attempt a_002
```

### Assistant Action

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "decision_summary": "",
    "diagnosis_summary": null,
    "target_constraint_ids": ["c_004", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "edit_instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap."
  }
}
```

### Environment Output

```yaml
result_attempt_id: a_004
comparison_attempt_id: a_002
fixed: []
regressed: []
persistent_failed: [c_004, c_008]
became_best: false
latest: a_004
best: a_002
remaining_image_budget: 0
```

## Final Submit

### Planner Input Delta

```yaml
latest_observation: a_004
episode_memory:
  recent_round: Round 4 full memory
  best_attempt: a_002, same_as_latest=false
runtime_state:
  remaining_image_budget: 0
  available_actions: [submit_attempt]
visible_images:
  - LATEST_IMAGE: attempt a_004
  - BEST_IMAGE: attempt a_002
```

### Assistant Action

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

## Verification Points

- `query_skill` is a planner action but creates no image attempt.
- `generate_image` is used for both first generation and regeneration.
- `edit_image.source_attempt_id` is explicit.
- Round 4 rolls back to `a_002` even though the latest image is `a_003`.
- The `a_004` transition compares `a_002 -> a_004`, not `a_003 -> a_004`.
- Final submission selects historical best `a_002`, not latest `a_004`.
