# Phase 0 — External Repository Archaeology

## Goal

在全新 v3 仓库开始写 runtime 前，对配置的外部只读源码建立可验证实现地图，并明确哪些内容 reuse、adapt、rewrite 或 retire。

## Inputs

- `configs/paths/local.yaml`
- legacy Gen-Retry root
- Gen-Searcher root
- GenEvolve root
- Geneval2 root / environment path

## Required outputs（全部写入当前新仓库）

1. `docs/architecture/external_repo_inventory.md`
2. `docs/architecture/legacy_to_v3_field_map.md`
3. `docs/architecture/reuse_adapt_rewrite_retire_matrix.md`
4. 更新 `docs/SOURCE_LEDGER.md`
5. `docs/architecture/implementation_gap_report.md`
6. `docs/architecture/phase1_file_plan.md`

## 每个外部根必须记录

- absolute path；
- repository / non-repository status；
- current commit、branch、dirty status（如适用）；
- license；
- inspected paths and symbols；
- expected reuse type；
- whether copying code is legally and architecturally appropriate。

## 必查内容：legacy Gen-Retry

- Geneval2 运行入口、结果 schema、normalizer；
- Qianwen-Image-Edit 生成与编辑调用方式、输入图片格式、输出 artifact；
- 旧 trajectory builder；
- raw assistant / canonical action 处理；
- best-so-far、fixed/regressed、lineage；
- turn mask / loss mask；
- SFT exporter；
- resume/cache/job manifest；
- 第一次 SFT 七个问题在代码中的具体位置。

## 必查内容：Gen-Searcher / GenEvolve

使用 `source_researcher` 做精准只读考古，优先查：

- messages / tool-call trajectory 的真实序列化；
- tool observation masking；
- heavy image generation 与 agent rollout 的解耦；
- skill retrieval / tool schema；
- replay、resume、cache、artifact provenance；
- SFT/RL 数据导出边界。

只记录 exact path、symbol、commit、license 和可落地接口经验，不写宽泛论文总结。

## Repository boundary

- 当前 v3 仓库：允许在 `docs/` 写 Phase 0 报告；
- 所有 external roots：严格只读；
- 不在 v3 `src/` 中创建指向 legacy 源码的 symlink；
- 不做 editable install 指向 legacy repo；
- 不复制代码，Phase 1 冻结后再根据证据决定。

## Constraints

- 不调用外部 API；
- 不生图；
- 不运行 Geneval2；
- 不改 schema；
- 不开始 runtime 重构；
- 不触发高层 reviewer，除非来源冲突直接阻塞 Protocol Freeze。

## Done when

- 每个 reuse/adapt/rewrite/retire 判断都有 path+symbol+commit/license 证据；
- 已确认所有 external roots 未被修改；
- Phase 1 可以只在新仓库内完成；
- `phase1_file_plan.md` 给出精确文件、接口、测试和迁移顺序。
