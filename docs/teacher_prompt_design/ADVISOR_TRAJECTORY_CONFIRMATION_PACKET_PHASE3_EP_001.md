# 最新轨迹导师确认包: `phase3_ep_001`

Date: 2026-07-15

Run directory: `runs/teacher_prompt_v1_validation/phase3_ep_001`

Readable trace: `docs/teacher_prompt_design/validation_trace_phase3_ep_001.md`

I/O analysis: `docs/teacher_prompt_design/validation_trajectory_io_analysis_phase3_ep_001.md`

Structured-output probe: `docs/teacher_prompt_design/STRUCTURED_OUTPUT_PROBE.md`

## 1. 一句话结论

这条轨迹已经体现了我们想要的核心结构:

`TaskSpec + PlannerView + visible images + Skills -> Teacher canonical action -> Qwen-Image-Edit execution -> Geneval2 atom feedback -> reducer updates history/best -> next Teacher action -> final submit best`

它不是一条 raw Teacher 完全无错的轨迹。它是一条经过严格验收后的 canonical 轨迹: raw Teacher 输出必须先通过 schema/reference/runtime/instruction validation，才能进入 image execution 和 canonical history。被拒绝的 raw 输出被记录用于审计，但不消耗 image budget，也不作为正向 SFT target。

本轨迹最重要的正例行为是:

- 先 `query_skill` 获取 counting/spatial capability guidance。
- 初始失败后重新 fresh generate，而不是直接 edit 低质量图。
- 看到 `a_001` 已经修好猫数量和玻璃材质后，改为局部 edit。
- 看到 `a_003` 退化后，不从 latest 继续，而是从 best `a_002` 分支修复。
- budget 用完后提交历史 best `a_002`，不是提交 latest `a_004`。

## 2. 这条轨迹是什么任务

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

Image-attempt budget:

```text
max_image_attempts = 5
```

Teacher model:

```text
gpt-5.5
```

Image backend:

```text
local Qwen-Image-Edit, 40 steps, 1024x1024, true_cfg_scale=4.0, guidance_scale=1.0
```

Evaluator:

```text
Geneval2 atom-level VQA, normalized into pass/fail/uncertain atom results
```

## 3. TaskSpec: 任务如何拆成可验证 atom

`task_spec.json` 把原始 prompt 拆成 11 个 verifier-facing atomic constraints。后续 Teacher 不是直接看一个模糊总分，而是看每个 atom 的状态。

| Atom | Type | Evaluator question | Expected |
| --- | --- | --- | --- |
| `c_001` | count | How many lions are in the image? | six |
| `c_002` | attribute | Are the lions glass? | Yes |
| `c_003` | object | Are there any lions in the image? | Yes |
| `c_004` | verb | Are the lions chasing the cats? | Yes |
| `c_005` | count | How many cats are in the image? | three |
| `c_006` | attribute | Are the cats red? | Yes |
| `c_007` | object | Are there any cats in the image? | Yes |
| `c_008` | position | Are the cats behind the donut? | Yes |
| `c_009` | count | How many donuts are in the image? | one |
| `c_010` | attribute | Is the donut brown? | Yes |
| `c_011` | object | Are there any donuts in the image? | Yes |

这些 atom 是 Geneval2 输出和 PlannerView 中 constraint state 的共同坐标系。Teacher 的 `target_constraint_ids` 和 `preserve_constraint_ids` 都必须引用这里的 atom ID。

## 4. 每轮 Teacher 输入是什么形式

每次 Teacher API 调用都由两部分组成:

1. `system`: 固定 Teacher policy。
2. `user`: 一个 multimodal message，第一段是结构化文本，后面跟可见图片标签和图片 payload。

持久化审计记录在 `planner_requests.jsonl`。为了不落盘图片 bytes，它只保存 image role、attempt ID、artifact ID、path hash。实际 API 请求会把图片用 data URL 送给 Teacher。

每个 `planner_requests.jsonl` record 主要字段:

| Field | 含义 |
| --- | --- |
| `request_id` | 当前 Teacher turn 的稳定 ID |
| `teacher_provider` / `teacher_model_id` | provider 和模型 |
| `system_prompt_version` / `system_prompt_sha256` | 固定 system prompt 的版本和 hash |
| `planner_view_ref` / `planner_view_sha256` | 本轮 PlannerView artifact 和 hash |
| `teacher_text_input` | 给 Teacher 的完整文本输入 |
| `visible_images` | Teacher 可见图片的 role/attempt/artifact/path hash |
| `retrieved_skill_ids` | 本轮刚返回的 full Skill content |
| `extra_observations` | 环境额外提示，如无图不可 edit、budget exhausted 等 |

`teacher_text_input` 里面包含:

- action protocol: allowed actions, required fields, valid templates。
- TaskSpec: original prompt 和 atomic constraints。
- PlannerView: latest attempt, best attempt, compact history, remaining budget, constraint state, latest transition。
- visible image labels: `LATEST_IMAGE`, `BEST_IMAGE`, `BEST_IMAGE_SAME_AS_LATEST`。
- active Skill operators: 之前 query 过并保留的 compact Skill operator summaries。
- retrieved full Skills: 仅在 `query_skill` 后立即返回完整 Markdown。
- extra observations: 例如首轮不能 edit/submit，budget 为 0 时必须 submit best。

## 5. Teacher 输出如何变成 canonical action

Teacher 被要求直接输出一个 canonical action JSON。runtime 不会把自由文本翻译成 action，也不会补字段。

链路是:

```text
raw Teacher text
-> JSON parse
-> action_protocol_v0_2 schema validation
-> constraint/attempt/skill reference validation
-> runtime validation, such as budget and source_attempt_id
-> image instruction quality validation
-> action_validated event
-> canonical_actions.jsonl
```

如果任意一步失败:

- 写入 `format_error` event。
- 写入 redacted `raw_teacher_outputs` artifact。
- 不执行 Qwen。
- 不执行 Geneval2。
- 不消耗 image-attempt budget。
- 不进入 canonical positive SFT target。

这就是 `turn_001` 漏 `mode` 为什么没有污染轨迹的原因。它是 raw 输出错误，不是 canonical action。

## 6. 全轨迹概览

| Metric | Value |
| --- | --- |
| Teacher requests | 12 |
| Accepted canonical actions | 7 |
| Rejected raw outputs | 5 |
| Image attempts | 5 |
| Final submitted attempt | `a_002` |
| Submit reason | `best_available_under_budget` |
| Best score | 9/11 atoms passed |
| Persistent failures in best | `c_004` chasing, `c_008` cats behind donut |

Image attempts:

| Attempt | Operation | Parent | Image artifact | Pass/11 | Failed atoms |
| --- | --- | --- | --- | ---: | --- |
| `a_000` | generate | none | `img_000` | 6/11 | `c_001`, `c_002`, `c_004`, `c_005`, `c_008` |
| `a_001` | generate | none | `img_001` | 8/11 | `c_001`, `c_004`, `c_008` |
| `a_002` | edit | `a_001` | `img_002` | 9/11 | `c_004`, `c_008` |
| `a_003` | edit | `a_002` | `img_003` | 8/11 | `c_002`, `c_004`, `c_008` |
| `a_004` | edit | `a_002` | `img_004` | 9/11 | `c_004`, `c_008` |

Final submission:

```json
{
  "submitted_attempt_id": "a_002",
  "best_attempt_id": "a_002",
  "reason_code": "best_available_under_budget"
}
```

## 7. 逐轮输入输出和来源

### `turn_000`: query foundational Skills

Teacher input state:

- `planner_view_000`
- no attempts
- remaining budget `5`
- visible images: none
- compact history: empty
- extra observation: no image exists yet, so do not edit or submit
- skill manifest lists available Skills by ID/summary

Teacher raw output:

```json
{
  "schema_version": "0.2",
  "action": "query_skill",
  "arguments": {
    "skill_ids": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_005",
      "c_008",
      "c_009"
    ]
  }
}
```

Runtime result:

- accepted as canonical `query_skill`
- skill store returns full Markdown for counting and spatial relation
- `skill_returned` event enters event log
- next PlannerView contains active Skill operator summaries

Why this step exists:

- The prompt includes exact counts and spatial/verb relations.
- We want explicit `query_skill -> tool_response` interaction before prompt rewrite.
- Skill content is context for later action construction, not an image execution.

### `turn_001`: first generate proposal, rejected by schema

Teacher input state:

- `planner_view_001`
- no attempts yet
- budget still `5`
- full retrieved Skills are now in context
- visible images: none
- extra observation again says no image exists, so do not edit or submit

Teacher raw intent:

- action: `generate_image`
- instruction content was reasonable: exact one brown donut, exactly three red cats behind donut, exactly six glass lions chasing cats, no extras/fused/cropped/reflection duplicates

Rejected raw issue:

```text
arguments.mode was missing
```

Runtime result:

- schema validation failed
- no canonical action
- no Qwen execution
- no Geneval2 evaluation
- no image budget consumed

Interpretation:

- Teacher understood the visual task.
- But the action-format constraint was not strong enough for this raw call.
- Separate structured-output testing shows an action-specific `response_format=json_schema` fixes this class of missing-required-field error for the same input.

### `turn_002`: accepted initial generation, creates `a_000`

Teacher input state:

- `planner_view_002`
- no accepted image attempts yet
- budget still `5`
- active Skill operators present from `turn_000`
- visible images: none

Canonical action:

```json
{
  "action": "generate_image",
  "arguments": {
    "mode": "initial",
    "target_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_004",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010",
      "c_011"
    ],
    "preserve_constraint_ids": [],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "fresh_layout",
      "counting",
      "spatial_relation"
    ]
  }
}
```

Generation instruction:

```text
Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts.
```

Execution and evaluation:

- Qwen request: `phase3_ep_001_a_000_generate`
- output image: `img_000`
- Geneval2 result: 6/11 pass
- failed: lion count, lion glass uncertain, chasing, cat count, cats behind donut

Reducer result:

- latest = `a_000`
- best = `a_000`
- remaining budget = `4`

How next input is created:

- `a_000` action, image artifact, Geneval2 atoms, and transition are appended as events.
- reducer rebuilds state.
- PlannerView builder exposes latest/best `a_000`, compact history length 1, failed atom IDs, and `img_000` as visible latest/best image.

### `turn_003`: second fresh generation, creates `a_001`

Teacher input state:

- `planner_view_003`
- latest = best = `a_000`
- visible images: `LATEST_IMAGE/BEST_IMAGE = img_000`
- budget `4`
- compact history includes `a_000`
- failed atoms: `c_001`, `c_002`, `c_004`, `c_005`, `c_008`

Canonical action:

```json
{
  "action": "generate_image",
  "arguments": {
    "mode": "initial",
    "strategy_tags": [
      "fresh_layout",
      "explicit_counting",
      "spatial_relation"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ]
  }
}
```

Generation instruction:

```text
Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects.
```

Why generate again rather than edit:

- `a_000` had broad failures: count, material, relation, cat count, depth.
- A fresh layout is a reasonable action because the image was not yet a good local-edit base.

Execution and evaluation:

- Qwen request: `phase3_ep_001_a_001_generate`
- output image: `img_001`
- Geneval2 result: 8/11 pass
- fixed compared with `a_000`: lion glass, cat count
- persistent failures: lion count, chasing, cats behind donut

Reducer result:

- latest = `a_001`
- best = `a_001`
- remaining budget = `3`

### `turn_004` to `turn_007`: edit proposals rejected by instruction-quality gate

Teacher input state for these turns:

- latest = best = `a_001`
- visible images: `img_001`
- budget `3`
- compact history includes `a_000`, `a_001`
- persistent failures: `c_001`, `c_004`, `c_008`
- stable passes include lion glass, lion object, cat count, cat red, cat object, donut count/color/object

Teacher repeated raw intent:

- edit source `a_001`
- add exactly two glass lions to reach six total
- strengthen lion-chasing-cat relation
- make cats behind the donut clearer
- preserve stable passes

Runtime result:

- all four raw edit proposals were rejected before execution
- no image budget consumed

Important diagnosis:

- These rejections were mostly linter false positives, not semantically bad Teacher actions.
- The old instruction-quality linter misread operation counts like "add exactly two additional lions so there are exactly six" as incompatible final-count claims.
- It also treated reciprocal spatial language like "cats behind donut; donut in front of cats" as a contradiction.

Correction applied during validation:

- operation counts and final counts are now separated.
- reciprocal depth statements are not treated as contradiction by default.
- the episode resumed without rerunning completed valid image attempts.

Remaining engineering caveat:

- the exact validation rejection payload was recorded in events, but not consistently injected into the next Teacher text input. This should be fixed before larger scale rollout.

### `turn_008`: accepted local edit, creates `a_002`

Teacher input state:

- same canonical state as after `a_001`
- latest = best = `a_001`
- budget still `3`
- visible image: `img_001`
- target failures: `c_001`, `c_004`, `c_008`

Canonical action:

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_001",
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_008"
    ],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ]
  }
}
```

Edit instruction:

```text
Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene.
```

Execution and evaluation:

- Qwen request: `phase3_ep_001_a_002_edit`
- source image: `img_001`
- output image: `img_002`
- Geneval2 result: 9/11 pass
- fixed: lion count
- persistent failures: chasing and cats behind donut

Reducer result:

- latest = `a_002`
- best = `a_002`
- remaining budget = `2`

Why this is good:

- It targets only failed atoms.
- It preserves stable atoms.
- It demonstrates local repair instead of regenerating everything.

### `turn_009`: relation-focused edit, creates `a_003`

Teacher input state:

- latest = best = `a_002`
- visible image: `img_002`
- budget `2`
- compact history length 3
- only failed atoms are `c_004` and `c_008`

Canonical action:

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": [
      "c_004",
      "c_008"
    ],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ]
  }
}
```

Edit instruction:

```text
Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects.
```

Execution and evaluation:

- Qwen request: `phase3_ep_001_a_003_edit`
- source image: `img_002`
- output image: `img_003`
- Geneval2 result: 8/11 pass
- persistent failures: chasing and cats behind donut
- regression: lion glass `c_002` failed/uncertain again

Reducer result:

- latest = `a_003`
- best remains `a_002`
- remaining budget = `1`

Why this turn matters:

- It creates the key history-aware decision point.
- The latest image is now worse than the best historical image.
- The next turn tests whether Teacher follows best-so-far rather than blindly continuing from latest.

### `turn_010`: branch from best, creates `a_004`

Teacher input state:

- latest = `a_003`
- best = `a_002`
- visible images include both:
  - `LATEST_IMAGE = img_003`
  - `BEST_IMAGE = img_002`
- budget `1`
- compact history length 4
- latest transition shows `a_003` regressed `c_002`

Canonical action:

```json
{
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_002",
    "target_constraint_ids": [
      "c_004",
      "c_008"
    ],
    "preserve_constraint_ids": [
      "c_001",
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_009",
      "c_010",
      "c_011"
    ]
  }
}
```

Edit instruction:

```text
Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap.
```

Execution and evaluation:

- Qwen request: `phase3_ep_001_a_004_edit`
- source image: `img_002`, not latest `img_003`
- output image: `img_004`
- Geneval2 result: 9/11 pass
- persistent failures: chasing and cats behind donut

Reducer result:

- latest = `a_004`
- best remains `a_002`
- remaining budget = `0`

Why this is the strongest positive behavior:

- Teacher was given latest and best images separately.
- Teacher chose `source_attempt_id: a_002`, the historical best, because latest `a_003` regressed.
- This is exactly the desired best-so-far branching behavior.

### `turn_011`: submit best

Teacher input state:

- budget `0`
- latest = `a_004`
- best = `a_002`
- visible images include both latest and best
- extra observation says submit best with `best_available_under_budget`

Canonical action:

```json
{
  "schema_version": "0.2",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_002",
    "reason_code": "best_available_under_budget"
  }
}
```

Runtime result:

- accepted
- final submission written to `submission.json`
- submitted attempt = `a_002`

Why this is correct:

- `a_002` and `a_004` both pass 9/11, but `a_002` is the reducer-owned best.
- Budget is exhausted, so no further image action is legal.
- The action uses canonical reason code, not a free-form explanation.

## 8. 每个 image attempt 后 prompt/instruction 如何变化

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

`a_000` generation expands it into:

- exact one brown donut in foreground
- exact three red cats behind donut
- exact six glass lions in background chasing cats
- no extra/cropped/fused/reflected/duplicate instances

`a_001` regeneration changes strategy:

- clean white seamless studio scene
- large foreground donut
- cats in middle ground behind donut
- lions in loose arc behind cats
- stronger countability and separation constraints

`a_002` edit changes strategy:

- source is `a_001`
- add exactly two transparent glass lions
- target failed atoms only: lion count, chasing, cats behind donut
- preserve all stable passes

`a_003` edit changes strategy:

- source is `a_002`
- no count edit anymore
- focus only on depth and motion cues
- preserve nine passing atoms

`a_004` edit changes strategy:

- source goes back to `a_002`, not latest `a_003`
- repair relation/depth from the best historical image
- preserve glass/count/color/object atoms that `a_003` partly regressed

## 9. 这条轨迹为什么像我们想要的 agent trajectory

它清楚展示了以下信息流:

1. User/task input becomes `TaskSpec`.
2. `TaskSpec` becomes atomized verifier constraints.
3. Environment state becomes `PlannerView`.
4. Teacher receives PlannerView, visible images, and Skill/tool context.
5. Teacher emits exactly one proposed action JSON.
6. Runtime rejects invalid raw output or accepts canonical action.
7. Accepted image actions call Qwen-Image-Edit.
8. Geneval2 evaluates every produced image by atom.
9. Reducer computes latest/best/history/transitions.
10. Next PlannerView carries this state back to Teacher.
11. Submission picks reducer-owned best under budget.

This is close to the Gen-Searcher/GenEvolve trajectory shape in the important way:

- input context is visible;
- assistant action is explicit;
- tool/image/evaluator observation is explicit;
- next action conditions on prior observation;
- invalid or non-target records are kept as context/audit, not trained as positive assistant targets.

## 10. 已知 caveats

### Raw Teacher still makes format mistakes

`turn_001` omitted required `mode`. This was rejected correctly. It does not enter canonical action history.

Action-specific `response_format=json_schema` was tested on this exact input and returned a valid `generate_image` action with `mode: initial`. The full repository schema cannot be passed directly to the provider because this endpoint rejects `uniqueItems` and `oneOf`, so the practical implementation is a provider-compatible action-specific schema plus our full local validators.

### Linter was too strict during this run

`turn_004` to `turn_007` were rejected mostly because the instruction-quality linter over-read valid edit wording:

- operation count: "add exactly two additional lions so there are exactly six total"
- reciprocal depth: "cats behind donut" and "donut in front of cats"

The linter was patched after diagnosis, and the run resumed without rerunning valid completed attempts.

### Image task remains visually hard

Best attempt passes 9/11 but still fails:

- `c_004`: lions chasing cats
- `c_008`: cats behind donut

This does not invalidate the trajectory structure. It shows the image backend/evaluator task remains hard for relation/depth, which should later motivate edit-strategy Skills or stronger relation-specific prompts.

## 11. Suggested decision for advisor

I would ask the advisor to approve this trajectory as a valid structural exemplar for Gen-Retry v3, with the following scope:

- approve as a canonical trajectory format example;
- approve as evidence of history-aware best-so-far branching;
- approve as evidence that Skill context is integrated into prompt rewrite/edit instruction construction;
- do not claim it proves Teacher raw output is error-free;
- do not claim it solves all visual relation/depth failures.

Recommended next engineering changes before larger rollout:

1. Add provider-compatible action-specific `response_format=json_schema`.
2. Inject structured validation rejection payload into the next Teacher input.
3. Keep full local schema/reference/runtime/instruction validation as final authority.
4. Keep `query_skill` context-only for SFT until more trajectories prove retrieval utility, unless a later review changes that policy.
