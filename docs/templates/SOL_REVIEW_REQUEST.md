# SOL_REVIEW_REQUEST

## Gate

`SFT Supervision Freeze`

## Decision to review

是否可以把规则合成的 Geneval2-compatible prompt/VQA 数据作为主要 SFT 来源，同时把官方 800 条 Geneval2 全部保留为最终测试集。

## Current evidence

- Relevant schema/ADR: `docs/phase4/sft_supervision_freeze.md`,
  `docs/phase5/geneval2_synthetic_prompt_pool_review.md`,
  `artifacts/phase5/geneval2_synthetic_prompt_review_samples.jsonl`.
- Minimal test/pilot summary: 6 条设计样例已通过现有
  `task_spec_from_geneval2_row` 解析，覆盖
  `attribute/count/object/position/verb`，与官方 800 条无 prompt 精确重复；
  尚未进行图像生成或 VQA 评估。
- Conflicting evidence, if any: 原始 GenEval 有官方规则采样器；GenEval2
  只发布固定 800 条数据与评估代码，没有官方 prompt 扩充器。当前 Phase 4
  按原始 prompt hash 分组，而大规模合成数据需要按语义家族分组。

## Questions（最多 3 个）

1. 判断合成数据是否可用，哪些问题可由静态/schema review 发现，哪些必须真实生成图像并运行 Geneval2 evaluator？
2. 最小但足以支持扩大到 SFT 规模的 pilot 应如何抽样、人工 review 和设定通过门槛？
3. 为避免测试泄漏、模板过拟合和 evaluator gaming，训练/验证/测试边界及语义家族去重应采用什么最小充分方案？

## Explicit non-goals

- 不审查生成器具体代码实现。
- 不重新设计 Geneval2 evaluator。
- 不决定最终 SFT 数量或训练超参数。

## Expected response

- blocking issues only;
- recommended decision;
- risks and one minimal validation experiment;
- no code implementation.
