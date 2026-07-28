# Training Trajectory Format Comparison

Purpose: 对比一条 GenEvolve/Gen-Searcher-style training trajectory 和一条 Gen-Retry trajectory。重点不是评测分数，而是看清楚:

- 模型每一轮看到了什么；
- 哪些 assistant 内容是训练目标；
- 哪些 tool / environment / evaluator 内容只是 context；
- 上一轮 observation 如何进入下一轮 input。

## 1. Source Grounding

GenEvolve repository evidence:

- `GenEvolve/README.md` describes the final answer as a prompt-reference program: `{"gen_prompt": ..., "reference_images": [...]}`.
- `GenEvolve/README.md` describes SFT data as chat-format ReAct trajectories ending in `<answer>{gen_prompt, reference_images}</answer>` plus reference images.
- `GenEvolve/genevolve/system_prompt.py` requires each round to output either `<think>...</think><tool_call>...</tool_call>` or `<think>...</think><answer>...</answer>`.
- `GenEvolve/genevolve/agent.py` parses `<tool_call>{...}</tool_call>` and `<answer>{...}</answer>` from raw assistant text, then resolves `IMG_###` references into image records.

Gen-Retry repository evidence:

- `docs/phase4/sft_supervision_freeze.md` freezes the v3 SFT message format: `system` loss 0, `user` loss 0, selected assistant canonical action loss 1.
- Raw Teacher output, raw tool payloads, Geneval2 observations, and environment-owned facts are never assistant targets.
- The concrete Gen-Retry example below is `runs/teacher_prompt_v1_validation/phase3_ep_001`.

## 2. GenEvolve-Style Training Trajectory

This is a formalized trajectory shape based on the GenEvolve README and agent prompt. It is not claiming to be one exact released dataset row; it shows the documented training format.

### Objective

Turn a user prompt into a grounded prompt-reference program:

```json
{
  "gen_prompt": "... the first reference image ...",
  "reference_images": [
    {
      "img_id": "IMG_001",
      "note": "what to copy from this reference"
    }
  ]
}
```

Some paper descriptions add metadata such as `selected_skills` and `rationale`; in the local GenEvolve code/README, the executable final answer fields are `gen_prompt` and `reference_images`.

### Formalized Messages

| Step | Role | Content shape | Seen by model? | Trained target? |
| --- | --- | --- | --- | --- |
| 0 | `system` | GenEvolve ReAct/tool prompt: output one `<think> + <tool_call>` or `<think> + <answer>` | yes | no |
| 1 | `user` | Original image-generation request | yes | no |
| 2 | `assistant` | `<think>Need visual/knowledge grounding...</think><tool_call>{"name":"image_search","arguments":{"query":"..."}}</tool_call>` | yes in later turns | yes, as assistant message in ReAct SFT unless subspan masking is applied elsewhere |
| 3 | `tool/user` | `<tool_response>IMG_001 ..., IMG_004 ...</tool_response>` plus retrieved/reference images | yes | no |
| 4 | `assistant` | `<think>Need prompt-writing guidance...</think><tool_call>{"name":"query_knowledge","arguments":{"skill_name":"spatial_layout"}}</tool_call>` | yes in later turns | yes, as assistant message |
| 5 | `tool/user` | Markdown Skill content for `spatial_layout` | yes | no |
| 6 | `assistant` | `<think>Use evidence and skill guidance...</think><answer>{"gen_prompt":"... the first reference image ...","reference_images":[...]}</answer>` | final assistant output | yes, as assistant message |

### What Is Learned

The model learns to produce the assistant-side ReAct trajectory:

```text
<think>brief plan / evidence summary</think>
<tool_call>{tool name + arguments}</tool_call>
...
<think>brief final synthesis</think>
<answer>{gen_prompt + reference_images}</answer>
```

The model sees tool results and images as context, but tool results themselves are not assistant targets.

### Why Rationale Exists There

In this task, rationale is useful because the final output is a prompt-reference program. The model must justify:

- why these references were selected;
- why these Skills were relevant;
- why the final `gen_prompt` is grounded by the evidence.

So the rationale explains final prompt construction and evidence selection.

## 3. Gen-Retry Trajectory

This is our real trajectory: `phase3_ep_001`.

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

The task is not to create one final prompt-reference program. The task is to run a verifier-grounded retry loop:

```text
PlannerView + visible images + Geneval2 atom feedback
-> exactly one Teacher action
-> Qwen image generation/edit
-> Geneval2 atom observation
-> updated PlannerView
-> next Teacher action
```

### Current SFT Rule

| Role / artifact | Seen by model? | Trained target? |
| --- | --- | --- |
| fixed system prompt | yes | no |
| TaskSpec | yes | no |
| PlannerView | yes | no |
| visible latest/best images | yes | no |
| returned Skill content | yes | no |
| Geneval2 atom results | yes, through next PlannerView | no |
| reducer facts: latest, best, history, transitions, budget | yes, through next PlannerView | no |
| assistant canonical `generate_image` / `edit_image` / `submit_attempt` | yes in history | yes, if selected positive/recovery target |
| assistant `query_skill` | yes in history/context | currently no, context-only |
| invalid raw Teacher output | audit only | no |

### Formalized Clean Messages

#### Turn 0: query Skill

```text
Seen input:
  system policy
  TaskSpec atoms c_001 ... c_011
  PlannerView: budget=5, history=[], visible_images=[]
  available Skill summaries

Train target:
  query_skill(
    skill_ids=[counting_and_instance_layout, spatial_relation_layout],
    target_constraint_ids=[c_001,c_004,c_005,c_008,c_009]
  )

Seen next observation:
  full Markdown Skills returned
```

Current SFT note:

```text
query_skill is currently context-only, not final positive target, until Skill utility policy is frozen.
```

#### Turn 1: generate `a_000`

```text
Seen input:
  TaskSpec
  PlannerView: budget=5, history=[]
  active Skills: counting + spatial relation
  visible_images=[]

Train target:
  generate_image(
    mode=initial,
    target=all atoms,
    preserve=[],
    skill_ids_used=[counting_and_instance_layout, spatial_relation_layout],
    strategy_tags=[fresh_layout,counting,spatial_relation],
    generation_instruction="exact one brown donut foreground; exactly three red cats behind it; exactly six glass lions chasing cats; all visible/separated; no extras/fusion/cropping/reflections"
  )

Environment observation, not target:
  Qwen -> img_000
  Geneval2 -> 6/11 pass
  failed=[c_001,c_002,c_004,c_005,c_008]
```

This observation becomes the next PlannerView:

```text
latest=a_000
best=a_000
history=[a_000]
budget=4
visible image=img_000
failed atoms and transition summary included
```

#### Turn 2: regenerate from blank `a_001`

```text
Seen input:
  latest=a_000, best=a_000
  visible image=img_000
  history=[a_000]
  budget=4
  broad failures: count/material/relation/cat-count/depth

Train target:
  generate_image(
    mode=initial,
    target=all atoms,
    strategy_tags=[fresh_layout,explicit_counting,spatial_relation],
    generation_instruction="clean white studio; foreground donut; three red cats behind donut; six translucent glass lions in separated arc behind cats; no extras/duplicates/reflections"
  )

Environment observation, not target:
  Qwen -> img_001
  Geneval2 -> 8/11 pass
  fixed=[c_002,c_005]
  failed=[c_001,c_004,c_008]
```

Next PlannerView:

```text
latest=a_001
best=a_001
history=[a_000,a_001]
budget=3
persistent failures narrowed to [lion count, chasing, behind donut]
stable passes available for preservation
```

#### Turn 3: edit `a_001 -> a_002`

```text
Seen input:
  latest=a_001, best=a_001
  visible image=img_001
  history=[a_000,a_001]
  failed=[c_001,c_004,c_008]
  stable passes=[c_002,c_003,c_005,c_006,c_007,c_009,c_010,c_011]
  budget=3

Train target:
  edit_image(
    source_attempt_id=a_001,
    target=[c_001,c_004,c_008],
    preserve=[c_002,c_003,c_005,c_006,c_007,c_009,c_010,c_011],
    skill_ids_used=[counting_and_instance_layout, spatial_relation_layout],
    strategy_tags=[localized_repair,counting,spatial_relation],
    edit_instruction="add exactly two transparent glass lions so final count is six; strengthen chasing and behind-donut relation; preserve cats, colors, donut, glass material, background; forbid extra objects, cropping, fusion, unrelated redraw"
  )

Environment observation, not target:
  Qwen edit -> img_002
  Geneval2 -> 9/11 pass
  fixed=[c_001]
  failed=[c_004,c_008]
```

Next PlannerView:

```text
latest=a_002
best=a_002
history=[a_000,a_001,a_002]
budget=2
only relation/depth failures remain
```

#### Turn 4: edit `a_002 -> a_003`

```text
Seen input:
  latest=a_002, best=a_002
  visible image=img_002
  failed=[c_004,c_008]
  stable passes=nine atoms
  budget=2

Train target:
  edit_image(
    source_attempt_id=a_002,
    target=[c_004,c_008],
    preserve=[nine passing atoms],
    strategy_tags=[localized_repair,depth_relation,motion_relation],
    edit_instruction="adjust only depth and motion cues; keep counts/material/colors; make cats behind donut and lions chasing cats clearer"
  )

Environment observation, not target:
  Qwen edit -> img_003
  Geneval2 -> 8/11 pass
  regressed=[c_002]
  failed=[c_002,c_004,c_008]
```

Next PlannerView:

```text
latest=a_003
best=a_002
history=[a_000,a_001,a_002,a_003]
budget=1
visible images=[LATEST img_003, BEST img_002]
latest transition marks c_002 regression
```

#### Turn 5: branch from best `a_002 -> a_004`

```text
Seen input:
  latest=a_003
  best=a_002
  visible images: latest img_003, best img_002
  history=[a_000,a_001,a_002,a_003]
  latest regressed c_002
  best only fails [c_004,c_008]
  budget=1

Train target:
  edit_image(
    source_attempt_id=a_002,
    target=[c_004,c_008],
    preserve=[nine passing atoms from best],
    strategy_tags=[best_branch,localized_repair,spatial_relation],
    edit_instruction="revise a_002, not a_003; preserve six glass lions, three red cats, one brown donut; repair chasing/depth relation"
  )

Environment observation, not target:
  Qwen edit -> img_004
  Geneval2 -> 9/11 pass
  failed=[c_004,c_008]
```

Next PlannerView:

```text
latest=a_004
best=a_002
budget=0
submit is the only legal next action
```

#### Turn 6: submit best

```text
Seen input:
  budget=0
  latest=a_004
  best=a_002
  visible images=[latest img_004, best img_002]
  extra observation: submit best_available_under_budget

Train target:
  submit_attempt(
    selected_attempt_id=a_002,
    reason_code=best_available_under_budget
  )

Final environment record:
  submitted=a_002
  best score=9/11
```

## 4. Side-by-Side Difference

| Question | GenEvolve-style trajectory | Gen-Retry trajectory |
| --- | --- | --- |
| Main goal | Build final `gen_prompt + reference_images` | Choose retry actions to improve verifier score |
| Assistant output form | `<think> + <tool_call>` or `<think> + <answer>` | exactly one canonical action JSON |
| Tool observations | search/image_search/knowledge results | Skill result, Qwen image result, Geneval2 atom result |
| What model sees next | previous messages and tool responses | PlannerView derived from previous events plus visible images |
| What is trained | assistant ReAct messages, likely including `<think>` and final `<answer>` unless subspan masking is added | selected assistant canonical action JSON only |
| What is masked/context | system/user/tool responses/images | system/user/PlannerView/images/tool/evaluator/raw outputs |
| Rationale role | explains evidence/reference/skill use for final prompt-reference program | better as derived display metadata; not needed in minimal executable action |
| Skill use | `query_knowledge(skill_name)` then final prompt uses guidance | `query_skill` returns Markdown; later image actions cite `skill_ids_used` |
| Final answer | `gen_prompt`, `reference_images` | `submit_attempt(selected_attempt_id, reason_code)` |

## 5. Implication For Our Design

For the first Gen-Retry SFT dataset, keep the target minimal:

```text
Train:
  assistant canonical action JSON

Seen but not trained:
  TaskSpec
  PlannerView
  visible latest/best images
  Skill content
  Qwen outputs
  Geneval2 atom observations
  reducer state
  raw Teacher outputs
  optional derived rationale / clean transcript summaries
```

This preserves GenEvolve/Gen-Searcher's useful trajectory readability while keeping our train target aligned with the actual executable control problem.
