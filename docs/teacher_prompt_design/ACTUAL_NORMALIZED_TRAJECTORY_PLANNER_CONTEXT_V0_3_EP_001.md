# Actual Normalized Trajectory: Planner IO Flow `phase3_ep_001`

这份文件按“输入如何进入 Planner、Planner 输出什么、环境如何更新下一轮输入”的顺序展示一条轨迹。

它借用 `docs/phase3/gen_retry_planner_io_field_design_phase3_ep001.md` 的五区展示法：

```text
PlannerContext
├── task_context
├── latest_observation
├── skill_context
├── episode_memory
└── runtime_state
```

说明：当前代码 artifact 中的实际字段名仍包含 `active_round` 和 `control`；本文为了给老师说明输入/输出逻辑，将它们归一展示为更直观的 `skill_context` 和 `runtime_state`。底层事件、hash、request id、路径、seed、token usage 不在本文展开。

---

## 1. Global Task Construction

原始输入 prompt：

```text
six glass lions chasing three red cats behind a brown donut
```

系统先将其拆成全局 atom constraints。这个 `task_context` 在整个 episode 中保持不变：

```text
c_001: six lions
c_002: lions are glass
c_003: lions exist
c_004: lions are chasing the cats
c_005: three cats
c_006: cats are red
c_007: cats exist
c_008: cats are behind the donut
c_009: one donut
c_010: donut is brown
c_011: donut exists
```

Geneval2 后续就是围绕这些 atom 做 VQA 评价，例如 `c_004` 对应：`Are the lions chasing the cats?`。

Image budget：最多 5 次 `generate_image` / `edit_image`。`query_skill` 和 `submit_attempt` 不消耗 image budget。

---

## 2. Shared Planner Output Contract

每次 teacher/planner 只输出一个 canonical Action：

```text
query_skill
generate_image
edit_image
submit_attempt
```

对 image Action，本文展示以下核心字段：

```yaml
decision_summary: 为什么选择这个 action / source
diagnosis_summary: 对失败原因的总体视觉判断，来自实际 diagnostic_hypotheses 的压缩表达
target_constraint_ids: 本轮要修哪些 atom
preserve_constraint_ids: 本轮要保护哪些已通过 atom
interventions: 当前 v0.3 canonical action 中保留的结构化视觉干预
generation_instruction / edit_instruction: 最终发给 Qwen-Image-Edit 的可执行 prompt
```

训练展示时，`Teacher Output` 是 assistant target；Skill 返回、Qwen 图片、Geneval2 结果、RoundRecord 和 best/latest 更新都是 environment observation。

---

## 3. Round / Action-Step Map

```text
Round 0A: action step s_000 -> query_skill
Round 0B: action step s_001 -> generate_image                      -> a_000
Round 1:  action step s_002 -> edit_image(source_attempt_id=a_000) -> a_001
Round 2:  action step s_003 -> edit_image(source_attempt_id=a_000) -> a_002
Round 3:  action step s_004 -> edit_image(source_attempt_id=a_000) -> a_003
Round 4:  action step s_005 -> edit_image(source_attempt_id=a_000) -> a_004
Final:    action step s_006 -> submit_attempt(selected_attempt_id=a_004)
```

---

## 4. Step 0：首次 Planner 调用 -> `query_skill`

此时只有全局任务，没有图片、没有 Skill 内容、没有历史。

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    null

  skill_context:
    active_skills: []

  episode_memory:
    recent_round:
      null
    earlier_rounds:
      []
    best_attempt:
      null

  runtime_state:
    remaining_image_budget: 5
    available_actions: [query_skill, generate_image]
```

### Teacher Output

```yaml
action: query_skill
skill_ids: [counting_and_instance_layout, spatial_relation_layout]
target_constraint_ids: [c_001, c_004, c_005, c_008, c_009]
```

### Environment Output

```yaml
skill_context added for the same Round 0:
  - skill_id: counting_and_instance_layout
    target_constraint_ids: [c_001, c_005, c_009]
    content: Make each instance visible, separated, bounded, and countable.
  - skill_id: spatial_relation_layout
    target_constraint_ids: [c_004, c_008]
    content: Use anchors, depth, orientation, and visibility cues for relations.

latest_observation: null
episode_memory: empty
remaining_image_budget: 5
```

---

## 5. Step 1：Skill-conditioned Planner 输入 -> `generate_image -> a_000`

与 Step 0 相比，唯一新增的是 `skill_context.active_skills`；仍然没有图片和历史结果。

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    null

  skill_context:
    active_skills:
      - skill_id: counting_and_instance_layout
        target_constraint_ids: [c_001, c_005, c_009]
        content: Make each instance visible, separated, bounded, and countable.
      - skill_id: spatial_relation_layout
        target_constraint_ids: [c_004, c_008]
        content: Use anchors, depth, orientation, and visibility cues for relations.

  episode_memory:
    recent_round:
      null
    earlier_rounds:
      []
    best_attempt:
      null

  runtime_state:
    remaining_image_budget: 5
    available_actions: [query_skill, generate_image]
```

### Teacher Output

```yaml
action: generate_image
mode: initial
decision_summary: No image exists yet, so start with a single fully constrained generation covering all required objects, counts, attributes, and relations.
diagnosis_summary: c_001,c_003: A fresh generation may omit some lions or merge them into fewer instances unless the count is stated explicitly. / c_005,c_007: A fresh generation may omit some cats or fuse them together unless three separate cats are specified. / c_008,c_009,c_010,c_011: The donut may be missing, the wrong color, or not clearly in front of the cats unless its count, color, and placement are explicit. / c_002,c_004: The lions may not read as glass or may not clearly appear to chase the cats unless both material and action cues are spelled out.
target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
preserve_constraint_ids: []
skill_ids_used: [counting_and_instance_layout, spatial_relation_layout]
interventions:
  - instance_count_layout targets=[c_001, c_002, c_003]: Render exactly six separate, fully visible glass lions with clear transparent material cues.
  - instance_count_layout targets=[c_005, c_006, c_007]: Render exactly three separate, fully visible red cats.
  - spatial_relation_layout targets=[c_008, c_009, c_010, c_011]: Place one brown donut in the foreground and put the cats behind it.
  - action_pose_cue targets=[c_004]: Pose the lions as actively chasing the cats, with forward-facing motion toward them.
generation_instruction: |-
  Create one clear scene with exactly six glass lions, exactly three red cats, and exactly one brown donut. Show the donut prominently in the foreground. Place all three cats behind the donut. Arrange the six lions as glass, transparent or translucent lions chasing the cats, with clear forward motion and orientation toward the cats. Keep every lion and cat fully visible, separate, and countable. Keep the donut fully visible and clearly brown. Use a simple uncluttered background, no extra animals or objects, no cropped, fused, duplicated, mirrored, or reflected instances, and no text or watermark.
```

### Environment Output

```yaml
Qwen-Image-Edit: generate from scratch
new_attempt: a_000
Geneval2:
  score: 8/11
  passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  failed: c_001 observed='4' expected='six'; c_004 observed='no' expected='Yes'; c_005 observed='2' expected='three'
  uncertain: []

RoundRecord r_000:
  queried_skills: [counting_and_instance_layout, spatial_relation_layout]
  image_action: generate_image
  result_attempt_id: a_000
  initial_failed: [c_001, c_004, c_005]
  became_best: True

Next PlannerContext changes:
  latest_observation: a_000
  episode_memory.recent_round: r_000
  episode_memory.best_attempt: a_000
  remaining_image_budget: 4
```

---

## 6. Step 2：Planner 输入包含上一轮结果 -> `edit_image -> a_001`

这一轮开始，Planner 第一次看到 `latest_observation` 和 `episode_memory.recent_round`。

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    attempt_id: a_000
    image_role: LATEST_IMAGE
    passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_001, c_004, c_005]
    uncertain: []

  skill_context:
    active_skills: []

  episode_memory:
    recent_round:
      action: generate_image
      source_attempt_id: null
      result_attempt_id: a_000
      decision_summary: No image exists yet, so start with a single fully constrained generation covering all required objects, counts, attributes, and relations.
      target_constraint_ids: [c_001, c_002, c_003, c_004, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
      fixed: []
      regressed: []
      persistent_failed: []
    earlier_rounds:
      []
    best_attempt:
      attempt_id: a_000
      image_role: BEST_IMAGE
      passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
      failed: [c_001, c_004, c_005]
      uncertain: []

  runtime_state:
    remaining_image_budget: 4
    available_actions: [query_skill, generate_image, edit_image, submit_attempt]
```

### Teacher Output

```yaml
action: edit_image
source_attempt_id: a_000
decision_summary: Edit the current best source because the donut, glass lion material, red cat attribute, and cat-behind-donut relation already pass; only lion count, cat count, and chase action need correction.
diagnosis_summary: c_001: The image shows four glass lions instead of the required six, leaving two missing lion instances. / c_005: The verifier counted only two cats, likely because one cat is not sufficiently distinct or countable; the scene needs exactly three clearly separated red cats. / c_004: The lions are visible but their posture and arrangement do not clearly communicate that they are chasing the cats.
target_constraint_ids: [c_001, c_004, c_005]
preserve_constraint_ids: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
interventions:
  - instance_count_layout targets=[c_001]: Add two separate fully visible glass lions in the back row so the total is exactly six lions.
  - instance_count_layout targets=[c_005]: Make exactly three fully visible, separated red cats behind the donut, with no hidden or fused cat bodies.
  - action_pose_cue targets=[c_004]: Repose and orient all six glass lions as running forward toward the three red cats, with raised paws and forward motion cues.
  - spatial_relation_layout targets=[c_004]: Keep the cats spatially behind the foreground brown donut while the lions chase from farther behind them.
edit_instruction: |-
  Target operation: edit attempt a_000 to correct only the animal count and chase action. Add two new transparent pale-blue glass lions so there are exactly six separate glass lions total. Ensure there are exactly three separate red cats total; make each cat fully visible and countable behind the donut. Pose all six lions as actively chasing the cats, with bodies facing the cats, forward-running stances, extended paws, and clear motion toward the cats.

  Spatial grounding: keep the single large brown donut in the foreground. Place all three red cats behind the donut in the middle ground, separated left, center, and right. Place the six glass lions in a back row and side positions behind the cats, all oriented forw ... [instruction continues in canonical artifact]
```

### Environment Output

```yaml
Qwen-Image-Edit: edit source_attempt_id=a_000
new_attempt: a_001
Geneval2:
  score: 8/11
  passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  failed: c_001 observed='4' expected='six'; c_004 observed='no' expected='Yes'; c_005 observed='2' expected='three'
  uncertain: []

RoundRecord r_001:
  source_attempt_id: a_000
  result_attempt_id: a_001
  fixed: []
  regressed: []
  persistent_failed: [c_001, c_004, c_005]
  became_best: False

Next PlannerContext changes:
  latest_observation: a_001
  best_attempt: a_000
  remaining_image_budget: 3
```

---

## 7. Step 3：Planner 输入包含上一轮结果 -> `edit_image -> a_002`

这一轮 Planner 会看到前一轮 action 的结果，以及更早尝试的压缩摘要。

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    attempt_id: a_001
    image_role: LATEST_IMAGE
    passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_001, c_004, c_005]
    uncertain: []

  skill_context:
    active_skills: []

  episode_memory:
    recent_round:
      action: edit_image
      source_attempt_id: a_000
      result_attempt_id: a_001
      decision_summary: Edit the current best source because the donut, glass lion material, red cat attribute, and cat-behind-donut relation already pass; only lion count, cat count, and chase action need correction.
      target_constraint_ids: [c_001, c_004, c_005]
      fixed: []
      regressed: []
      persistent_failed: [c_001, c_004, c_005]
    earlier_rounds:
      - r_000: generate_image null -> a_000; fixed=[]; regressed=[]; persistent_failed=[]
    best_attempt:
      attempt_id: a_000
      image_role: BEST_IMAGE
      passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
      failed: [c_001, c_004, c_005]
      uncertain: []

  runtime_state:
    remaining_image_budget: 3
    available_actions: [query_skill, generate_image, edit_image, submit_attempt]
```

### Teacher Output

```yaml
action: edit_image
source_attempt_id: a_000
decision_summary: Use the best prior attempt as the source because it already preserves the donut and three cats, while only the lion count and chase pose remain unresolved.
diagnosis_summary: c_001: The scene still contains only four lions instead of six, so two additional distinct glass lions are needed. / c_004: The lions are present but their orientation and motion do not clearly read as chasing the cats.
target_constraint_ids: [c_001, c_004]
preserve_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
interventions:
  - instance_count_layout targets=[c_001]: Add exactly two new separate glass lions so the total is six, keeping all lions fully visible and countable.
  - action_pose_cue targets=[c_004]: Repose all six glass lions with forward-running bodies, heads aimed toward the cats, and clear pursuit motion so the chase is unmistakable.
  - spatial_relation_layout targets=[c_004]: Keep the lions positioned behind the three red cats and keep the cats behind the foreground donut so the pursuit reads from back to front.
edit_instruction: |-
  Target operation: edit attempt a_000 by adding exactly two distinct glass lions and re-posing all six lions so they clearly chase the cats. Keep the lions transparent/glass and fully visible, with all six countable.

  Spatial grounding: keep the single brown donut in the foreground center. Keep exactly three red cats behind the donut in the middle ground, separated and fully visible. Place the six glass lions behind the cats in the background, oriented toward the cats with forward motion and pursuit cues.

  Preservation lock: preserve the existing donut count of one, the brown donut color, the three red cats, the cats-behind-donut relationship, the glass appearance of the lions, the simple white background, and t ... [instruction continues in canonical artifact]
```

### Environment Output

```yaml
Qwen-Image-Edit: edit source_attempt_id=a_000
new_attempt: a_002
Geneval2:
  score: 8/11
  passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
  failed: c_001 observed='4' expected='six'; c_004 observed='no' expected='Yes'
  uncertain: c_005 observed='4' expected='three'

RoundRecord r_002:
  source_attempt_id: a_000
  result_attempt_id: a_002
  fixed: []
  regressed: []
  persistent_failed: [c_001, c_004, c_005]
  became_best: False

Next PlannerContext changes:
  latest_observation: a_002
  best_attempt: a_000
  remaining_image_budget: 2
```

---

## 8. Step 4：Planner 输入包含上一轮结果 -> `edit_image -> a_003`

这一轮 Planner 会看到前一轮 action 的结果，以及更早尝试的压缩摘要。

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    attempt_id: a_002
    image_role: LATEST_IMAGE
    passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_001, c_004]
    uncertain: [c_005]

  skill_context:
    active_skills: []

  episode_memory:
    recent_round:
      action: edit_image
      source_attempt_id: a_000
      result_attempt_id: a_002
      decision_summary: Use the best prior attempt as the source because it already preserves the donut and three cats, while only the lion count and chase pose remain unresolved.
      target_constraint_ids: [c_001, c_004]
      fixed: []
      regressed: []
      persistent_failed: [c_001, c_004, c_005]
    earlier_rounds:
      - r_000: generate_image null -> a_000; fixed=[]; regressed=[]; persistent_failed=[]
      - r_001: edit_image a_000 -> a_001; fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
    best_attempt:
      attempt_id: a_000
      image_role: BEST_IMAGE
      passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
      failed: [c_001, c_004, c_005]
      uncertain: []

  runtime_state:
    remaining_image_budget: 2
    available_actions: [query_skill, generate_image, edit_image, submit_attempt]
```

### Teacher Output

```yaml
action: edit_image
source_attempt_id: a_000
decision_summary: Edit the best source because it has the correct three red cats behind one brown donut, while the unresolved failures are the lion count and clear chase action.
diagnosis_summary: c_001: The image shows only four distinct glass lions instead of six. / c_004: The lions are arranged too frontally and do not clearly read as pursuing the cats.
target_constraint_ids: [c_001, c_004]
preserve_constraint_ids: [c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
interventions:
  - instance_count_layout targets=[c_001]: Replace the current lion group with exactly six smaller, fully separated, fully visible glass lions arranged in two staggered rows of three behind the cats.
  - action_pose_cue targets=[c_004]: Pose every lion as running forward with heads and bodies aimed toward the red cats, using pursuit spacing from the background toward the cats.
  - spatial_relation_layout targets=[c_004]: Keep all six lions behind the three cats, and keep the three cats behind the foreground donut so the chase reads back-to-front.
edit_instruction: |-
  Target operation: edit attempt a_000 by replacing only the glass-lion group with exactly six distinct glass lions total. Make the six lions smaller if needed so all six are fully visible, separated, and easy to count, arranged as two staggered rows of three behind the cats. Keep each lion transparent blue-green glass.

  Spatial grounding: keep the single large brown donut in the foreground. Keep exactly three red cats behind the donut in the middle ground. Place all six glass lions behind the cats in the background, with each lion running toward the cats so the lions are clearly chasing the cats from back to front.

  Preservation lock: preserve the one brown donut, the donut position and hole, the exactly three r ... [instruction continues in canonical artifact]
```

### Environment Output

```yaml
Qwen-Image-Edit: edit source_attempt_id=a_000
new_attempt: a_003
Geneval2:
  score: 8/11
  passed: [c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
  failed: c_001 observed='4' expected='six'; c_002 observed='no' expected='Yes'; c_004 observed='no' expected='Yes'
  uncertain: []

RoundRecord r_003:
  source_attempt_id: a_000
  result_attempt_id: a_003
  fixed: [c_005]
  regressed: [c_002]
  persistent_failed: [c_001, c_004]
  became_best: False

Next PlannerContext changes:
  latest_observation: a_003
  best_attempt: a_000
  remaining_image_budget: 1
  memory warning: regressed [c_002]
```

---

## 9. Step 5：latest/best 分离后回到历史 source -> `edit_image -> a_004`

这一轮的关键是：latest `a_003` 出现 `c_002` regression，Planner 选择回到历史 source `a_000`，而不是沿着 latest 继续。

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    attempt_id: a_003
    image_role: LATEST_IMAGE
    passed: [c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_001, c_002, c_004]
    uncertain: []

  skill_context:
    active_skills: []

  episode_memory:
    recent_round:
      action: edit_image
      source_attempt_id: a_000
      result_attempt_id: a_003
      decision_summary: Edit the best source because it has the correct three red cats behind one brown donut, while the unresolved failures are the lion count and clear chase action.
      target_constraint_ids: [c_001, c_004]
      fixed: [c_005]
      regressed: [c_002]
      persistent_failed: [c_001, c_004]
    earlier_rounds:
      - r_000: generate_image null -> a_000; fixed=[]; regressed=[]; persistent_failed=[]
      - r_001: edit_image a_000 -> a_001; fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
      - r_002: edit_image a_000 -> a_002; fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
    best_attempt:
      attempt_id: a_000
      image_role: BEST_IMAGE
      passed: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
      failed: [c_001, c_004, c_005]
      uncertain: []

  runtime_state:
    remaining_image_budget: 1
    available_actions: [query_skill, generate_image, edit_image, submit_attempt]
```

### Teacher Output

```yaml
action: edit_image
source_attempt_id: a_000
decision_summary: Use the historical best source rather than the latest because the best preserves the glass-lion attribute, while one final edit can still target the unresolved lion count, cat count clarity, and chase action.
diagnosis_summary: c_001: Only four distinct lions are visible instead of six, so two additional glass lions must be added without disturbing the existing objects. / c_004: The pursuit is not explicit enough because the lions read as posed behind the cats rather than actively chasing them. / c_005: The three red cats need to remain separated and fully visible so the count is unambiguous.
target_constraint_ids: [c_001, c_004, c_005]
preserve_constraint_ids: [c_002, c_003, c_006, c_007, c_008, c_009, c_010, c_011]
interventions:
  - instance_count_layout targets=[c_001]: Add exactly two additional separated glass lions to the existing four-lion group so the final total is six fully visible lions.
  - instance_count_layout targets=[c_005]: Keep exactly three separated red cats visible behind the donut with no extra or missing cats.
  - action_pose_cue targets=[c_004]: Pose every lion as actively running toward the red cats, with the cats visually fleeing in front of the lion pack.
  - spatial_relation_layout targets=[c_004]: Maintain clear foreground donut, middle-ground cats, and background lions so the chase reads from back to front.
edit_instruction: |-
  Target operation: edit attempt a_000 by keeping the current scene but add exactly two more transparent blue-green glass lions to the existing lion group, making exactly six glass lions total. Keep exactly three red cats total, fully visible and separated. Make all six lions clearly running after the cats, with forward-leaning bodies, raised paws, and heads aimed toward the cats.

  Spatial grounding: keep the single large brown donut in the foreground. Keep the three red cats behind the donut in the middle ground, separated left, center, and right. Place the six glass lions behind the cats in the background as a visible pursuit pack: four existing lions plus two added lions in the rear gaps, all oriented from the ... [instruction continues in canonical artifact]
```

### Environment Output

```yaml
Qwen-Image-Edit: edit source_attempt_id=a_000
new_attempt: a_004
Geneval2:
  score: 10/11
  passed: [c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
  failed: c_004 observed='no' expected='Yes'
  uncertain: []

RoundRecord r_004:
  source_attempt_id: a_000
  result_attempt_id: a_004
  fixed: [c_001, c_005]
  regressed: []
  persistent_failed: [c_004]
  became_best: True

Next PlannerContext changes:
  latest_observation: a_004
  best_attempt: a_004
  remaining_image_budget: 0
```

---

## 10. Final Step：budget exhausted -> `submit_attempt`

### Teacher Input

```yaml
Planner Input:
  task_context:
    original_prompt: "six glass lions chasing three red cats behind a brown donut"
    atom_constraints: [c_001 ... c_011]  # see Shared Task above

  latest_observation:
    attempt_id: a_004
    image_role: LATEST_IMAGE
    passed: [c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
    failed: [c_004]
    uncertain: []

  skill_context:
    active_skills: []

  episode_memory:
    recent_round:
      action: edit_image
      source_attempt_id: a_000
      result_attempt_id: a_004
      decision_summary: Use the historical best source rather than the latest because the best preserves the glass-lion attribute, while one final edit can still target the unresolved lion count, cat count clarity, and chase action.
      target_constraint_ids: [c_001, c_004, c_005]
      fixed: [c_001, c_005]
      regressed: []
      persistent_failed: [c_004]
    earlier_rounds:
      - r_000: generate_image null -> a_000; fixed=[]; regressed=[]; persistent_failed=[]
      - r_001: edit_image a_000 -> a_001; fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
      - r_002: edit_image a_000 -> a_002; fixed=[]; regressed=[]; persistent_failed=[c_001, c_004, c_005]
      - r_003: edit_image a_000 -> a_003; fixed=[c_005]; regressed=[c_002]; persistent_failed=[c_001, c_004]
    best_attempt:
      attempt_id: a_004
      image_role: BEST_IMAGE
      passed: [c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
      failed: [c_004]
      uncertain: []

  runtime_state:
    remaining_image_budget: 0
    available_actions: [submit_attempt]
```

### Teacher Output

```yaml
action: submit_attempt
selected_attempt_id: a_004
reason_code: best_available_under_budget
decision_summary: The image-attempt budget is exhausted, so submit the historical best attempt despite the remaining chase-action failure.
```

### Environment Output

```yaml
submitted_attempt_id: a_004
best_attempt_id: a_004
attempt_order: a_000 -> a_001 -> a_002 -> a_003 -> a_004
final_geneval2:
  score: 10/11
  passed: [c_001, c_002, c_003, c_005, c_006, c_007, c_008, c_009, c_010, c_011]
  failed: c_004 observed='no' expected='Yes'
  uncertain: []
```

---

## 11. 这条轨迹证明了什么

```text
1. 原始 prompt 先变成全局 task_context，后续每轮不再重新解析。
2. query_skill 不生成图片，只更新同一 Round 内的 skill_context。
3. generate_image / edit_image 是 Planner Action；Qwen 执行只是该 Action 的环境执行。
4. 每次图片产生后，Geneval2 评价 atom，Reducer 写入 RoundRecord。
5. 下一轮 Planner 输入不只看到最新分数，还看到上一轮具体 Action、source、prompt 路线和真实 fixed/regressed/persistent_failed。
6. 当 latest 与 best/source 不一致时，Planner 可以精确选择 source_attempt_id，而不是只能沿着 latest 继续。
7. 最终提交是 submit_attempt action；它不创建图片，只提交当前预算下的 best attempt。
```

SFT 边界：每个 `Teacher Output` 是 assistant target；`Teacher Input`、Skill 返回、Qwen 图片、Geneval2 结果、RoundRecord 和 best/latest 更新都是 context / environment observation。
