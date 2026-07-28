# Planner I/O v0.5 Field Design Packet

Status: implemented and offline-validated on 2026-07-26.

Purpose: make the planner input/output fields clear enough for SFT review while preserving the core Gen-Retry loop:

```text
PlannerContext + visible images
-> one assistant planner action
-> environment executes tool/image/evaluator
-> reducer updates state and memory
-> next PlannerContext
```

## 1. Design Principles

1. Separate state from history.

   The planner needs to know the newest image state, but it also needs to know how that state was produced. These are different facts.

2. Train only the assistant action.

   The SFT target is one canonical action JSON. Tool responses, generated images, Geneval2 results, fixed/regressed sets, best/latest updates, and budget updates are context with loss 0.

3. Avoid duplicate evaluator text.

   Keep the full latest atom state once. Store older rounds as action plus transition summaries.

4. Preserve rollback semantics.

   `edit_image.source_attempt_id` must be explicit because the source can be latest or historical best.

5. Keep only executable free text.

   The action includes only the final executable image instruction. A native
   GPT-5.5 teacher-only A/B pilot kept action correctness at 10/10, but two
   broad-failure regeneration summaries repeated target/preserve intent without
   explaining generate-over-edit selection. Sol therefore retained v0.5
   without `decision_summary`. Required-but-zero-loss remains invalid because
   the field would be untrained at inference.

## 2. v0.5 Planner Input

```yaml
planner_context:
  task_context:
    original_prompt
    max_image_attempts
    atom_constraints:
      - constraint_id
        constraint_type
        requirement
        evaluator_question

  latest_attempt:
    attempt_id
    constraint_results:
      passed_constraint_ids
      failed_constraint_ids
      uncertain_constraint_ids
      observations:
        - constraint_id
          status
          observed_value

  skill_context:
    active_skills:
      - skill_id
        target_constraint_ids
        guidance
        guidance_level

  episode_memory:
    last_completed_image_round
    prior_image_rounds
    best_attempt

  runtime_state:
    remaining_image_budget
    available_actions

visible_images:
  - role: latest | best
    attempt_id
    artifact_id
```

Before the first image:

```yaml
planner_context.latest_attempt: null
planner_context.skill_context.active_skills: []
planner_context.episode_memory.last_completed_image_round: null
planner_context.episode_memory.prior_image_rounds: []
planner_context.episode_memory.best_attempt: null
visible_images: []
```

## 3. Dynamic Field Meanings

| Field | Role | Why Necessary | SFT Risk Control |
|---|---|---|---|
| `task_context` | Immutable task and Geneval2 atom constraints. | Gives stable target IDs and evaluator questions for every action. | Never changes across rounds, so it is not a future-leak source. |
| `latest_attempt` | Newest image state. | Answers: what image state does the planner see now? | Contains state only, not the previous action plan. |
| `skill_context` | Currently retrieved capability guidance. | Lets `query_skill` affect the next action without copying raw tool history forever. | Tool response itself remains loss 0; older guidance can be summarized deterministically. |
| `last_completed_image_round` | Previous image-producing round. | Answers: what did the last action try, from which source, and what happened? | Stores action/outcome alignment, not raw teacher output. |
| `prior_image_rounds` | Older compressed rounds. | Prevents repeated failed strategies without replaying every long prompt. | Deterministic compression from canonical fields only. |
| `best_attempt` | Historical best attempt. | Enables rollback and submit-best when latest regresses. | If best equals latest, do not duplicate the full constraint state. |
| `runtime_state` | Budget and legal actions. | Prevents illegal image calls after budget exhaustion. | Environment-owned, loss 0. |
| `visible_images` | Multimodal image bindings outside JSON context. | The planner can inspect latest and best pixels. | Paths/artifacts are observations, never assistant targets. |

## 4. Non-Duplication Rule

`latest_attempt` and `last_completed_image_round` often refer to the same result attempt, but they do not store the same information.

```yaml
latest_attempt:
  attempt_id: a_003
  failed_constraint_ids: [c_002, c_004, c_008]

last_completed_image_round:
  image_action:
    action: edit_image
    source_attempt_id: a_002
    target_constraint_ids: [c_004, c_008]
  result_attempt_id: a_003
  observed_outcome:
    baseline_attempt_id: a_002
    fixed_constraint_ids: []
    regressed_constraint_ids: [c_002]
    persistent_failed_constraint_ids: [c_004, c_008]
```

The first block is the current state. The second block is the causal explanation of how the state was produced.

When `best_attempt.attempt_id == latest_attempt.attempt_id`, v0.5 should store only a reference:

```yaml
best_attempt:
  attempt_id: a_003
  constraint_results_ref: latest_attempt
```

When best differs from latest, v0.5 stores best's own compact constraint state:

```yaml
best_attempt:
  attempt_id: a_002
  constraint_results:
    passed_constraint_ids: [...]
    failed_constraint_ids: [c_004, c_008]
    uncertain_constraint_ids: []
```

## 5. v0.5 Planner Output

The planner emits exactly one action JSON. It never emits score, best attempt updates, Geneval2 outcomes, image paths, or fixed/regressed sets.

### `query_skill`

```json
{
  "schema_version": "0.5",
  "action": "query_skill",
  "arguments": {
    "skill_ids": ["spatial_relation_layout"],
    "target_constraint_ids": ["c_004", "c_008"]
  }
}
```

Purpose: retrieve capability guidance. It is a real planner action, but remains context-only for SFT until skill utility is accepted.

### `generate_image`

```json
{
  "schema_version": "0.5",
  "action": "generate_image",
  "arguments": {
    "target_constraint_ids": ["c_001", "c_002", "c_003"],
    "preserve_constraint_ids": [],
    "instruction": "Create an image that shows exactly ..."
  }
}
```

Purpose: create a new image without a source image. This covers both first generation and from-scratch regeneration.

### `edit_image`

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": ["c_004", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_005"],
    "instruction": "Make a minimal localized edit to ..."
  }
}
```

Purpose: modify a specific historical attempt. The source must be explicit.

### `submit_attempt`

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

Purpose: end the episode by submitting the best available historical attempt.

## 6. Why These Output Fields Are Necessary

| Field | Used By | Why Necessary |
|---|---|---|
| `action` | executor/router | Selects query, generate, edit, or submit. |
| `skill_ids` | skill store | Makes skill use an explicit action instead of hidden prompt magic. |
| `source_attempt_id` | edit executor and reducer | Prevents latest/best/source confusion during rollback. |
| `selected_attempt_id` | submit executor | Allows non-latest best submission. |
| `target_constraint_ids` | planner, validator, analysis | Shows which atoms the action is trying to fix. |
| `preserve_constraint_ids` | image instruction and SFT audit | Makes regression avoidance explicit. |
| `instruction` | Qwen-Image-Edit adapter | The actual prompt sent to image generation/edit execution. |
| `reason_code` | submit audit | Structured reason for episode termination. |

Fields intentionally excluded:

- `mode`: redundant with `generate_image` vs `edit_image`.
- `strategy_tags`: vague and superseded by target/preserve plus instruction.
- `skill_ids_used`: skill usage is already represented by explicit `query_skill` and `skill_context`.
- `decision_summary`: a native teacher-only pilot failed the required 10/10
  state-to-decision criterion; two summaries did not justify
  generate-over-edit selection.
- `diagnosis_summary`: likely free-text noise; executable diagnosis should be reflected in target IDs and instruction.
- `fixed/regressed/became_best/score`: environment-owned facts, never assistant target.

## 7. SFT Message Rule

A trainable sample should look like:

```text
system: fixed planner contract                     loss 0
user: PlannerContext + visible image bindings      loss 0
assistant: one canonical action JSON               loss 1 if selected
```

For skill retrieval, the complete multi-turn transcript must be:

```text
assistant: query_skill action                      loss 0 until skill utility is accepted
tool/user: skill content observation               loss 0
assistant: generate/edit/submit action             loss 1 only if selected
```

Display files may contain comments or `_note` fields, but training records must not.

## 8. Implemented Freeze Checks

1. Added `schemas/action_protocol_v0_5.schema.json`.
2. Added `schemas/planner_context_v0_5.schema.json`.
3. Amended `ADR-0005` to make v0.5 the new rollout/SFT protocol.
4. Kept old v0.2-v0.4 actions as historical context rather than rewriting them
   into native v0.5 targets.
5. Added invariant tests for:
   - target/preserve disjointness;
   - valid source and selected attempt IDs;
   - no future outcome leakage;
   - no tool/evaluator/environment tokens with loss 1;
   - best/latest de-duplication.
6. `query_skill` remains context-only until skill utility is accepted.

## 9. Recommended Decision

v0.5 is adopted as a clarity revision, not a new research mechanism.

The real change is:

```text
latest_observation -> latest_attempt
recent_round -> last_completed_image_round
earlier_rounds -> prior_image_rounds
generation/edit *_instruction -> instruction
drop decision_summary and diagnosis_summary from target
```

This keeps the SFT target small while still teaching the planner to choose actions, choose sources, protect passed atoms, and write executable Qwen instructions.
