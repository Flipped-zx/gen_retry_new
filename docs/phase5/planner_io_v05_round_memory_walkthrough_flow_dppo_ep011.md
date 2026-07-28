# Planner I/O v0.5 Native Round/Memory Walkthrough: Flow-DPPO ep_011

Source trajectory:
`runs/phase5_flow_dppo20/phase3_ep_011/`

Prompt:

```text
a pink checkered cookie in front of four flowers under four metal pigs
```

This is a native v0.5 trajectory, not a projection from an older action
schema. It is the clearest completed trajectory in the Flow-DPPO 20-prompt
batch for showing how Agent decisions, visible images, Round Memory, and
environment updates connect.

Its image path is:

```text
a_000: first generation, 10/11 atoms
  |
  +-- edit a_000 -> a_001, still 10/11
  |
  +-- edit a_000 -> a_002, 11/11, submitted
```

The second edit branches from historical best `a_000`; it does not blindly
continue from latest `a_001`.

## 1. Agent Input And Output Boundary

Every Agent call receives:

```yaml
system_prompt:
  fixed Planner Action Protocol v0.5

planner_context:
  task_context
  latest_attempt
  skill_context
  episode_memory
  runtime_state

visible_images:
  actual latest and/or best images

extra_observations:
  environment notices, when needed
```

The Agent emits exactly one canonical action:

```yaml
schema_version: "0.5"
action: query_skill | generate_image | edit_image | submit_attempt
arguments: action-specific fields
```

The environment then executes the action:

```text
query_skill
  -> load selected SKILL.md content
  -> update skill_context

generate_image / edit_image
  -> Qwen-Image-Edit execution
  -> image Attempt
  -> Geneval2 atom evaluation
  -> deterministic outcome, best/latest, budget, and Round Memory update

submit_attempt
  -> select an existing attempt
  -> end the episode
```

The Agent does not produce evaluator results, transitions, best/latest
updates, or scores. Those are environment-owned observations visible only to
later Agent calls.

## 2. Fixed System Prompt

The same system prompt is used for all five Agent calls. Its relevant actual
contract is shown once here and is not repeated in each round:

```text
Role: verifier-grounded multimodal image retry planner.

Return exactly one JSON object matching action_protocol_v0_5.
Top-level keys: schema_version, action, arguments.
Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill:
- request at most three catalog Skill IDs;
- bind the query to target_constraint_ids;
- do not immediately query again after a successful query;
- apply retrieved operators in the next image action.

generate_image / edit_image:
- include target_constraint_ids, preserve_constraint_ids, and instruction;
- edit_image also requires source_attempt_id;
- instruction is the exact executable text sent to Qwen-Image-Edit;
- do not output decision_summary, diagnosis_summary, strategy_tags,
  diagnostic_hypotheses, or interventions in v0.5.

Image/source selection:
- use the actual visible LATEST_IMAGE and BEST_IMAGE;
- compare latest and best when they differ;
- do not blindly continue from latest.

submit_attempt:
- select an existing attempt;
- use all_constraints_passed, best_available_under_budget, or
  no_productive_action_remaining.
```

The system also contains the six valid Skill IDs and strict JSON examples.
Credential values, local paths, evaluator probabilities, and future outcomes
are never included.

## 3. Stable Task Context

`task_context` is identical in every PlannerContext:

```yaml
task_context:
  original_prompt: a pink checkered cookie in front of four flowers under four metal pigs
  max_image_attempts: 5
  atom_constraints:
    c_001: count, exactly one cookie
    c_002: attribute, cookie is pink
    c_003: attribute, cookie is checkered
    c_004: object, cookie exists
    c_005: position, cookie is in front of flowers
    c_006: count, exactly four flowers
    c_007: object, flowers exist
    c_008: position, flowers are under pigs
    c_009: count, exactly four pigs
    c_010: attribute, pigs are metal
    c_011: object, pigs exist
```

These constraints come from the selected Flow-DPPO Geneval2 row. They are
episode-global evaluator questions, not facts inferred from an image.

## 4. Round 0: Query Skills, Then Generate `a_000`

Round 0 contains two Agent action steps. `query_skill` prepares the same
Planning Round; the Round ends only after `generate_image` produces and
evaluates an image.

### Step 0A Input To Agent

There is no image or history yet:

```yaml
planner_context:
  task_context: [stable task context from Section 3]
  latest_attempt: null
  skill_context:
    active_skills: []
  episode_memory:
    last_completed_image_round: null
    prior_image_rounds: []
    best_attempt: null
  runtime_state:
    available_actions: [query_skill, generate_image]
    remaining_image_budget: 5

visible_images: []
extra_observations:
  - No image attempts exist yet; do not edit or submit.
```

### Step 0A Output From Agent

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
      "c_003",
      "c_005",
      "c_006",
      "c_008",
      "c_009",
      "c_010"
    ]
  }
}
```

### Environment Update After Step 0A

No image is created, no Geneval2 evaluation runs, and the image budget remains
five. The environment loads the complete selected `SKILL.md` files into the
next PlannerContext:

```yaml
skill_context.active_skills:
  - skill_id: counting_and_instance_layout
    target_constraint_ids: [c_001, c_006, c_009]
    guidance_level: full
    guidance: [complete counting_and_instance_layout/SKILL.md]

  - skill_id: spatial_relation_layout
    target_constraint_ids: [c_005, c_008]
    guidance_level: full
    guidance: [complete spatial_relation_layout/SKILL.md]

  - skill_id: attribute_entity_binding
    target_constraint_ids: [c_002, c_003, c_010]
    guidance_level: full
    guidance: [complete attribute_entity_binding/SKILL.md]
```

This tool response is context for the next action and has training loss zero.

### Step 0B Input To Agent

Only `skill_context` changed:

```yaml
planner_context:
  task_context: [unchanged]
  latest_attempt: null
  skill_context:
    active_skills:
      - counting_and_instance_layout, full guidance
      - spatial_relation_layout, full guidance
      - attribute_entity_binding, full guidance
  episode_memory:
    last_completed_image_round: null
    prior_image_rounds: []
    best_attempt: null
  runtime_state:
    available_actions: [query_skill, generate_image]
    remaining_image_budget: 5

visible_images: []
```

### Step 0B Output From Agent

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
      "c_010",
      "c_011"
    ],
    "preserve_constraint_ids": [],
    "instruction": "Create a clear scene with exactly one cookie total: a single pink checkered cookie in the foreground center, fully visible, with an obvious pink-and-light checkerboard pattern. Place exactly four flowers total in a separated row behind the cookie, each flower fully visible enough to count, so the cookie is clearly in front of the flowers with depth overlap. Place exactly four metal pigs total above the flowers in the upper part of the image, each pig fully visible, separated, and shiny metallic with reflective highlights. The flowers must be under the pigs, with vertical separation showing all four flowers below all four pigs. Do not include any extra cookies, flowers, or pigs; no cropped, fused, reflected, background, decorative, or partially hidden duplicate instances."
  }
}
```

### Environment Update After Round 0

Qwen-Image-Edit runs without a source image and creates `a_000`. Geneval2
evaluates all 11 frozen atoms:

```yaml
latest_attempt:
  attempt_id: a_000
  passed_constraint_ids:
    [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_008]
  uncertain_constraint_ids: []
  key_observation:
    c_008: "Are the flowers under the pigs?" -> "no"

episode_memory.last_completed_image_round:
  skill_queries:
    - counting_and_instance_layout -> [c_001, c_006, c_009]
    - spatial_relation_layout -> [c_005, c_008]
    - attribute_entity_binding -> [c_002, c_003, c_010]
  image_action:
    action: generate_image
    source_attempt_id: null
    target_constraint_ids: [c_001 ... c_011]
    preserve_constraint_ids: []
    instruction: [exact Step 0B instruction]
  result_attempt_id: a_000
  observed_outcome:
    baseline_attempt_id: null
    initial_failed_constraint_ids: [c_008]
    initial_uncertain_constraint_ids: []
    became_best: true

episode_memory.prior_image_rounds: []
episode_memory.best_attempt:
  attempt_id: a_000
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 4
visible_images:
  - a_000 as LATEST_IMAGE
  - a_000 as BEST_IMAGE_SAME_AS_LATEST
```

The active Skills are retained, but their complete Markdown is deterministically
compressed to summary guidance after the image round.

## 5. Round 1: Edit `a_000`, Producing `a_001`

### Input To Agent

The Agent now sees image state, the exact action that produced it, and the
actual image:

```yaml
planner_context:
  task_context: [unchanged]

  latest_attempt:
    attempt_id: a_000
    passed_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_008]
    uncertain_constraint_ids: []

  skill_context:
    active_skills:
      - counting_and_instance_layout, summary guidance
      - spatial_relation_layout, summary guidance
      - attribute_entity_binding, summary guidance

  episode_memory:
    last_completed_image_round:
      image_action: generate_image
      source_attempt_id: null
      result_attempt_id: a_000
      initial_failed_constraint_ids: [c_008]
      became_best: true
    prior_image_rounds: []
    best_attempt:
      attempt_id: a_000
      constraint_results_ref: latest_attempt

  runtime_state:
    available_actions: [query_skill, generate_image, edit_image, submit_attempt]
    remaining_image_budget: 4

visible_images:
  - a_000 as LATEST_IMAGE
  - a_000 as BEST_IMAGE_SAME_AS_LATEST
```

`latest_attempt` says what is currently wrong. The detailed previous Round
says which prompt produced that state.

### Output From Agent

The Agent chooses a local edit, targets only failed relation `c_008`, and
preserves the ten passing atoms:

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "target_constraint_ids": ["c_008"],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ],
    "instruction": "Target operation: edit attempt a_000 to make the vertical relation unambiguous: place all four flowers clearly under all four metal pigs, with the pigs in a single upper row and the flowers in a clearly lower row beneath them. Spatial grounding: keep exactly four shiny metal pigs fully visible across the upper part of the image, and keep exactly four flowers fully visible enough to count in a separated row below the pigs; ensure the highest point of every flower is below the lowest visible part of every pig, with a clean vertical gap so no flower overlaps into the pigs' level. Preservation lock: preserve the single large pink checkered cookie in the foreground center, its color and checkerboard pattern, the cookie remaining in front of the flowers, the exact counts of one cookie, four flowers, and four pigs, and the pigs' metallic reflective material. Forbidden changes: do not add or remove cookies, flowers, or pigs; do not crop, fuse, duplicate, reflect, or hide any instance; do not change the cookie pattern, pig material, flower identities, or overall simple white-background composition."
  }
}
```

### Environment Update After Round 1

Qwen-Image-Edit uses `a_000` as the source and creates `a_001`. Geneval2
reports no thresholded atom change:

```yaml
latest_attempt:
  attempt_id: a_001
  passed_constraint_ids:
    [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
  failed_constraint_ids: [c_008]
  uncertain_constraint_ids: []

episode_memory.last_completed_image_round:
  skill_queries: []
  image_action:
    action: edit_image
    source_attempt_id: a_000
    target_constraint_ids: [c_008]
    preserve_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    instruction: [exact Round 1 instruction]
  result_attempt_id: a_001
  observed_outcome:
    baseline_attempt_id: a_000
    fixed_constraint_ids: []
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: [c_008]
    preserved_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    became_best: false

episode_memory.prior_image_rounds:
  - action: generate_image
    source_attempt_id: null
    result_attempt_id: a_000
    target_constraint_ids: [c_001 ... c_011]
    outcome_summary:
      result_failed_constraint_ids: [c_008]
      became_best: true

episode_memory.best_attempt:
  attempt_id: a_000
  constraint_results:
    passed_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_008]
    uncertain_constraint_ids: []

runtime_state.remaining_image_budget: 3
visible_images:
  - a_001 as LATEST_IMAGE
  - a_000 as BEST_IMAGE
```

Because `a_001` did not beat `a_000`, latest and best are now different. The
next Agent call receives both images and both state records.

## 6. Round 2: Branch From Best `a_000`, Producing `a_002`

### Input To Agent

This is the trajectory's main decision point:

```yaml
planner_context:
  task_context: [unchanged]

  latest_attempt:
    attempt_id: a_001
    passed_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    failed_constraint_ids: [c_008]
    uncertain_constraint_ids: []

  skill_context:
    active_skills:
      - counting_and_instance_layout, summary guidance
      - spatial_relation_layout, summary guidance
      - attribute_entity_binding, summary guidance

  episode_memory:
    last_completed_image_round:
      image_action:
        action: edit_image
        source_attempt_id: a_000
        target_constraint_ids: [c_008]
        preserve_constraint_ids:
          [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
        instruction: [exact Round 1 instruction]
      result_attempt_id: a_001
      observed_outcome:
        fixed_constraint_ids: []
        regressed_constraint_ids: []
        persistent_failed_constraint_ids: [c_008]
        preserved_constraint_ids:
          [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
        became_best: false

    prior_image_rounds:
      - generate_image, null -> a_000, c_008 still failed, became_best true

    best_attempt:
      attempt_id: a_000
      passed_constraint_ids:
        [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
      failed_constraint_ids: [c_008]
      uncertain_constraint_ids: []

  runtime_state:
    available_actions: [query_skill, generate_image, edit_image, submit_attempt]
    remaining_image_budget: 3

visible_images:
  - a_001 as LATEST_IMAGE
  - a_000 as BEST_IMAGE
```

The input distinguishes:

- latest state: `a_001` still fails `c_008`;
- immediate cause: the previous `a_000 -> a_001` edit was ineffective;
- historical best: `a_000`;
- remaining budget: three image attempts.

v0.5 intentionally has no `decision_summary`. Therefore the trace does not
claim a hidden rationale. The observable decision is encoded by the selected
action, source, targets, preservation set, and executable instruction.

### Output From Agent

The Agent chooses `source_attempt_id: a_000`, not latest `a_001`, and changes
the intervention wording to demand a wider empty vertical gap:

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "target_constraint_ids": ["c_008"],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ],
    "instruction": "Target operation: edit attempt a_000 to make the flowers clearly under the pigs by separating the vertical rows: move all four metal pigs higher into the top third of the image and move the four flower blossoms lower into a middle row beneath them, so every flower is entirely below every pig with a wide blank white gap between pig feet and flower tops. Spatial grounding: keep the four pigs in a single upper row, fully visible and separated; keep the four flowers in a single lower row directly below the pigs, fully countable, with the highest petal of each flower below the lowest hoof or body edge of every pig and no petal overlapping any pig. Preservation lock: preserve exactly one large pink checkered cookie in the foreground center, preserve the cookie in front of the flowers, preserve exactly four flowers, exactly four pigs, the pigs' shiny metal material, the cookie's pink color and checkerboard pattern, and the simple white background. Forbidden changes: do not add, remove, crop, duplicate, fuse, reflect, or hide any cookie, flower, or pig; do not change the cookie pattern, pig material, object identities, counts, or overall front-cookie composition."
  }
}
```

### Environment Update After Round 2

The Round begins from the latest observation `a_001`, but execution uses the
explicit source `a_000`. The transition and outcome are therefore correctly
computed as `a_000 -> a_002`:

```yaml
latest_attempt:
  attempt_id: a_002
  passed_constraint_ids: [c_001 ... c_011]
  failed_constraint_ids: []
  uncertain_constraint_ids: []

episode_memory.last_completed_image_round:
  image_action:
    action: edit_image
    source_attempt_id: a_000
    target_constraint_ids: [c_008]
    preserve_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    instruction: [exact Round 2 instruction]
  result_attempt_id: a_002
  observed_outcome:
    baseline_attempt_id: a_000
    fixed_constraint_ids: [c_008]
    regressed_constraint_ids: []
    persistent_failed_constraint_ids: []
    preserved_constraint_ids:
      [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_009, c_010, c_011]
    became_best: true

completed RoundRecord:
  start_observation_ref:
    attempt_id: a_001
  image_action.source_attempt_id: a_000
  result_attempt_id: a_002

episode_memory.prior_image_rounds:
  - generate_image, null -> a_000
  - edit_image, a_000 -> a_001, no gain

episode_memory.best_attempt:
  attempt_id: a_002
  constraint_results_ref: latest_attempt

runtime_state.remaining_image_budget: 2
visible_images:
  - a_002 as LATEST_IMAGE
  - a_002 as BEST_IMAGE_SAME_AS_LATEST
```

## 7. Terminal Submit Action

### Input To Agent

```yaml
latest_attempt:
  attempt_id: a_002
  passed_constraint_ids: [c_001 ... c_011]
  failed_constraint_ids: []
  uncertain_constraint_ids: []

episode_memory.last_completed_image_round:
  action: edit_image
  source_attempt_id: a_000
  result_attempt_id: a_002
  fixed_constraint_ids: [c_008]
  regressed_constraint_ids: []
  became_best: true

episode_memory.prior_image_rounds:
  - generate_image, null -> a_000
  - edit_image, a_000 -> a_001, no gain

episode_memory.best_attempt:
  attempt_id: a_002
  constraint_results_ref: latest_attempt

runtime_state:
  remaining_image_budget: 2

visible_images:
  - a_002 as LATEST_IMAGE
  - a_002 as BEST_IMAGE_SAME_AS_LATEST
```

### Output From Agent

```json
{
  "schema_version": "0.5",
  "action": "submit_attempt",
  "arguments": {
    "reason_code": "all_constraints_passed",
    "selected_attempt_id": "a_002"
  }
}
```

`submit_attempt` creates no image, consumes no image budget, and creates no
image RoundRecord. It terminates the episode with two unused image attempts.

## 8. State And Score Path

| Attempt | Source/action | Passed atoms | Failed atoms | Pass ratio | Soft-TIFA AM | Soft-TIFA GM |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| `a_000` | fresh `generate_image` | 10/11 | `c_008` | 90.91% | 91.92 | 83.44 |
| `a_001` | edit `a_000` | 10/11 | `c_008` | 90.91% | 87.80 | 78.05 |
| `a_002` | branch edit `a_000` | 11/11 | none | 100.00% | 95.26 | 94.64 |

Geneval2 atom status is part of the next PlannerContext. Soft-TIFA AM is the
atom-level continuous score; Soft-TIFA GM is the prompt-level score. Both are
post-hoc validation metrics computed from persisted correct-answer
probabilities and were not shown to the Agent during this rollout:

```text
image_AM = 100 * mean(atom_probability)
image_GM = 100 * exp(mean(log(max(atom_probability, 1e-300))))
```

The reducer's RoundRecord `score_delta` is pass-ratio change relative to the
declared source, not Soft-TIFA AM or GM:

```yaml
r_000, fresh -> a_000:
  score_delta: 0.9090909091
  net_atom_gain: 0
  became_best: true

r_001, a_000 -> a_001:
  score_delta: 0.0
  net_atom_gain: 0
  became_best: false

r_002, a_000 -> a_002:
  score_delta: 0.0909090909
  net_atom_gain: 1
  became_best: true
```

## 9. What Changed Between Agent Calls

| Agent call | Main new input | Agent output | Environment result |
| --- | --- | --- | --- |
| Step 0A | task and empty state | `query_skill` | full Skill Markdown enters `skill_context` |
| Step 0B | full Skill guidance | `generate_image` | `a_000`, 10/11, first best |
| Round 1 | `a_000` atom state, prior generate action, visible `a_000` | edit `a_000` for `c_008` | `a_001`, no atom gain, best remains `a_000` |
| Round 2 | latest `a_001`, ineffective last edit, best `a_000`, both images | branch edit from `a_000` with stronger spatial separation | `a_002`, `c_008` fixed, 11/11, new best |
| Submit | all-pass `a_002` and success outcome | submit `a_002` | episode ends |

The complete persisted evidence remains available in:

- `planner_contexts/planner_context_000.json` through
  `planner_context_004.json`;
- `canonical_actions.jsonl`;
- `round_records/round_record_000.json` through `round_record_002.json`;
- `geneval2/a_000.json` through `geneval2/a_002.json`;
- `images/img_000.png` through `images/img_002.png`;
- `submission.json`.

This walkthrough is the concise field-review view. The complete audit trace,
including sanitized Teacher requests and environment events, is
`docs/phase5/flow_dppo20_analysis/trajectory_trace_phase3_ep_011.md`.
