# SOURCE_LEDGER

目的：将已经确认的外部经验固化，开发时不反复浪费上下文重新搜索。具体代码复用仍须在 Phase 0 记录 commit hash、文件路径和许可证。

| Source | Evidence | 可借鉴 | 不直接照搬 | 状态 |
|---|---|---|---|---|
| Gen-Searcher paper + `tulerfeng/Gen-Searcher` | repository-grounded / paper-grounded | Agent action 与工具 observation 交替；SFT/RL 与重型图像执行解耦；只训练 agent 输出 | 搜索工具、OOD 任务本身不是本项目主线 | Phase 0 补 exact paths/commit |
| GenEvolve paper + `MeiGen-AI/GenEvolve` | repository-grounded / paper-grounded | 真实 tool calls；skill 查询；结构化 program；best/worst 轨迹差异形成经验 | 其轨迹主要是生成前搜索/参考编排；本项目是生成后 retry | Phase 0 补 exact paths/commit |
| GenAgent paper | paper-grounded | image observation 与 assistant action interleaving；环境 image token 不作为 agent target | free-form self-judge + prompt rewrite；无外部 atom verifier | 本地论文/报告补 section |
| GEMS paper | paper-grounded | compressed memory 优于 raw thought；skill/memory 工程 | 最终仍是 history-conditioned rewrite；经验自由文本比例较高 | 本地论文/报告补 section |
| RS-Gen paper | paper-grounded | generate-review-correct；generate/edit 逻辑动作；terminal visual anchoring | training-free prompted workflow；未公开可训练 message schema | 已阅读，Phase 0 记录本地路径 |
| Codex AGENTS.md official docs | official-doc-grounded | root `AGENTS.md` 持久项目指令；分层覆盖 | 不把所有开发文档塞入 AGENTS.md，避免大小限制 | verified 2026-07-14 |
| Codex Subagents official docs | official-doc-grounded | `.codex/agents/*.toml` project agents；model/reasoning/sandbox 可配置 | exact model ID 必须由本地可用模型决定 | verified 2026-07-14 |

## Phase 0 写入格式

```text
source_name:
repository_url:
commit_hash:
license:
exact_paths:
  - path: ...
    symbol: ...
borrowed_idea:
local_adaptation:
copy_code: yes/no
notes:
```
