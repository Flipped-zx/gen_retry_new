# Muse Image 可借鉴点与 Gen-Retry 初步对比/消融计划

## 0. 结论先行

真正值得借鉴的不是 Muse Image 的整套产品能力，而是三个实验问题：

1. 在相同图像调用预算下，自适应 `edit / regenerate / submit` 是否优于
   独立 Best-of-N 重采样？
2. retry 的提升究竟来自 verifier、看图、canonical history，还是仅仅来自
   多调用了几次 Qianwen-Image-Edit？
3. 当测试时预算增加时，质量、成本和回归风险如何变化？

这三个问题正好能抬高 Gen-Retry 的证据质量，又不需要把 Muse Image 的
search、coding、Muse Spark、个性化、多参考合成或产品功能套进 v3。

当前 20 条轨迹的 `137/200 -> 171/200` atom pass、Soft-TIFA GM
`20.99 -> 47.25`、AM `69.38 -> 84.70` 是重要的运行时和行为证据，但它们
仍是 first-to-best 的**描述性增益**，不是 retry planner 的因果增益。
下一步实验必须控制额外图像调用、verifier 选优和随机采样。

## 1. 来源纠正与证据边界

用户提到的 2026 agentic Muse Image 技术博客实际来自 **Meta
Superintelligence Labs**：

<https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/>

它不是 Google 2023 年的同名 Muse masked-transformer 图像模型。后者的
官方项目页是 <https://muse-model.github.io/>，研究重点是快速离散 token
生成与编辑，不是 agentic retry。

截至 2026-07-29，Muse Image 可核验的主要技术来源是 Meta 官方博客。
定向检索未找到公开 paper、model card、代码、权重、reward 定义或可复现
ablation protocol。博客的 search/self-refinement/test-time-compute 图表
均标注为 internal ablation。self-refinement chart 报告的 pairwise
preference 是：

| Task | Self-refinement on | Self-refinement off |
| --- | ---: | ---: |
| Text-to-image | 57.1% | 42.9% |
| Single-image editing | 56.3% | 43.7% |
| Multi-image editing | 56.6% | 43.4% |

search chart 在 identities/brands/landmarks/facts 上分别报告 search-on
`70.2/67.9/67.3/56.6%`。但正文没有披露样本量、置信区间、完整 baseline、
rater/judge 协议或显著性检验，所以这些数字只能准确记录，不能用于
cross-system 数值比较。

因此它适合充当：

- related-system motivation；
- equal-image-call-budget baseline 的设计依据；
- action routing 和 test-time scaling 的问题来源。

它不适合充当：

- 可直接运行的 baseline；
- 数值可比的 leaderboard 对手；
- 证明 Gen-Retry 与其机制相同的证据；
- 证明 Gen-Retry 优于或追平 Muse Image 的证据。

官方来源的本地记录位于
`references/web/muse_image_meta_2026-07-07/`。考虑到网页未声明可复用
内容许可，仓库保存 canonical URL、来源清单和研究型转述，不转载整页 HTML
或媒体资产。

## 2. 只借鉴五个“精品”

### 2.1 把 self-refinement 当作动作路由，而不是固定 prompt rewrite

Muse Image 博客描述的关键行为是：局部问题走 edit，全局问题走 fresh
generation，事实/精确构造问题可切换工具。与 v3 最有价值的交集是前两项。

v3 已经把它变成更可审计的显式动作：

- `generate_image`：无 source 的重新生成；
- `edit_image`：指定 `source_attempt_id` 的局部修改；
- `submit_attempt`：提交任意历史 attempt；
- `query_skill`：真实 tool interaction，但当前仍为 loss 0 context。

应借鉴的是“根据失败形态分配动作”的研究问题，不是引入新的
`refine_prompt`、search 或 code action。

### 2.2 图像调用预算必须与 Best-of-N 匹配

Meta 的博客明确把 deliberate reasoning/self-refinement 与 Best-of-N
进行内部对比。这直接暴露了我们当前证据的最大缺口：first attempt 对
five-attempt best 并没有控制图像计算量。

Gen-Retry 后续必须至少有：

- single-shot；
- equal-budget Best-of-K fresh regenerations；
- fixed verifier heuristic；
- full adaptive retry planner。

否则无法区分“会规划”与“只是多抽样”。

这里应准确称为 **equal image-call budget**，不是自动等于
compute-matched。generate/edit GPU 成本、planner tokens、Geneval2 calls、
early submission 和 wall time 仍需单独记账；只有这些也匹配时才能称
equal total compute。

### 2.3 报告 anytime curve，而不是只报最终最好值

Muse Image 强调 test-time compute scaling。对 v3 来说，最可复现的对应
不是复刻其 Elo 曲线，而是按 attempt budget `k=1...K` 报告：

- best-so-far Soft-TIFA GM / AM；
- all-pass@k；
- submitted GM；
- target-fix / preserve-regression；
- GPU-seconds、planner tokens、evaluator calls 和 wall time。

这样可以回答“第几次 retry 仍然值得”，也能检测重复无效策略。

### 2.4 编辑必须同时测修复与保持

Meta 展示了多轮编辑连贯性，但没有公开可复现 preservation protocol。
Gen-Retry 的 atom rubric 和 source-relative reducer 反而允许更强的实验：

- target atom 是否被修复；
- preserve atom 是否回归；
- edit historical best 是否优于 edit latest；
- action instruction 是否造成 catastrophic regression。

这是 v3 可以比封闭产品博客做得更严谨的地方。

### 2.5 Google RichHF 提示：细粒度 feedback 本身也要消融

如果用户记忆中的“Google 做过类似事情”指的是 verifier 引导生成，那么
真正接近的是 Google 2024 的
`Rich Human Feedback for Text-to-Image Generation`：

<https://research.google/blog/rich-human-feedback-for-text-to-image-generation/>

RAHF 预测 scalar scores、artifact/misalignment heatmaps 和缺失/错误
prompt tokens；作者用它筛选 Muse 候选做 fine-tuning，也把 heatmap 转成
inpainting mask，生成多个 repairs 后再按 predicted plausibility 选优。

值得借鉴的不是把 RAHF 套进 v3，而是新增一条反馈粒度消融：

- full atom-level Geneval2 feedback；
- aggregate-only feedback（只给 passed/failed counts，不给 atom IDs、
  expected/observed 和 transition）；
- no verifier feedback。

这能区分“有一个总体质量信号”和“细粒度失败定位”对 action targeting 的
贡献。RichHF 没有 sequential action planner、edit-vs-regenerate 学习、
immutable events、historical best lineage 或 recovery supervision，因此
不会吞掉 v3 的贡献。

## 3. 不借鉴的部分

以下内容目前不进入 v3 主线：

- web search 和实时事实 grounding：属于 Gen-Searcher/OOD 问题；
- code execution、QR code、plot rendering：不是当前 Geneval2 任务空间；
- Muse Spark 协作、多 Agent 规划：会扩大主问题；
- 多参考图合成和用户个性化：改变输入协议与任务分布；
- Arena Elo 排名：模型、提示、预算和 judge 都不匹配；
- Content Seal 和产品部署：重要但不是当前 retry policy 贡献；
- “self-refinement 由 RL 自发涌现”的训练叙事：Meta 未公开足够证据让
  我们复刻，而且 v3 当前研究的是显式可训练 action policy。

## 4. 与现有工作的互补关系

| 工作 | 已有可借鉴证据 | 与 Gen-Retry 的关键差异 | 实验上怎么用 |
| --- | --- | --- | --- |
| Muse Image | edit/regenerate/tool routing；test-time compute；Best-of-N 对照 | 闭源；内部 reward/轨迹不公开；面向产品和 human-preference Elo | 只借实验问题，不作为可运行 baseline |
| Google RichHF + Muse | scalar/spatial/token feedback；候选筛选；heatmap inpainting | 固定 pipeline，无 edit-vs-regenerate policy、history/lineage/recovery | 增加 feedback-granularity ablation 和独立 human audit |
| GenEvolve | tool-orchestrated visual trajectory；skill retrieval；assistant-only masking | 输出 prompt-reference program，不用 atom verifier/rollback best | 证明 tool/message 设计先例；不混同贡献 |
| Flow-DPPO | 20k Geneval2 synthetic training；GM metric；in-domain reward 优化 | 训练 image model，不训练 retry policy | 作为数据/metric precedent，不直接比 92.6 GM |
| GenEval2 | atom VQA、Soft-TIFA AM/GM、官方 800 benchmark | evaluator 也是反馈源，会产生 circularity | 主评估器，同时增加独立 audit |
| GenAgent/GEMS/RS-Gen | image observation、memory、generate-review-correct 背景 | 缺少 v3 的 strict action/event/reducer ownership | related-work 背景；需要时再做定向 baseline grounding |
| Legacy Gen-Retry | 大量 failure signature；regenerate-only 历史 | 协议旧且 action 单一 | 用于 failure taxonomy，不作为当前正向 target |

本项目可防守的贡献应表述为：

> 一个可训练、可回放的序贯 retry policy：联合可见图片、atom verifier
> feedback、canonical action/outcome history、显式历史 source 和固定预算，
> 每轮输出一个 executable action，并能在非单调结果中分支和提交历史最优。

当前还不能表述为“训练后的 Qwen3-VL 已提升图像质量”，因为现有 live
轨迹的 Planner/Teacher 仍是 GPT-5.5。

## 5. 三个必须分开的 estimand

不要把以下问题混成一个总分：

1. **Retry search value**：相同 image budget 下，自适应 retry 是否优于
   single-shot、Best-of-K 和 fixed heuristic？
2. **Context component value**：在 planner/backend 固定时，verifier
   (`V`)、visible image (`I`) 和 canonical history (`H`) 各自贡献多少？
3. **Student learning value**：SFT Qwen3-VL 是否优于同 checkpoint 的 base
   planner，以及是否接近 Teacher？

前两项可以在训练前完成；第三项只能在形成冻结 student checkpoint 后完成。

## 6. 分阶段实验计划

### Stage 0 — 复用当前 20 条轨迹，零新增生图

目的：补齐描述统计、估计方差和 live pilot 成本，不做 model-level claim。

必须完成：

- 以 prompt 为独立统计单位，对 first-to-submitted 和 first-to-peak GM/AM
  做 prompt-cluster bootstrap 95% CI；
- 画 `k=1...5` 的 best-so-far GM、AM、pass 和 all-pass anytime curve；
- 报告 submitted-to-peak regret；当前 submitted GM `47.25` 低于
  post-hoc peak GM `53.33`；
- 分 atom type、difficulty 和 action sequence 报 target-fix /
  preserve-regression；
- 量化 historical branch、latest bias、重复无效策略和 premature/late
  submit。

注意：200 个 atoms 和 92 个 attempts 不是 292 个独立样本；统计单位是
20 个 prompts。当前 20 条轨迹也已经 design-exposed，只能做探索性分析。

### Stage 1 — 冻结状态的 `V x I x H` planner-only screen

这是最便宜的 component screen，不调用 Qwen-Image-Edit 或 Geneval2。

从 immutable event prefixes 构造覆盖以下情况的 locked contexts：

- broad failure；
- 一到两个 local failures；
- edit 后出现 regression；
- 重复 ineffective action；
- latest 明显劣于 historical best；
- all-pass、budget-stop 和 submit。

跑完整 `2^3` 输入组合：

- `V`：latest atom observation 和 verifier-derived transitions；
- `I`：与 attempt 绑定的真实图片 pixels；
- `H`：prior rounds、best/latest、lineage、fixed/regressed/persistent。

TaskSpec 和 remaining budget 在所有 cells 中保留。只评估 action quality：

- schema/reference validity；
- edit vs regenerate；
- source attempt 选择；
- target/preserve coverage；
- strategy-repeat avoidance；
- submit/stop 选择。

禁止把 future outcome、peak attempt、完整轨迹标签或分数编码进 context。
该阶段只筛选哪些组件会改变决策，不能单独证明图像 outcome 提升。

在 `V=on` 的 cells 内再做一个 nested screen：full atom-level feedback
对 aggregate-only counts。这是从 RichHF 得到的最小高价值扩展，不需要
引入 heatmap 模型或改变现有 Geneval2 evaluator。

planner-only screen 只能决定成本优先级或帮助收窄 claim，不能证明
atom-level feedback 改善了实际图片。只要最终仍把 atom-level grounding
作为贡献，confirmatory live 必须至少包含：

- full atom-level feedback vs aggregate-only counts；
- full atom-level feedback vs no-verifier。

aggregate-only vs no-verifier 可作为解释性补充，不是单独的阻塞对比。

### Stage 2 — one-step matched mechanism study

从同一个已缓存 source state 分支，每个候选动作只获得一次相同配置的 image
call：

| 状态 | 对照 | 核心指标 |
| --- | --- | --- |
| 少量 local failures | targeted edit vs fresh regenerate | target fix、preserve regression、GM delta |
| latest 回归、history best 更好 | edit historical best vs edit latest | source regret、catastrophic regression |
| 上轮 edit 无效 | strategy switch vs materially equivalent repeat | fix rate、wasted-call rate |
| verb/action 失败 | action-pose repair vs frozen generic repair | verb fix、其他 atoms 保持 |
| passed atoms 很多 | target+preserve instruction vs target-only | preserved-atom regression |

必须固定 source artifact、TaskSpec、remaining budget、attempt-index seed、
Qwen 配置和 evaluator。这里得到的是局部 action effect，不是 full-policy
effect。

### Stage 3 — matched live retry development study

先做四个最有信息量的 arms：

| Arm | 作用 |
| --- | --- |
| Single shot | 成本和质量下界 |
| Equal-image-call-budget Best-of-K regenerate | 控制额外图像调用和 verifier 选优 |
| Fixed greedy verifier heuristic | 控制 atom feedback + edit 能力，但没有 learned multimodal/history planning |
| Full `V+I+H` planner | 当前提出的方法 |

所有 arms 共用同一张初始图片；retry arms 再获得相同数量的额外 attempts。
这样既节省成本，也把研究问题限定为“初图之后如何 retry”。若 full planner
不能稳定超过 Best-of-K 和 heuristic，不应继续扩张昂贵 component live
ablation。

只有 Stage 1 显示某一 component 会实质改变决策、且四臂 pilot 显示 full
planner 有 outcome 信号后，才把 `-V`、`-I`、`-H` 晋级为 live arms：

| Arm | 删除内容 |
| --- | --- |
| `-V` | 隐藏 evaluator observations、所有 verifier-derived best/transition 和记分 metadata |
| `-I` | 隐藏 pixels、caption/description、可读 filename 和视觉 metadata；artifact IDs 保持 opaque |
| `-H` | 只保留 latest image/result、TaskSpec 和 budget；无 prior rounds/best/branch |

Skills 在核心实验中固定关闭，或向所有 arms 预加载同一份内容。当前 Skill
utility 没有通过 capability-isolated 验证，不能与 `V/I/H` 主张混在一起。

Stage 3 是 development pilot，不预先声称统计显著。最终 confirmatory N
应根据 paired prompt-level variance 和预先声明的最小有意义 GM 差异做
power analysis；当前没有 matched ablation variance，不能凭空写一个
“充分样本量”。

### Stage 4 — confirmatory replication

使用从此刻开始冻结、与 SFT 和上述 development prompts 语义家族不重叠的
prompt split。官方 800 rows 已在 Phase 3 被读取并抽取过十条，不能再声称
“完全 untouched”；最终报告必须披露 development exposure。

优先增加不同 prompts，而不是只堆同 prompt seeds。若需要估计 backend
随机性，再加入第二 seed。预注册：

- primary metric 和 selector；
- maximum sample size；
- early-stop/sequential rule；
- full-vs-baseline 和 full-vs-dropout 的主要比较；
- 多重比较修正；
- 人工/独立 evaluator audit 子集。

### Stage 5 — Student SFT ablation

在同一 frozen full context 下比较：

- base Qwen3-VL planner；
- SFT Qwen3-VL planner；
- GPT-5.5 Teacher upper reference。

保持 planner decoding、parser retry、Qwen backend、Geneval2、prompt split
和 attempt budget 一致。该阶段才能回答“训练出的 retry policy 是否有效”。

## 7. 最小充分 ablation matrix

### Must-run

| 对比 | 隔离的因素 | Primary/关键 process endpoint |
| --- | --- | --- |
| Full vs single-shot | retry 总价值但未控制 compute | submitted GM、all-pass、cost |
| Full vs equal-image-call-budget Best-of-K | adaptive planning，而非多采样 | GM@K、anytime AUC、cost efficiency |
| Full vs fixed heuristic | learned image/history reasoning | GM、target fix、preserve regression |
| Full vs `-V` | atom verifier grounding | target-fix efficiency |
| atom-level `V` vs aggregate-only `V` | feedback 粒度而非总分存在性 | target coverage、fix efficiency、preserve regression |
| Full vs `-I` | image awareness | source/action correctness、visual audit |
| Full vs `-H` | canonical history/rollback | branch benefit、submission/source regret |
| historical-best source vs latest source | non-monotonic recovery | catastrophic regression、GM delta |
| target+preserve vs target-only | preservation contract | passed-atom regression |
| base vs SFT student | supervision contribution | submitted GM、valid action rate |

### Separate validation, not part of the core claim

| 对比 | 原因 |
| --- | --- |
| no Skill vs queried Skill vs same content preloaded | 区分 guidance content 与 retrieval/action 的价值 |
| operational `best_by_pass` + submitted-GM primary + post-hoc `best_by_gm@K` | 已采纳的预实验报告语义；任何 selector 改动需另走 ADR |
| verb-enriched diagnostic cohort | 当前 best 仅 `7/15` verb atoms，需专门诊断但不能替代总体分布 |
| human/independent evaluator audit | general image-quality claim 的必需项；否则只报告 Geneval2-defined objective |

完整 live `2^3` factorial、不同 budgets、不同 backend/resolution 都是
nice-to-have；在核心四臂结果成立前不值得烧 GPU。

## 8. 公平性与可复现控制

可比较 arms 必须冻结：

- 同一 Qianwen-Image-Edit build 和 generate/edit mode；
- 40 steps、1024 x 1024、CFG/guidance、preprocessing；
- 同一 Geneval2 build、rubric、threshold、answer-probability 算法；
- 每张 image attempt 后使用同一 evaluator schedule；
- 同一 planner checkpoint、system contract、decoding 和 parser retry；
- 同一 prompt/rubric、initial image、maximum image attempts；
- attempt-index seeds、cache key、artifact naming 和 execution order；
- full 与 fixed heuristic 使用同一 generate/edit/source/submit action
  availability；Best-of-K 作为明示 regenerate-only control；
- Skill policy；
- terminal selector。

相同 prompt/base seed 内使用 common random numbers。worker 上的 arm 执行顺序
要 counterbalance，避免机器热身或资源拥塞与某个 arm 绑定。只有 action、
source artifact、seed 和 backend config 字节等价时才可跨 arm 复用 cache。

共享初图在 physical spend 中只计一次，在每个 arm 的 deployed logical cost
中都应计一次。

每个 arm 还必须记录 generate 与 edit 的 GPU-seconds、Geneval2 calls、
planner input/output/reasoning tokens、early submission、failed requests 和
wall time。除非这些总成本也匹配，报告只写 equal image-call budget。

## 9. 指标与统计

### Primary

5.6 Sol review 后的预实验建议是：

- 保留当前 thresholded pass-count + earlier tie break 作为 operational
  `submitted` / `best_by_pass` selector；
- final efficacy primary 使用 prompt-level **submitted Soft-TIFA GM**；
- `best_by_gm@K` 只作为 post-hoc oracle secondary；
- GM 在 planner 决策时保持不可见，除非后续 ADR 明确改变 ownership。

不要在 ablation 中静默切到 GM-only 或 pass-count/GM lexicographic selector；
两者都会改变 protocol semantics，必须另走 ADR 和回归验证。当前系统可声称
“submitted GM 提升”，不能声称“planner 直接优化 GM”。

### Secondary

- submitted atom pass fraction；
- all-pass episode rate；
- Soft-TIFA AM；
- reducer-best 和 post-hoc peak GM；
- submitted-to-peak regret；
- success@attempt `k` 和 anytime AUC；
- target-fix / preserve-regression；
- historical-branch benefit；
- attempts、GPU-hour、planner tokens、evaluator calls、latency 和 dollar；
- invalid action/reference rate。

verb 必须单列。verb-enriched cohort 的结果需要按目标 prompt distribution
重加权，不能直接代替总体结果。

### Statistical unit and tests

- 以 original prompt 为 block 和独立单位；
- primary paired contrasts 用 paired permutation/randomization test；
- GM/AM/pass/anytime/cost 用 prompt-cluster bootstrap 95% CI；
- 单 seed 的 paired all-pass 可用 exact McNemar；
- 多 seeds 用 prompt-cluster bootstrap 或 prompt/seed mixed model；
- atom-level 分析用 clustered logistic/GEE 或 mixed model，禁止 naïve
  atom-binomial；
- full-vs-strong-baseline 和 full-vs-three-dropout family 用 Holm correction。

factor interaction 在没有专门 power 前只标为 exploratory。prefixes、
attempts、atoms 和 seeds 都是 repeated measurements；seeds 嵌套在 prompt
下，不能当成新的独立 prompts。

## 10. Failure taxonomy

每次失败 transition 至少标注：

- perception/evaluation：verifier 错误、不确定或与人工看图冲突；
- action selection：edit/regenerate 选错、过早 submit、浪费 retry；
- history/source：latest bias、source 错误、没有恢复历史最优；
- targeting：漏掉 failed atom 或不必要地修改 passed atom；
- preservation：count/identity/attribute/position/verb regression；
- instruction：含糊、矛盾、过宽、关系描述不可执行；
- backend execution：action 合理但生成器未实现；
- protocol/runtime：invalid JSON/reference、resume/cache/duplicate defect；
- Skill：query 不相关、返回内容未使用、只有开销没有结果。

这个 taxonomy 同时服务 one-step mechanism study、SFT sample filtering 和
论文 qualitative analysis。

## 11. Leakage 与 evaluator circularity

- 每个 original prompt 和 semantic family 只能属于一个 split；
- 当前 20 条和 Phase 3 official-prompt 记录全部视为 design-exposed；
- 每个 context 只能由 immutable event prefix 构建；
- GM/AM/probabilities/peak identity 默认 post-hoc，不进入 PlannerContext；
- artifact ID 和路径不能编码 score/best；
- raw Teacher output 不进入 memory 或 positive target；
- confirmatory 前冻结 schema、prompt、Skill、selector 和 evaluator；
- 人工 reviewer 对 arm 和 aggregate outcome 盲审；
- `-V` 同时删除 best labels、fixed/regressed/persistent 和任何编码 score 的
  metadata；aggregate-only 不泄漏 atom IDs 或 expected/observed；
- `-I` 同时删除 caption/description、可读 filename 和视觉 metadata；
- planner-only action labels 只基于 event prefix，不能看 later outcome；
- 对冻结 confirmatory subset 做一个不向 planner/selector 提供反馈的
  independent VLM 或 blinded human pairwise audit。若不做，结论只能限定为
  Geneval2-defined objective，不能扩张为 general image-quality claim。

## 12. 现在不能做的 claim

不能声称：

- first-to-best 增益已经证明 planner 的因果价值；
- 20 条 selected trajectories 是 model-level improvement；
- 当前结果是官方 800-prompt Geneval2 leaderboard；
- query_skill 已被证明有效或应成为正向 SFT target；
- verb 能力已经解决；
- 当前 pass-count reducer 在优化 GM；
- leave-one-out 一定证明 `V/I/H` 都必要，而不考虑 interaction；
- SFT 有效，直到 base-vs-SFT student 真正运行；
- 与 Muse Image 数值可比、机制相同、持平或领先；
- 结果可泛化到其他 backend、prompt distribution、evaluator、resolution
  或 budget。

## 13. 决策顺序

1. 先用现有 20 条做 Stage 0，零 GPU；
2. 再做 Stage 1 planner-only `2^3` screen；
3. 用 Stage 2 one-step matched calls 验证真正有争议的 action/source；
4. 只运行 Stage 3 的四个高信息量 arms；
5. 若 full 胜过 Best-of-K 与 heuristic，再升级 live `-V/-I/-H`；
6. 单独验证 Skill；
7. 冻结 selector/primary metric 和 confirmatory split；
8. SFT 后运行 base-vs-student-vs-Teacher。

这个顺序最大化每个 GPU/API dollar 的证据量，并保留 v3 当前干净的
action、memory 和 evaluator ownership，不让 Muse Image 的产品范围把研究
问题带偏。
