# Gen-Retry Planner 输入/输出字段设计确认稿

**基于轨迹：`phase3_ep_001`**

本文只讨论一件事：

> 在每次调用 Planner 时，Agent 应该看到哪些字段；Planner 输出一个 Action 时，应包含哪些字段。

暂不展开底层 artifact、训练实现、RoundRecord 的完整落盘格式，也不为旧 schema 设计兼容层。

---

## 1. 任务设定

对于一个原始 prompt：

```text
six glass lions chasing three red cats behind a brown donut
```

系统先将其拆分为 atom-level constraints：

```text
c_001: six lions
c_002: lions are glass
c_003: lions exist
c_004: lions are chasing the cats
c_005: three cats
c_006: cats are red
c_007: cats exist
c_008: cats are behind the donut
c_009: one donut
c_010: donut is brown
c_011: donut exists
```

每个 episode 最多允许 **5 次 image attempts**：

```text
generate_image
edit_image
```

均消耗一次 image budget。

以下 Action 不消耗 image budget：

```text
query_skill
submit_attempt
```

Planner 每次只输出一个 canonical Action：

```text
query_skill
generate_image
edit_image
submit_attempt
```

---

# 2. 最终建议：PlannerContext 的五个区

```text
PlannerContext
├── task_context
├── latest_observation
├── skill_context
├── episode_memory
└── runtime_state
```

这五个区分别回答：

```text
task_context       最终任务是什么？
latest_observation 当前最新结果是什么状态？
skill_context      当前已经获得了哪些能力知识？
episode_memory     过去尝试过什么，结果如何？
runtime_state      还剩多少预算，现在允许做什么？
```

---

## 2.1 `task_context`

整个 episode 中保持不变。

```yaml
task_context:
  original_prompt: "six glass lions chasing three red cats behind a brown donut"

  atom_constraints:
    - id: c_001
      type: count
      expected: six lions

    - id: c_002
      type: attribute
      expected: lions are glass

    # ... c_003 to c_011
```

### 为什么保留

它是整个任务的固定目标。

### 不属于 Memory

Prompt 和 constraints 不应称为历史 Memory，因为它们不是过去发生的事情，而是始终不变的 task specification。

---

## 2.2 `latest_observation`

表示当前最新 image attempt 的状态。

首次生成前：

```yaml
latest_observation: null
```

产生 `a_000` 后：

```yaml
latest_observation:
  attempt_id: a_000
  image_role: LATEST_IMAGE

  constraint_results:
    passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_001, c_004, c_005]
    uncertain: []
```

### 为什么必须包含 `attempt_id`

`attempt_id` 不是为了让模型按 round 回看文本，而是一个稳定的图片引用句柄。

Planner 后续需要输出：

```json
{
  "source_attempt_id": "a_000"
}
```

或者：

```json
{
  "selected_attempt_id": "a_004"
}
```

因此不能只告诉模型“这是 Round 3 的图片”。

原因是：

1. 一个 Round 可以先包含 `query_skill`，再产生图片；
2. edit 和 submit 操作的对象是 Attempt，而不是 Round；
3. 分支编辑时，多个后续 Attempt 可以来自同一个历史 Attempt；
4. latest 和 best 可能来自不同 Round。

### 避免重复

`latest_attempt_id` 只放在 `latest_observation` 中。

不再在 `runtime_state` 或其他区域重复保存一份。

---

## 2.3 `skill_context`

`query_skill` 执行后，下一次 Planner 调用需要看到 Skill 的实际内容。

不建议同时保留：

```text
skill_requires
queried_skill_ids
query_target_constraint_ids
retrieved_skill_content
active_capability_skills
skill_ids_used
```

这些字段存在明显重叠。

### 建议合并为一个结构

```yaml
skill_context:
  active_skills:
    - skill_id: counting_and_instance_layout
      target_constraint_ids: [c_001, c_005, c_009]
      content: >
        Construct prompts that make every instance visible,
        separated, bounded and countable.

    - skill_id: spatial_relation_layout
      target_constraint_ids: [c_004, c_008]
      content: >
        Construct prompts using anchors, depth, orientation
        and visibility cues.
```

它已经同时表达：

```text
查询到了什么 Skill
这些 Skill 面向哪些 constraints
Skill 的实际内容是什么
```

### 建议删除 `skill_requires`

如果 Planner 判断需要 Skill，它直接输出：

```json
{
  "action": "query_skill",
  "arguments": {
    "skill_ids": [...],
    "target_constraint_ids": [...]
  }
}
```

这已经是正式决策。

再增加：

```text
skill_requires
```

只会重复表达“我需要哪些 Skill”。

### `skill_ids_used` 是否保留

第一版建议不设为 image Action 的必填字段。

原因：

1. 当前 Round 查询了哪些 Skills，环境已经知道；
2. Skill 内容已经出现在 `skill_context`；
3. Planner 是否真正使用 Skill，不能只靠模型自报可靠验证；
4. 最终 instruction 本身才是 Skill 是否落地的主要证据；
5. 强制再输出一遍会增加 schema 重复。

Round 完成后，环境可以确定性记录：

```text
本 Round 在 image Action 前激活过哪些 Skills
```

若以后需要研究“同时激活多个 Skill 时，Planner 实际选择了哪一个”，再将 `skill_ids_used` 作为可选字段加入，而不是当前必填字段。

---

## 2.4 `episode_memory`

Planner 不需要看到所有底层日志，而需要看到有助于下一次决策的历史摘要。

```text
episode_memory
├── recent_round
├── earlier_rounds
└── best_attempt
```

### `recent_round`

最新完成的一轮，保留较完整信息：

```yaml
recent_round:
  image_action:
    action: edit_image
    source_attempt_id: a_000

    decision_summary: >
      Edit the historical best because the latest attempt
      did not improve the targets and regressed the glass attribute.

    diagnosis_summary: >
      The remaining failures appear to come from weak pursuit
      cues rather than missing objects.

    target_constraint_ids: [c_001, c_004, c_005]
    preserve_constraint_ids: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]

    instruction: "..."

  result_attempt_id: a_004

  observed_outcome:
    fixed: [c_001, c_005]
    regressed: []
    persistent_failed: [c_004]
    preserved: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
```

### `earlier_rounds`

更早轮次压缩保存：

```yaml
earlier_rounds:
  - source_attempt_id: null
    result_attempt_id: a_000
    action: generate_image
    decision_summary: "Generate the first complete layout."
    target_constraint_ids: [c_001, c_002, "...", c_011]
    outcome:
      initial_failed: [c_001, c_004, c_005]
      became_best: true

  - source_attempt_id: a_000
    result_attempt_id: a_001
    action: edit_image
    decision_summary: "Repair counts and chase action on the current best."
    target_constraint_ids: [c_001, c_004, c_005]
    outcome:
      fixed: []
      regressed: []
      persistent_failed: [c_001, c_004, c_005]
```

更早历史不重复携带完整长 prompt。

### `best_attempt`

历史最佳单独突出：

```yaml
best_attempt:
  attempt_id: a_000
  image_role: BEST_IMAGE

  constraint_results:
    passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_001, c_004, c_005]
    uncertain: []
```

### 为什么 best 必须有自己的 `attempt_id`

因为 Planner 可能需要明确输出：

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000"
  }
}
```

不能只说“编辑历史最好那一轮”。

---

## 2.5 `runtime_state`

这里只保留**会随状态动态变化、且无法由静态 system prompt 完全决定的信息**。

```yaml
runtime_state:
  remaining_image_budget: 3

  available_actions:
    - query_skill
    - generate_image
    - edit_image
    - submit_attempt
```

### 是否需要 `available_actions`

Action 集合本身属于 system prompt：

```text
query_skill
generate_image
edit_image
submit_attempt
```

但某一时刻哪些 Action 合法是动态的：

```text
首次生成前：
  edit_image 和 submit_attempt 不合法

已有图片且有预算：
  四类 Action 均可能合法

预算为 0：
  generate_image 和 edit_image 不合法
```

因此建议：

- 静态 Action Schema 放在 system prompt；
- 当前动态可用 Action 放在 `runtime_state.available_actions`。

它占用 token 很少，却能减少非法调用。

### `runtime_state` 中不再放什么

不再重复：

```text
latest_attempt_id
best_attempt_id
```

因为它们已经分别存在于：

```text
latest_observation.attempt_id
episode_memory.best_attempt.attempt_id
```

---

# 3. Planner 输出字段：最小而充分的设计

## 3.1 `query_skill`

```json
{
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

不增加：

```text
decision_summary
skill_requires
```

因为已有参数已经清楚表达局部目的。

---

## 3.2 `generate_image`

建议字段：

```json
{
  "action": "generate_image",
  "arguments": {
    "decision_summary": "No image exists yet, so generate one complete layout that prioritizes exact counts and clear spatial relations.",

    "diagnosis_summary": "Exact counts and the chase/depth relations are the highest-risk parts of the task.",

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

    "generation_instruction": "Create one clear scene with exactly six glass lions..."
  }
}
```

### `decision_summary`

每个 generate/edit Action 只有一个总体 summary。

它回答：

```text
为什么选择 generate/edit？
为什么选择这个 source？
本轮总体采取什么路线？
```

不是每个 constraint 一条 decision。

### `diagnosis_summary`

建议保留为**可选的单个总体字段**，而不是：

```text
diagnostic_hypotheses[]
```

它只在模型对失败原因存在额外、可操作的视觉判断时使用。

首次生成时也可以省略：

```json
{
  "diagnosis_summary": null
}
```

因为首次生成前还没有图片可诊断。

### 不保留 `repair_plan[].change`

第一版建议删除：

```text
repair_plan
interventions
change
operation
```

原因：

1. `target_constraint_ids` 已说明修什么；
2. `decision_summary` 已说明总体路线；
3. `diagnosis_summary` 可说明视觉失败原因；
4. 最终 instruction 已经完整说明具体如何修改；
5. 再要求若干 `change` 条目会与 instruction 高度重复。

若以后需要跨任务聚合 operation 类型，可以从完整 trajectory 离线标注或抽取，不必让在线 Planner 每轮重复生成一套中间描述。

---

## 3.3 `edit_image`

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",

    "decision_summary": "Return to the historical best instead of continuing from the latest because the latest regressed the glass attribute.",

    "diagnosis_summary": "The remaining failure is primarily weak chase visibility; the object counts and attributes should be preserved.",

    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_005"
    ],

    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010",
      "c_011"
    ],

    "edit_instruction": "Edit attempt a_000. Preserve the glass lions, red cats and brown donut..."
  }
}
```

整个 Action 已经表达：

```text
选择 edit
选择 source
说明总体决策
说明必要的视觉诊断
指定 target / preserve
写出最终可执行 Prompt
```

无需再添加独立 `repair_plan`。

---

## 3.4 `submit_attempt`

```json
{
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_004",
    "reason_code": "best_available_under_budget"
  }
}
```

标准提交不增加重复的自由文本 decision。

只有提交的不是环境判定 best，或：

```text
reason_code = other
```

时，才要求可选：

```text
submission_rationale
```

---

# 4. 当前轨迹中，输入如何逐步增加

## Step 0：首次 Planner 调用

```yaml
PlannerContext:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001, "...", c_011]

  latest_observation: null

  skill_context:
    active_skills: []

  episode_memory:
    recent_round: null
    earlier_rounds: []
    best_attempt: null

  runtime_state:
    remaining_image_budget: 5
    available_actions:
      - query_skill
      - generate_image
```

Planner 输出：

```text
query_skill
```

---

## Step 1：`query_skill` 后、首次生成前

与 Step 0 相比，只新增：

```yaml
skill_context:
  active_skills:
    - skill_id: counting_and_instance_layout
      target_constraint_ids: [c_001, c_005, c_009]
      content: "..."

    - skill_id: spatial_relation_layout
      target_constraint_ids: [c_004, c_008]
      content: "..."
```

以下内容仍不变：

```text
latest_observation = null
episode_memory = empty
remaining_image_budget = 5
```

Planner 随后输出：

```text
generate_image
```

---

## Step 2：首次生成 `a_000` 后

下一轮输入新增：

```yaml
latest_observation:
  attempt_id: a_000
  image_role: LATEST_IMAGE
  constraint_results:
    passed: [...]
    failed: [c_001, c_004, c_005]
    uncertain: []

episode_memory:
  recent_round:
    queried_skills:
      - counting_and_instance_layout
      - spatial_relation_layout

    image_action:
      action: generate_image
      decision_summary: "..."
      target_constraint_ids: [c_001, "...", c_011]
      instruction: "..."

    result_attempt_id: a_000
    observed_outcome:
      initial_failed: [c_001, c_004, c_005]

  best_attempt:
    attempt_id: a_000
    image_role: BEST_IMAGE
    constraint_results: [...]

runtime_state:
  remaining_image_budget: 4
  available_actions:
    - query_skill
    - generate_image
    - edit_image
    - submit_attempt
```

新的 Planner 不仅知道：

```text
a_000 哪些 constraints 失败
```

还知道：

```text
上一轮查询了什么 Skill
上一轮选择了什么 Action
上一轮总体怎么考虑
上一轮最终 Prompt 是什么
该 Prompt 实际产生了什么结果
```

---

## Step 3：出现 latest 与 best 分离后

当前轨迹后部可能出现：

```yaml
latest_observation:
  attempt_id: a_003
  image_role: LATEST_IMAGE
  constraint_results:
    failed: [c_001, c_002, c_004]

episode_memory:
  recent_round:
    source_attempt_id: a_000
    result_attempt_id: a_003
    observed_outcome:
      fixed: [c_005]
      regressed: [c_002]
      persistent_failed: [c_001, c_004]

  best_attempt:
    attempt_id: a_000
    image_role: BEST_IMAGE
    constraint_results:
      failed: [c_001, c_004, c_005]

runtime_state:
  remaining_image_budget: 1
  available_actions:
    - query_skill
    - generate_image
    - edit_image
    - submit_attempt
```

Planner 可以明确输出：

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "decision_summary": "Use the historical best instead of the latest because the latest regressed c_002.",
    "diagnosis_summary": "The final attempt should preserve material attributes while strengthening the unresolved count and chase cues.",
    "target_constraint_ids": [c_001, c_004, c_005],
    "preserve_constraint_ids": [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011],
    "edit_instruction": "..."
  }
}
```

`attempt_id` 在这里是必要的，因为它允许 Planner 精确选择历史 source，而不是只说“回到之前较好的一轮”。

---

# 5. 建议删除、合并与保留的字段

| 当前或候选字段 | 建议 | 原因 |
|---|---|---|
| `active_round` | 不暴露给 Planner | Round ID、step ID 属于 runtime bookkeeping |
| `skill_requires` | 删除 | 与 `query_skill` Action 重复 |
| `queried_skill_ids` | 合并 | 合入 `skill_context.active_skills[]` |
| `query_target_constraint_ids` | 合并 | 放入每个 active skill 条目 |
| `retrieved_skill_content` | 合并 | 放入每个 active skill 条目 |
| `skill_ids_used` | 第一版不设为必填 | 与 active skills 重复，且模型自报不可靠 |
| `decision_summary` | 保留 | 每个 image Action 一个总体决策摘要 |
| `diagnostic_hypotheses[]` | 简化 | 改成可选单个 `diagnosis_summary` |
| `repair_plan[]` | 删除 | 与 target、decision 和 instruction 重复 |
| `interventions[].change` | 删除 | 主要内容已进入最终 instruction |
| `target_constraint_ids` | 保留 | 明确本轮修复范围 |
| `preserve_constraint_ids` | 保留 | 明确避免 regression 的边界 |
| `latest_attempt_id` in control | 删除 | 已在 `latest_observation.attempt_id` |
| `best_attempt_id` in control | 删除 | 已在 `best_attempt.attempt_id` |
| `remaining_image_budget` | 保留 | 动态决策条件 |
| `available_actions` | 保留 | 当前合法 Action 会随状态变化 |

---

# 6. 最终推荐 Schema

## PlannerContext

```yaml
PlannerContext:
  task_context:
    original_prompt: string
    atom_constraints: list

  latest_observation:
    attempt_id: string
    image_role: LATEST_IMAGE
    constraint_results:
      passed: list
      failed: list
      uncertain: list

  skill_context:
    active_skills:
      - skill_id: string
        target_constraint_ids: list
        content: string

  episode_memory:
    recent_round: object | null
    earlier_rounds: list
    best_attempt:
      attempt_id: string
      image_role: BEST_IMAGE
      constraint_results: object

  runtime_state:
    remaining_image_budget: integer
    available_actions: list
```

## Image Action

```yaml
generate_image:
  decision_summary: string
  diagnosis_summary: string | null
  target_constraint_ids: list
  preserve_constraint_ids: list
  generation_instruction: string
```

```yaml
edit_image:
  source_attempt_id: string
  decision_summary: string
  diagnosis_summary: string | null
  target_constraint_ids: list
  preserve_constraint_ids: list
  edit_instruction: string
```

---

# 7. 一句话概括

> Planner 输入只保留任务目标、当前结果、当前有效 Skill、分层历史和动态预算；Planner 的 generate/edit 输出只保留一个总体决策摘要、一个可选总体诊断、target/preserve 边界以及最终可执行 Prompt，不再要求重复的 `skill_requires`、逐约束 hypothesis 或 `repair_plan.change`。
