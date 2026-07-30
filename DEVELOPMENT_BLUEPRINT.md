# Gen-Retry v3：Rubric / Geneval2 驱动的多轮图像 Retry Agent 开发蓝图

## 0. 一句话目标

训练一个 verifier-grounded、image-aware、history-aware 的图像 retry policy：

```text
原始 Prompt + 固定原子约束
+ 当前/历史图片
+ Geneval2 atom feedback
+ Geneval2 prompt-level GM（pass-count 相同时用于 best tie-break）
+ canonical attempt memory
+ skill/tool manifest
+ remaining budget
→ query_skill / generate_image / edit_image / submit_attempt
```

它学习的不是“再写一遍 Prompt”，而是：选择动作、选择 source attempt、选择修复/保留约束、构造本轮可执行图像指令，并在非单调结果中恢复或提交历史最优。

---

## 1. 研究边界

### 当前主问题

单个 Prompt 内的多次生成/编辑如何构成可训练、可回放、可溯源的序贯决策轨迹。

```text
state_t
→ planner action_t
→ environment-owned image execution
→ image I_t
→ Geneval2 V_t
→ deterministic transition Δ_t
→ state_{t+1}
```

训练对象：`state_t → action_t`。

### 第一阶段不扩张为主问题

- 搜索/OOD grounding；
- 多 Agent 大型系统；
- 训练图像模型本体；
- 自由文本长 reflection；
- 立即进行 RL；
- 让 Planner 预测 score、fixed/regressed、best-so-far 等环境事实。

---

## 2. 固定组件

| 组件 | 职责 | 训练 |
|---|---|---:|
| Qwen3-VL-8B-Instruct | Retry policy / planner | 后续 SFT，可能 RL |
| Qwen-Image-2512 | 执行 source-free 生成和重新生成 | 冻结 |
| Qwen-Image-Edit-2511 | 执行有 source 的图像编辑 | 冻结 |
| Geneval2 | Rubric / atom-level evaluator | 冻结 |
| GPT-5.5 Teacher API | Pilot action、SFT teacher、有限 review | 外部服务 |
| Event Store + Reducer | Canonical memory | 程序逻辑 |
| Skill Store | 按需返回短 Skill | 程序工具 |

关键口径：

```text
generate_image → Qwen-Image-2512（无 source）
edit_image     → Qwen-Image-Edit-2511（有 source_image）
```

逻辑动作不能合并，因为 source、风险、保存约束和训练信用不同。Planner
只选择逻辑动作；环境通过独立版本化的 execution profile 选择 backend，
backend/model/mode 不进入 SFT target。

---

## 3. 一条 Episode 的真实循环

```text
Prompt P
→ Constraint/Rubric Builder
→ TaskSpec(P, C={c1...cn})
→ PlannerContext S0
→ Planner emits one action A0
→ Environment validates A0
→ Execution profile routes and executes A0
→ Image I0
→ Geneval2 evaluates every ci
→ Reducer creates Attempt a0, transition, best-so-far, compact memory
→ PlannerContext S1 (image + V0 + round memory + budget)
→ Planner emits A1
→ ...
→ submit_attempt(selected historical attempt)
```

### 每一轮内部

```text
[Agent Input]
TaskSpec + visible images + latest feedback + active round + round memory
+ tool/skill manifest + budget
        ↓
[Agent Output]
一个 action JSON
- action type
- target constraints
- preserve constraints
- source attempt（edit 时）
- decision summary / diagnostic hypotheses / interventions
- 本轮 generation/edit instruction
        ↓
[Environment]
Schema validation → executor → image → Geneval2
        ↓
[Memory]
fixed / regressed / persistent / stable pass
+ lineage + best-so-far + remaining budget
        ↺
```

### Refine Prompt 的位置

不设置单独的 `refine_prompt` 工具。每次 `generate_image` 或 `edit_image` 的 action 参数中，必须包含本轮可执行指令。否则会制造无必要的多一轮轨迹和信用分配问题。

---

## 4. 动作集合

新 rollout / SFT 正式 Schema：`schemas/action_protocol_v0_5.schema.json`。v0.2-v0.4 仅保留历史事件兼容。

### query_skill

读取与当前失败状态匹配的短技能内容。Skill 只进入 working context，不永久复制进 memory。

### generate_image

用于初始生成或从头重生成。无 source image。

### edit_image

基于一个明确的历史 attempt 局部修改。必须指定 `source_attempt_id`、修复约束、保存约束和编辑指令。

### submit_attempt

提交任意历史 attempt，不要求是 latest。

---

## 5. 信息所有权

### Planner 拥有

- action type；
- source attempt 选择；
- target/preserve constraint IDs；
- skill 查询；
- target/preserve constraint IDs 与统一的 generation/edit `instruction`；
- submit 选择。

### Environment 拥有

- 图片 artifact；
- Geneval2 pass/fail/uncertain；
- observed/expected；
- scores；
- fixed/regressed/persistent/new fail；
- best-so-far；
- remaining budget；
- parent lineage；
- API metadata；
- schema validity。

Planner 不得把环境事实当成待预测 target。

新 episode 的 best 排序由环境固定为：
`higher pass-count → higher Soft-TIFA GM → earlier Attempt`。GM 不是 Action
字段，也不能让更少 pass-count 的 Attempt 取代更多 pass-count 的 Attempt。

---

## 6. Canonical Memory

### 6.1 Event sourcing

所有事实先写不可变事件 `events.jsonl`，再由纯函数 reducer 生成：

- `episode_state.json`
- `planner_context.json`

禁止 Planner 直接写 Memory；禁止 raw assistant response 进入持久 Memory。

### 6.2 Attempt record 最小内容

```text
attempt_id / parent_attempt_id
canonical action
source image / output image artifact
Geneval2 constraint results
action outcome transition
best-so-far state
strategy lineage
```

### 6.3 Compact Planner View

必留：latest、best-so-far、最近 transition、regression 点、strategy switch 点、remaining budget。

折叠：无状态变化的重复尝试、旧 raw prompts、完整 raw Geneval2 行、旧 tool payload。

---

## 7. Experience

### Episode Memory

当前 prompt 内的可验证 action–outcome 历史。

### Cross-task Experience Card

只有在多条真实 transition 支持后才生成：

```text
failure signature
→ preferred action / strategy
→ target fix rate / regression rate
→ backend/tool scope
```

经验以结构化字段为主，可附一句不超过 50 tokens 的摘要。不得把单条 teacher reflection 直接当作 lifelong experience。

---

## 8. 仓库边界与模块结构

v3 使用全新 clean-room Git 仓库。旧 Gen-Retry、Gen-Searcher、GenEvolve 和 Geneval2 通过本地路径作为只读证据源，不与 v3 源码混放，也不作为生产时隐式依赖。

```text
agentic_image/
├── gen-retry-v3/          # 当前新仓库，唯一写入根
├── gen-retry-legacy/      # 旧实现，只读
├── Gen-Searcher/          # 参考仓库，只读
├── GenEvolve/             # 参考仓库，只读
└── Geneval2/              # evaluator 环境/源码
```

外部路径统一由 `configs/paths/local.yaml` 配置；Phase 0 把可复用证据记录到 `docs/SOURCE_LEDGER.md` 和架构映射文档。

### v3 模块结构

```text
gen-retry-v3/
├── AGENTS.md
├── .codex/
├── configs/
├── docs/
├── schemas/
├── skills/
├── src/gen_retry/
│   ├── domain/
│   ├── protocol/
│   ├── agent/
│   ├── tools/
│   │   ├── qianwen_image_edit_adapter.py
│   │   ├── geneval2_adapter.py
│   │   └── skill_store.py
│   ├── runtime/
│   ├── data/
│   ├── analysis/
│   └── cli/
├── tests/
├── runs/
└── reports/
```

核心 adapters：

```python
class QwenImageAdapter:
    def generate(self, instruction, request_id, config): ...

class QianwenImageEditAdapter:
    def edit(self, source_image, instruction, request_id, config): ...
```

上层 action protocol 不绑定具体 SDK。

---

## 9. 五条真实 Pilot

A. Direct success：`generate → all pass → submit`

B. Monotonic regenerate：`generate → global fail → regenerate → pass`

C. Local edit：`generate → one local fail → edit → pass`

D. Non-monotonic recovery：`a0 good → a1 fixes target but regresses → branch from a0 → a2 pass`

E. Persistent failure：`retries fail → budget exhausted → submit best historical attempt`

每条必须自动和人工分析：action legality、target/preserve、source correctness、history use、instruction quality、target fix、regression、repeated strategy、branching、final selection、provenance。

---

## 10. SFT

真实 multi-turn messages：

```text
system
user(TaskSpec + images + planner view)
assistant(canonical action JSON)       ← train
tool(skill/image/evaluator/memory)     ← mask
assistant(next canonical action JSON)  ← train
...
```

仅训练 assistant canonical action tokens。

Harmful action：作为环境历史事实保留，默认不作为正向 target；其后的正确 recovery action 作为 target。

同一 original prompt 的所有 attempts 必须在同一 split。

---

## 11. 第一次 SFT 七个问题的自动防回归

1. 一个 discriminated action union，不再多套大 JSON。
2. action-only target，不生成长诊断报告。
3. raw output 只做 parse + schema/reference/runtime validation；通过者按原 JSON 作为 canonical action 记录；不得补字段、改 action、改引用，且 raw 禁止进入 Memory。
4. 环境事实与模型决策严格分离。
5. Skill 必须是真实 query/tool response。
6. Schema、parser、prompt、fixtures、exporter 版本一致并有 contract tests。
7. 明确 loss mask、harmful/recovery supervision、token audit 和截断检查。

---

## 12. 开发顺序与门禁

### Phase 0 — External Repository Archaeology

在新仓库中只读检查外部 legacy/source roots，建立 reuse/migrate/retire 映射。所有报告写入新仓库；禁止修改外部仓库或直接让 v3 运行时依赖旧源码。

### Phase 1 — Protocol Freeze（Gate 1）

冻结 TaskSpec、Action、Event、Planner View、Artifact IDs、backend semantics。

### Phase 2 — Mock Replay Runtime

实现 parser、validator、event store、reducer、planner view、fake executor、fake Geneval2，确保 deterministic replay。

### Phase 3 — Five Live Pilots（Gate 2）

接入真实 Qianwen-Image-Edit、Geneval2、Teacher API，运行五条并分析。

### Phase 4 — SFT Supervision Freeze（Gate 3）

冻结消息模板、loss mask、target selection、harmful/recovery policy、token budget。

### Phase 5 — Dataset Build

批量构建、质量过滤、split、审计报告。

每一 Gate 只让高层 reviewer 审查核心不可逆问题，其他工作由 5.5 High/XHigh 执行。
