# Planner I/O v0.5 Round/Memory Walkthrough

Source trajectory: `runs/teacher_prompt_v1_validation/phase3_ep_001/events.jsonl`

Prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

This document projects the real trajectory into the proposed v0.5 field design. It is for field review, not a trainable SFT file.

Important note: this source trajectory was produced before v0.5. Sol rejected
post-hoc `decision_summary` labels, so the final projected actions below contain
only native structured decisions and the executable `instruction`.

## 1. What The Agent Sees Every Step

Every planner call gives the agent three things:

```yaml
system_prompt:
  fixed planner protocol and legal action schema

planner_context:
  task_context
  latest_attempt
  skill_context
  episode_memory
  runtime_state

visible_images:
  latest and/or best image bindings, when images exist
```

The agent outputs exactly one action:

```yaml
action:
  query_skill | generate_image | edit_image | submit_attempt
arguments:
  action-specific JSON fields
```

The agent does not output Geneval2 scores, fixed/regressed atoms, best/latest updates, image paths, or remaining budget. Those are produced by the environment and reducer, then become part of the next `planner_context`.

## 2. What Memory Means In v0.5

The memory given to the agent has three layers:

```yaml
latest_attempt:
  the newest image state
  answers: "what does the latest image pass/fail now?"

episode_memory.last_completed_image_round:
  the previous image-producing round
  answers: "what action produced latest_attempt, from which source, and what changed?"

episode_memory.prior_image_rounds:
  compressed older image rounds
  answers: "what strategies already happened earlier?"

episode_memory.best_attempt:
  the historical best image state
  answers: "if latest regressed, which attempt can I rollback to or submit?"
```

So `latest_attempt` is state. `last_completed_image_round` is cause. They may point to the same result image, but they do not duplicate the same job.

## 3. Global Task Context

This part is stable and appears in every planner input.

```yaml
task_context:
  original_prompt: six glass lions chasing three red cats behind a brown donut
  max_image_attempts: 5
  atom_constraints:
    c_001: count, six lions
    c_002: attribute, lions are glass
    c_003: object, lions exist
    c_004: verb, lions chasing cats
    c_005: count, three cats
    c_006: attribute, cats are red
    c_007: object, cats exist
    c_008: position, cats behind donut
    c_009: count, one donut
    c_010: attribute, donut is brown
    c_011: object, donut exists
```

## 4. Round 0: Skill Query + First Generation

Round 0 contains two planner action steps. It ends only after the first image is generated and evaluated.

### Step 0A Input To Agent

```yaml
planner_context.latest_attempt: null
planner_context.skill_context.active_skills: []
planner_context.episode_memory.last_completed_image_round: null
planner_context.episode_memory.prior_image_rounds: []
planner_context.episode_memory.best_attempt: null
planner_context.runtime_state:
  remaining_image_budget: 5
  available_actions: [query_skill, generate_image]
visible_images: []
```

### Step 0A Output From Agent

```json
{
  "schema_version": "0.5",
  "action": "query_skill",
  "arguments": {
    "skill_ids": [
      "counting_and_instance_layout",
      "action_pose_relation",
      "spatial_relation_layout"
    ],
    "target_constraint_ids": ["c_001", "c_004", "c_005", "c_008", "c_009"]
  }
}
```

### Environment Update After Step 0A

No image is created and no image budget is consumed.

The next planner input gets:

```yaml
planner_context.skill_context.active_skills:
  - skill_id: counting_and_instance_layout
    target_constraint_ids: [c_001, c_005, c_009]
    guidance_level: full
  - skill_id: action_pose_relation
    target_constraint_ids: [c_004]
    guidance_level: full
  - skill_id: spatial_relation_layout
    target_constraint_ids: [c_008]
    guidance_level: full
```

The skill content is an observation with loss 0. It is visible to the next action but is not an assistant target.

### Step 0B Input To Agent

The agent now sees the same task, still no image, but with active skill guidance:

```yaml
planner_context.latest_attempt: null
planner_context.skill_context.active_skills:
  - counting_and_instance_layout, full guidance
  - action_pose_relation, full guidance
  - spatial_relation_layout, full guidance
planner_context.episode_memory.last_completed_image_round: null
planner_context.runtime_state.remaining_image_budget: 5
visible_images: []
```

### Step 0B Output From Agent

v0.5 projected action:

```json
{
  "schema_version": "0.5",
  "action": "generate_image",
  "arguments": {
    "target_constraint_ids": ["c_001", "c_002", "c_003", "c_004", "c_005", "c_006", "c_007", "c_008", "c_009", "c_010", "c_011"],
    "preserve_constraint_ids": [],
    "instruction": "Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts."
  }
}
```

### Environment Update After Round 0

Qwen creates `a_000`; Geneval2 evaluates it.

```yaml
latest_attempt:
  attempt_id: a_000
  passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_001, c_004, c_005, c_008]
  uncertain_constraint_ids: [c_002]

episode_memory.last_completed_image_round:
  skill_queries:
    - counting_and_instance_layout -> [c_001, c_005, c_009]
    - action_pose_relation -> [c_004]
    - spatial_relation_layout -> [c_008]
  image_action:
    action: generate_image
    source_attempt_id: null
    target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
    preserve_constraint_ids: []
    instruction: [same as action instruction]
  result_attempt_id: a_000
  observed_outcome:
    baseline_attempt_id: null
    initial_passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
    initial_failed_constraint_ids: [c_001, c_004, c_005, c_008]
    initial_uncertain_constraint_ids: [c_002]

episode_memory.best_attempt:
  attempt_id: a_000
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 4
visible_images:
  - role: latest
    attempt_id: a_000
  - role: best
    attempt_id: a_000
```

## 5. Round 1: Regenerate From Scratch

### Input To Agent

The agent sees the latest image state and the previous round that caused it:

```yaml
latest_attempt:
  attempt_id: a_000
  failed_constraint_ids: [c_001, c_004, c_005, c_008]
  uncertain_constraint_ids: [c_002]

skill_context.active_skills:
  - counting_and_instance_layout, summary guidance
  - spatial_relation_layout, summary guidance

episode_memory.last_completed_image_round:
  image_action.action: generate_image
  result_attempt_id: a_000
  observed_outcome.initial_failed_constraint_ids: [c_001, c_004, c_005, c_008]
  observed_outcome.initial_uncertain_constraint_ids: [c_002]

episode_memory.prior_image_rounds: []
episode_memory.best_attempt:
  attempt_id: a_000
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 4
visible_images: [a_000 as latest/best]
```

### Output From Agent

The old trajectory chose a fresh generation instead of editing `a_000`.

```json
{
  "schema_version": "0.5",
  "action": "generate_image",
  "arguments": {
    "target_constraint_ids": ["c_001", "c_002", "c_003", "c_004", "c_005", "c_006", "c_007", "c_008", "c_009", "c_010", "c_011"],
    "preserve_constraint_ids": [],
    "instruction": "Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects."
  }
}
```

### Environment Update After Round 1

```yaml
latest_attempt:
  attempt_id: a_001
  passed_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_001, c_004, c_008]
  uncertain_constraint_ids: []

episode_memory.last_completed_image_round:
  image_action.action: generate_image
  result_attempt_id: a_001
  observed_outcome:
    baseline_attempt_id: a_000
    fixed_constraint_ids: [c_002, c_005]
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_001, c_004, c_008]

episode_memory.prior_image_rounds:
  - round 0 compact summary: first generation created a_000 with count/cat/relation failures

episode_memory.best_attempt:
  attempt_id: a_001
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 3
visible_images: [a_001 as latest/best]
```

## 6. Round 2: Edit Current Best

### Input To Agent

```yaml
latest_attempt:
  attempt_id: a_001
  failed_constraint_ids: [c_001, c_004, c_008]

episode_memory.last_completed_image_round:
  image_action.action: generate_image
  result_attempt_id: a_001
  observed_outcome:
    fixed_constraint_ids: [c_002, c_005]
    persistent_failed_constraint_ids: [c_001, c_004, c_008]

episode_memory.prior_image_rounds:
  - r_000 summary

episode_memory.best_attempt:
  attempt_id: a_001
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 3
visible_images: [a_001 as latest/best]
```

### Output From Agent

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",
    "target_constraint_ids": ["c_001", "c_004", "c_008"],
    "preserve_constraint_ids": ["c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "instruction": "Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene."
  }
}
```

### Environment Update After Round 2

```yaml
latest_attempt:
  attempt_id: a_002
  passed_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_004, c_008]

episode_memory.last_completed_image_round:
  image_action:
    action: edit_image
    source_attempt_id: a_001
    target_constraint_ids: [c_001, c_004, c_008]
    preserve_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  result_attempt_id: a_002
  observed_outcome:
    baseline_attempt_id: a_001
    fixed_constraint_ids: [c_001]
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_004, c_008]

episode_memory.prior_image_rounds:
  - r_000 compact summary
  - r_001 compact summary

episode_memory.best_attempt:
  attempt_id: a_002
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 2
visible_images: [a_002 as latest/best]
```

This is the cleanest successful transition in the trajectory: the edit fixed the lion count without breaking preserved atoms.

## 7. Round 3: Edit Latest, Causing Regression

### Input To Agent

```yaml
latest_attempt:
  attempt_id: a_002
  failed_constraint_ids: [c_004, c_008]

episode_memory.last_completed_image_round:
  image_action.action: edit_image
  image_action.source_attempt_id: a_001
  observed_outcome.fixed_constraint_ids: [c_001]
  observed_outcome.persistent_failed_constraint_ids: [c_004, c_008]

episode_memory.best_attempt:
  attempt_id: a_002
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 2
visible_images: [a_002 as latest/best]
```

### Output From Agent

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": ["c_004", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "instruction": "Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects."
  }
}
```

### Environment Update After Round 3

```yaml
latest_attempt:
  attempt_id: a_003
  passed_constraint_ids: [c_001, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_002, c_004, c_008]

episode_memory.last_completed_image_round:
  image_action:
    action: edit_image
    source_attempt_id: a_002
    target_constraint_ids: [c_004, c_008]
    preserve_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  result_attempt_id: a_003
  observed_outcome:
    baseline_attempt_id: a_002
    fixed_constraint_ids: []
    regressed_constraint_ids: [c_002]
    persistent_failed_constraint_ids: [c_004, c_008]

episode_memory.best_attempt:
  attempt_id: a_002
  constraint_results:
    passed_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_004, c_008]
    uncertain_constraint_ids: []

runtime_state.remaining_image_budget: 1
visible_images:
  - latest: a_003
  - best: a_002
```

This is where v0.5 memory matters most. The agent sees that latest `a_003` is worse than best `a_002`, and it also sees why: the last edit tried to fix relation atoms but regressed `c_002` glass material.

## 8. Round 4: Roll Back To Best And Edit

### Input To Agent

```yaml
latest_attempt:
  attempt_id: a_003
  failed_constraint_ids: [c_002, c_004, c_008]

episode_memory.last_completed_image_round:
  image_action.source_attempt_id: a_002
  image_action.target_constraint_ids: [c_004, c_008]
  observed_outcome:
    fixed_constraint_ids: []
    regressed_constraint_ids: [c_002]
    persistent_failed_constraint_ids: [c_004, c_008]

episode_memory.best_attempt:
  attempt_id: a_002
  failed_constraint_ids: [c_004, c_008]

runtime_state.remaining_image_budget: 1
visible_images:
  - latest: a_003
  - best: a_002
```

### Output From Agent

The old trajectory correctly chose the historical best source, not latest.

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": ["c_004", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap."
  }
}
```

### Environment Update After Round 4

```yaml
latest_attempt:
  attempt_id: a_004
  passed_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_004, c_008]

episode_memory.last_completed_image_round:
  image_action:
    action: edit_image
    source_attempt_id: a_002
    target_constraint_ids: [c_004, c_008]
  result_attempt_id: a_004
  observed_outcome:
    baseline_attempt_id: a_002
    fixed_constraint_ids: []
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_004, c_008]

episode_memory.best_attempt:
  attempt_id: a_002
  constraint_results:
    passed_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_004, c_008]

runtime_state.remaining_image_budget: 0
```

The edit preserved the best score but did not improve it. Since best update is strict improvement, `a_002` remains the submitted best.

## 9. Final Submit

### Input To Agent

```yaml
latest_attempt:
  attempt_id: a_004
  failed_constraint_ids: [c_004, c_008]

episode_memory.best_attempt:
  attempt_id: a_002
  failed_constraint_ids: [c_004, c_008]

runtime_state:
  remaining_image_budget: 0
  available_actions: [submit_attempt]

visible_images:
  - latest: a_004
  - best: a_002
```

### Output From Agent

```json
{
  "schema_version": "0.5",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_002",
    "reason_code": "best_available_under_budget"
  }
}
```

## 10. What This Teaches The Agent

The v0.5 memory is designed so the agent can learn the following decisions:

1. Use `query_skill` before image generation when the task has count and relation constraints.
2. Use `generate_image` when no image exists or the latest image has many global failures.
3. Use `edit_image` when a source attempt has many preserved atoms and a small set of repair targets.
4. Use `source_attempt_id` to rollback from latest to best after regression.
5. Use `submit_attempt` on historical best when budget is exhausted.

The key input/output boundary is:

```text
Agent sees:
  task_context + latest_attempt + skill_context + episode_memory + runtime_state + visible_images

Agent predicts:
  one action JSON

Environment writes back:
  image attempt, Geneval2 atom results, transition, best/latest, budget
```

This is the exact reason we maintain memory: not to let the agent rewrite history, but to give it compact causal evidence for the next decision.
