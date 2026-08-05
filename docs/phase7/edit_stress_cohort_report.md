# Flow-DPPO v9 Edit-Stress Cohort 选择报告

**冻结日期**：2026-08-05  
**范围**：`runs/phase7_flow_dppo1000_v9_fresh8_v1` 的 1000 条完整轨迹。  
**用途**：为后续 paired quality pilot 选择可审计的多次 edit、深 lineage 和 Geneval2/质量方向冲突样本。本报告只读现有 canonical artifacts；没有改写任何 run、image 或 Geneval2 结果。

## 证据与口径

读取的冻结证据：

- `docs/status.md`
- `docs/phase7/checkpoints/flow_dppo1000_v9_ckpt_1000_audit.md`
- `docs/phase7/flow_dppo1000_v9_final_analysis_report.md`
- `artifacts/phase7/flow_dppo1000_v9_official_mix_selected_prompts.json`
- `artifacts/phase7/flow_dppo1000_v9_fresh8_v1_prepared_rollouts.json`
- 每条轨迹的 `episode_state.json`、`manifest.json`、`task_spec.json`、`images/`、`geneval2/`

批次完整性：1000/1000 manifests closed；3443 个 Attempt、3443 张 PNG、3443 个 Geneval2 report、1000 个 event log。Manifest 的 artifact type 只有 `image`、`geneval2_report`、`event_log`、`round_record`、`planner_context`、`raw_model_output`、`task_spec`，没有 HPS/quality sidecar。

冻结筛选规则：

1. 统计单位是 episode；同一 episode 的 Attempts 不是独立样本。
2. `edit_count` 是 canonical Attempts 中 `operation=edit` 的数量。
3. `edit_depth` 是从 Attempt 沿 `parent_attempt_id` 回溯到 root generate 的最大边数；root 深度为 0。`D2` 表示最大深度恰为 2，`D3+` 表示最大深度至少 3。
4. 语义/质量冲突只在直接 parent→child 上判定：
   - `U`（semantic-up/quality-down）：Geneval2 passed-atom 差值 `Δpass>0` 且持久 `primary_score`（Soft-TIFA GM）差值 `ΔGM<0`。
   - `D`（semantic-down/quality-up）：`Δpass<0` 且 `ΔGM>0`。
   - `N`：该 episode 没有上述相反方向的 transition，仅作为中性 edit-stress 对照。
5. 主 cohort 按 `D2/D3+ × easy/medium/hard × U/D/N` 各取 1 条；cell 中按冲突绝对幅度优先、再按 episode ID 稳定排序。N cell 按最大 edit 数、再按 atom gain 排序。该规则只用于选择，不改变 canonical best/submission。

## 全池统计

| 筛选池 | Episode 数 | easy / medium / hard |
| --- | ---: | ---: |
| 至少 2 次 edit | 623 | 155 / 247 / 221 |
| 至少 3 次 edit | 539 | 118 / 221 / 200 |
| `edit_depth >= 2` | 498 | 120 / 201 / 177 |
| `D2`（最大深度=2） | 240 | 65 / 92 / 83 |
| `D3+`（最大深度>=3） | 258 | 55 / 109 / 94 |
| `U` episode | 40 | 8 / 14 / 18 |
| `D` episode | 86 | 16 / 26 / 44 |
| 同一 episode 同时出现 U 与 D | 10 | 2 / 4 / 4 |
| 首图到 submitted 的 GM 下降 | 19 | 3 / 6 / 10 |

`U` 有 40 个 episode-level transition；`D` 有 86 个 episode、106 个 transition（部分轨迹多次回归）。19 个首图→submitted GM 下降均换取了一个额外 passed atom，这是 pass-count-first 选择策略的已知 trade-off，不是 HPS 证据。

## 冻结的 18 条典型 cohort

`C` 是实际 `task_spec.constraints` 数；`atom_count` 只用于官方 difficulty tier，不能替代 `C`。`pair` 是要重评分的直接 parent→child image pair；图片位于对应 episode 的 `images/img_NNN.png`，Geneval2 位于 `geneval2/a_NNN.json`。

| 层 | 类型 | Episode（prompt） | tier / atom_count / C | edits / depth | pair（Attempt，Δpass，ΔGM） | fixed / regressed | best=submitted |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| D2 | U | `phase3_ep_970`（seven metal yellow croissants） | easy / 4 / 4 | 4 / 2 | `a_000→a_001` (+1, -0.0358) | c_002 / - | a_004 |
| D2 | D | `phase3_ep_931`（a wooden yellow cookie and a plastic sheep） | easy / 5 / 7 | 4 / 2 | `a_001→a_003` (-2, +0.4341) | - / c_002,c_004 | a_001 |
| D2 | N | `phase3_ep_283`（a glass white rabbit and six horses） | easy / 5 / 6 | 4 / 2 | `a_000→a_001` (+2, +0.0217) | c_001,c_004 / - | a_001 |
| D2 | U | `phase3_ep_926`（five bicycles to the right of seven cows to the right of four raccoons） | medium / 8 / 8 | 4 / 2 | `a_000→a_002` (+1, -0.7068) | c_001,c_004 / c_007 | a_002 |
| D2 | D | `phase3_ep_118`（seven toys to the left of seven cows on top of five suitcases） | medium / 8 / 8 | 4 / 2 | `a_002→a_004` (-2, +0.2551) | - / c_001,c_007 | a_002 |
| D2 | N | `phase3_ep_134`（four toys in front of five birds under six candles） | medium / 8 / 8 | 4 / 2 | `a_000→a_001` (+3, +0.2068) | c_001,c_002,c_005 / - | a_001 |
| D2 | U | `phase3_ep_296`（six croissants to the left of five purple bagels to the right of six plastic donuts） | hard / 10 / 10 | 4 / 2 | `a_000→a_001` (+1, -0.0309) | c_004 / - | a_001 |
| D2 | D | `phase3_ep_855`（four cats behind seven koalas to the left of five green pigs） | hard / 9 / 9 | 4 / 2 | `a_002→a_004` (-1, +0.6268) | - / c_003 | a_002 |
| D2 | N | `phase3_ep_671`（four glass cars under six elephants behind seven trumpets） | hard / 9 / 9 | 4 / 2 | `a_001→a_004` (+1, +0.2230) | c_006 / - | a_004 |
| D3+ | U | `phase3_ep_177`（a metal striped bagel） | easy / 3 / 4 | 4 / 3 | `a_000→a_001` (+1, -0.2239) | c_002 / - | a_003 |
| D3+ | D | `phase3_ep_899`（five koalas chasing three monkeys） | easy / 5 / 5 | 4 / 4 | `a_003→a_004` (-2, +0.3246) | - / c_001,c_003 | a_003 |
| D3+ | N | `phase3_ep_307`（six striped metal elephants and a horse） | easy / 5 / 6 | 4 / 3 | `a_000→a_001` (+2, +0.0276) | c_002,c_003 / - | a_002 |
| D3+ | U | `phase3_ep_461`（seven birds playing with a koala to the left of seven trucks） | medium / 7 / 8 | 4 / 3 | `a_001→a_002` (+1, -0.4131) | c_003 / - | a_004 |
| D3+ | D | `phase3_ep_181`（six croissants on top of a pig chasing six flamingos） | medium / 7 / 8 | 4 / 3 | `a_003→a_004` (-1, +0.4167) | - / c_007 | a_003 |
| D3+ | N | `phase3_ep_789`（seven wooden backpacks and five white plastic horses） | medium / 7 / 7 | 4 / 4 | `a_001→a_002` (+1, +0.5307) | c_006 / - | a_004 |
| D3+ | U | `phase3_ep_783`（seven plastic pigs in front of seven umbrellas in front of six candles） | hard / 9 / 9 | 4 / 3 | `a_001→a_003` (+1, -0.2573) | c_001,c_005 / c_008 | a_003 |
| D3+ | D | `phase3_ep_063`（six plastic stone turtles to the right of six croissants to the left of a cat） | hard / 9 / 10 | 4 / 3 | `a_003→a_004` (-1, +0.6357) | - / c_003 | a_003 |
| D3+ | N | `phase3_ep_648`（five yellow zebras on top of five suitcases to the right of six checkered horses） | hard / 10 / 10 | 4 / 4 | `a_003→a_004` (+4, +0.2441) | c_001,c_002,c_003,c_004 / - | a_004 |

所有 18 条轨迹的 canonical Attempt IDs 均为 `a_000`–`a_004`，实际存在 `img_000.png`–`img_004.png`（5 张，90 张图合计）；每个 edit 的 `parent_attempt_id`、source image artifact、child image artifact、Geneval2 report 和 manifest hash 都可配对。表中的 `best=submitted` 只是当前 reducer 结果；不能把同一轨迹的 5 张图当成 5 个独立 episode。

## HPS / quality 缺口

本批次没有 HPS sidecar，也没有可直接 join 的第三方 quality score。可用的质量代理只有环境拥有的 Geneval2 Soft-TIFA GM/AM；因此当前可以审计 U/D 语义冲突，但不能声称“ HPS 下降”。要冻结 HPS 版本，必须对全批次 3443 张 PNG（至少覆盖全部 623 个 `edit_count>=2` episode）离线重评分，而不是只评分已经挑出的 18 条。

离线重评分最小输入/输出清单：

- 输入：每个 `episode_id/attempt_id`、`image_artifact_id`、PNG 路径、manifest `sha256`、原始 prompt、父 Attempt、source image；18 条 cohort 的原始 prompt 均在 `task_spec.json` 与官方 selection artifact 中存在。
- 固定 provenance：HPS 模型/权重 fingerprint、预处理与裁剪、文本 tokenizer、归一化、batch/seed、运行时间和代码版本。
- 输出 sidecar：`episode_id`、`attempt_id`、`parent_attempt_id`、image sha256、`hps_metric_id/version`、score、模型与预处理 hash、error/status。必须 append-only、按 image hash 去重，不能覆盖 `episode_state` 或 `geneval2`。
- 配对判定：在同一 episode 内比较 parent 与 child 的 HPS；`ΔHPS<0` 才标为 HPS drop。再与 `Δpass`、`ΔGM` 交叉表，避免把跨 prompt 差异误当质量回归。

## 后续 paired pilot 建议

先执行 18 条冻结 cohort 的全 Attempt paired 重评分，随后按 `U`、`D`、`N` 和 D2/D3+ 分层报告 `ΔHPS`、`ΔGM`、`Δpass`；显著性与置信区间按 episode cluster bootstrap，不能按 Attempt 独立抽样。阈值冻结后使用与这 18 条不重叠的 60 条 confirmation manifest；历史图片补打 HPS 只做 held-out diagnostic，缓解效果必须重新运行成对 `G`/`G+H` arms。若资源有限，calibration 优先 12 条 U/D 冲突对，再补 6 条 N 对照；但最终一般性结论仍应回填全 623 条多 edit 池的 sidecar coverage。

**当前结论**：edit-stress 候选充足，18 条分层 cohort 已可审计且图像/原始 prompt 全部可配对；HPS 下降结论暂时缺数据，不能用 Geneval2 GM 下降替代 HPS。没有触发 protocol、memory、SFT 或 reviewer gate。
