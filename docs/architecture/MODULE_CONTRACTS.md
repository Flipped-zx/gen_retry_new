# Module Contracts：模块输入、输出与所有权

本文件用于阻止模块边界在开发中逐渐混乱。

## 1. Constraint / Rubric Builder

**输入**：原始 prompt、Geneval2 benchmark metadata/rubric。

**输出**：`TaskSpec`，包含 immutable constraints。

**不得做**：调用生成器；预测图片结果；写 attempt memory。

---

## 2. Planner View Builder

**输入**：TaskSpec、canonical episode state、artifact refs、tool/skill manifest。

**输出**：短的 `PlannerView`。

**负责**：latest/best image refs、latest feedback、compact history、budget。

**不得做**：调用 LLM；重写 action；生成新环境事实。

---

## 3. Retry Planner（Qwen3-VL / Teacher）

**输入**：system policy + PlannerView + 可见图片 + tool/skill responses。

**输出**：一个符合 `action_protocol_v0_2` 的 JSON action。

**不得输出**：score、fixed/regressed、best-so-far、路径、seed、API metadata、长诊断报告。

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

## 6. QianwenImageEditAdapter

统一底层后端。

### generate

**输入**：generation instruction、model config、request ID。

**输出**：new image artifact + backend metadata。

**约束**：无 source attempt。

### edit

**输入**：source image artifact、edit instruction、model config、request ID。

**输出**：edited image artifact + backend metadata。

**约束**：source attempt/image 必须存在且 lineage 可追踪。

**共同要求**：幂等 request ID、缓存、超时、重试、artifact hash、secret redaction。

---

## 7. Geneval2 Adapter

**输入**：TaskSpec constraints + image artifact。

**输出**：canonical per-constraint observation。

**负责**：标准化 pass/fail/uncertain、expected/observed、confidence（若有）。

**不得做**：决定 edit/regenerate；修改 planner action。

---

## 8. Event Store

**输入**：validated domain events。

**输出**：append-only `events.jsonl`。

**要求**：原子写、去重、事件 ID、schema version、producer、input refs。

---

## 9. State Reducer

**输入**：从 episode 起点开始的 canonical events。

**输出**：EpisodeState、AttemptRecord、constraint transitions、best-so-far。

**要求**：纯函数、确定性、可从头 replay。

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

**要求**：只训练 assistant action；同 prompt group 不跨 split；harmful actions 默认不做正 target；记录 token percentiles。
