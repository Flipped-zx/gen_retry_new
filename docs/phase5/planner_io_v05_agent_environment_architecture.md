# Planner I/O v0.5: Agent Input, Action Output, and Environment Update

## 1. One Decision Step

The Teacher is the Planner Agent. One decision step has this boundary:

```text
fixed system contract
+ point-in-time PlannerContext
+ visible latest/best images
+ environment notices
                    |
                    v
          Agent emits exactly one action
                    |
                    v
 query Skill or execute Qwen-Image-Edit or submit
                    |
                    v
 Geneval2 atom evaluation + deterministic Reducer
                    |
                    v
 RoundRecord + next PlannerContext
```

Only the canonical action is Agent output. Images, Geneval2 answers and
probabilities, transitions, best/latest state, budget, and score are
environment-owned facts.

## 2. Complete Agent Input

The logical input is:

```json
{
  "system": "<fixed v0.5 planner contract>",
  "user": {
    "planner_context": {
      "task_context": {},
      "latest_attempt": {},
      "skill_context": {},
      "episode_memory": {},
      "runtime_state": {}
    },
    "visible_images": [],
    "extra_observations": [],
    "response_contract": "action_protocol_v0_5"
  }
}
```

The production Teacher request renders this information as one text block plus
actual multimodal image inputs. Paths are not treated as visual evidence.

### 2.1 `task_context`

```json
{
  "original_prompt": "...",
  "max_image_attempts": 5,
  "atom_constraints": [
    {
      "constraint_id": "c_001",
      "constraint_type": "count",
      "requirement": "Expected answer: four",
      "evaluator_question": "How many flowers are in the image?"
    }
  ]
}
```

This is immutable for the episode. The VQA atoms are loaded from the selected
Flow-DPPO Geneval2 row; they are not inferred from generated images.

### 2.2 `latest_attempt`

```json
{
  "attempt_id": "a_001",
  "constraint_results": {
    "passed_constraint_ids": ["c_001"],
    "failed_constraint_ids": ["c_002"],
    "uncertain_constraint_ids": [],
    "observations": [
      {
        "constraint_id": "c_002",
        "status": "fail",
        "observed_value": " no"
      }
    ]
  }
}
```

This answers only: what is true of the newest image now? It does not explain
which action produced it. It is `null` before the first image.

### 2.3 `skill_context`

```json
{
  "active_skills": [
    {
      "skill_id": "spatial_relation_layout",
      "target_constraint_ids": ["c_008"],
      "guidance": "<SKILL.md content or deterministic summary>",
      "guidance_level": "full"
    }
  ]
}
```

Immediately after `query_skill`, `guidance` is the hash-tracked complete
`skills/<skill_id>/SKILL.md` content and `guidance_level` is `full`. After the
image round completes, the Skill remains active but is compressed to its
deterministic summary with `guidance_level: summary`.

The Skill is therefore operational context for the next image action. It is
not a hidden prompt and it is not itself the image instruction.

### 2.4 `episode_memory.last_completed_image_round`

```json
{
  "skill_queries": [
    {
      "skill_id": "spatial_relation_layout",
      "target_constraint_ids": ["c_008"]
    }
  ],
  "image_action": {
    "action": "edit_image",
    "source_attempt_id": "a_000",
    "target_constraint_ids": ["c_008"],
    "preserve_constraint_ids": ["c_001", "c_002"],
    "instruction": "<exact instruction sent to Qwen>"
  },
  "result_attempt_id": "a_001",
  "observed_outcome": {
    "baseline_attempt_id": "a_000",
    "fixed_constraint_ids": [],
    "regressed_constraint_ids": [],
    "persistent_failed_constraint_ids": ["c_008"],
    "preserved_constraint_ids": ["c_001", "c_002"],
    "new_uncertain_constraint_ids": [],
    "became_best": false
  }
}
```

This is the detailed previous image round. It aligns what the Agent attempted
with what actually happened.

For the first image, no previous image exists. Its outcome instead uses:

```json
{
  "baseline_attempt_id": null,
  "initial_failed_constraint_ids": ["c_008"],
  "initial_uncertain_constraint_ids": [],
  "became_best": true
}
```

The complete first-attempt pass state remains in `latest_attempt`; it is not
duplicated in this compressed outcome.

### 2.5 `episode_memory.prior_image_rounds`

Older rounds retain only:

```json
{
  "action": "edit_image",
  "source_attempt_id": "a_000",
  "result_attempt_id": "a_001",
  "target_constraint_ids": ["c_008"],
  "preserve_constraint_ids": ["c_001", "c_002"],
  "outcome_summary": {
    "result_failed_constraint_ids": ["c_008"],
    "result_uncertain_constraint_ids": [],
    "fixed_constraint_ids": [],
    "regressed_constraint_ids": [],
    "became_best": false
  }
}
```

The exact instruction is retained for the immediately previous round, while
older rounds are compressed. Compression is deterministic; no online LLM
summary invents a reason or diagnosis.

### 2.6 `episode_memory.best_attempt`

If best differs from latest, its constraint state is supplied separately:

```json
{
  "attempt_id": "a_002",
  "constraint_results": {}
}
```

If best equals latest, the memory stores:

```json
{
  "attempt_id": "a_002",
  "constraint_results_ref": "latest_attempt"
}
```

This avoids duplicating the same atom state while preserving explicit best
identity. The actual `LATEST_IMAGE` and `BEST_IMAGE` are also attached when
they differ.

### 2.7 `runtime_state`

```json
{
  "remaining_image_budget": 2,
  "available_actions": [
    "query_skill",
    "generate_image",
    "edit_image",
    "submit_attempt"
  ]
}
```

This is environment-owned control state. `query_skill` does not consume image
budget; `generate_image` and `edit_image` each consume one image attempt.

## 3. What Changes After Each Action

| Agent action | Immediate environment result | PlannerContext change |
| --- | --- | --- |
| `query_skill` | `skill_returned` with Skill ID, version, hash, reference, summary, and full Markdown in the tool observation | `skill_context.active_skills` gains full guidance; image state and budget do not change |
| `generate_image` | Qwen image, Geneval2 atom probabilities/statuses, transition, value | latest changes; budget -1; previous round moves into memory; best may change |
| `edit_image` | Same as generation, but outcome is compared with the declared `source_attempt_id` | latest changes; budget -1; fixed/regressed/preserved state recorded; best may remain historical |
| `submit_attempt` | selected attempt and reason are validated and persisted | episode ends; no image, Geneval2 call, or new RoundRecord |

The main dynamic fields are therefore:

```text
latest_attempt
skill_context.active_skills
episode_memory.last_completed_image_round
episode_memory.prior_image_rounds
episode_memory.best_attempt
runtime_state.remaining_image_budget
visible_images
```

`task_context` does not change.

## 4. Complete Agent Output Space

The Agent emits exactly one JSON object.

### Query a Skill

```json
{
  "schema_version": "0.5",
  "action": "query_skill",
  "arguments": {
    "skill_ids": ["spatial_relation_layout"],
    "target_constraint_ids": ["c_008"]
  }
}
```

### Generate or Regenerate

```json
{
  "schema_version": "0.5",
  "action": "generate_image",
  "arguments": {
    "target_constraint_ids": ["c_001", "c_002"],
    "preserve_constraint_ids": [],
    "instruction": "<complete executable generation prompt>"
  }
}
```

A later source-free `generate_image` means the Planner abandoned the current
image branch and requested a fresh image. There is no separate `mode` field.

### Edit an Explicit Source

```json
{
  "schema_version": "0.5",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": ["c_008"],
    "preserve_constraint_ids": ["c_001", "c_002"],
    "instruction": "<complete executable edit prompt>"
  }
}
```

Rollback/branch behavior is learned through `source_attempt_id`. If latest is
`a_004` and the action selects historical best `a_002`, the action is
explicitly branching from `a_002`.

### Submit

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

## 5. Dedicated Environment Records

| Record | Purpose |
| --- | --- |
| `events.jsonl` | Immutable source of truth for every action and environment event |
| `canonical_actions.jsonl` | Valid Agent outputs only |
| `tool_observations.jsonl` | Skill returns and image execution observations |
| `geneval2/<attempt>.json` | Raw per-atom question, expected answer, observed token, and correct-answer probability |
| `geneval2_results.jsonl` | Normalized pass/fail/uncertain atom results |
| `round_records/*.json` | Source action to result attempt to observed outcome alignment |
| `planner_contexts/*.json` | Exact point-in-time input state |
| `episode_state.json` | Final Reducer state including latest, best, budget, and submission |
| `trajectory_analysis.md` | Post-hoc behavior and SFT-candidate labeling |

The Reducer computes `fixed`, `regressed`, `persistent_failed`, `preserved`,
uncertainty changes, best update, atom gain, and score delta. The Agent does
not write these fields.

The current `RoundRecord.value.score_delta` is the change in thresholded atom
pass ratio, not either Geneval2 Soft-TIFA continuous score. Per-atom
correct-answer probabilities remain in the Geneval2 report and are used
post-hoc by the Phase 5 validation report to compute:

```text
image AM = mean(correct_answer_probability)
image GM = exp(mean(log(max(correct_answer_probability, 1e-300))))
batch AM = 100 * mean(image AM)
batch GM = 100 * mean(image GM)
```

AM is the atom-level continuous metric. GM is the prompt-level metric and the
primary Flow-DPPO reporting score. The Planner currently sees normalized
pass/fail/uncertain status and observed answers, but not the raw probability,
AM, or GM. Reducer best ordering is passed-atom count with earlier-attempt tie
breaking.

## 6. SFT Boundary

```text
system contract                         loss 0
PlannerContext + images                 loss 0
query_skill action                      loss 0 for now
skill_returned                          loss 0
selected generate/edit/submit action    loss 1
image/Geneval2/Reducer/RoundRecord       loss 0
raw or rejected Teacher output          loss 0
```

The action schema intentionally has no `decision_summary`. Consequently, a
report can demonstrate that a Planner saw a regression and selected historical
best, but it cannot claim access to an unrecorded hidden rationale.

## 7. Current Skill-Input Implementation Note

The next action after a Skill query does receive the complete Markdown.
However, the current Teacher text renders the same active Skill guidance once
inside serialized `PlannerContext` and again in a separate `Active Skills`
block. Also, the sidecar request field `retrieved_skill_ids` remains empty even
though `PlannerContext.skill_context.active_skills` is populated.

These are trace/token-accounting issues, not missing Skill conditioning. Future
cleanup should keep one canonical Skill rendering and make the sidecar ID list
agree with the actual PlannerContext, without rewriting completed trajectories.
