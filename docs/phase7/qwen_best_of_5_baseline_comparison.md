# Qwen-Image Best-of-5 Baseline 与 200 条 Retry 轨迹对比

## 结论

在完全对齐的 200 个 prompt / 1,419 个 Geneval2 atom 上，Agent 提交结果相对 Qwen-Image 原始 prompt、5 次独立生成后按最高 Soft-TIFA GM 取优的 baseline，增加 **+259 个通过 atom**，GM 提升 **+41.97 分**，全通过轨迹增加 **+69 条**。

这个提升在更严格的 pass-count-first baseline 重选下仍然成立：Agent 仍多通过 229 个 atom，GM 高 42.36 分。因此主结论不是由两边 selector 不一致造成的。

## 主结果

| 指标 | Qwen Best-of-5（最高 GM） | Agent 首图 | Agent 提交 | Agent - Baseline |
| --- | ---: | ---: | ---: | ---: |
| 通过 atoms | 1042/1419 | 1159/1419 | 1301/1419 | +259 |
| Atom pass rate | 73.43% | 81.68% | 91.68% | +18.25 points |
| Soft-TIFA AM | 74.32 | 81.87 | 90.90 | +16.58 |
| Soft-TIFA GM | 31.53 | 42.58 | 73.50 | +41.97 |
| 全通过轨迹 | 42/200 | 51/200 | 111/200 | +69 |
| 图像调用数 | 1000 | 200 | 684 | -316 |

- 失败 atom 从 377 降到 118，减少 68.70%。
- 全通过率从 21.00% 升到 55.50%，绝对提升 +34.50 points，相对增加 164.29%。
- 配对 episode bootstrap 95% 区间：atom pass-rate 增量 [15.87, 20.67] points，GM 增量 [35.90, 47.95]，全通过率增量 [27.50, 41.50] points。

## 配对胜负

- Pass count：Agent 更高 136 条、持平 53 条、更低 11 条。
- GM：Agent 更高 169 条、更低 31 条。
- 按项目冻结的 pass-count-first 比较：Agent 胜 167 条，负 33 条。
- 全通过迁移：baseline 未全过但 Agent 全过 74 条；baseline 全过但 Agent 未全过 5 条。

## 难度分层

| 难度 | Episodes | Baseline atoms | Agent atoms | Δatoms | Baseline GM | Agent GM | ΔGM | 全通过变化 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| easy | 75 | 312/374 | 346/374 | +34 | 55.93 | 80.19 | +24.26 | 34 -> 55 |
| medium | 75 | 392/556 | 516/556 | +124 | 21.31 | 73.05 | +51.74 | 8 -> 39 |
| hard | 50 | 338/489 | 439/489 | +101 | 10.28 | 64.15 | +53.87 | 0 -> 17 |

提升主要集中在 medium/hard：两层分别增加 124 和 101 个通过 atom；hard baseline 没有全通过样本，Agent 达到 17/50。

## Atom 类型

| 类型 | Total | Baseline pass | Agent pass | Δpass | Pass-rate Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| object | 459 | 451 (98.26%) | 455 (99.13%) | +4 | +0.87 points |
| attribute | 304 | 213 (70.07%) | 282 (92.76%) | +69 | +22.70 points |
| count | 459 | 267 (58.17%) | 395 (86.06%) | +128 | +27.89 points |
| position | 175 | 106 (60.57%) | 159 (90.86%) | +53 | +30.29 points |
| verb | 22 | 5 (22.73%) | 10 (45.45%) | +5 | +22.73 points |

绝对增量最大的是 count（+128），其次是 attribute（+69）和 position（+53）。Verb 从 5/22 提升到 10/22，但最终仍只有 45.45%，仍是最明显的内容瓶颈。

## Selector 敏感性

新增 JSON 用最高 GM 选图；项目 reducer 则先比较 pass count。两种规则在 24/200 条上选择不同图片。

| Baseline 选择规则 | Passed atoms | Atom pass rate | AM | GM | 全通过 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 最高 GM | 1042/1419 | 73.43% | 74.32 | 31.53 | 42/200 |
| Pass count -> GM -> earlier | 1072/1419 | 75.55% | 76.06 | 31.14 | 42/200 |

协议对齐选择器让 baseline 多保留 30 个通过 atom，但平均 GM 略降 0.40 分。即使用这个更强的 atom-pass baseline，Agent 仍增加 229 个通过 atom。

## Best-of-K 采样收益

| 前 K 张按最高 GM 取优 | Atom pass rate | AM | GM | 全通过 |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 65.19% | 66.54 | 18.32 | 22/200 |
| 2 | 68.99% | 70.32 | 23.71 | 30/200 |
| 3 | 71.32% | 72.23 | 27.50 | 36/200 |
| 4 | 72.23% | 73.19 | 29.31 | 38/200 |
| 5 | 73.43% | 74.32 | 31.53 | 42/200 |

从第 1 个候选到 Best-of-5，baseline 自身 GM 提高 13.22 分、atom pass rate 提高 8.25 points、全通过增加 20 条。因此当前 baseline 已包含明显的随机采样取优收益，不应与后续真正的单次生成 baseline 混称为同一口径。

## 提升来源的描述性拆分

- Baseline Best-of-5 -> Agent 首图：+117 atoms，GM +11.05，全通过 +9。
- Agent 首图 -> Agent 最终提交：+142 atoms，GM +30.92，全通过 +60。

算术上，总 atom 增量 259 中有 117 出现在 Agent 首图阶段，142 来自后续 retry；总 GM 增量 41.97 中有 11.05 出现在首图，30.92 来自 retry。这不是因果归因：首图 prompt、采样配置和 baseline 的 Best-of-5 选择都没有被独立控制。

## Agent 落后样本

Agent 有 11 条的提交 pass count 低于 Best-of-5 baseline。逐条列出，便于后续诊断：

| Episode | Tier | Baseline pass | Agent pass | Δpass | Baseline GM | Agent GM |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| phase3_ep_147 | easy | 5/6 | 3/6 | -2 | 41.39 | 8.95 |
| phase3_ep_162 | easy | 4/4 | 3/4 | -1 | 95.74 | 6.74 |
| phase3_ep_042 | easy | 4/5 | 3/5 | -1 | 85.57 | 6.06 |
| phase3_ep_149 | medium | 8/8 | 7/8 | -1 | 97.15 | 21.59 |
| phase3_ep_098 | easy | 5/5 | 4/5 | -1 | 96.67 | 30.15 |
| phase3_ep_087 | hard | 7/9 | 6/9 | -1 | 22.96 | 1.47 |
| phase3_ep_171 | easy | 6/6 | 5/6 | -1 | 99.91 | 82.11 |
| phase3_ep_100 | medium | 6/6 | 5/6 | -1 | 100.00 | 82.88 |
| phase3_ep_138 | easy | 3/4 | 2/4 | -1 | 7.42 | 2.35 |
| phase3_ep_107 | easy | 3/5 | 2/5 | -1 | 2.59 | 7.26 |
| phase3_ep_199 | hard | 9/10 | 8/10 | -1 | 27.92 | 70.67 |

最大正向 atom 增量的五条：

| Episode | Tier | Baseline pass | Agent pass | Δpass | ΔGM |
| --- | --- | ---: | ---: | ---: | ---: |
| phase3_ep_070 | medium | 3/8 | 8/8 | +5 | +96.16 |
| phase3_ep_008 | hard | 5/10 | 10/10 | +5 | +91.85 |
| phase3_ep_013 | medium | 3/8 | 8/8 | +5 | +90.56 |
| phase3_ep_109 | medium | 1/7 | 6/7 | +5 | +82.79 |
| phase3_ep_144 | hard | 4/10 | 9/10 | +5 | +73.29 |

## 口径与限制

- 对齐验证：200/200 prompt 文本和 VQA 列表逐项完全一致；selection SHA256 为 `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`，baseline SHA256 为 `528398c655a02f59b772ff958d354f12458a7bec36aebe5aba28b70b555da30a`。
- `evaluation_detail.json` 没有 prompt_id，当前按 JSON key `0..199` 对齐 selection rank `1..200`；完全一致的 prompt/VQA 提供了内容校验，但后续产物应显式写入 prompt_id。
- Baseline 文件没有保存 Qwen-Image 的 model revision、steps、resolution、seed、negative prompt、运行 commit 或 evaluator version；因此不能把差异归因到 Agent policy 本身，也不能声称严格等算力。
- Baseline 固定生成 1,000 张；Agent 共 684 次图像调用（253 generate + 431 edit），少 31.60%。但 generate 和 edit 单次成本未在 baseline 文件中对齐，图像调用数不等于精确 FLOPs 或 GPU-seconds。
- Baseline atom 概率存在最大 1.14e-07 的数值越界；分析在验证其小于容差后 clamp 到 [0,1]。两位小数展示不受影响。
- Bootstrap 区间只衡量这个固定配对 cohort 对 episode 重采样的稳定性。200 条是按分布设计选出的固定集合，不是 IID 样本，区间不能支持对任意真实 prompt 的泛化声明。

## 总体判断

当前证据支持：在这 200 条固定 Flow-DPPO synthetic-train prompt 上，完整 retry 系统相对原始 prompt 的 Qwen-Image Best-of-5 有大幅且分层一致的综合提升，并且用了更少的图像调用。提升在 pass-count 对齐 selector 后仍然稳健。

当前证据不支持：把全部增量解释为 history-aware retry 的独立因果效果。下一步单次生成 baseline 应保留完整 execution profile，并至少加入：原始 prompt 单次、Agent 首轮改写 prompt 单次、等 5-call 的纯 regenerate Best-of-5、完整 Agent 四个臂，才能拆分 prompt rewriting、随机采样、verifier selection、edit 与 history-aware decision 的贡献。
