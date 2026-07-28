# Gen-Retry Planner I/O v0.4 — Codex Implementation Reference

> 本文件是本轮重构的**唯一设计基准**。
> Codex 不应自行增加新的 Action、字段、Memory 层级或兼容逻辑。
> 所有实现、测试和 normalized trajectory 都必须以本文为准。

---

# 1. 重构目标

将当前 Planner I/O 从字段重复、历史表达不统一的 v0.2/v0.3 结构，收敛为：

```text
Planner Input
├── System Protocol
├── PlannerContext
└── Visible Images

Planner Output
└── Exactly One Canonical Action
```

每个 Prompt：

```text
original prompt
→ atom-level constraints
→ 最多 5 次 generate/edit
→ 每步 Planner Action
→ Environment execution
→ Geneval2 verification
→ Memory/state update
→ 下一步 Planner Input
→ submit
```

底层图像后端统一为：

```text
QianwenImageEditAdapter
```

但 Planner 逻辑动作保持区分：

```text
generate_image
  = no source image
  = fresh generation / regeneration

edit_image
  = requires source_attempt_id
  = image-conditioned editing from a historical attempt
```

不增加独立的：

```text
regenerate_image
```

---

# 2. 最终 Action Space

```text
query_skill
generate_image
edit_image
submit_attempt
```

统一外壳：

```json
{
  "schema_version": "0.4",
  "action": "ACTION_NAME",
  "arguments": {}
}
```

每个 assistant turn 必须只输出一个 Action JSON，不输出 Markdown、解释性正文或环境结果。

---

# 3. Planner Input

完整 Planner 输入由三部分组成：

```text
PlannerInput
├── system_protocol
├── planner_context
└── visible_images
```

---

## 3.1 System Protocol

放在 system message，保持固定：

```text
system_protocol
├── Planner role and objective
├── complete Action space
├── schema of each Action
├── budget rules
├── source-selection rules
├── image visibility rules
└── forbidden outputs
```

System Protocol 定义**全部可能 Action**；当前状态下的合法 Action 子集由 `runtime_state.available_actions` 提供。

---

## 3.2 PlannerContext

唯一合法的顶层结构：

```yaml
planner_context:
  task_context: {}
  latest_observation: null | {}
  skill_context: {}
  episode_memory: {}
  runtime_state: {}
```

不得增加：

```text
active_round
compact_history
constraint_state
latest_transition
retrieved_experiences
skill_requires
tool_manifest
```

这些旧字段中的有效信息，应按本文映射到新的五个区域。

---

## 3.3 `task_context`

```yaml
task_context:
  original_prompt: string
  max_image_attempts: integer

  atom_constraints:
    - constraint_id: string
      constraint_type: string
      requirement: string
      evaluator_question: string | null
```

含义：

```text
original_prompt
  原始生成要求

max_image_attempts
  单 episode 最多 generate/edit 次数，本任务为 5

atom_constraints
  Prompt 拆解后的可验证目标
```

该部分在整个 episode 内不变，不属于 Memory。

---

## 3.4 `latest_observation`

首次生成前：

```yaml
latest_observation: null
```

已有图片后：

```yaml
latest_observation:
  attempt_id: string

  constraint_results:
    passed_constraint_ids: [string]
    failed_constraint_ids: [string]
    uncertain_constraint_ids: [string]

    observations:
      - constraint_id: string
        observed_value: string | number | boolean | null
```

`attempt_id` 必须保留，因为：

```text
edit_image.source_attempt_id
submit_attempt.selected_attempt_id
```

都需要精确引用 Attempt。

不要在 `runtime_state` 中再次重复 latest attempt ID。

---

## 3.5 `skill_context`

```yaml
skill_context:
  active_skills:
    - skill_id: string
      target_constraint_ids: [string]
      guidance: string
      guidance_level: full | summary
```

它统一替代：

```text
queried_skill_ids
query_target_constraint_ids
retrieved_skill_content
active_capability_skills
retrieved_experiences
skill_requires
```

规则：

```text
query_skill 刚返回时：
  guidance_level = full

后续轮次需要压缩时：
  guidance_level = summary
```

不要求 image Action 再输出 `skill_ids_used`。

原因：

```text
1. 环境已知道当前激活的 Skills；
2. Skill 内容已在 skill_context 中；
3. 模型自报是否“实际使用”无法可靠验证；
4. 最终 instruction 才是 Skill 是否落地的主要证据。
```

---

## 3.6 `episode_memory`

```yaml
episode_memory:
  recent_round: null | RoundMemoryFull
  earlier_rounds: [RoundMemoryCompact]
  best_attempt: null | BestAttempt
```

---

### 3.6.1 `recent_round`

最新完成的 image-producing round，保留较完整信息：

```yaml
recent_round:
  skill_queries:
    - skill_id: string
      target_constraint_ids: [string]

  image_action:
    action: generate_image | edit_image
    source_attempt_id: string | null
    decision_summary: string
    diagnosis_summary: string | null
    target_constraint_ids: [string]
    preserve_constraint_ids: [string]
    instruction: string

  result_attempt_id: string

  observed_outcome:
    comparison_attempt_id: string | null

    initial_passed_constraint_ids: [string]
    initial_failed_constraint_ids: [string]
    initial_uncertain_constraint_ids: [string]

    fixed_constraint_ids: [string]
    regressed_constraint_ids: [string]
    persistent_failed_constraint_ids: [string]
    preserved_constraint_ids: [string]
    new_uncertain_constraint_ids: [string]

    became_best: boolean
```

说明：

- 首次 generate：
  - `comparison_attempt_id = null`
  - 使用 `initial_*`
  - 不伪造 fixed/regressed
- edit：
  - `comparison_attempt_id = source_attempt_id`
  - transition 必须相对于真实 source 计算

---

### 3.6.2 `earlier_rounds`

更早轮次压缩为：

```yaml
earlier_rounds:
  - action: generate_image | edit_image
    source_attempt_id: string | null
    result_attempt_id: string

    decision_summary: string
    target_constraint_ids: [string]
    preserve_constraint_ids: [string]

    outcome_summary:
      fixed_constraint_ids: [string]
      regressed_constraint_ids: [string]
      persistent_failed_constraint_ids: [string]
      became_best: boolean
```

更早历史默认不再向 Planner 重复提供：

```text
完整 instruction
完整 diagnosis
完整 evaluator 文本
完整 Skill Markdown
```

但底层 immutable artifacts 必须继续完整落盘。

---

### 3.6.3 `best_attempt`

```yaml
best_attempt:
  attempt_id: string
  same_as_latest: boolean

  constraint_results:
    passed_constraint_ids: [string]
    failed_constraint_ids: [string]
    uncertain_constraint_ids: [string]
```

`best_attempt` 独立存在，是为了支持：

```text
latest != best
```

以及：

```json
{
  "source_attempt_id": "historical_best_attempt"
}
```

不要在 `runtime_state` 中重复 best attempt ID。

---

## 3.7 `runtime_state`

```yaml
runtime_state:
  remaining_image_budget: integer

  available_actions:
    - query_skill
    - generate_image
    - edit_image
    - submit_attempt
```

合法动作示例：

```text
首次生成前：
  query_skill
  generate_image

已有图片且预算 > 0：
  query_skill
  generate_image
  edit_image
  submit_attempt

预算 = 0：
  submit_attempt
```

---

## 3.8 Visible Images

图片本体不塞进 PlannerContext 路径字符串，而作为多模态输入提供。

规则：

```text
无 Attempt：
  不传图片

latest == best：
  只传一张图片，并绑定 attempt_id

latest != best：
  同时传：
    LATEST_IMAGE
    BEST_IMAGE
```

每张图片前必须带文本标签：

```text
LATEST_IMAGE: attempt a_003
BEST_IMAGE: attempt a_002
```

---

# 4. Planner Output Schemas

---

## 4.1 `query_skill`

```yaml
action: query_skill

arguments:
  skill_ids: [string]
  target_constraint_ids: [string]
```

示例：

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

不要增加：

```text
decision_summary
skill_requires
reason
```

因为 action + arguments 已经完整表达该步骤目的。

---

## 4.2 `generate_image`

```yaml
action: generate_image

arguments:
  decision_summary: string
  diagnosis_summary: string | null
  target_constraint_ids: [string]
  preserve_constraint_ids: [string]
  generation_instruction: string
```

示例：

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "Regenerate from scratch because the current attempt misses several core constraints, making a fresh layout more reliable than editing.",

    "diagnosis_summary": "The current image has insufficient instance counts and weak chase and depth evidence.",

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

    "generation_instruction": "Create a clean white studio scene with exactly six glass lions..."
  }
}
```

字段含义：

```text
decision_summary
  一个总体决策摘要：
  为什么 generate，以及总体采取什么路线

diagnosis_summary
  可选总体视觉诊断
  首次生成前通常为 null

target_constraint_ids
  本轮要覆盖/重修的 constraints

preserve_constraint_ids
  fresh generation 通常为空

generation_instruction
  直接交给 QianwenImageEditAdapter 的最终 Prompt
```

不要增加：

```text
mode
strategy_tags
skill_ids_used
diagnostic_hypotheses[]
interventions[]
repair_plan[]
change
```

---

## 4.3 `edit_image`

```yaml
action: edit_image

arguments:
  source_attempt_id: string
  decision_summary: string
  diagnosis_summary: string | null
  target_constraint_ids: [string]
  preserve_constraint_ids: [string]
  edit_instruction: string
```

示例：

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",

    "decision_summary": "Return to the historical best instead of continuing from the latest because the latest regressed the glass-lion attribute.",

    "diagnosis_summary": "The previous relation edit was ineffective and too destructive; only motion and depth evidence should be revised.",

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

    "edit_instruction": "Revise attempt a_002 while preserving all correct counts, colors and materials..."
  }
}
```

字段含义：

```text
source_attempt_id
  本次 edit 的真实图片来源

decision_summary
  为什么 edit、为什么选择这个 source、总体路线是什么

diagnosis_summary
  可选的总体视觉问题判断

target_constraint_ids
  本轮明确修复的 constraints

preserve_constraint_ids
  本轮明确保护的 constraints

edit_instruction
  直接交给 QianwenImageEditAdapter 的最终编辑 Prompt
```

---

## 4.4 `submit_attempt`

```yaml
action: submit_attempt

arguments:
  selected_attempt_id: string
  reason_code: string
```

示例：

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

标准提交不增加重复的 `decision_summary`。

仅在未来允许：

```text
reason_code = other
```

时，才考虑可选 `submission_rationale`；本轮实现不必加入。

---

# 5. 已敲定的删除 / 合并决策

| 旧字段 / 候选字段 | 最终处理 | 原因 |
|---|---|---|
| `active_round` | 不暴露给 Planner | round_id / step_id 是 runtime bookkeeping |
| `skill_requires` | 删除 | 与正式 `query_skill` Action 重复 |
| `queried_skill_ids` | 合入 `skill_context.active_skills[]` | 避免分散 |
| `query_target_constraint_ids` | 合入每个 active skill | 直接绑定 Skill 与目标 |
| `retrieved_skill_content` | 合入 `guidance` | 统一 Skill 上下文 |
| `retrieved_experiences` | 删除/迁移 | Capability Skill 进入 skill_context；未来 Decision Experience 另设计 |
| `strategy_tags` | 删除 | 与 decision、target 和 instruction 重复，命名不稳定 |
| `skill_ids_used` | 不设为必填 | 与 active skills 重复，模型自报难验证 |
| `diagnostic_hypotheses[]` | 简化 | 改成一个可选总体 `diagnosis_summary` |
| `interventions[]` | 删除 | 与 target/preserve 和 instruction 重复 |
| `repair_plan[]` | 删除 | 增加中间层，但信息增量低 |
| `change` | 删除 | 具体改变已在最终 instruction 中 |
| `mode` | 删除 | generate action 已隐含无 source |
| `compact_history` | 替换 | 改为 recent_round + earlier_rounds |
| `latest_transition` | 合入 recent_round outcome | 避免单独重复 |
| `constraint_state` | 删除或由 observation/memory 推导 | 与 latest/best/history 高度重复 |
| `runtime_state.latest_attempt_id` | 删除 | 已在 latest_observation |
| `runtime_state.best_attempt_id` | 删除 | 已在 best_attempt |

---

# 6. 真实轨迹在新设计下的动作序列

基准轨迹：

```text
s_000 query_skill
s_001 generate_image              -> a_000
s_002 generate_image              -> a_001
s_003 edit_image(source=a_001)    -> a_002
s_004 edit_image(source=a_002)    -> a_003
s_005 edit_image(source=a_002)    -> a_004
s_006 submit_attempt(a_002)
```

关键要求：

```text
1. regenerate 仍为 generate_image；
2. a_003 是 latest，但 a_002 是 best；
3. s_005 必须允许 source_attempt_id = a_002；
4. a_004 的 transition 必须比较 a_002 -> a_004；
5. 最终可以 submit a_002，而不是 latest a_004。
```

---

# 7. Round-by-Round Planner Input / Output 参考

---

## Step 0 — `query_skill`

### Planner Input

```yaml
planner_context:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    max_image_attempts: 5
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

### Planner Output

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

### Next Input Delta

```yaml
skill_context:
  active_skills:
    - skill_id: counting_and_instance_layout
      target_constraint_ids: [c_001, c_005, c_009]
      guidance: "[full Skill guidance]"
      guidance_level: full

    - skill_id: spatial_relation_layout
      target_constraint_ids: [c_004, c_008]
      guidance: "[full Skill guidance]"
      guidance_level: full
```

不新增 Attempt，不消耗预算。

---

## Step 1 — First `generate_image -> a_000`

### Planner Input

在 Step 0 输入基础上：

```yaml
skill_context:
  active_skills:
    - counting_and_instance_layout
    - spatial_relation_layout
```

其余仍为：

```text
latest_observation = null
episode_memory = empty
remaining_image_budget = 5
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "Generate the first complete scene from scratch using the retrieved counting and spatial guidance.",

    "diagnosis_summary": null,

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

    "generation_instruction": "Create a single scene with exactly one brown donut in the foreground..."
  }
}
```

### Environment Result

```text
attempt = a_000
remaining budget = 4
latest = a_000
best = a_000
```

### Next Input Delta

```yaml
latest_observation:
  attempt_id: a_000
  constraint_results:
    passed_constraint_ids: [...]
    failed_constraint_ids: [...]
    uncertain_constraint_ids: [...]

episode_memory:
  recent_round:
    skill_queries:
      - counting_and_instance_layout
      - spatial_relation_layout

    image_action:
      action: generate_image
      source_attempt_id: null
      decision_summary: "..."
      diagnosis_summary: null
      target_constraint_ids: [...]
      preserve_constraint_ids: []
      instruction: "[full generation instruction]"

    result_attempt_id: a_000
    observed_outcome:
      comparison_attempt_id: null
      initial_passed_constraint_ids: [...]
      initial_failed_constraint_ids: [...]
      initial_uncertain_constraint_ids: [...]
      became_best: true

  best_attempt:
    attempt_id: a_000
    same_as_latest: true
    constraint_results: [...]

runtime_state:
  remaining_image_budget: 4
```

---

## Step 2 — Regeneration `generate_image -> a_001`

### Planner Input

包含：

```text
task_context
latest_observation = a_000
active Skills
recent_round = generation of a_000
best_attempt = a_000
remaining budget = 4
LATEST_IMAGE = a_000
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "generate_image",
  "arguments": {
    "decision_summary": "Regenerate from scratch because the first attempt misses several core constraints, making local editing less reliable.",

    "diagnosis_summary": "The first image has insufficient object counts and weak chase and depth evidence.",

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

    "generation_instruction": "Create a clean white studio scene with exactly one large brown donut..."
  }
}
```

### Next Input Delta

```text
latest_observation = a_001

new recent_round = generation of a_001

old recent_round (a_000)
  -> compressed into earlier_rounds

best_attempt
  -> update if a_001 is better

remaining budget
  4 -> 3
```

---

## Step 3 — `edit_image(a_001) -> a_002`

### Planner Input

包含：

```text
latest_observation = a_001
best_attempt = a_001
recent_round = generate a_001
earlier_rounds = [generate a_000]
LATEST_IMAGE = a_001
remaining budget = 3
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",

    "decision_summary": "Edit the current best because most object and attribute constraints already pass and the remaining failures are localized.",

    "diagnosis_summary": "The image needs two additional distinct lions and stronger pursuit and foreground-depth cues.",

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

    "edit_instruction": "Edit attempt a_001 by adding exactly two additional transparent glass lions..."
  }
}
```

### Next Input Delta

```yaml
latest_observation:
  attempt_id: a_002
  constraint_results: [...]

episode_memory:
  recent_round:
    image_action:
      action: edit_image
      source_attempt_id: a_001
      decision_summary: "..."
      diagnosis_summary: "..."
      target_constraint_ids: [c_001, c_004, c_008]
      preserve_constraint_ids: [...]
      instruction: "[full edit instruction]"

    result_attempt_id: a_002

    observed_outcome:
      comparison_attempt_id: a_001
      fixed_constraint_ids: [c_001]
      regressed_constraint_ids: []
      persistent_failed_constraint_ids: [c_004, c_008]
      preserved_constraint_ids: [...]

  best_attempt:
    attempt_id: a_002
    same_as_latest: true

runtime_state:
  remaining_image_budget: 2
```

---

## Step 4 — `edit_image(a_002) -> a_003`

### Planner Input

包含：

```text
latest = best = a_002
recent_round = edit a_001 -> a_002
earlier_rounds = previous generate rounds
remaining budget = 2
LATEST_IMAGE = a_002
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",

    "decision_summary": "Continue from the current best and restrict the edit to the two remaining relation failures.",

    "diagnosis_summary": "The image lacks sufficiently explicit motion and depth evidence for chasing and cats-behind-donut.",

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

    "edit_instruction": "Adjust only the depth and motion cues..."
  }
}
```

### Environment Result

```text
a_002 -> a_003

regressed:
  c_002

persistent failed:
  c_004
  c_008
```

### Next Input Delta

```text
latest_observation = a_003
best_attempt = a_002
same_as_latest = false
remaining budget = 1

visible images:
  LATEST_IMAGE = a_003
  BEST_IMAGE = a_002
```

---

## Step 5 — Rollback `edit_image(a_002) -> a_004`

### Planner Input

包含：

```text
latest_observation = a_003
recent_round shows c_002 regression
best_attempt = a_002
remaining budget = 1

visible:
  LATEST_IMAGE = a_003
  BEST_IMAGE = a_002
```

### Planner Output

```json
{
  "schema_version": "0.4",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",

    "decision_summary": "Return to the historical best because the latest failed to improve the targets and regressed the glass-lion attribute.",

    "diagnosis_summary": "The previous relation edit was ineffective and too destructive; only motion and depth evidence should be revised.",

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

    "edit_instruction": "Revise attempt a_002 while preserving all correct counts, colors and materials..."
  }
}
```

### Next Input Delta

```text
new attempt = a_004

transition comparison:
  a_002 -> a_004

not:
  a_003 -> a_004

latest = a_004
best remains a_002
remaining budget = 0
available actions = [submit_attempt]
```

---

## Step 6 — `submit_attempt`

### Planner Input

```text
latest = a_004
best = a_002
remaining budget = 0
available actions = [submit_attempt]

visible:
  LATEST_IMAGE = a_004
  BEST_IMAGE = a_002
```

### Planner Output

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

---

# 8. Codex 实现要求

Codex 必须完成：

```text
1. 定义 action_protocol_v0_4 JSON Schema。
2. 定义 PlannerContext v0.4 数据模型。
3. 更新 teacher system/user contract。
4. 更新 PlannerContext renderer。
5. 更新 response parser 与 validator。
6. 更新 reducer：
   - recent_round
   - earlier_rounds
   - best_attempt
   - source-relative transition
7. 更新 SFT trajectory serializer。
8. 删除 v0.2/v0.3 仅为旧字段保留的兼容逻辑。
9. 用真实 phase3_ep_001 做 golden replay。
10. 输出新的 normalized trajectory。
```

不得自行：

```text
增加 regenerate_image
增加 repair_plan
恢复 interventions
恢复 strategy_tags
要求 skill_ids_used
把 active_round 暴露给 Planner
改变 5 次 image budget
更换生成后端
改变 Geneval2 评测逻辑
改变 best-attempt 判定规则
```

---

# 9. 验收标准

必须验证：

```text
1. 每个 Planner turn 只输出一个合法 Action。
2. query_skill 不产生 Attempt、不消耗预算。
3. generate/edit 均调用 QianwenImageEditAdapter。
4. generate 无 source；edit 必须有 source_attempt_id。
5. latest != best 时同时提供两张图片。
6. edit outcome 相对真实 source 计算。
7. recent_round 保留完整 instruction。
8. earlier_rounds 使用压缩格式。
9. budget = 0 时只能 submit。
10. phase3_ep_001 行为序列可完整重放：
    query
    -> generate
    -> generate
    -> edit
    -> regressive edit
    -> rollback edit
    -> submit historical best
```

---

# 10. 最终原则

> Planner 输入固定为任务目标、最新观察、Skill 上下文、分层历史和动态运行状态；Planner 输出固定为一个形式化 Action。generate/edit 只保留一个总体决策摘要、一个可选总体诊断、target/preserve 边界和最终可执行 Prompt。环境负责执行、验证和构造下一轮状态。
