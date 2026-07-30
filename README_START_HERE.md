# Gen-Retry v3 Codex 开发启动包（v0.3，新仓库版）

本版本默认采用**全新 Git 仓库**开发，不再把启动包覆盖到旧 `gen-retry` 仓库中。旧项目、Gen-Searcher、GenEvolve 与 Geneval2 只作为只读证据源，通过显式路径配置供 Codex 考古和复用。


## 固定系统口径

```text
Policy model       : Qwen3-VL-8B-Instruct（后续 SFT）
Image execution    : qwen_dual_backend@1
Generate backend   : Qwen-Image-2512（source-free generation / restart）
Edit backend       : Qwen-Image-Edit-2511（source-conditioned editing）
Evaluator          : Geneval2 atom-level verifier
Teacher            : GPT-5.5 API（Pilot / SFT teacher）
Persistent state   : immutable events + deterministic reducer
Agent actions      : query_skill / generate_image / edit_image / submit_attempt
```

`generate_image` 与 `edit_image` 是不同的逻辑动作，并由环境按执行配置确定性路由：

```text
generate_image → Qwen-Image-2512（无 source，创建 root Attempt）
edit_image     → Qwen-Image-Edit-2511（必须有 source，创建 child Attempt）
```

Planner 不输出 backend、model 或 mode；这些均为环境 provenance。动作协议和
Action Protocol 仍为 v0.5；PlannerContext v0.6 额外暴露环境计算的
Geneval2 prompt-level GM，并只在 atom pass-count 相同时用于 best
tie-break。执行配置独立版本化为 `qwen_dual_backend@1`。

## 你现在要做的事情

1. 在旧仓库旁边创建全新的 `gen-retry-v3` 目录。
2. 将本启动包内容复制到新目录，不要覆盖旧仓库。
3. `git init` 并提交一次仅含启动包的 bootstrap commit。
4. 复制路径模板：

```bash
cp configs/paths/legacy_repos.example.yaml configs/paths/local.yaml
```

填写旧项目、Gen-Searcher、GenEvolve、Geneval2 的绝对路径。`local.yaml` 不提交。

5. 复制模型配置：

```bash
cp configs/models/local.example.yaml configs/models/local.yaml
```

填写部署名称与本地配置；密钥只放环境变量。

6. 配置 Codex 执行者和 reviewer：

```bash
python scripts/configure_codex_agents.py \
  --executor-model '<你的 Codex 5.5 模型 ID>' \
  --reviewer-model '<你的高层 reviewer / 5.6 模型 ID>'
```

7. 从**新仓库根目录**启动 Codex，先执行 `CODEX_FIRST_PROMPT.md`，只做 Phase 0。

## 新仓库为什么更合适

- 不与旧版同名文件、旧 Schema、旧 Prompt 和旧 SFT exporter 混在一起；
- v3 可以从一开始保持事件溯源、严格 Schema 与 action-only target；
- 旧实现仍可按文件级证据复用，而不是整仓迁移；
- 失败时容易回退，不会破坏旧实验环境；
- 更容易向老师展示一条干净、可复现的实现主线。

## Codex 如何读取旁边的旧仓库

Codex 应从新仓库启动，并通过 `configs/paths/local.yaml` 中的绝对路径读取旧仓库。旧目录在项目规则中被声明为只读；普通实现只写新仓库。

启动后先运行 `/status` 检查 workspace。不要对旧仓库使用 `--add-dir`，除非你明确希望赋予额外写权限；`--add-dir` 的语义是增加可写目录。

若运行环境不允许直接读取 workspace 外目录，优先方案是：

1. 针对具体文件批准只读访问；或
2. 在新仓库 `references/manifests/` 中保存路径、commit、符号和摘要；或
3. 制作只读 source snapshot，而不是把旧代码复制进 `src/`。

## 开发顺序

```text
New Repo Bootstrap
→ External Source Map
→ Repository Archaeology
→ Protocol Freeze
→ Mock Replay Runtime
→ 5 条真实 Pilot
→ Pilot Review
→ SFT Supervision Freeze
→ 批量轨迹构建
```

## 重要文件

- `NEW_REPO_BOOTSTRAP.md`：新目录与 Git 初始化命令。
- `AGENTS.md`：Codex 项目级长期规则。
- `DEVELOPMENT_BLUEPRINT.md`：目标、模块、协议和阶段。
- `configs/paths/legacy_repos.example.yaml`：外部只读源码路径模板。
- `docs/architecture/MODULE_CONTRACTS.md`：每个模块输入、输出、所有权。
- `schemas/`：协议唯一真值。
- `examples/one_episode_trajectory.jsonl`：可回放多轮轨迹。
- `tasks/`：按顺序交给 Codex 的开发任务。
- `docs/SOURCE_LEDGER.md`：已 ground 的外部经验。

## 本包明确不做的事情

- 不修改旧仓库；
- 不包含 API key；
- 不直接调用 Qianwen-Image-Edit、Geneval2 或 Teacher API；
- 不在 Protocol Freeze 前批量生成 SFT 数据；
- 不允许把旧版大 JSON target 原样迁入 v3。
