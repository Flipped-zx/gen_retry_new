# Module Contracts：模块输入、输出与所有权

本文件用于阻止模块边界在开发中逐渐混乱。

## 1. Constraint / Rubric Builder

**输入**：原始 prompt、Geneval2 benchmark metadata/rubric。

**输出**：`TaskSpec`，包含 immutable constraints。

**不得做**：调用生成器；预测图片结果；写 attempt memory。

---

## 2. PlannerContext Builder

**输入**：TaskSpec、canonical episode state、artifact refs、tool/skill manifest。

**输出**：版本化 `PlannerContext`；完成图像 round 后可派生并持久化
`RoundRecord` artifact。新 episode 使用 v0.7，历史 v0.6 按原版本回放。

**负责**：task context、latest attempt、active planning round、last/prior
completed image-round memory、v0.7 prior executable instructions、deduplicated
best/latest refs、same-pass historical evidence image refs、budget/control
state、source-based atom/GM outcome comparison，以及按 persisted hash 恢复
retrieval-time Skill observation。

**不得做**：调用 LLM；重写 action；生成新环境事实；把 future evaluator outcome 注入当前 action target。

---

## 3. Retry Planner（Qwen3-VL / Teacher）

**输入**：system policy + PlannerContext + 可见图片 + tool/skill responses。

**输出**：一个符合 `action_protocol_v0_5` 的 JSON action。

**策略要求**：不得盲目复读已失败干预；相同 action/source/targets 在具体
视觉干预发生实质变化时可以再次使用。历史 source 选择必须同时受可见图片
和记录的 atom 证据约束。

**不得输出**：`decision_summary`、`diagnosis_summary`、score、fixed/regressed、best-so-far、路径、seed、API metadata、长诊断报告。

---

## 4. Action Parser / Validator

**输入**：raw assistant text。

**输出**：canonical action 或 structured format error。

**负责**：严格 JSON parse、Schema validate、ID/reference checks。

**不得做**：擅自修补语义字段后继续执行；不得把 raw response 写入 memory。

---

## 5. Skill Store

**输入**：skill IDs、target constraint IDs。

**输出**：短 skill content + version/hash。

**不得做**：写 planner action；自动调用生成器；把完整 skill 永久复制到 episode memory。

---

## 6. Image Execution Profile And Adapters

环境根据 episode 锁定的 execution profile 将逻辑动作确定性路由到本地
adapter。Planner 不选择 backend、model、pipeline 或 mode。

### QwenImageAdapter.generate

**输入**：generation instruction、model config、request ID。

**输出**：new image artifact + backend metadata。

**约束**：只执行 `generate_image`；无 source attempt；创建 root Attempt。

### QianwenImageEditAdapter.edit

**输入**：source image artifact、edit instruction、model config、request ID。

**输出**：edited image artifact + backend metadata。

**约束**：只执行 `edit_image`；source attempt/image 必须存在且 lineage
可追踪；创建 declared source 的 child Attempt。

**共同要求**：幂等 request ID、缓存、artifact hash、完整 profile/model/
pipeline/sampling/source/output provenance、resume profile lock、secret
redaction。当前 accepted profile 为 `qwen_dual_backend@1`。

---

## 7. Geneval2 Adapter

**输入**：TaskSpec constraints + image artifact。

**输出**：canonical per-constraint observation + environment-owned prompt-level
Soft-TIFA GM。

**负责**：标准化 pass/fail/uncertain、expected/observed、correct-answer
probability，以及按冻结公式计算 `geneval2_soft_tifa_gm@flow_dppo_v1`。

**不得做**：决定 edit/regenerate；修改 planner action。

---

## 8. Event Store

**输入**：validated domain events。

**输出**：append-only `events.jsonl`。

**要求**：原子写、去重、事件 ID、schema version、producer、input refs。

---

## 9. State Reducer

**输入**：从 episode 起点开始的 canonical events。

**输出**：EpisodeState、AttemptRecord、constraint/GM transitions、best-so-far。

**要求**：纯函数、确定性、可从头 replay；新 episode 按 pass-count、GM、
更早 Attempt 的顺序选择 best，旧 episode 保持原排序。

**不得做**：LLM 推理；读取外部网络；修改 events。

---

## 10. Experience Miner

**输入**：多 episode 的真实 canonical transitions。

**输出**：统计支持的 Experience Cards。

**不得做**：用单条 reflection 直接创建经验；将未执行动作当效果证据。

---

## 11. SFT Exporter

**输入**：accepted canonical trajectories + images + supervision policy。

**输出**：multi-turn training records + exact loss masks + audit report。

**要求**：只训练 assistant action；同 prompt group 不跨 split；harmful actions 默认不做正 target；记录 token percentiles；按 execution profile
和 PlannerContext/score-policy tuple 分组；从目标动作之前的事件前缀重建输入。

---

## 12. RL Rollout Collector

**输入**：frozen policy checkpoint、fresh train-only TaskSpecs、canonical
PlannerContext、image executors、Geneval2 和 versioned rollout policy。

**输出**：immutable on-policy action samples、token log-probability artifacts、
executed image/evaluator events、exact state/policy hashes 和 prompt/pivot
group IDs。

**要求**：trainable group 内每个 candidate 必须来自同一个 canonical state
和 sampling policy；使用新 request IDs 和 artifact-backed resume；forced
diagnostic candidates 与 policy-gradient candidates 分开。每个 candidate
必须记录逐 Action assistant-token 计数；单个 Action 不得超过 1,400，整条
episode 的 assistant-action 累计不得超过 16,000。每批必须同时记录计划组、
有效组和因基础设施失败排除的组，不能只输出成功子集。

**不得做**：把 Teacher trajectories 标成 on-policy；训练 image backend；
使用 official test prompts；让 environment observations 进入 loss。

---

## 13. RL Reward And Credit Builder

**输入**：canonical executed transitions、environment-owned best/submission、
Geneval2 atom/GM facts、query-to-image attribution 和 versioned reward config。

**输出**：audited terminal、source-relative intervention、best-before-relative
progress、Skill-delayed、episode 和 same-state local advantages。

**要求**：保持 pass-count-first/GM-tie-break 语义；edit 与 declared source
及动作前 reducer-best 分别比较；source-free initial generation 不得伪造
fixed/regressed atoms；延迟 Skill credit 必须守恒；mixed-state、mixed-policy
或 off-policy policy-gradient groups 必须拒绝；zero-variance groups 必须
标记为 loss-zero。策略非法输出可有显式负奖励；后端、传输或 Geneval2
基础设施失败必须在 advantage batch 外重试，不得静默写成合法零分。
naive baseline 必须只使用 submitted terminal utility，禁止暗含 process
reward、call cost、all-pass bonus、submit regret shaping、Skill credit 或 pivot。

**不得做**：修改 reducer best-so-far；奖励 raw tool responses；注入 future
outcome；把 forced action probe 当作 on-policy data。

---

## 14. RL Trainer Adapter

**输入**：action-token masks、old/current/reference log-probabilities、versioned
advantage batches 和 optimizer/runtime config。

**输出**：resumable policy checkpoints，以及 active reference-KL、entropy、
clipping、action、reward-component 和 validation metrics。

**要求**：只训练 canonical assistant action tokens；optimizer batch 绑定
source hashes；old/reference log-prob 必须与 sampled token artifact 对齐；
raw sampled response、sampled token、mask、old/reference log-prob、event 和
reward artifact 必须逐文件验 hash；rollout group/candidate digest 必须与
return batch 交叉绑定；sampling config digest、checkpoint digest、policy
revision、candidate uniqueness/count 和 token-mask 长度必须在 optimizer
admission 前验证；reference-KL 不得是 inert config；checkpoint optimizer/
sampler state；保持 prompt-group split。rollout 与优化使用 staged topology：
先释放 policy/image/Geneval2 rollout services，再让全部八张卡进入 FSDP。
任何 verl tensorization 必须消费 `prepare_optimizer_batch` 的输出，不得直接
信任框架内部重算的 old/reference log-prob。W&B 配置必须脱敏，offline smoke
不要求 API key；online 只从环境变量读取凭据。

**阶段准入**：有效组比例至少 0.95、policy-invalid candidate 比例至多
0.05、zero-variance 组比例至多 0.35。前三者分别在 rollout admission 和
optimizer admission 中 fail closed。runtime preflight 只在自定义 adapter
的六项 typed test report 通过后返回 `READY_FOR_SMOKE`；只有 hash-bound
32-group resume/replay 报告通过后才返回 `READY_FOR_OPTIMIZATION`。所有
evidence ref 必须解析在 repository root 内；optimization gate 必须重验
rollout/advantage Schema、重跑 admission/advantage/optimizer join，并以重算
计数核对 smoke report。

**不得做**：通过 Qwen image execution、Geneval2、tool responses、image
observations 或 reducer facts 反向传播。
