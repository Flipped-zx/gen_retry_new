# Actual Normalized Trajectory: PlannerContext v0.3 `phase3_ep_001`

这份文件按“给老师看一条轨迹”的方式展示，而不是按调试日志展示。它替代原来过长的 raw trace：system prompt、全局约束和固定协议只出现一次，后续 round 用代指。

核心约定：

- `round`：一次为了产出新 image attempt 的完整过程。它可以包含 0-N 个 `query_skill` action，再接一个 `generate_image` / `edit_image` image action。
- `action step`：teacher/planner 每次输出的一个 canonical action。每个 assistant turn 仍然只输出一个 action。
- `Round 0` 由 `query_skill` 和第一次 `generate_image -> a_000` 共同构成。
- `Round 1-4` 各包含一个 image action，并分别产生 `a_001` 到 `a_004`。
- `submit_attempt` 是最终提交 action，不创建 image attempt。
- 被 validator 拒绝的 raw teacher turn 不展示；这里展示的是真正执行的 validated canonical trajectory。
- 机械字段不展开：request id、token usage、后端采样参数、完整文件路径都在 artifact 中存在，但这里不作为展示重点。
- `sha256` 是完整 system prompt 的校验指纹，用来证明 exact prompt identity；它不是 teacher 决策语义，所以本文不展示 hash，占位处直接展示 system prompt 内容。

## What Is `PlannerContext`

`PlannerContext` 是环境在每次调用 teacher 前整理出来的“当前状态包”。它不是 teacher 输出，也不是单独的 SFT target。

它的顶层结构是：

```text
task_context        原始 prompt、max attempts、Geneval2 atom constraints
latest_observation  当前 latest attempt 的图片引用和 pass/fail/uncertain atom
active_round        当前 round 已发生的 query_skill 和 active skills
episode_memory      recent_round / earlier_rounds / best_attempt
control             budget、legal actions、latest/best ids、visible images
```

一个 image-producing round 的真实结构是：

```text
PlannerContext + visible images + optional retrieved skills
  -> teacher emits query_skill, or directly emits generate_image/edit_image
  -> query_skill returns Skill content as environment context
  -> teacher emits terminal image action
  -> Qwen-Image-Edit executes the instruction
  -> Geneval2 evaluates the new image with atom VQA
  -> reducer builds RoundRecord and next PlannerContext
```

RoundRecord 是 reducer 从 immutable events 确定性构造的，不是 teacher 自己写的总结。它把当时的 action plan、最终 prompt、source attempt、result attempt、Geneval2 outcome、fixed/regressed/persistent atoms 对齐。

## Round And Action-Step Map

```text
round 0:
  action step s_000 -> query_skill
  action step s_001 -> generate_image                       -> a_000
round 1:
  action step s_002 -> edit_image(source_attempt_id=a_000)  -> a_001
round 2:
  action step s_003 -> edit_image(source_attempt_id=a_000)  -> a_002
round 3:
  action step s_004 -> edit_image(source_attempt_id=a_000)  -> a_003
round 4:
  action step s_005 -> edit_image(source_attempt_id=a_000)  -> a_004

final:
  action step s_006 -> submit_attempt(selected_attempt_id=a_004)
```

这条轨迹的重要行为：后续 edit 并没有盲目沿着 latest 继续，而是多次选择历史 best/source `a_000`。最终 `a_004` 从 `a_000` 编辑得到，并成为 best。

## Shared Task

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

Geneval2 atom constraints:

```text
c_001: count | expected=six | VQA=How many lions are in the image?
c_002: attribute | expected=Yes | VQA=Are the lions glass?
c_003: object | expected=Yes | VQA=Are there any lions in the image?
c_004: verb | expected=Yes | VQA=Are the lions chasing the cats?
c_005: count | expected=three | VQA=How many cats are in the image?
c_006: attribute | expected=Yes | VQA=Are the cats red?
c_007: object | expected=Yes | VQA=Are there any cats in the image?
c_008: position | expected=Yes | VQA=Are the cats behind the donut?
c_009: count | expected=one | VQA=How many donuts are in the image?
c_010: attribute | expected=Yes | VQA=Is the donut brown?
c_011: object | expected=Yes | VQA=Are there any donuts in the image?
```

Shared System Prompt, shown once:

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

Role:
  Verifier-grounded multimodal image retry planner. Maximize the best valid
  attempt under the remaining image-attempt budget.

Output contract:
  Return exactly one JSON object matching action_protocol_v0_3.
  No markdown, no prose, no environment facts, no paths, no scores.
  The top-level keys must be schema_version, action, arguments.

Allowed actions:
  query_skill, generate_image, edit_image, submit_attempt.

query_skill:
  arguments.skill_ids is an array.
  arguments.target_constraint_ids is an array.
  Request at most two skills.
  Do not query a Skill already active unless its content changed or a required
  operator is demonstrably absent.
  After a successful query_skill, apply the retrieved operators in the next
  image action instead of immediately querying again.

generate_image / edit_image:
  These are Planner Actions, not hidden executor internals.
  Their arguments must contain the action plan and the exact executable text
  sent to Qwen-Image-Edit.
  Include decision_summary, diagnostic_hypotheses, interventions,
  target_constraint_ids, preserve_constraint_ids, skill_ids_used, and the final
  instruction.
  Do not include strategy_tags.

Action-plan fields:
  decision_summary is a short action-choice rationale, not chain-of-thought.
  diagnostic_hypotheses bind visual failure causes to constraint IDs.
  interventions bind concrete visual changes to target constraint IDs and use
  only: instance_count_layout, spatial_relation_layout, action_pose_cue,
  attribute_binding.

Instruction fields:
  generate_image uses arguments.generation_instruction.
  edit_image uses arguments.edit_instruction.
  Generation instructions must state exact entities/counts, attributes, layout,
  relation/depth cues, visibility, separation, and no extras/fused/cropped
  instances.
  Edit instructions must include target operation, spatial grounding,
  preservation lock, and forbidden changes.

Source and budget rules:
  Use edit_image only with a source_attempt_id already visible in
  PlannerContext latest_observation, episode_memory, or control.
  Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path
  string alone.
  Compare latest and best when they differ before choosing source_attempt_id.
  If remaining_image_budget is 0, submit the best available attempt with
  reason_code = best_available_under_budget.
```

Shared User Prompt / Action Contract, shown once:

```text
Return exactly one JSON object with action = query_skill, generate_image,
edit_image, or submit_attempt.

query_skill: skill_ids + target_constraint_ids.
generate_image: action plan + generation_instruction.
edit_image: source_attempt_id + action plan + edit_instruction.
submit_attempt: selected_attempt_id + reason_code + decision_summary.

Do not output environment facts such as scores, paths, seeds, or best-so-far.
Environment outputs, images, Geneval2 results, and RoundRecords are context only.
```

## Round 0A: `query_skill`

这是 Round 0 的第一个 action step。它不调用 Qwen-Image-Edit，也不创建 attempt；它服务于下一步 prompt rewrite / first generation。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_000 start_attempt=none
  remaining_image_budget = 5
  latest_observation = none
  best_attempt = none
  visible_images = []
  active_round.planning_actions = []
  active_capability_skills = []
  episode_memory.recent_round = none
  episode_memory.earlier_rounds = []

available skills:
  counting_and_instance_layout
  spatial_relation_layout
  attribute_entity_binding
  local_edit_preservation

extra observation:
  No image attempts exist yet; do not edit or submit.
```

### Teacher Output

```json
{
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
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
query_skill returns:
  counting_and_instance_layout: Construct generation or edit instructions for exact counts by making each instance visible, separate, bounded, and countable.
  spatial_relation_layout: Construct generation or edit instructions for spatial or directional relations using anchors, depth, orientation, and visibility cues.

These skills enter the next Teacher Input through active_round.active_capability_skills.
They are environment context, not assistant targets.
```

## Round 0B: First Generation -> `a_000`

这是 Round 0 的第二个 action step。它使用 Round 0A 查询到的 Skill context，写出第一次完整 generation prompt，并产生第一张图片。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_000 start_attempt=none
  remaining_image_budget = 5
  latest_observation = none
  best_attempt = none
  visible_images = []
  active_round.planning_action = s_000 query_skill skills=[counting_and_instance_layout, spatial_relation_layout] targets=[c_001, c_004, c_005, c_008, c_009]
  active_capability_skills = [counting_and_instance_layout, spatial_relation_layout]
  episode_memory.recent_round = none
  episode_memory.earlier_rounds = []

retrieved skills:
  [counting_and_instance_layout content from Round 0A]
  [spatial_relation_layout content from Round 0A]
```

### Teacher Output

```json
{
  "action": "generate_image",
  "arguments": {
    "decision_summary": "No image exists yet, so start with a single fully constrained generation covering all required objects, counts, attributes, and relations.",
    "diagnostic_hypotheses": [
      {
        "constraint_ids": [
          "c_001",
          "c_003"
        ],
        "hypothesis": "A fresh generation may omit some lions or merge them into fewer instances unless the count is stated explicitly.",
        "visual_targets": [
          "six glass lions"
        ]
      },
      {
        "constraint_ids": [
          "c_005",
          "c_007"
        ],
        "hypothesis": "A fresh generation may omit some cats or fuse them together unless three separate cats are specified.",
        "visual_targets": [
          "three red cats"
        ]
      },
      {
        "constraint_ids": [
          "c_008",
          "c_009",
          "c_010",
          "c_011"
        ],
        "hypothesis": "The donut may be missing, the wrong color, or not clearly in front of the cats unless its count, color, and placement are explicit.",
        "visual_targets": [
          "one brown donut",
          "cats behind the donut"
        ]
      },
      {
        "constraint_ids": [
          "c_002",
          "c_004"
        ],
        "hypothesis": "The lions may not read as glass or may not clearly appear to chase the cats unless both material and action cues are spelled out.",
        "visual_targets": [
          "glass lions",
          "lions chasing cats"
        ]
      }
    ],
    "generation_instruction": "Create one clear scene with exactly six glass lions, exactly three red cats, and exactly one brown donut. Show the donut prominently in the foreground. Place all three cats behind the donut. Arrange the six lions as glass, transparent or translucent lions chasing the cats, with clear forward motion and orientation toward the cats. Keep every lion and cat fully visible, separate, and countable. Keep the donut fully visible and clearly brown. Use a simple uncluttered background, no extra animals or objects, no cropped, fused, duplicated, mirrored, or reflected instances, and no text or watermark.",
    "interventions": [
      {
        "change": "Render exactly six separate, fully visible glass lions with clear transparent material cues.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_001",
          "c_002",
          "c_003"
        ],
        "visual_targets": [
          "six glass lions"
        ]
      },
      {
        "change": "Render exactly three separate, fully visible red cats.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_005",
          "c_006",
          "c_007"
        ],
        "visual_targets": [
          "three red cats"
        ]
      },
      {
        "change": "Place one brown donut in the foreground and put the cats behind it.",
        "operation": "spatial_relation_layout",
        "target_constraint_ids": [
          "c_008",
          "c_009",
          "c_010",
          "c_011"
        ],
        "visual_targets": [
          "brown donut",
          "red cats"
        ]
      },
      {
        "change": "Pose the lions as actively chasing the cats, with forward-facing motion toward them.",
        "operation": "action_pose_cue",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      }
    ],
    "mode": "initial",
    "preserve_constraint_ids": [],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
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
    ]
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
image backend:
  generate from scratch using generation_instruction

new attempt:
  attempt_id = a_000
  image = img_000

Geneval2:
  pass = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  fail = c_001 observed='4' expected='six', c_004 observed='no' expected='Yes', c_005 observed='2' expected='three'
  uncertain = []
  score = 8/11 = 0.727

RoundRecord observed_outcome:
  comparison = {'attempt_id': None, 'reason': 'initial_generation'}
  initial_passed = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  initial_failed = [c_001, c_004, c_005]
  initial_uncertain = []
  fixed = []
  regressed = []
  persistent_failed = []
  new_uncertain = []
  preserved = []
  value = {'became_best': True, 'net_atom_gain': 0, 'score_delta': 0.7272727272727273}

state for next planner call:
  latest_attempt = a_000
  best_attempt = a_000
  remaining_budget = 4
```

## Round 1: `edit_image` -> `a_001`

Teacher 看到 `a_000` 已经通过多数非目标 atom，于是从当前 best/source `a_000` 做 edit，而不是重新生成。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_001 start_attempt=a_000
  remaining_image_budget = 4
  latest_observation = a_000 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004, c_005] uncertain=[]
  best_attempt = a_000 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004, c_005] uncertain=[]
  visible_images = [latest:a_000->IMG_000, best:a_000->IMG_000]
  active_round.planning_actions = []
  active_capability_skills = []
  episode_memory.recent_round = r_000 generate_image(source=none -> a_000); fixed=[]; regressed=[]; persistent_failed=[]
  episode_memory.earlier_rounds = []
```

### Teacher Output

```json
{
  "action": "edit_image",
  "arguments": {
    "decision_summary": "Edit the current best source because the donut, glass lion material, red cat attribute, and cat-behind-donut relation already pass; only lion count, cat count, and chase action need correction.",
    "diagnostic_hypotheses": [
      {
        "constraint_ids": [
          "c_001"
        ],
        "hypothesis": "The image shows four glass lions instead of the required six, leaving two missing lion instances.",
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "constraint_ids": [
          "c_005"
        ],
        "hypothesis": "The verifier counted only two cats, likely because one cat is not sufficiently distinct or countable; the scene needs exactly three clearly separated red cats.",
        "visual_targets": [
          "red cats"
        ]
      },
      {
        "constraint_ids": [
          "c_004"
        ],
        "hypothesis": "The lions are visible but their posture and arrangement do not clearly communicate that they are chasing the cats.",
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      }
    ],
    "edit_instruction": "Target operation: edit attempt a_000 to correct only the animal count and chase action. Add two new transparent pale-blue glass lions so there are exactly six separate glass lions total. Ensure there are exactly three separate red cats total; make each cat fully visible and countable behind the donut. Pose all six lions as actively chasing the cats, with bodies facing the cats, forward-running stances, extended paws, and clear motion toward the cats.\n\nSpatial grounding: keep the single large brown donut in the foreground. Place all three red cats behind the donut in the middle ground, separated left, center, and right. Place the six glass lions in a back row and side positions behind the cats, all oriented forward toward the cats so the chase direction reads from back to front.\n\nPreservation lock: preserve the existing glossy brown donut, its single count, its foreground position, the simple white background, the glass material and pale transparent look of the lions, the red color of the cats, and the cats-behind-donut relationship.\n\nForbidden changes: do not add or remove the donut, do not change the donut color, do not make more or fewer than six lions, do not make more or fewer than three cats, do not add extra animals or objects, do not crop, fuse, mirror, or reflect any animal instances, and do not redraw unrelated scene elements.",
    "interventions": [
      {
        "change": "Add two separate fully visible glass lions in the back row so the total is exactly six lions.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_001"
        ],
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "change": "Make exactly three fully visible, separated red cats behind the donut, with no hidden or fused cat bodies.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_005"
        ],
        "visual_targets": [
          "red cats"
        ]
      },
      {
        "change": "Repose and orient all six glass lions as running forward toward the three red cats, with raised paws and forward motion cues.",
        "operation": "action_pose_cue",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      },
      {
        "change": "Keep the cats spatially behind the foreground brown donut while the lions chase from farther behind them.",
        "operation": "spatial_relation_layout",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats",
          "brown donut"
        ]
      }
    ],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010",
      "c_011"
    ],
    "skill_ids_used": [],
    "source_attempt_id": "a_000",
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_005"
    ]
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
image backend:
  edit source_attempt_id=a_000 using edit_instruction

new attempt:
  attempt_id = a_001
  image = img_001
  parent/source = a_000

Geneval2:
  pass = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  fail = c_001 observed='4' expected='six', c_004 observed='no' expected='Yes', c_005 observed='2' expected='three'
  uncertain = []
  score = 8/11 = 0.727

RoundRecord observed_outcome:
  comparison = {'attempt_id': 'a_000', 'reason': 'edit_source'}
  fixed = []
  regressed = []
  persistent_failed = [c_001, c_004, c_005]
  new_uncertain = []
  preserved = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  value = {'became_best': False, 'net_atom_gain': 0, 'score_delta': 0.0}

state for next planner call:
  latest_attempt = a_001
  best_attempt = a_000
  remaining_budget = 3
```

## Round 2: `edit_image` -> `a_002`

`a_001` 没有提升 best，Teacher 回到 `a_000` 继续尝试修 lion count 和 chasing。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_002 start_attempt=a_001
  remaining_image_budget = 3
  latest_observation = a_001 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004, c_005] uncertain=[]
  best_attempt = a_000 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004, c_005] uncertain=[]
  visible_images = [latest:a_001->IMG_001, best:a_000->IMG_000]
  active_round.planning_actions = []
  active_capability_skills = []
  episode_memory.recent_round = r_001 edit_image(source=a_000 -> a_001); fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
  episode_memory.earlier_rounds = r_000:generate_image none->a_000 fixed=[] regressed=[]
```

### Teacher Output

```json
{
  "action": "edit_image",
  "arguments": {
    "decision_summary": "Use the best prior attempt as the source because it already preserves the donut and three cats, while only the lion count and chase pose remain unresolved.",
    "diagnostic_hypotheses": [
      {
        "constraint_ids": [
          "c_001"
        ],
        "hypothesis": "The scene still contains only four lions instead of six, so two additional distinct glass lions are needed.",
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "constraint_ids": [
          "c_004"
        ],
        "hypothesis": "The lions are present but their orientation and motion do not clearly read as chasing the cats.",
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      }
    ],
    "edit_instruction": "Target operation: edit attempt a_000 by adding exactly two distinct glass lions and re-posing all six lions so they clearly chase the cats. Keep the lions transparent/glass and fully visible, with all six countable.\n\nSpatial grounding: keep the single brown donut in the foreground center. Keep exactly three red cats behind the donut in the middle ground, separated and fully visible. Place the six glass lions behind the cats in the background, oriented toward the cats with forward motion and pursuit cues.\n\nPreservation lock: preserve the existing donut count of one, the brown donut color, the three red cats, the cats-behind-donut relationship, the glass appearance of the lions, the simple white background, and the overall clean scene composition.\n\nForbidden changes: do not add or remove cats or donuts, do not make fewer or more than six lions, do not change the cats from red, do not change the donut from brown, do not crop, fuse, mirror, or hide any animal instance, and do not introduce extra objects or scene clutter.",
    "interventions": [
      {
        "change": "Add exactly two new separate glass lions so the total is six, keeping all lions fully visible and countable.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_001"
        ],
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "change": "Repose all six glass lions with forward-running bodies, heads aimed toward the cats, and clear pursuit motion so the chase is unmistakable.",
        "operation": "action_pose_cue",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      },
      {
        "change": "Keep the lions positioned behind the three red cats and keep the cats behind the foreground donut so the pursuit reads from back to front.",
        "operation": "spatial_relation_layout",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats",
          "brown donut"
        ]
      }
    ],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010",
      "c_011"
    ],
    "skill_ids_used": [],
    "source_attempt_id": "a_000",
    "target_constraint_ids": [
      "c_001",
      "c_004"
    ]
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
image backend:
  edit source_attempt_id=a_000 using edit_instruction

new attempt:
  attempt_id = a_002
  image = img_002
  parent/source = a_000

Geneval2:
  pass = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  fail = c_001 observed='4' expected='six', c_004 observed='no' expected='Yes'
  uncertain = c_005 observed='4' expected='three'
  score = 8/11 = 0.727

RoundRecord observed_outcome:
  comparison = {'attempt_id': 'a_000', 'reason': 'edit_source'}
  fixed = []
  regressed = []
  persistent_failed = [c_001, c_004, c_005]
  new_uncertain = [c_005]
  preserved = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  value = {'became_best': False, 'net_atom_gain': 0, 'score_delta': 0.0}

state for next planner call:
  latest_attempt = a_002
  best_attempt = a_000
  remaining_budget = 2
```

## Round 3: `edit_image` -> `a_003`

Teacher 仍选择 `a_000` 作为 source，尝试重排 lion group 和动作线索。该步修复 cat count，但回退 glass attribute。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_003 start_attempt=a_002
  remaining_image_budget = 2
  latest_observation = a_002 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004] uncertain=[c_005]
  best_attempt = a_000 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004, c_005] uncertain=[]
  visible_images = [latest:a_002->IMG_002, best:a_000->IMG_000]
  active_round.planning_actions = []
  active_capability_skills = []
  episode_memory.recent_round = r_002 edit_image(source=a_000 -> a_002); fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
  episode_memory.earlier_rounds = r_000:generate_image none->a_000 fixed=[] regressed=[] | r_001:edit_image a_000->a_001 fixed=[] regressed=[]
```

### Teacher Output

```json
{
  "action": "edit_image",
  "arguments": {
    "decision_summary": "Edit the best source because it has the correct three red cats behind one brown donut, while the unresolved failures are the lion count and clear chase action.",
    "diagnostic_hypotheses": [
      {
        "constraint_ids": [
          "c_001"
        ],
        "hypothesis": "The image shows only four distinct glass lions instead of six.",
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "constraint_ids": [
          "c_004"
        ],
        "hypothesis": "The lions are arranged too frontally and do not clearly read as pursuing the cats.",
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      }
    ],
    "edit_instruction": "Target operation: edit attempt a_000 by replacing only the glass-lion group with exactly six distinct glass lions total. Make the six lions smaller if needed so all six are fully visible, separated, and easy to count, arranged as two staggered rows of three behind the cats. Keep each lion transparent blue-green glass.\n\nSpatial grounding: keep the single large brown donut in the foreground. Keep exactly three red cats behind the donut in the middle ground. Place all six glass lions behind the cats in the background, with each lion running toward the cats so the lions are clearly chasing the cats from back to front.\n\nPreservation lock: preserve the one brown donut, the donut position and hole, the exactly three red cats, the cats' red color, the cats-behind-donut relationship, the clean white background, and the glossy glass material of the lions.\n\nForbidden changes: do not add or remove cats or donuts, do not change the cats from red, do not change the donut from brown, do not create fewer or more than six lions, do not crop, overlap, fuse, mirror, or hide any lion or cat, and do not add extra objects, text, labels, scenery, or clutter.",
    "interventions": [
      {
        "change": "Replace the current lion group with exactly six smaller, fully separated, fully visible glass lions arranged in two staggered rows of three behind the cats.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_001"
        ],
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "change": "Pose every lion as running forward with heads and bodies aimed toward the red cats, using pursuit spacing from the background toward the cats.",
        "operation": "action_pose_cue",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      },
      {
        "change": "Keep all six lions behind the three cats, and keep the three cats behind the foreground donut so the chase reads back-to-front.",
        "operation": "spatial_relation_layout",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats",
          "brown donut"
        ]
      }
    ],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_005",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010",
      "c_011"
    ],
    "skill_ids_used": [],
    "source_attempt_id": "a_000",
    "target_constraint_ids": [
      "c_001",
      "c_004"
    ]
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
image backend:
  edit source_attempt_id=a_000 using edit_instruction

new attempt:
  attempt_id = a_003
  image = img_003
  parent/source = a_000

Geneval2:
  pass = [c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
  fail = c_001 observed='4' expected='six', c_002 observed='no' expected='Yes', c_004 observed='no' expected='Yes'
  uncertain = []
  score = 8/11 = 0.727

RoundRecord observed_outcome:
  comparison = {'attempt_id': 'a_000', 'reason': 'edit_source'}
  fixed = [c_005]
  regressed = [c_002]
  persistent_failed = [c_001, c_004]
  new_uncertain = []
  preserved = [c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  value = {'became_best': False, 'net_atom_gain': 0, 'score_delta': 0.0}

state for next planner call:
  latest_attempt = a_003
  best_attempt = a_000
  remaining_budget = 1
```

## Round 4: `edit_image` -> `a_004`

这是最后一次 image attempt。Teacher 明确选择 historical best/source `a_000`，而不是 latest `a_003`，因为 latest 出现了 glass-lion attribute regression。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_004 start_attempt=a_003
  remaining_image_budget = 1
  latest_observation = a_003 pass=[c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_002, c_004] uncertain=[]
  best_attempt = a_000 pass=[c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_001, c_004, c_005] uncertain=[]
  visible_images = [latest:a_003->IMG_003, best:a_000->IMG_000]
  active_round.planning_actions = []
  active_capability_skills = []
  episode_memory.recent_round = r_003 edit_image(source=a_000 -> a_003); fixed=[c_005]; regressed=[c_002]; persistent_failed=[c_001, c_004]
  episode_memory.earlier_rounds = r_000:generate_image none->a_000 fixed=[] regressed=[] | r_001:edit_image a_000->a_001 fixed=[] regressed=[] | r_002:edit_image a_000->a_002 fixed=[] regressed=[]
```

### Teacher Output

```json
{
  "action": "edit_image",
  "arguments": {
    "decision_summary": "Use the historical best source rather than the latest because the best preserves the glass-lion attribute, while one final edit can still target the unresolved lion count, cat count clarity, and chase action.",
    "diagnostic_hypotheses": [
      {
        "constraint_ids": [
          "c_001"
        ],
        "hypothesis": "Only four distinct lions are visible instead of six, so two additional glass lions must be added without disturbing the existing objects.",
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "constraint_ids": [
          "c_004"
        ],
        "hypothesis": "The pursuit is not explicit enough because the lions read as posed behind the cats rather than actively chasing them.",
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      },
      {
        "constraint_ids": [
          "c_005"
        ],
        "hypothesis": "The three red cats need to remain separated and fully visible so the count is unambiguous.",
        "visual_targets": [
          "red cats"
        ]
      }
    ],
    "edit_instruction": "Target operation: edit attempt a_000 by keeping the current scene but add exactly two more transparent blue-green glass lions to the existing lion group, making exactly six glass lions total. Keep exactly three red cats total, fully visible and separated. Make all six lions clearly running after the cats, with forward-leaning bodies, raised paws, and heads aimed toward the cats.\n\nSpatial grounding: keep the single large brown donut in the foreground. Keep the three red cats behind the donut in the middle ground, separated left, center, and right. Place the six glass lions behind the cats in the background as a visible pursuit pack: four existing lions plus two added lions in the rear gaps, all oriented from the back toward the cats and donut.\n\nPreservation lock: preserve the donut as one brown donut with its hole, preserve the cats' red color and the cats-behind-donut relationship, preserve the clean white background, and preserve the lions as transparent translucent glass lions.\n\nForbidden changes: do not remove or recolor any cat, do not add extra cats, do not add or remove donuts, do not make the lions solid or furry, do not create fewer or more than six lions, do not crop, hide, fuse, mirror, or overlap animals so they become hard to count, and do not add text, labels, scenery, or extra objects.",
    "interventions": [
      {
        "change": "Add exactly two additional separated glass lions to the existing four-lion group so the final total is six fully visible lions.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_001"
        ],
        "visual_targets": [
          "glass lions"
        ]
      },
      {
        "change": "Keep exactly three separated red cats visible behind the donut with no extra or missing cats.",
        "operation": "instance_count_layout",
        "target_constraint_ids": [
          "c_005"
        ],
        "visual_targets": [
          "red cats"
        ]
      },
      {
        "change": "Pose every lion as actively running toward the red cats, with the cats visually fleeing in front of the lion pack.",
        "operation": "action_pose_cue",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats"
        ]
      },
      {
        "change": "Maintain clear foreground donut, middle-ground cats, and background lions so the chase reads from back to front.",
        "operation": "spatial_relation_layout",
        "target_constraint_ids": [
          "c_004"
        ],
        "visual_targets": [
          "glass lions",
          "red cats",
          "brown donut"
        ]
      }
    ],
    "preserve_constraint_ids": [
      "c_002",
      "c_003",
      "c_006",
      "c_007",
      "c_008",
      "c_009",
      "c_010",
      "c_011"
    ],
    "skill_ids_used": [],
    "source_attempt_id": "a_000",
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_005"
    ]
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
image backend:
  edit source_attempt_id=a_000 using edit_instruction

new attempt:
  attempt_id = a_004
  image = img_004
  parent/source = a_000

Geneval2:
  pass = [c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
  fail = c_004 observed='no' expected='Yes'
  uncertain = []
  score = 10/11 = 0.909

RoundRecord observed_outcome:
  comparison = {'attempt_id': 'a_000', 'reason': 'edit_source'}
  fixed = [c_001, c_005]
  regressed = []
  persistent_failed = [c_004]
  new_uncertain = []
  preserved = [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  value = {'became_best': True, 'net_atom_gain': 2, 'score_delta': 0.18181818181818182}

state for next planner call:
  latest_attempt = a_004
  best_attempt = a_004
  remaining_budget = 0
```

## Submit

这是最终 action step。它是 teacher 的正式 action，但不创建新的 image attempt。

### Teacher Input

```text
system:
  [Shared System Prompt above]

user:
  [Shared User Prompt / Action Contract above]

task:
  [shared original prompt + c_001 ... c_011 atom constraints]

PlannerContext:
  current_round = r_005 start_attempt=a_004
  remaining_image_budget = 0
  latest_observation = a_004 pass=[c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_004] uncertain=[]
  best_attempt = a_004 pass=[c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011] fail=[c_004] uncertain=[]
  visible_images = [latest:a_004->IMG_004, best:a_004->IMG_004]
  active_round.planning_actions = []
  active_capability_skills = []
  episode_memory.recent_round = r_004 edit_image(source=a_000 -> a_004); fixed=[c_001, c_005]; regressed=[]; persistent_failed=[c_004]
  episode_memory.earlier_rounds = r_000:generate_image none->a_000 fixed=[] regressed=[] | r_001:edit_image a_000->a_001 fixed=[] regressed=[] | r_002:edit_image a_000->a_002 fixed=[] regressed=[] | r_003:edit_image a_000->a_003 fixed=[c_005] regressed=[c_002]

extra observation:
  remaining_image_budget = 0; submit the best available attempt.
```

### Teacher Output

```json
{
  "action": "submit_attempt",
  "arguments": {
    "decision_summary": "The image-attempt budget is exhausted, so submit the historical best attempt despite the remaining chase-action failure.",
    "reason_code": "best_available_under_budget",
    "selected_attempt_id": "a_004"
  },
  "schema_version": "0.3"
}
```

### Environment Output

```text
submitted_attempt_id = a_004
best_attempt_id = a_004
attempt_order = a_000 -> a_001 -> a_002 -> a_003 -> a_004

Final Geneval2:
  pass = [c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
  fail = c_004 observed='no' expected='Yes'
  uncertain = []
  score = 10/11 = 0.909
```

## What This Trajectory Demonstrates

```text
round 0 / action step s_000:
  teacher queries counting and spatial skills before first prompt rewrite

round 0 / action step s_001:
  teacher writes a full generation action plan and generation_instruction

rounds 1-4 / action steps s_002-s_005:
  teacher repeatedly sees latest_observation + recent_round/earlier_round memory
  and chooses an edit source explicitly, usually historical best/source a_000

round 3:
  the edit fixes c_005 but regresses c_002, and this regression becomes visible
  in the next PlannerContext

round 4:
  teacher avoids latest a_003, edits historical source a_000, fixes c_001/c_005,
  preserves the previously passed atoms, and leaves only c_004 chasing failed

final:
  budget is exhausted; teacher submits best attempt a_004
```

For SFT display, the training target is the `Teacher Output` block in each step. `Teacher Input`, Skill results, Qwen images, Geneval2 results, RoundRecords, and best/latest updates are context or environment observation only.
