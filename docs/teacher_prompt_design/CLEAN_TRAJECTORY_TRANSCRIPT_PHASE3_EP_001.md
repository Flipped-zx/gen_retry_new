# Clean Trajectory Transcript: `phase3_ep_001`

Purpose: 给导师展示一条结构清晰的 Gen-Retry trajectory。这里保留主线 canonical trajectory，弱化 debug 细节，只展示每轮 Teacher 看到了什么、输出了什么 action、环境返回了什么 observation，以及这些 observation 如何进入下一轮输入。

Run: `runs/teacher_prompt_v1_validation/phase3_ep_001`

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

## 1. System Prompt Design

Teacher 的 system prompt 不是让模型写分析报告，而是让它扮演一个 verifier-grounded image retry planner。

核心设计:

- 目标: 在有限 image-attempt budget 内最大化 best valid image attempt。
- 输出: 每轮只输出一个 canonical action JSON，不输出 prose，不输出 chain-of-thought。
- 证据: 同时使用 visible image 和 Geneval2 atom feedback。
- 历史: 使用 fixed / regressed / persistent failure / stable pass history。
- 分支: 当 latest 和 best 不同，必须比较二者后再选择 edit source。
- Skill: Skills 只指导 `generation_instruction` / `edit_instruction` 的写法，不替 Teacher 决定 generate/edit/submit。
- 约束: 不重复 materially equivalent ineffective instruction，除非新 instruction 有具体变化。

## 2. Action Protocol

Teacher 每轮只能选择一个 action:

```text
query_skill
generate_image
edit_image
submit_attempt
```

关键协议限制:

| Action | Required fields | 作用 |
| --- | --- | --- |
| `query_skill` | `skill_ids`, `target_constraint_ids` | 请求 Skill Markdown，作为后续 prompt/edit instruction 的写法指导 |
| `generate_image` | `mode`, `target_constraint_ids`, `preserve_constraint_ids`, `strategy_tags`, `skill_ids_used`, `generation_instruction` | 从空白生成一张新图 |
| `edit_image` | `source_attempt_id`, `target_constraint_ids`, `preserve_constraint_ids`, `strategy_tags`, `skill_ids_used`, `edit_instruction` | 基于已有 attempt 做局部编辑 |
| `submit_attempt` | `selected_attempt_id`, `reason_code` | budget 用完或已满足条件时提交 best |

Runtime guardrails:

- raw Teacher text 必须 parse 成 JSON。
- JSON 必须符合 action schema。
- `source_attempt_id`、constraint IDs、Skill IDs 必须引用已存在对象。
- budget 为 0 时只能 `submit_attempt`。
- `edit_image` 必须引用已有 source attempt。
- image instruction 必须可执行，且不能与 preserve/target 约束冲突。
- 未通过校验的 raw output 只作为 audit 记录，不进入 clean trajectory，不消耗 image budget，不作为 SFT positive target。

## 3. How Observation Becomes Next Input

每次 image action 后，环境做三步解析，把非结构化结果变成下一轮 Teacher 可读的 structured input:

```text
Qwen image artifact
-> Geneval2 per-atom VQA result
-> normalized atom status: pass / fail / uncertain
-> reducer computes latest, best, compact_history, transition, remaining_budget
-> PlannerView renderer builds next Teacher input
```

因此下一轮 Teacher 不是只看到“上一张图不好”，而是看到:

- latest attempt ID;
- best attempt ID;
- visible latest/best image;
- passed atom IDs;
- failed atom IDs;
- fixed/regressed/persistent failures;
- remaining image budget;
- compact attempt history.

## 4. Clean Main Trajectory

### Turn 0: Query Skills

**Teacher input**

```text
Task: six glass lions chasing three red cats behind a brown donut
Budget: 5 image attempts
History: empty
Visible images: none
Atom constraints: c_001 ... c_011
Available skill summaries: counting, spatial relation, attribute binding, local edit preservation
Extra observation: no image exists yet, so do not edit or submit
```

**Assistant action**

```json
{
  "schema_version": "0.2",
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

**Tool observation**

```text
Returned full Markdown for:
- counting_and_instance_layout
- spatial_relation_layout
```

**Effect on next input**

The next Teacher input includes these retrieved Skills as full content, and later PlannerViews retain compact active Skill operator summaries.

---

### Turn 1: Generate Initial Image `a_000`

**Teacher input**

```text
TaskSpec: 11 atom constraints
Budget: 5
History: empty
Visible images: none
Active Skills: counting_and_instance_layout, spatial_relation_layout
```

**Assistant action**

```json
{
  "schema_version": "0.2",
  "action": "generate_image",
  "arguments": {
    "mode": "initial",
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
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "fresh_layout",
      "counting",
      "spatial_relation"
    ],
    "generation_instruction": "Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts."
  }
}
```

**Environment observation**

```text
Qwen output: img_000
Geneval2: 6/11 atoms passed
Failed: c_001 lion count, c_002 lion glass uncertain, c_004 chasing, c_005 cat count, c_008 cats behind donut
State: latest = a_000, best = a_000, remaining_budget = 4
```

**Effect on next input**

Next PlannerView includes `a_000` as both latest and best, passes/failures by atom, the transition summary, and `img_000` as visible image evidence.

---

### Turn 2: Regenerate From Blank `a_001`

**Teacher input**

```text
Latest/best: a_000
Visible image: img_000
Budget: 4
History: [a_000]
Failed atoms: c_001, c_002, c_004, c_005, c_008
Interpretation: broad failures remain, so fresh layout is still reasonable
```

**Assistant action**

```json
{
  "schema_version": "0.2",
  "action": "generate_image",
  "arguments": {
    "mode": "initial",
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
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "fresh_layout",
      "explicit_counting",
      "spatial_relation"
    ],
    "generation_instruction": "Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects."
  }
}
```

**Environment observation**

```text
Qwen output: img_001
Geneval2: 8/11 atoms passed
Fixed relative to a_000: c_002 lion glass, c_005 cat count
Still failed: c_001 lion count, c_004 chasing, c_008 cats behind donut
State: latest = a_001, best = a_001, remaining_budget = 3
```

**Effect on next input**

Next PlannerView shows `a_001` as a better base. It exposes the stable passes and the three persistent failures, making a targeted edit preferable to another broad regeneration.

---

### Turn 3: Local Edit From `a_001` -> `a_002`

**Teacher input**

```text
Latest/best: a_001
Visible image: img_001
Budget: 3
History: [a_000, a_001]
Persistent failures: c_001 lion count, c_004 chasing, c_008 cats behind donut
Stable passes to preserve: c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011
```

**Assistant action**

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",
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
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "localized_repair",
      "counting",
      "spatial_relation"
    ],
    "edit_instruction": "Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene."
  }
}
```

**Environment observation**

```text
Qwen output: img_002
Geneval2: 9/11 atoms passed
Fixed relative to a_001: c_001 lion count
Still failed: c_004 chasing, c_008 cats behind donut
State: latest = a_002, best = a_002, remaining_budget = 2
```

**Effect on next input**

Next PlannerView now shows only two failed relation/depth atoms. The stable passes are locked for preservation, so the next action can focus only on relation cues.

---

### Turn 4: Relation-Focused Edit From `a_002` -> `a_003`

**Teacher input**

```text
Latest/best: a_002
Visible image: img_002
Budget: 2
History: [a_000, a_001, a_002]
Failed atoms: c_004 chasing, c_008 cats behind donut
Stable passes: nine atoms
```

**Assistant action**

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
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
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "localized_repair",
      "depth_relation",
      "motion_relation"
    ],
    "edit_instruction": "Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects."
  }
}
```

**Environment observation**

```text
Qwen output: img_003
Geneval2: 8/11 atoms passed
Still failed: c_004 chasing, c_008 cats behind donut
Regressed: c_002 lion glass
State: latest = a_003, best = a_002, remaining_budget = 1
```

**Effect on next input**

Next PlannerView includes two visible images: `LATEST_IMAGE = img_003` and `BEST_IMAGE = img_002`. It also exposes the regression from latest, so Teacher can branch from best instead of continuing from the worse latest attempt.

---

### Turn 5: Branch From Best `a_002` -> `a_004`

**Teacher input**

```text
Latest: a_003
Best: a_002
Visible images: img_003 as latest, img_002 as best
Budget: 1
History: [a_000, a_001, a_002, a_003]
Latest transition: a_003 regressed c_002 lion glass
Persistent failures from best: c_004 chasing, c_008 cats behind donut
```

**Assistant action**

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
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
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "best_branch",
      "localized_repair",
      "spatial_relation"
    ],
    "edit_instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap."
  }
}
```

**Environment observation**

```text
Qwen output: img_004
Geneval2: 9/11 atoms passed
Still failed: c_004 chasing, c_008 cats behind donut
State: latest = a_004, best = a_002, remaining_budget = 0
```

**Effect on next input**

Next PlannerView says budget is exhausted and exposes best `a_002`. Therefore the only legal action is to submit the best available attempt.

---

### Turn 6: Submit Best

**Teacher input**

```text
Budget: 0
Latest: a_004
Best: a_002
Visible images: latest img_004, best img_002
Extra observation: submit best available with reason_code best_available_under_budget
```

**Assistant action**

```json
{
  "schema_version": "0.2",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_002",
    "reason_code": "best_available_under_budget"
  }
}
```

**Final result**

```text
Submitted: a_002
Reason: best_available_under_budget
Best score: 9/11 atoms passed
Remaining unresolved atoms: c_004 chasing, c_008 cats behind donut
```

## 5. What This Demonstrates

This trajectory demonstrates the intended training/inference shape:

```text
system policy
user structured state + images
assistant one action
tool/environment observation
user next structured state carrying previous observation
assistant next action
...
```

Key behavior:

- Skill retrieval happens as an explicit action and tool response.
- Generation prompt rewrite is conditioned on Skill content.
- Each image attempt is evaluated by Geneval2 at atom level.
- Atom results are parsed into structured PlannerView fields.
- Later actions target failed atoms and preserve passed atoms.
- Best-so-far is environment-owned, not invented by Teacher.
- Teacher can branch from best when latest regresses.
- Final submission uses canonical budget-aware reason code.

## 6. Small Implementation Note

The clean transcript above shows only accepted canonical actions. During live execution, raw Teacher text is always stored redacted and validated first. Invalid raw outputs are audit-only. For example, one raw `generate_image` omitted required `mode`; schema validation rejected it, so it is not part of the clean canonical trajectory.

We have separately tested provider-level structured output on that exact failed input. An action-specific `response_format=json_schema` returned a valid `generate_image` action with `mode: initial`. This should be adopted as a stricter decoding layer, while keeping the existing local validators as final authority.
