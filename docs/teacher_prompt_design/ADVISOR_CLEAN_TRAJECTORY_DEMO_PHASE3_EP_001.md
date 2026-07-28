# Advisor Demo: Clean Gen-Retry Trajectory `phase3_ep_001`

这份文档用于给导师快速确认 trajectory 结构。它只展示主线: system 设计、协议限制、每轮 Teacher 输入、Teacher action、环境 observation，以及 observation 如何进入下一轮输入。

## 1. System / Protocol Design

**System prompt 设计目标**

- Teacher 是 verifier-grounded image retry planner。
- 目标是在 `max_image_attempts=5` 内最大化 best valid image attempt。
- 每轮只输出一个 canonical action JSON，不输出解释或 chain-of-thought。
- Teacher 必须同时使用 visible image 和 Geneval2 atom feedback。
- Teacher 必须使用 history: fixed / regressed / persistent failures / stable passes。
- 当 latest 和 best 不同，Teacher 必须比较二者后再选择 edit source。
- Skill 只用于改写 `generation_instruction` / `edit_instruction`，不替 Teacher 决定 action。

**Action protocol**

```text
query_skill(skill_ids, target_constraint_ids)
generate_image(mode, target_constraint_ids, preserve_constraint_ids, strategy_tags, skill_ids_used, generation_instruction)
edit_image(source_attempt_id, target_constraint_ids, preserve_constraint_ids, strategy_tags, skill_ids_used, edit_instruction)
submit_attempt(selected_attempt_id, reason_code)
```

**Runtime 限制**

- raw Teacher output 必须 parse 成 JSON 并通过 schema/reference/runtime/instruction validation。
- 不合格 raw output 只做 audit，不进入 clean trajectory，不消耗 image budget。
- `edit_image` 必须引用已有 attempt。
- budget 为 0 时只能 `submit_attempt`。
- 每次 image attempt 都由 Qwen 生成/编辑，再由 Geneval2 评测成 atom-level structured feedback。

## 2. How Previous Result Becomes Next Input

每轮 image action 后:

```text
Qwen image
-> Geneval2 atom VQA
-> normalized pass/fail/uncertain
-> reducer computes latest, best, compact_history, transition, remaining_budget
-> next PlannerView
-> next Teacher input
```

所以 Teacher 下一轮看到的是结构化状态，不是模糊描述:

```text
latest_attempt, best_attempt, visible latest/best image,
passed atoms, failed atoms, fixed/regressed/persistent failures,
stable passes, remaining budget, compact history
```

## 3. Task

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

Geneval2 atoms:

```text
c_001 lion count = six
c_002 lions are glass
c_003 lions exist
c_004 lions chasing cats
c_005 cat count = three
c_006 cats are red
c_007 cats exist
c_008 cats behind donut
c_009 donut count = one
c_010 donut is brown
c_011 donut exists
```

## 4. Clean Trajectory

### Turn 0: retrieve Skills

**Teacher input**

```text
Prompt + 11 atoms
Budget: 5
History: empty
Visible images: none
Available Skill summaries: counting, spatial relation, attribute binding, local edit preservation
```

**Teacher action**

```text
query_skill(
  skill_ids = [counting_and_instance_layout, spatial_relation_layout],
  target_constraint_ids = [c_001, c_004, c_005, c_008, c_009]
)
```

**Tool observation**

```text
Returned full Markdown Skills:
- counting_and_instance_layout
- spatial_relation_layout
```

**Next input gets**

```text
Full Skill content immediately after query.
Compact active Skill operators in later PlannerViews.
```

---

### Turn 1: initial generation `a_000`

**Teacher input**

```text
Prompt + atoms
Budget: 5
History: empty
Visible images: none
Active Skills: counting + spatial relation
```

**Teacher action**

```text
generate_image(
  mode = initial,
  target = all atoms,
  preserve = [],
  skill_ids_used = [counting_and_instance_layout, spatial_relation_layout],
  instruction = exact one brown donut foreground; exactly three red cats behind donut;
                exactly six glass lions chasing cats; all objects visible/separated;
                no extra/cropped/fused/reflected duplicates
)
```

**Environment observation**

```text
Qwen -> img_000
Geneval2 -> 6/11 pass
Failed: c_001 lion count, c_002 glass uncertain, c_004 chasing, c_005 cat count, c_008 behind donut
State -> latest=a_000, best=a_000, budget=4
```

**Next input gets**

```text
visible image img_000
compact history [a_000]
failed atoms and transition summary
```

---

### Turn 2: fresh regeneration `a_001`

**Teacher input**

```text
Latest/best: a_000
Visible image: img_000
Budget: 4
History: [a_000]
Failures: count/material/relation/cat-count/depth are broad
```

**Teacher action**

```text
generate_image(
  mode = initial,
  strategy = fresh_layout + explicit_counting + spatial_relation,
  instruction = clean white studio layout; large brown donut foreground;
                three red cats middle ground behind donut;
                six translucent glass lions in separated arc behind cats;
                no cropping/fusion/duplicates/reflections/extras
)
```

**Environment observation**

```text
Qwen -> img_001
Geneval2 -> 8/11 pass
Fixed: c_002 glass, c_005 cat count
Still failed: c_001 lion count, c_004 chasing, c_008 behind donut
State -> latest=a_001, best=a_001, budget=3
```

**Next input gets**

```text
a_001 is now a stronger edit base.
Persistent failures are narrowed to [lion count, chasing, behind donut].
Stable passes are available as preserve constraints.
```

---

### Turn 3: targeted edit `a_001 -> a_002`

**Teacher input**

```text
Latest/best: a_001
Visible image: img_001
Budget: 3
History: [a_000, a_001]
Failed atoms: c_001, c_004, c_008
Stable passes: c_002, c_003, c_005, c_006, c_007, c_009, c_010, c_011
```

**Teacher action**

```text
edit_image(
  source_attempt_id = a_001,
  target = [c_001, c_004, c_008],
  preserve = [all stable passes],
  instruction = add exactly two transparent glass lions so final count is six;
                make six lions visibly chasing three red cats;
                keep donut foreground and cats behind it;
                preserve cats, colors, donut, glass material, background;
                forbid extra cats/donuts/lions, cropping, fusion, hiding, unrelated redraw
)
```

**Environment observation**

```text
Qwen edit -> img_002
Geneval2 -> 9/11 pass
Fixed: c_001 lion count
Still failed: c_004 chasing, c_008 behind donut
State -> latest=a_002, best=a_002, budget=2
```

**Next input gets**

```text
Only relation/depth failures remain.
All count/object/color/material constraints are stable passes to preserve.
```

---

### Turn 4: relation/depth edit `a_002 -> a_003`

**Teacher input**

```text
Latest/best: a_002
Visible image: img_002
Budget: 2
History: [a_000, a_001, a_002]
Failed atoms: c_004 chasing, c_008 behind donut
Stable passes: nine atoms
```

**Teacher action**

```text
edit_image(
  source_attempt_id = a_002,
  target = [c_004, c_008],
  preserve = [nine passing atoms],
  instruction = adjust only depth and motion cues;
                donut in bottom foreground occluding cats' lower paws;
                lions in rear row running toward cats;
                preserve exact counts, glass lions, red cats, brown donut
)
```

**Environment observation**

```text
Qwen edit -> img_003
Geneval2 -> 8/11 pass
Still failed: c_004 chasing, c_008 behind donut
Regressed: c_002 lion glass
State -> latest=a_003, best=a_002, budget=1
```

**Next input gets**

```text
latest=a_003 is worse than best=a_002.
PlannerView includes both visible images:
- LATEST_IMAGE: img_003
- BEST_IMAGE: img_002
Transition marks c_002 regression.
```

---

### Turn 5: branch from best `a_002 -> a_004`

**Teacher input**

```text
Latest: a_003
Best: a_002
Visible images: latest img_003, best img_002
Budget: 1
History: [a_000, a_001, a_002, a_003]
Latest regressed c_002, so do not blindly continue from latest
Best still only fails c_004 and c_008
```

**Teacher action**

```text
edit_image(
  source_attempt_id = a_002,
  target = [c_004, c_008],
  preserve = [nine passing atoms from best],
  instruction = revise a_002, not a_003;
                keep six glass lions, three red cats, one brown donut;
                strengthen chasing relation and behind-donut depth;
                preserve counts/colors/materials and centered composition
)
```

**Environment observation**

```text
Qwen edit -> img_004
Geneval2 -> 9/11 pass
Still failed: c_004 chasing, c_008 behind donut
State -> latest=a_004, best=a_002, budget=0
```

**Next input gets**

```text
Budget exhausted.
Best remains a_002.
Only legal next action is submit_attempt.
```

---

### Turn 6: submit best

**Teacher input**

```text
Budget: 0
Latest: a_004
Best: a_002
Visible images: latest img_004, best img_002
Extra observation: submit best with reason_code best_available_under_budget
```

**Teacher action**

```text
submit_attempt(
  selected_attempt_id = a_002,
  reason_code = best_available_under_budget
)
```

**Final result**

```text
Submitted: a_002
Best score: 9/11
Remaining failures: c_004 chasing, c_008 behind donut
```

## 5. What This Shows

This trajectory has the desired Gen-Searcher / GenEvolve-style interaction shape:

```text
system policy
-> structured user state + visible images
-> assistant action
-> tool/env observation
-> next structured user state containing previous observation
-> next assistant action
```

The key behavior to show the advisor:

- Skill retrieval is an explicit action.
- Skill result conditions prompt rewrite.
- Geneval2 atom feedback is parsed into structured PlannerView input.
- Later actions target failed atoms and preserve passed atoms.
- Latest/best distinction is visible to Teacher.
- Teacher branches from best when latest regresses.
- Final action submits reducer-owned best under budget.

## 6. Small Note On Invalid Raw Output

The clean transcript omits invalid raw outputs. In the live run, one raw `generate_image` missed required `mode`; runtime schema validation rejected it before image execution. This is a protocol guardrail, not part of the clean canonical trajectory.

We tested `response_format=json_schema` on that exact input. An action-specific schema returned a valid `generate_image(mode=initial)`, so the next implementation step should add provider-compatible structured output while keeping local validation.
