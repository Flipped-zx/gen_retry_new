# Planner I/O v0.4 Field Confirmation Short

Source trajectory: `runs/teacher_prompt_v1_validation/phase3_ep_001/events.jsonl`

Purpose: this document is for confirming whether the Planner input/output fields are reasonable. It avoids the full long prompts and keeps only the structure needed to understand the trajectory.

## 1. One-Step Loop

Each planner step follows this loop:

```text
Planner Input
  system_prompt
  planner_context
  visible_images

Planner Output
  exactly one action JSON

Environment
  execute action if needed
  run Geneval2 if an image is produced
  reducer computes latest/best/outcome/budget
  build next planner_context
```

The planner chooses actions. The environment owns image results, atom scores, fixed/regressed constraints, best attempt, latest attempt, and remaining budget.

## 2. Actual Input Fields

```yaml
system_prompt:
  fixed planner protocol:
    - output exactly one JSON action
    - legal actions: query_skill, generate_image, edit_image, submit_attempt
    - generate_image has no source image
    - edit_image requires source_attempt_id
    - budget 0 means only submit_attempt

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
  - role: latest | best
    attempt_id
    artifact_id
```

Before the first image, `latest_observation=null`, `episode_memory.recent_round=null`, `episode_memory.best_attempt=null`, and `visible_images=[]`.

## 3. Actual Output Action Space

The planner output is exactly one action JSON. It never outputs scores, best attempt, fixed/regressed constraints, image paths, or environment facts.

### 3.1 `query_skill`

Purpose: retrieve capability guidance for the current prompt/constraint state. It does not create an image and does not consume image budget.

```json
{
  "schema_version": "0.4",
  "action": "query_skill",
  "arguments": {
    "skill_ids": ["..."],
    "target_constraint_ids": ["..."]
  }
}
```

### 3.2 `generate_image`

Purpose: create a new image without a source image. This covers both first generation and regeneration from scratch.

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "...",
    "diagnosis_summary": null,
    "target_constraint_ids": ["..."],
    "preserve_constraint_ids": [],
    "generation_instruction": "..."
  }
}
```

### 3.3 `edit_image`

Purpose: edit a specific historical attempt. The source can be the latest attempt or a previous best attempt.

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_xxx",
    "decision_summary": "...",
    "diagnosis_summary": "...",
    "target_constraint_ids": ["..."],
    "preserve_constraint_ids": ["..."],
    "edit_instruction": "..."
  }
}
```

### 3.4 `submit_attempt`

Purpose: end the episode by submitting one historical attempt. It does not need to be the latest attempt.

```json
{
  "schema_version": "0.4",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_xxx",
    "reason_code": "best_available_under_budget"
  }
}
```

### 3.5 Output Ownership

The planner owns only the action choice and action arguments:

```text
action type
source_attempt_id for edit_image
selected_attempt_id for submit_attempt
target_constraint_ids
preserve_constraint_ids
decision_summary
diagnosis_summary
generation_instruction / edit_instruction
```

The planner does not own:

```text
latest attempt
best attempt
Geneval2 atom status
fixed_constraint_ids
regressed_constraint_ids
persistent_failed_constraint_ids
remaining_image_budget
visible image bindings
```

Those are computed by the environment and become part of the next Planner Input.

## 4. Real Trajectory, Short Version

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

Image budget: `5`

Atom constraints:

```text
c_001 six lions
c_002 lions glass
c_003 lions exist
c_004 lions chasing cats
c_005 three cats
c_006 cats red
c_007 cats exist
c_008 cats behind donut
c_009 one donut
c_010 donut brown
c_011 donut exists
```

### Round Table

| Round | Planner input state | Planner output | Environment result | What enters next input |
|---|---|---|---|---|
| 1A | no image, no skills, budget 5 | `query_skill` | returns counting + spatial skills | `skill_context.active_skills` |
| 1B | no image, active skills present, budget 5 | `generate_image` | creates `a_000`; 6 pass, 4 fail, 1 uncertain | `latest_observation=a_000`, `recent_round`, `best_attempt=a_000`, budget 4 |
| 2 | latest/best `a_000`, failures visible | `generate_image` | creates `a_001`; fixes `c_002,c_005`; still fails `c_001,c_004,c_008` | `latest_observation=a_001`, `best_attempt=a_001`, Round 1 compacted, budget 3 |
| 3 | latest/best `a_001`, remaining failures visible | `edit_image(source=a_001)` | creates `a_002`; fixes `c_001`; still fails `c_004,c_008` | `latest_observation=a_002`, `best_attempt=a_002`, budget 2 |
| 4 | latest/best `a_002`, only relation failures remain | `edit_image(source=a_002)` | creates `a_003`; regresses `c_002`; still fails `c_004,c_008` | `latest_observation=a_003`, `best_attempt=a_002`, latest != best, budget 1 |
| 5 | latest `a_003`, best `a_002`, both images visible | `edit_image(source=a_002)` | creates `a_004`; no improvement; best remains `a_002` | `latest_observation=a_004`, `best_attempt=a_002`, budget 0 |
| Final | budget 0, only submit legal | `submit_attempt(a_002)` | episode ends | submitted historical best |

## 5. Per-Round Field View

This section shows the real field paths that matter each round. Long instructions are abbreviated as `[instruction text]`; the full text is stored in the action field itself.

### Round 1A: Query Skills

Planner input:

```yaml
planner_context.latest_observation: null
planner_context.skill_context.active_skills: []
planner_context.episode_memory.recent_round: null
planner_context.episode_memory.earlier_rounds: []
planner_context.episode_memory.best_attempt: null
planner_context.runtime_state.remaining_image_budget: 5
planner_context.runtime_state.available_actions: [query_skill, generate_image]
visible_images: []
```

Planner output:

```yaml
action: query_skill
arguments.skill_ids:
  - counting_and_instance_layout
  - spatial_relation_layout
arguments.target_constraint_ids: [c_001, c_004, c_005, c_008, c_009]
```

Next input update:

```yaml
planner_context.skill_context.active_skills:
  - skill_id: counting_and_instance_layout
    target_constraint_ids: [c_001, c_005, c_009]
    guidance_level: full
  - skill_id: spatial_relation_layout
    target_constraint_ids: [c_004, c_008]
    guidance_level: full
```

### Round 1B: First Generation

Planner input:

```yaml
planner_context.latest_observation: null
planner_context.skill_context.active_skills:
  - counting_and_instance_layout
  - spatial_relation_layout
planner_context.runtime_state.remaining_image_budget: 5
visible_images: []
```

Planner output:

```yaml
action: generate_image
arguments.decision_summary: ""
arguments.diagnosis_summary: null
arguments.target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
arguments.preserve_constraint_ids: []
arguments.generation_instruction: [instruction text for six glass lions, three red cats, one brown donut]
```

Next input update:

```yaml
planner_context.latest_observation.attempt_id: a_000
planner_context.latest_observation.constraint_results:
  passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_001, c_004, c_005, c_008]
  uncertain_constraint_ids: [c_002]

planner_context.episode_memory.recent_round:
  image_action.action: generate_image
  image_action.source_attempt_id: null
  result_attempt_id: a_000
  observed_outcome.comparison_attempt_id: null
  observed_outcome.initial_passed_constraint_ids: [c_003, c_006, c_007, c_009, c_010, c_011]
  observed_outcome.initial_failed_constraint_ids: [c_001, c_004, c_005, c_008]
  observed_outcome.initial_uncertain_constraint_ids: [c_002]
  observed_outcome.became_best: true

planner_context.episode_memory.best_attempt.attempt_id: a_000
planner_context.episode_memory.best_attempt.same_as_latest: true
planner_context.runtime_state.remaining_image_budget: 4
visible_images: [{role: latest, attempt_id: a_000}]
```

### Round 2: Regenerate

Planner input:

```yaml
planner_context.latest_observation.attempt_id: a_000
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_001, c_004, c_005, c_008]
planner_context.episode_memory.recent_round.result_attempt_id: a_000
planner_context.episode_memory.best_attempt.attempt_id: a_000
planner_context.runtime_state.remaining_image_budget: 4
visible_images: [{role: latest, attempt_id: a_000}]
```

Planner output:

```yaml
action: generate_image
arguments.target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
arguments.preserve_constraint_ids: []
arguments.generation_instruction: [regeneration instruction text]
```

Next input update:

```yaml
planner_context.latest_observation.attempt_id: a_001
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_001, c_004, c_008]

planner_context.episode_memory.recent_round:
  image_action.action: generate_image
  image_action.source_attempt_id: null
  result_attempt_id: a_001
  observed_outcome.comparison_attempt_id: a_000
  observed_outcome.fixed_constraint_ids: [c_002, c_005]
  observed_outcome.regressed_constraint_ids: []
  observed_outcome.persistent_failed_constraint_ids: [c_001, c_004, c_008]
  observed_outcome.became_best: true

planner_context.episode_memory.earlier_rounds:
  - result_attempt_id: a_000
    action: generate_image
    outcome_summary.became_best: true

planner_context.episode_memory.best_attempt.attempt_id: a_001
planner_context.episode_memory.best_attempt.same_as_latest: true
planner_context.runtime_state.remaining_image_budget: 3
visible_images: [{role: latest, attempt_id: a_001}]
```

### Round 3: Edit `a_001`

Planner input:

```yaml
planner_context.latest_observation.attempt_id: a_001
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_001, c_004, c_008]
planner_context.episode_memory.best_attempt.attempt_id: a_001
planner_context.episode_memory.best_attempt.same_as_latest: true
planner_context.runtime_state.remaining_image_budget: 3
visible_images: [{role: latest, attempt_id: a_001}]
```

Planner output:

```yaml
action: edit_image
arguments.source_attempt_id: a_001
arguments.target_constraint_ids: [c_001, c_004, c_008]
arguments.preserve_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
arguments.edit_instruction: [edit instruction to add lions and strengthen chasing/depth]
```

Next input update:

```yaml
planner_context.latest_observation.attempt_id: a_002
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_004, c_008]

planner_context.episode_memory.recent_round:
  image_action.action: edit_image
  image_action.source_attempt_id: a_001
  result_attempt_id: a_002
  observed_outcome.comparison_attempt_id: a_001
  observed_outcome.fixed_constraint_ids: [c_001]
  observed_outcome.regressed_constraint_ids: []
  observed_outcome.persistent_failed_constraint_ids: [c_004, c_008]
  observed_outcome.became_best: true

planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: true
planner_context.runtime_state.remaining_image_budget: 2
visible_images: [{role: latest, attempt_id: a_002}]
```

### Round 4: Edit `a_002` And Regress

Planner input:

```yaml
planner_context.latest_observation.attempt_id: a_002
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_004, c_008]
planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: true
planner_context.runtime_state.remaining_image_budget: 2
visible_images: [{role: latest, attempt_id: a_002}]
```

Planner output:

```yaml
action: edit_image
arguments.source_attempt_id: a_002
arguments.target_constraint_ids: [c_004, c_008]
arguments.preserve_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
arguments.edit_instruction: [edit instruction to adjust motion/depth]
```

Next input update:

```yaml
planner_context.latest_observation.attempt_id: a_003
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_002, c_004, c_008]

planner_context.episode_memory.recent_round:
  image_action.action: edit_image
  image_action.source_attempt_id: a_002
  result_attempt_id: a_003
  observed_outcome.comparison_attempt_id: a_002
  observed_outcome.fixed_constraint_ids: []
  observed_outcome.regressed_constraint_ids: [c_002]
  observed_outcome.persistent_failed_constraint_ids: [c_004, c_008]
  observed_outcome.became_best: false

planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: false
planner_context.runtime_state.remaining_image_budget: 1
visible_images:
  - {role: latest, attempt_id: a_003}
  - {role: best, attempt_id: a_002}
```

### Round 5: Roll Back And Edit `a_002`

Planner input:

```yaml
planner_context.latest_observation.attempt_id: a_003
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_002, c_004, c_008]

planner_context.episode_memory.recent_round.result_attempt_id: a_003
planner_context.episode_memory.recent_round.observed_outcome.regressed_constraint_ids: [c_002]

planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: false

planner_context.runtime_state.remaining_image_budget: 1

visible_images:
  - {role: latest, attempt_id: a_003}
  - {role: best, attempt_id: a_002}
```

Planner output:

```yaml
action: edit_image
arguments.source_attempt_id: a_002
arguments.target_constraint_ids: [c_004, c_008]
arguments.preserve_constraint_ids: [c_001, c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011]
arguments.edit_instruction: [rollback edit instruction from best attempt a_002]
```

Next input update:

```yaml
planner_context.latest_observation.attempt_id: a_004
planner_context.latest_observation.constraint_results.failed_constraint_ids: [c_004, c_008]

planner_context.episode_memory.recent_round:
  image_action.action: edit_image
  image_action.source_attempt_id: a_002
  result_attempt_id: a_004
  observed_outcome.comparison_attempt_id: a_002
  observed_outcome.fixed_constraint_ids: []
  observed_outcome.regressed_constraint_ids: []
  observed_outcome.persistent_failed_constraint_ids: [c_004, c_008]
  observed_outcome.became_best: false

planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: false

planner_context.runtime_state.remaining_image_budget: 0
planner_context.runtime_state.available_actions: [submit_attempt]

visible_images:
  - {role: latest, attempt_id: a_004}
  - {role: best, attempt_id: a_002}
```

### Final Submit

Planner input:

```yaml
planner_context.latest_observation.attempt_id: a_004
planner_context.episode_memory.best_attempt.attempt_id: a_002
planner_context.episode_memory.best_attempt.same_as_latest: false
planner_context.runtime_state.remaining_image_budget: 0
planner_context.runtime_state.available_actions: [submit_attempt]
visible_images:
  - {role: latest, attempt_id: a_004}
  - {role: best, attempt_id: a_002}
```

Planner output:

```yaml
action: submit_attempt
arguments.selected_attempt_id: a_002
arguments.reason_code: best_available_under_budget
```

## 6. Main State-Update Logic

The most important part of the trajectory is not that every input is restated. It is how each action changes the next `planner_context`.

```text
Planner Output(action)
-> Environment executes it
-> Geneval2 evaluates the new image if one is produced
-> Reducer compares source/current attempts
-> Next PlannerContext is rebuilt
```

Each image-producing action mainly updates:

```text
planner_context.latest_observation
planner_context.episode_memory.recent_round
planner_context.episode_memory.earlier_rounds
planner_context.episode_memory.best_attempt
planner_context.runtime_state
visible_images
```

### Field Intent

`planner_context.latest_observation`

Current latest image state. Every new generated/edited image updates this to the new attempt's Geneval2 atom results.

`planner_context.episode_memory.recent_round`

What the immediately previous image-producing round did and what happened. It aligns action and outcome: source, target/preserve, instruction, fixed/regressed/persistent constraints, and whether it became best.

`planner_context.episode_memory.earlier_rounds`

Older rounds in compact form. When a new `recent_round` is created, the previous `recent_round` moves here with action/source/result/target/preserve/outcome summary, without repeating the long instruction.

`planner_context.episode_memory.best_attempt`

The best historical attempt so far. It can differ from latest, which lets the planner roll back to a better source or submit a non-latest best attempt.

`planner_context.runtime_state`

Remaining image budget and currently legal actions. When budget reaches 0, `available_actions=[submit_attempt]`.

`visible_images`

Multimodal image bindings outside PlannerContext. When latest and best differ, the planner sees both `latest` and `best` images.

## 7. Action Effects In This Trajectory

### Round 1B: `generate_image -> a_000`

The first image is created.

```text
planner_context.latest_observation = a_000
planner_context.episode_memory.recent_round = Round 1 generate action + initial atom results
planner_context.episode_memory.best_attempt = a_000
planner_context.runtime_state.remaining_image_budget = 4
visible_images = [latest a_000]
```

Effect on the next planner call: the planner can now see which atoms passed, failed, and were uncertain in `a_000`.

### Round 2: `generate_image -> a_001`

The planner regenerates from scratch. The reducer compares `a_001` against `a_000`.

```text
fixed_constraint_ids = [c_002, c_005]
regressed_constraint_ids = []
persistent_failed_constraint_ids = [c_001, c_004, c_008]
became_best = true
```

Next input update:

```text
planner_context.latest_observation = a_001
planner_context.episode_memory.recent_round = Round 2 generate + outcome vs a_000
planner_context.episode_memory.earlier_rounds = [Round 1 compact]
planner_context.episode_memory.best_attempt = a_001
planner_context.runtime_state.remaining_image_budget = 3
visible_images = [latest a_001]
```

Effect on the next planner call: it knows regeneration fixed glass-lion attribute and cat count, but lion count, chasing, and cats-behind-donut still fail.

### Round 3: `edit_image(source_attempt_id=a_001) -> a_002`

The planner edits the current best.

```text
fixed_constraint_ids = [c_001]
regressed_constraint_ids = []
persistent_failed_constraint_ids = [c_004, c_008]
became_best = true
```

Next input update:

```text
planner_context.latest_observation = a_002
planner_context.episode_memory.recent_round = Round 3 edit from a_001 + outcome vs a_001
planner_context.episode_memory.earlier_rounds += Round 2 compact
planner_context.episode_memory.best_attempt = a_002
planner_context.runtime_state.remaining_image_budget = 2
visible_images = [latest a_002]
```

Effect on the next planner call: it knows the edit fixed lion count, while relation constraints remain unresolved.

### Round 4: `edit_image(source_attempt_id=a_002) -> a_003`

The planner tries to fix the relation constraints from the current best, but the edit regresses one preserved atom.

```text
fixed_constraint_ids = []
regressed_constraint_ids = [c_002]
persistent_failed_constraint_ids = [c_004, c_008]
became_best = false
```

Next input update:

```text
planner_context.latest_observation = a_003
planner_context.episode_memory.recent_round = Round 4 edit from a_002 + regression outcome
planner_context.episode_memory.earlier_rounds += Round 3 compact
planner_context.episode_memory.best_attempt = a_002
planner_context.runtime_state.remaining_image_budget = 1
visible_images = [latest a_003, best a_002]
```

Effect on the next planner call: it can see latest is not best, `a_003` regressed `c_002`, and `a_002` remains available as the better source.

### Round 5: `edit_image(source_attempt_id=a_002) -> a_004`

The planner rolls back to the historical best source `a_002` instead of editing latest `a_003`.

```text
fixed_constraint_ids = []
regressed_constraint_ids = []
persistent_failed_constraint_ids = [c_004, c_008]
became_best = false
```

Next input update:

```text
planner_context.latest_observation = a_004
planner_context.episode_memory.recent_round = rollback edit from a_002 + outcome vs a_002
planner_context.episode_memory.best_attempt = a_002
planner_context.runtime_state.remaining_image_budget = 0
planner_context.runtime_state.available_actions = [submit_attempt]
visible_images = [latest a_004, best a_002]
```

Effect on the final planner call: budget is exhausted, `a_004` did not beat `a_002`, so the only legal action is to submit the historical best.

### Final: `submit_attempt(selected_attempt_id=a_002)`

```text
action = submit_attempt
selected_attempt_id = a_002
reason_code = best_available_under_budget
```

This demonstrates that the planner can submit the best historical attempt rather than blindly submitting the latest attempt.

## 8. Why These Fields Are Enough

The planner can decide the next action because it sees:

- current evaluated state in `latest_observation`;
- active skill guidance in `skill_context`;
- the most recent action and outcome in `episode_memory.recent_round`;
- compressed older attempts in `episode_memory.earlier_rounds`;
- the best historical candidate in `episode_memory.best_attempt`;
- remaining budget and legal action set in `runtime_state`;
- actual latest/best images in `visible_images`.

The planner does not need to output score, regression, best attempt, or budget. Those are computed by Geneval2 and the reducer, then injected into the next Planner Input.
