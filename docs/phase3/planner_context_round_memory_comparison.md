# PlannerContext / Round Memory Single-Trajectory Comparison

This report compares one original v0.2 trajectory with one new v0.3 trajectory for the same task:

- Task: `six glass lions chasing three red cats behind a brown donut`
- Old run: `runs/teacher_prompt_v1_validation/phase3_ep_001`
- New run: `runs/planner_context_v0_3/phase3_ep_001`
- New readable trace: `docs/phase3/trajectory_trace_planner_context_v0_3_ep_001.md`

The comparison is an architecture and readability check, not a statistically meaningful performance claim.

## 1. Architecture Delta

### Old v0.2 PlannerView

The old planner input was `PlannerView` with these main fields:

- `latest_attempt`
- `best_attempt`
- `constraint_state`
- `latest_transition`
- `compact_history`
- `retrieved_experiences`
- `visible_images`
- `remaining_budget`

It showed attempt-level state, but `compact_history` only stored attempt summaries:

```json
{
  "action_type": "edit_image",
  "attempt_id": "a_003",
  "parent_attempt_id": "a_002",
  "passed_constraint_ids": ["c_001", "c_003", "c_005", "..."],
  "failed_constraint_ids": ["c_002", "c_004", "c_008"]
}
```

What was missing:

- no completed Planning Round object;
- no record that `query_skill` belonged to Round 0;
- no preserved action decision summary;
- no diagnostic hypotheses;
- no structured intervention operations;
- no deterministic alignment between final prompt and actual fixed/regressed atoms;
- rollback had to be inferred from `source_attempt_id` and latest/best state.

### New v0.3 PlannerContext

The new planner input is `PlannerContext`:

```json
{
  "task_context": {},
  "latest_observation": {},
  "active_round": {},
  "episode_memory": {},
  "control": {}
}
```

The new memory split is:

- `active_round`: current round's non-image planning actions and active skills.
- `episode_memory.recent_round`: full previous completed RoundRecord.
- `episode_memory.earlier_rounds`: compressed deterministic round summaries.
- `episode_memory.best_attempt`: best image state plus the producing round/action summary.
- `control`: budget, legal actions, visible latest/best images, current step/round indexes.

Completed RoundRecords are generated deterministically from immutable events and are now persisted under:

```text
runs/planner_context_v0_3/phase3_ep_001/round_records/
```

They answer:

```text
start observation
-> query_skill actions and tool responses
-> terminal generate/edit action
-> final Qwen instruction
-> result attempt
-> observed fixed/regressed/persistent atoms
-> best/latest value update
```

## 2. Action Schema Delta

Old v0.2 `generate_image` / `edit_image` mainly carried:

- `mode` for generate;
- `source_attempt_id` for edit;
- `target_constraint_ids`;
- `preserve_constraint_ids`;
- `skill_ids_used`;
- final instruction;
- legacy `strategy_tags`.

New v0.3 `generate_image` / `edit_image` carries the complete Planner Action Plan:

```json
{
  "decision_summary": "why this action/source now",
  "diagnostic_hypotheses": [
    {
      "constraint_ids": ["c_001"],
      "hypothesis": "visual cause, not just the failed atom name"
    }
  ],
  "interventions": [
    {
      "operation": "instance_count_layout",
      "target_constraint_ids": ["c_001"],
      "change": "concrete visual intervention"
    }
  ],
  "target_constraint_ids": ["..."],
  "preserve_constraint_ids": ["..."],
  "skill_ids_used": ["..."],
  "generation_instruction": "or edit_instruction"
}
```

`strategy_tags` is removed from v0.3. The normalized operation registry is intentionally small:

- `instance_count_layout`
- `spatial_relation_layout`
- `action_pose_cue`
- `attribute_binding`

`query_skill`, `generate_image`, `edit_image`, and `submit_attempt` are all canonical Planner Actions. Qwen sampling and Geneval2 evaluation are environment execution/observation, not assistant targets.

## 3. Round-Level Trajectory Summary

### Old v0.2 Valid Actions

| Step | Action | Source | Result | Geneval2 State | Memory Result |
| --- | --- | --- | --- | --- | --- |
| s0 | `query_skill` | none | no image | no eval | skills appear as `retrieved_experiences`, not as round planning action |
| s1 | `generate_image` | none | `a_000` | 6 pass, 4 fail, 1 uncertain | best=`a_000`; persistent `c_001,c_002,c_004,c_005,c_008` |
| s2 | `generate_image` | none | `a_001` | 8 pass, 3 fail | best=`a_001`; fixed `c_002,c_005` |
| s3 | `edit_image` | `a_001` | `a_002` | 9 pass, 2 fail | best=`a_002`; fixed `c_001` |
| s4 | `edit_image` | `a_002` | `a_003` | 8 pass, 3 fail | latest=`a_003`; best=`a_002`; regressed `c_002` |
| s5 | `edit_image` | `a_002` | `a_004` | 9 pass, 2 fail | rollback source=`a_002`; best remains `a_002` |
| s6 | `submit_attempt` | none | submit `a_002` | final 9/11 | budget exhausted |

### New v0.3 Valid Actions

| Round | Actions | Source | Result | Geneval2 State | Memory Result |
| --- | --- | --- | --- | --- | --- |
| r0 | `query_skill` + `generate_image` | none | `a_000` | 8 pass, 3 fail | best=`a_000`; failed `c_001,c_004,c_005` |
| r1 | `edit_image` | `a_000` | `a_001` | 8 pass, 3 fail | no gain; best remains `a_000` |
| r2 | `edit_image` | `a_000` | `a_002` | 8 pass, 2 fail, 1 uncertain | no best gain; `c_005` uncertain |
| r3 | `edit_image` | `a_000` | `a_003` | 8 pass, 3 fail | fixed `c_005`, regressed `c_002`; best remains `a_000` |
| r4 | `edit_image` | `a_000` | `a_004` | 10 pass, 1 fail | fixed `c_001,c_005`; best=`a_004` |
| final | `submit_attempt` | none | submit `a_004` | final 10/11 | budget exhausted |

The new run used the same image-attempt budget of 5. It submitted a better single trajectory result than the old run, but that is not the main claim here.

## 4. Same-Position Planner Input Comparison

### Position A: After Skill Query, Before First Image Generation

Old input: `planner_views/planner_view_002.json`

```json
{
  "latest_attempt": null,
  "best_attempt": null,
  "compact_history": [],
  "constraint_state": {
    "c_001": {"status": "not_evaluated"},
    "c_002": {"status": "not_evaluated"}
  },
  "retrieved_experiences": [
    "skill:counting_and_instance_layout@1.0.0",
    "skill:spatial_relation_layout@1.0.0"
  ]
}
```

New input: `planner_contexts/planner_context_007.json`

```json
{
  "latest_observation": null,
  "active_round": {
    "round_id": "r_000",
    "start_attempt_id": null,
    "planning_actions": [
      {
        "step_id": "s_000",
        "action": "query_skill",
        "requested_skill_ids": [
          "counting_and_instance_layout",
          "spatial_relation_layout"
        ],
        "target_constraint_ids": ["c_001", "c_004", "c_005", "c_008", "c_009"],
        "tool_response_ref": {"event_id": "evt_0005"}
      }
    ],
    "active_capability_skills": [
      {"skill_id": "counting_and_instance_layout"},
      {"skill_id": "spatial_relation_layout"}
    ]
  },
  "episode_memory": {
    "recent_round": null,
    "earlier_rounds": [],
    "best_attempt": null
  },
  "control": {
    "remaining_image_budget": 5,
    "legal_actions": ["query_skill", "generate_image"]
  }
}
```

New information added:

- `query_skill` is explicitly Round 0 action `s_000`.
- The skill result is linked by `tool_response_ref`.
- Active skills are scoped to the same round that will call `generate_image`.
- No image attempt has been created yet.

### Position B: After an Edit Caused Regression

Old input: `planner_views/planner_view_010.json`

```json
{
  "latest_attempt": {
    "attempt_id": "a_003",
    "parent_attempt_id": "a_002",
    "passed_constraint_ids": ["c_001", "c_003", "c_005", "..."],
    "failed_constraint_ids": ["c_002", "c_004", "c_008"]
  },
  "best_attempt": {
    "attempt_id": "a_002",
    "failed_constraint_ids": ["c_004", "c_008"]
  },
  "latest_transition": {
    "from_attempt_id": "a_002",
    "to_attempt_id": "a_003",
    "regressed": ["c_002"],
    "persistent_failed": ["c_004", "c_008"]
  },
  "compact_history": [
    {"attempt_id": "a_000", "action_type": "generate_image"},
    {"attempt_id": "a_001", "action_type": "generate_image"},
    {"attempt_id": "a_002", "action_type": "edit_image"},
    {"attempt_id": "a_003", "action_type": "edit_image"}
  ]
}
```

This shows the regression but not what the model intended, what prompt caused it, or which operation should be avoided.

New input: `planner_contexts/planner_context_017.json`

```json
{
  "latest_observation": {
    "attempt_id": "a_003",
    "failed_constraint_ids": ["c_001", "c_002", "c_004"],
    "passed_constraint_ids": ["c_003", "c_005", "c_006", "..."]
  },
  "episode_memory": {
    "recent_round": {
      "round_id": "r_003",
      "image_action": {
        "action": "edit_image",
        "source_attempt_id": "a_000",
        "decision_summary": "Edit the best source because it has the correct three red cats behind one brown donut...",
        "interventions": [
          {"operation": "instance_count_layout", "target_constraint_ids": ["c_001"]},
          {"operation": "action_pose_cue", "target_constraint_ids": ["c_004"]},
          {"operation": "spatial_relation_layout", "target_constraint_ids": ["c_004"]}
        ]
      },
      "observed_outcome": {
        "fixed_constraint_ids": ["c_005"],
        "regressed_constraint_ids": ["c_002"],
        "persistent_failed_constraint_ids": ["c_001", "c_004"]
      },
      "outcome_comparison_ref": {
        "attempt_id": "a_000",
        "reason": "edit_source"
      }
    },
    "best_attempt": {
      "attempt_id": "a_000",
      "passed_constraint_ids": ["c_002", "c_003", "c_006", "..."],
      "failed_constraint_ids": ["c_001", "c_004", "c_005"]
    }
  },
  "control": {
    "latest_attempt_id": "a_003",
    "best_attempt_id": "a_000",
    "visible_images": [
      {"attempt_id": "a_003", "role": "latest"},
      {"attempt_id": "a_000", "role": "best"}
    ],
    "remaining_image_budget": 1
  }
}
```

New information added:

- the regressed atom `c_002` is tied to the exact edit source `a_000 -> a_003`;
- the last prompt and action plan are recoverable in `recent_round.image_action`;
- best/latest divergence is explicit in `control.visible_images`;
- the next action can avoid the route that damaged glass-lion material.

### Position C: Before Rollback Edit

Old action at `turn_010`:

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": ["c_004", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_005", "..."],
    "edit_instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats..."
  }
}
```

New action at `turn_020`:

```json
{
  "schema_version": "0.3",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "decision_summary": "Use the historical best source rather than the latest because the best preserves the glass-lion attribute...",
    "diagnostic_hypotheses": [
      {
        "constraint_ids": ["c_001"],
        "hypothesis": "Only four distinct lions are visible instead of six..."
      },
      {
        "constraint_ids": ["c_004"],
        "hypothesis": "The pursuit is not explicit enough..."
      },
      {
        "constraint_ids": ["c_005"],
        "hypothesis": "The three red cats need to remain separated and fully visible..."
      }
    ],
    "interventions": [
      {"operation": "instance_count_layout", "target_constraint_ids": ["c_001"]},
      {"operation": "instance_count_layout", "target_constraint_ids": ["c_005"]},
      {"operation": "action_pose_cue", "target_constraint_ids": ["c_004"]},
      {"operation": "spatial_relation_layout", "target_constraint_ids": ["c_004"]}
    ],
    "preserve_constraint_ids": ["c_002", "c_003", "c_006", "c_007", "..."],
    "edit_instruction": "Target operation: edit attempt a_000 by keeping the current scene but add exactly two more transparent blue-green glass lions..."
  }
}
```

The key difference is that the new action itself explains why it is rolling back to `a_000`, what visual failure it diagnoses, what operations it will apply, and what prompt Qwen receives.

## 5. Memory Can Answer the Required Questions

| Question | Old v0.2 | New v0.3 |
| --- | --- | --- |
| Why query Skill? | Not preserved in round memory. | `active_round.planning_actions` records requested skill IDs and target constraints. |
| How did queried Skill enter the image action? | Skill summaries appear globally as retrieved experiences. | `active_round.active_capability_skills` is visible before image action; completed RoundRecord keeps queried IDs. |
| Why choose generate/edit? | Mostly implicit in final instruction. | `decision_summary` is explicit. |
| Why choose this source? | Source ID exists for edit but no decision text. | `decision_summary`, `source_attempt_id`, and visible latest/best state are aligned. |
| What did the model think failed? | Failed atom IDs only. | `diagnostic_hypotheses` binds visual causes to constraint IDs. |
| What did the prompt do? | Final instruction exists, but not tied to operations. | Final instruction plus structured `interventions[].operation`. |
| What fixed/regressed? | `latest_transition`, relative to reducer state. | `observed_outcome` inside the completed RoundRecord with `outcome_comparison_ref`. |
| Should this route be avoided? | Must infer from attempt summaries. | Earlier/recent round summaries expose operations, source, fixed/regressed/persistent atoms. |

## 6. Token and Character Density

### Planner Input Character Size

| Position | Old PlannerView chars | New PlannerContext chars | Note |
| --- | ---: | ---: | --- |
| Before first image action | 2,838 | 4,090 | New includes active round + skill response link. |
| After first evaluated image | 4,201 | 9,241 | New keeps full recent RoundRecord and prompt/action plan. |
| Before rollback/final edit | 5,206 | 10,211 | New is larger but contains prompt, diagnosis, operations, outcome, best/latest images. |
| Before submit | 5,545 | 11,579 | New contains five completed rounds plus best attempt summary. |

### Teacher Request Usage for Valid Actions

| Action | Old prompt tokens | New prompt tokens |
| --- | ---: | ---: |
| first `query_skill` | 2,508 | 3,017 |
| first `generate_image` | 3,201 | 3,622 |
| first valid `edit_image` | 6,324 | 7,271 |
| regression/final-repair edit area | 6,456-6,574 | 7,284-7,489 |
| submit | 6,731 | 7,846 |

The new context is not shorter. Its advantage is higher decision density per token:

- it replaces opaque compact attempt rows with explicit RoundRecords;
- it avoids duplicating raw evaluator prose;
- it keeps the complete most recent round but compresses earlier rounds;
- it summarizes best attempt separately so latest and best are not conflated;
- it stores the model-authored action plan separately from environment-owned outcome.

## 7. Outcome Comparison

| Metric | Old v0.2 | New v0.3 |
| --- | ---: | ---: |
| Image attempts | 5 | 5 |
| Final submitted attempt | `a_002` | `a_004` |
| Final pass atoms | 9 / 11 | 10 / 11 |
| Final fail atoms | `c_004`, `c_008` | `c_004` |
| Regression occurred | yes, `c_002` in `a_003` | yes, `c_002` in `a_003` |
| Rollback occurred | yes, `a_002 -> a_004` | yes, `a_000 -> a_004` |
| Submit best, not necessarily latest | yes | yes |

The new submitted image still fails `c_004` (`Are the lions chasing the cats?`). The important architecture result is that the trajectory clearly records:

- what the teacher saw;
- what action it chose;
- why it chose that source;
- what hypotheses and interventions it committed to;
- what final image instruction was executed;
- what Geneval2 observed afterward;
- how that outcome updates latest and best.

## 8. Implementation References

Primary implementation changes:

- `schemas/action_protocol_v0_3.schema.json`
- `schemas/planner_context_v0_3.schema.json`
- `schemas/episode_event_v0_2.schema.json`
- `src/gen_retry/runtime/planner_context.py`
- `src/gen_retry/phase3/live_runner.py`
- `src/gen_retry/protocol/action_parser.py`
- `src/gen_retry/protocol/reference_validator.py`
- `src/gen_retry/protocol/provider_schemas.py`
- `src/gen_retry/agent/teacher_client.py`
- `src/gen_retry/sft/supervision.py`
- `src/gen_retry/cli/export_trajectory_trace.py`

Design and review docs:

- `docs/phase3/planner_context_round_memory_design.md`
- `docs/reviews/planner_context_round_memory_design_review_request.md`
- `docs/decisions/ADR-0005-sft-supervision-freeze.md`

Validation artifacts:

- New run: `runs/planner_context_v0_3/phase3_ep_001`
- RoundRecords: `runs/planner_context_v0_3/phase3_ep_001/round_records/`
- Trace: `docs/phase3/trajectory_trace_planner_context_v0_3_ep_001.md`
