# Conversation Trace: phase3_ep_001

This report renders one completed trajectory as a readable GenSearcher-style conversation trace.

## Task

- Run dir: `runs/teacher_prompt_v1_validation/phase3_ep_001`
- Original prompt: six glass lions chasing three red cats behind a brown donut
- Max image attempts: 5
- Submitted attempt: `a_002` (`best_available_under_budget`)
- Best attempt: `a_002`
- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`

## Atom Rubric

| ID | Type | Requirement | Evaluator Question |
| --- | --- | --- | --- |
| `c_001` | `count` | Expected answer: six | How many lions are in the image? |
| `c_002` | `attribute` | Expected answer: Yes | Are the lions glass? |
| `c_003` | `object` | Expected answer: Yes | Are there any lions in the image? |
| `c_004` | `verb` | Expected answer: Yes | Are the lions chasing the cats? |
| `c_005` | `count` | Expected answer: three | How many cats are in the image? |
| `c_006` | `attribute` | Expected answer: Yes | Are the cats red? |
| `c_007` | `object` | Expected answer: Yes | Are there any cats in the image? |
| `c_008` | `position` | Expected answer: Yes | Are the cats behind the donut? |
| `c_009` | `count` | Expected answer: one | How many donuts are in the image? |
| `c_010` | `attribute` | Expected answer: Yes | Is the donut brown? |
| `c_011` | `object` | Expected answer: Yes | Are there any donuts in the image? |

## Turns

### turn_000 - assistant `query_skill`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_000`
- PlannerView: `planner_views/planner_view_000.json`
- Remaining budget: 5
- Latest attempt: none
- Best attempt: none
- Visible images: none
- Extra observations: `No image attempts exist yet; do not edit or submit.`
- Retrieved skills in context: none
- Active compact operators: none
- Latest equals best: n/a

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 0
- Image labels/order: none

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":null,"compact_history":[],"constraint_state":{"c_001":{"attempt_ids":[],"status":"not_evaluated"},"c_002":{"attempt_ids":[],"status":"not_evaluated"},"c_003":{"attempt_ids":[],"status":"not_evaluated"},"c_004":{"attempt_ids":[],"status":"not_evaluated"},"c_005":{"attempt_ids":[],"status":"not_evaluated"},"c_006":{"attempt_ids":[],"status":"not_evaluated"},"c_007":{"attempt_ids":[],"status":"not_evaluated"},"c_008":{"attempt_ids":[],"status":"not_evaluated"},"c_009":{"attempt_ids":[],"status":"not_evaluated"},"c_010":{"attempt_ids":[],"status":"not_evaluated"},"c_011":{"attempt_ids":[],"status":"not_evaluated"}},"episode_id":"phase3_ep_001","latest_attempt":null,"latest_transition":null,"remaining_budget":5,"retrieved_experiences":[],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[]}

Visible image labels:

[]

Latest equals best:

false

Active Skill operators:

[]

Retrieved skills:

[]

Extra observations:

["No image attempts exist yet; do not edit or submit."]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `b752e3cdb95b0ee69d869eea5cb974b6931dbf6f58018d853104b5edb45a2ad6`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"query_skill\",\"arguments\":{\"skill_ids\":[\"counting_and_instance_layout\",\"spatial_relation_layout\"],\"target_constraint_ids\":[\"c_001\",\"c_004\",\"c_005\",\"c_008\",\"c_009\"]}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_000",
  "response_metadata": {
    "created": 1784104726,
    "id": "resp_00d61d76c24151b6016a57470d5dfc81998bf69a3500e69ab1",
    "raw_text_sha256": "b752e3cdb95b0ee69d869eea5cb974b6931dbf6f58018d853104b5edb45a2ad6",
    "usage": {
      "completion_tokens": 452,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 391,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 2508,
      "prompt_tokens_details": null,
      "total_tokens": 2960
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

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
  "schema_version": "0.2"
}
```

**Tool Output**

- Skill return event: `evt_0005` for action `evt_0004`
- `counting_and_instance_layout`: Construct generation or edit instructions for exact counts by making each instance visible, separate, bounded, and countable. (`skills/counting_and_instance_layout/SKILL.md`)
- `spatial_relation_layout`: Construct generation or edit instructions for spatial or directional relations using anchors, depth, orientation, and visibility cues. (`skills/spatial_relation_layout/SKILL.md`)

### turn_002 - assistant `generate_image`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_002`
- PlannerView: `planner_views/planner_view_002.json`
- Remaining budget: 5
- Latest attempt: none
- Best attempt: none
- Visible images: none
- Extra observations: `No image attempts exist yet; do not edit or submit.`
- Retrieved skills in context: none
- Active compact operators: `active_skill_operator:counting_and_instance_layout`, `active_skill_operator:spatial_relation_layout`
- Latest equals best: n/a

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 0
- Image labels/order: none

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":null,"compact_history":[],"constraint_state":{"c_001":{"attempt_ids":[],"status":"not_evaluated"},"c_002":{"attempt_ids":[],"status":"not_evaluated"},"c_003":{"attempt_ids":[],"status":"not_evaluated"},"c_004":{"attempt_ids":[],"status":"not_evaluated"},"c_005":{"attempt_ids":[],"status":"not_evaluated"},"c_006":{"attempt_ids":[],"status":"not_evaluated"},"c_007":{"attempt_ids":[],"status":"not_evaluated"},"c_008":{"attempt_ids":[],"status":"not_evaluated"},"c_009":{"attempt_ids":[],"status":"not_evaluated"},"c_010":{"attempt_ids":[],"status":"not_evaluated"},"c_011":{"attempt_ids":[],"status":"not_evaluated"}},"episode_id":"phase3_ep_001","latest_attempt":null,"latest_transition":null,"remaining_budget":5,"retrieved_experiences":[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[]}

Visible image labels:

[]

Latest equals best:

false

Active Skill operators:

[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}]

Retrieved skills:

[]

Extra observations:

["No image attempts exist yet; do not edit or submit."]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `65add28b7f37d9c845094a227774430cb4f838d636a53536268e67b1fcded67d`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"generate_image\",\"arguments\":{\"generation_instruction\":\"Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts.\",\"mode\":\"initial\",\"preserve_constraint_ids\":[],\"skill_ids_used\":[\"counting_and_instance_layout\",\"spatial_relation_layout\"],\"strategy_tags\":[\"fresh_layout\",\"counting\",\"spatial_relation\"],\"target_constraint_ids\":[\"c_001\",\"c_002\",\"c_003\",\"c_004\",\"c_005\",\"c_006\",\"c_007\",\"c_008\",\"c_009\",\"c_010\",\"c_011\"]}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_002",
  "response_metadata": {
    "created": 1784104757,
    "id": "resp_0f875d4e593a8d80016a5747276f048199b1598c2e7cd84275",
    "raw_text_sha256": "65add28b7f37d9c845094a227774430cb4f838d636a53536268e67b1fcded67d",
    "usage": {
      "completion_tokens": 740,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 516,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 3201,
      "prompt_tokens_details": null,
      "total_tokens": 3941
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

```json
{
  "action": "generate_image",
  "arguments": {
    "generation_instruction": "Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts.",
    "mode": "initial",
    "preserve_constraint_ids": [],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "fresh_layout",
      "counting",
      "spatial_relation"
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
  "schema_version": "0.2"
}
```

- Action instruction:

> Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts.

**Image Tool Output**

- Attempt: `a_000`
- Parent/source attempt: none
- Image artifact: `runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_000.png`
- Operation: `generate`
- Render params: steps=40, size=1024x1024, true_cfg=4.0, guidance=1.0, seed=0
- Runtime: `diffusers.QwenImageEditPlusPipeline`

**Instruction Quality**

- Verdict: `pass`
- Vague-language flags: none
- Contradiction flags: none
- Overbroad-edit flags: none
- Notes: none

**Exact Qwen-Image-Edit Input**

- Operation: `generate`
- Source attempt: none
- Instruction:

> Create a single scene with exactly one brown donut in the foreground. Place exactly three red cats fully visible and separated behind the donut in the midground. Place exactly six glass lions fully visible and separated in the background, chasing the cats, with the lions oriented toward the cats in a clear pursuit pose. Keep all lions glass-like and transparent, keep the cats red, keep the donut brown, and do not add any other animals or objects. Do not create extra, cropped, fused, reflected, duplicate, or partially hidden lions, cats, or donuts.

**Verifier Output / Memory Reduction**

- Pass count: 6/11
- Fixed vs source/latest: none
- Regressed vs source/latest: none
- Stable pass: `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011`
- Persistent failed: `c_001`, `c_002`, `c_004`, `c_005`, `c_008`
- Best after this turn: `a_000`

| Atom | Status | Observed | Expected |
| --- | --- | --- | --- |
| `c_001` | `fail` | 2 | six |
| `c_002` | `uncertain` |  no | Yes |
| `c_003` | `pass` |  yes | Yes |
| `c_004` | `fail` |  no | Yes |
| `c_005` | `fail` | 0 | three |
| `c_006` | `pass` |  yes | Yes |
| `c_007` | `pass` |  yes | Yes |
| `c_008` | `fail` |  no | Yes |
| `c_009` | `pass` | 1 | one |
| `c_010` | `pass` |  yes | Yes |
| `c_011` | `pass` |  yes | Yes |

### turn_003 - assistant `generate_image`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_003`
- PlannerView: `planner_views/planner_view_003.json`
- Remaining budget: 4
- Latest attempt: `a_000` generate_image pass=6 fail=5
- Best attempt: `a_000` generate_image pass=6 fail=5
- Visible images: `latest:a_000:img_000`, `best:a_000:img_000`
- Extra observations: none
- Retrieved skills in context: none
- Active compact operators: `active_skill_operator:counting_and_instance_layout`, `active_skill_operator:spatial_relation_layout`
- Latest equals best: true

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 1
- Image labels/order: `LATEST_IMAGE:a_000:img_000`, `BEST_IMAGE_SAME_AS_LATEST:a_000:img_000`

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]},"compact_history":[{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]}],"constraint_state":{"c_001":{"attempt_ids":["a_000"],"latest_observed":"2","status":"fail"},"c_002":{"attempt_ids":["a_000"],"latest_observed":" no","status":"uncertain"},"c_003":{"attempt_ids":["a_000"],"latest_observed":" yes","status":"pass"},"c_004":{"attempt_ids":["a_000"],"latest_observed":" no","status":"fail"},"c_005":{"attempt_ids":["a_000"],"latest_observed":"0","status":"fail"},"c_006":{"attempt_ids":["a_000"],"latest_observed":" yes","status":"pass"},"c_007":{"attempt_ids":["a_000"],"latest_observed":" yes","status":"pass"},"c_008":{"attempt_ids":["a_000"],"latest_observed":" no","status":"fail"},"c_009":{"attempt_ids":["a_000"],"latest_observed":"1","status":"pass"},"c_010":{"attempt_ids":["a_000"],"latest_observed":" yes","status":"pass"},"c_011":{"attempt_ids":["a_000"],"latest_observed":" yes","status":"pass"}},"episode_id":"phase3_ep_001","latest_attempt":{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]},"latest_transition":{"fixed":[],"from_attempt_id":null,"new_failed":[],"persistent_failed":["c_001","c_002","c_004","c_005","c_008"],"regressed":[],"stable_pass":["c_003","c_006","c_007","c_009","c_010","c_011"],"to_attempt_id":"a_000"},"remaining_budget":4,"retrieved_experiences":[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[{"artifact_id":"img_000","attempt_id":"a_000","display_id":"IMG_000","role":"latest"},{"artifact_id":"img_000","attempt_id":"a_000","display_id":"IMG_000","role":"best"}]}

Visible image labels:

[{"artifact_id":"img_000","attempt_id":"a_000","label":"LATEST_IMAGE: attempt a_000, artifact img_000","role":"latest"},{"artifact_id":"img_000","attempt_id":"a_000","label":"BEST_IMAGE_SAME_AS_LATEST: attempt a_000, artifact img_000","role":"best"}]

Latest equals best:

true

Active Skill operators:

[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}]

Retrieved skills:

[]

Extra observations:

[]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `e5be85a3b1bbb4bc67e3d86bf2292e76d6737184f7edea986835e610a2510066`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"generate_image\",\"arguments\":{\"generation_instruction\":\"Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects.\",\"mode\":\"initial\",\"preserve_constraint_ids\":[],\"skill_ids_used\":[\"counting_and_instance_layout\",\"spatial_relation_layout\"],\"strategy_tags\":[\"fresh_layout\",\"explicit_counting\",\"spatial_relation\"],\"target_constraint_ids\":[\"c_001\",\"c_002\",\"c_003\",\"c_004\",\"c_005\",\"c_006\",\"c_007\",\"c_008\",\"c_009\",\"c_010\",\"c_011\"]}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_003",
  "response_metadata": {
    "created": 1784105043,
    "id": "resp_0a2664f8ffbff18e016a57481570ac819b8468b39032a51550",
    "raw_text_sha256": "e5be85a3b1bbb4bc67e3d86bf2292e76d6737184f7edea986835e610a2510066",
    "usage": {
      "completion_tokens": 3345,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 3106,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 6197,
      "prompt_tokens_details": null,
      "total_tokens": 9542
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

```json
{
  "action": "generate_image",
  "arguments": {
    "generation_instruction": "Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects.",
    "mode": "initial",
    "preserve_constraint_ids": [],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "strategy_tags": [
      "fresh_layout",
      "explicit_counting",
      "spatial_relation"
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
  "schema_version": "0.2"
}
```

- Action instruction:

> Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects.

**Image Tool Output**

- Attempt: `a_001`
- Parent/source attempt: none
- Image artifact: `runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_001.png`
- Operation: `generate`
- Render params: steps=40, size=1024x1024, true_cfg=4.0, guidance=1.0, seed=1
- Runtime: `diffusers.QwenImageEditPlusPipeline`

**Instruction Quality**

- Verdict: `pass`
- Vague-language flags: none
- Contradiction flags: none
- Overbroad-edit flags: none
- Notes: none

**Exact Qwen-Image-Edit Input**

- Operation: `generate`
- Source attempt: none
- Instruction:

> Create a clean white seamless studio scene with exactly one large brown donut in the foreground at the bottom center. Place exactly three red cats fully visible and separated in the middle ground behind the donut. Place exactly six glass lions fully visible and separated behind the cats in the background, arranged in a loose arc and leaning forward toward the cats so they clearly appear to be chasing them. Make all six lions translucent cyan glass; make all three cats solid red; make the donut brown. Keep every animal fully visible with no cropping, no fused bodies, no duplicates, no reflections, no extra animals, no text, and no extra objects.

**Verifier Output / Memory Reduction**

- Pass count: 8/11
- Fixed vs source/latest: `c_002`, `c_005`
- Regressed vs source/latest: none
- Stable pass: `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011`
- Persistent failed: `c_001`, `c_004`, `c_008`
- Best after this turn: `a_001`

| Atom | Status | Observed | Expected |
| --- | --- | --- | --- |
| `c_001` | `fail` | 4 | six |
| `c_002` | `pass` |  yes | Yes |
| `c_003` | `pass` |  yes | Yes |
| `c_004` | `fail` |  no | Yes |
| `c_005` | `pass` | 3 | three |
| `c_006` | `pass` |  yes | Yes |
| `c_007` | `pass` |  yes | Yes |
| `c_008` | `fail` |  no | Yes |
| `c_009` | `pass` | one | one |
| `c_010` | `pass` |  yes | Yes |
| `c_011` | `pass` |  yes | Yes |

### turn_008 - assistant `edit_image`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_008`
- PlannerView: `planner_views/planner_view_008.json`
- Remaining budget: 3
- Latest attempt: `a_001` generate_image pass=8 fail=3
- Best attempt: `a_001` generate_image pass=8 fail=3
- Visible images: `latest:a_001:img_001`, `best:a_001:img_001`
- Extra observations: none
- Retrieved skills in context: none
- Active compact operators: `active_skill_operator:counting_and_instance_layout`, `active_skill_operator:spatial_relation_layout`
- Latest equals best: true

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 2
- Image labels/order: `LATEST_IMAGE:a_001:img_001`, `BEST_IMAGE_SAME_AS_LATEST:a_001:img_001`

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":{"action_type":"generate_image","attempt_id":"a_001","failed_constraint_ids":["c_001","c_004","c_008"],"image_artifact_id":"img_001","parent_attempt_id":null,"passed_constraint_ids":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"compact_history":[{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"generate_image","attempt_id":"a_001","failed_constraint_ids":["c_001","c_004","c_008"],"image_artifact_id":"img_001","parent_attempt_id":null,"passed_constraint_ids":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]}],"constraint_state":{"c_001":{"attempt_ids":["a_000","a_001"],"latest_observed":"4","status":"fail"},"c_002":{"attempt_ids":["a_000","a_001"],"latest_observed":" yes","status":"pass"},"c_003":{"attempt_ids":["a_000","a_001"],"latest_observed":" yes","status":"pass"},"c_004":{"attempt_ids":["a_000","a_001"],"latest_observed":" no","status":"fail"},"c_005":{"attempt_ids":["a_000","a_001"],"latest_observed":"3","status":"pass"},"c_006":{"attempt_ids":["a_000","a_001"],"latest_observed":" yes","status":"pass"},"c_007":{"attempt_ids":["a_000","a_001"],"latest_observed":" yes","status":"pass"},"c_008":{"attempt_ids":["a_000","a_001"],"latest_observed":" no","status":"fail"},"c_009":{"attempt_ids":["a_000","a_001"],"latest_observed":"one","status":"pass"},"c_010":{"attempt_ids":["a_000","a_001"],"latest_observed":" yes","status":"pass"},"c_011":{"attempt_ids":["a_000","a_001"],"latest_observed":" yes","status":"pass"}},"episode_id":"phase3_ep_001","latest_attempt":{"action_type":"generate_image","attempt_id":"a_001","failed_constraint_ids":["c_001","c_004","c_008"],"image_artifact_id":"img_001","parent_attempt_id":null,"passed_constraint_ids":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"latest_transition":{"fixed":["c_002","c_005"],"from_attempt_id":"a_000","new_failed":[],"persistent_failed":["c_001","c_004","c_008"],"regressed":[],"stable_pass":["c_003","c_006","c_007","c_009","c_010","c_011"],"to_attempt_id":"a_001"},"remaining_budget":3,"retrieved_experiences":[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[{"artifact_id":"img_001","attempt_id":"a_001","display_id":"IMG_001","role":"latest"},{"artifact_id":"img_001","attempt_id":"a_001","display_id":"IMG_001","role":"best"}]}

Visible image labels:

[{"artifact_id":"img_001","attempt_id":"a_001","label":"LATEST_IMAGE: attempt a_001, artifact img_001","role":"latest"},{"artifact_id":"img_001","attempt_id":"a_001","label":"BEST_IMAGE_SAME_AS_LATEST: attempt a_001, artifact img_001","role":"best"}]

Latest equals best:

true

Active Skill operators:

[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}]

Retrieved skills:

[]

Extra observations:

[]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `5bf8b921a5ed2bd90d6d0a2357d3f85118f4e809470d6ae75ae9d91eea8be1e1`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"edit_image\",\"arguments\":{\"source_attempt_id\":\"a_001\",\"edit_instruction\":\"Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene.\",\"target_constraint_ids\":[\"c_001\",\"c_004\",\"c_008\"],\"preserve_constraint_ids\":[\"c_002\",\"c_003\",\"c_005\",\"c_006\",\"c_007\",\"c_009\",\"c_010\",\"c_011\"],\"skill_ids_used\":[\"counting_and_instance_layout\",\"spatial_relation_layout\"],\"strategy_tags\":[\"localized_repair\",\"add_missing_instances\",\"spatial_relation_repair\"]}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_008",
  "response_metadata": {
    "created": 1784105490,
    "id": "resp_01e0e3d15343b58c016a574a05202c819a9ca6b96226045392",
    "raw_text_sha256": "5bf8b921a5ed2bd90d6d0a2357d3f85118f4e809470d6ae75ae9d91eea8be1e1",
    "usage": {
      "completion_tokens": 528,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 213,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 6324,
      "prompt_tokens_details": {
        "audio_tokens": null,
        "cached_tokens": 5376
      },
      "total_tokens": 6852
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

```json
{
  "action": "edit_image",
  "arguments": {
    "edit_instruction": "Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene.",
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
    ],
    "source_attempt_id": "a_001",
    "strategy_tags": [
      "localized_repair",
      "add_missing_instances",
      "spatial_relation_repair"
    ],
    "target_constraint_ids": [
      "c_001",
      "c_004",
      "c_008"
    ]
  },
  "schema_version": "0.2"
}
```

- Action instruction:

> Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene.

**Image Tool Output**

- Attempt: `a_002`
- Parent/source attempt: `a_001`
- Image artifact: `runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_002.png`
- Operation: `edit`
- Render params: steps=40, size=1024x1024, true_cfg=4.0, guidance=1.0, seed=2
- Runtime: `diffusers.QwenImageEditPlusPipeline`

**Instruction Quality**

- Verdict: `pass`
- Vague-language flags: none
- Contradiction flags: none
- Overbroad-edit flags: none
- Notes: none

**Exact Qwen-Image-Edit Input**

- Operation: `edit`
- Source attempt: `a_001`
- Instruction:

> Target operation: edit attempt a_001 by adding exactly two additional transparent glass lions so there are exactly six glass lions total, and adjust the lion poses and gaze so the six lions are clearly chasing the three red cats. Spatial grounding: keep the single brown donut large in the foreground at the bottom/front; keep all three red cats in the middle ground behind the donut with the donut visibly in front of them; place the six glass lions in a separated back row behind the cats, oriented forward toward the cats as if pursuing them. Preservation lock: preserve the existing three red cats, their red color, the single brown donut, the donut color, the clean white background, and the glass material of all lions. Forbidden changes: do not add or remove cats, do not add any extra donuts, do not create more or fewer than six lions, do not crop, fuse, hide, mirror, or overlap animal instances, and do not redraw unrelated parts of the scene.

**Verifier Output / Memory Reduction**

- Pass count: 9/11
- Fixed vs source/latest: `c_001`
- Regressed vs source/latest: none
- Stable pass: `c_002`, `c_003`, `c_005`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011`
- Persistent failed: `c_004`, `c_008`
- Best after this turn: `a_002`

| Atom | Status | Observed | Expected |
| --- | --- | --- | --- |
| `c_001` | `pass` | 6 | six |
| `c_002` | `pass` |  yes | Yes |
| `c_003` | `pass` |  yes | Yes |
| `c_004` | `fail` |  no | Yes |
| `c_005` | `pass` | 3 | three |
| `c_006` | `pass` |  yes | Yes |
| `c_007` | `pass` |  yes | Yes |
| `c_008` | `fail` |  no | Yes |
| `c_009` | `pass` | one | one |
| `c_010` | `pass` |  yes | Yes |
| `c_011` | `pass` |  yes | Yes |

### turn_009 - assistant `edit_image`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_009`
- PlannerView: `planner_views/planner_view_009.json`
- Remaining budget: 2
- Latest attempt: `a_002` edit_image pass=9 fail=2
- Best attempt: `a_002` edit_image pass=9 fail=2
- Visible images: `latest:a_002:img_002`, `best:a_002:img_002`
- Extra observations: none
- Retrieved skills in context: none
- Active compact operators: `active_skill_operator:counting_and_instance_layout`, `active_skill_operator:spatial_relation_layout`
- Latest equals best: true

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 3
- Image labels/order: `LATEST_IMAGE:a_002:img_002`, `BEST_IMAGE_SAME_AS_LATEST:a_002:img_002`

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"compact_history":[{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"generate_image","attempt_id":"a_001","failed_constraint_ids":["c_001","c_004","c_008"],"image_artifact_id":"img_001","parent_attempt_id":null,"passed_constraint_ids":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]}],"constraint_state":{"c_001":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":"6","status":"pass"},"c_002":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" yes","status":"pass"},"c_003":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" yes","status":"pass"},"c_004":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" no","status":"fail"},"c_005":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":"3","status":"pass"},"c_006":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" yes","status":"pass"},"c_007":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" yes","status":"pass"},"c_008":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" no","status":"fail"},"c_009":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":"one","status":"pass"},"c_010":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" yes","status":"pass"},"c_011":{"attempt_ids":["a_000","a_001","a_002"],"latest_observed":" yes","status":"pass"}},"episode_id":"phase3_ep_001","latest_attempt":{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"latest_transition":{"fixed":["c_001"],"from_attempt_id":"a_001","new_failed":[],"persistent_failed":["c_004","c_008"],"regressed":[],"stable_pass":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],"to_attempt_id":"a_002"},"remaining_budget":2,"retrieved_experiences":[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[{"artifact_id":"img_002","attempt_id":"a_002","display_id":"IMG_002","role":"latest"},{"artifact_id":"img_002","attempt_id":"a_002","display_id":"IMG_002","role":"best"}]}

Visible image labels:

[{"artifact_id":"img_002","attempt_id":"a_002","label":"LATEST_IMAGE: attempt a_002, artifact img_002","role":"latest"},{"artifact_id":"img_002","attempt_id":"a_002","label":"BEST_IMAGE_SAME_AS_LATEST: attempt a_002, artifact img_002","role":"best"}]

Latest equals best:

true

Active Skill operators:

[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}]

Retrieved skills:

[]

Extra observations:

[]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `486a73e32c42dfdb9bcdac0624cddb25762e17b6c9636549cf47ecf6d79f7e55`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"edit_image\",\"arguments\":{\"source_attempt_id\":\"a_002\",\"edit_instruction\":\"Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects.\",\"target_constraint_ids\":[\"c_004\",\"c_008\"],\"preserve_constraint_ids\":[\"c_001\",\"c_002\",\"c_003\",\"c_005\",\"c_006\",\"c_007\",\"c_009\",\"c_010\",\"c_011\"],\"skill_ids_used\":[\"counting_and_instance_layout\",\"spatial_relation_layout\"],\"strategy_tags\":[\"localized_repair\",\"depth_relation_repair\",\"verb_action_cue\"]}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_009",
  "response_metadata": {
    "created": 1784105735,
    "id": "resp_0334e6f286e637e8016a574afa07508196acec1fdea4645587",
    "raw_text_sha256": "486a73e32c42dfdb9bcdac0624cddb25762e17b6c9636549cf47ecf6d79f7e55",
    "usage": {
      "completion_tokens": 512,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 164,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 6456,
      "prompt_tokens_details": null,
      "total_tokens": 6968
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

```json
{
  "action": "edit_image",
  "arguments": {
    "edit_instruction": "Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects.",
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
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "source_attempt_id": "a_002",
    "strategy_tags": [
      "localized_repair",
      "depth_relation_repair",
      "verb_action_cue"
    ],
    "target_constraint_ids": [
      "c_004",
      "c_008"
    ]
  },
  "schema_version": "0.2"
}
```

- Action instruction:

> Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects.

**Image Tool Output**

- Attempt: `a_003`
- Parent/source attempt: `a_002`
- Image artifact: `runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_003.png`
- Operation: `edit`
- Render params: steps=40, size=1024x1024, true_cfg=4.0, guidance=1.0, seed=3
- Runtime: `diffusers.QwenImageEditPlusPipeline`

**Instruction Quality**

- Verdict: `pass`
- Vague-language flags: none
- Contradiction flags: none
- Overbroad-edit flags: none
- Notes: none

**Exact Qwen-Image-Edit Input**

- Operation: `edit`
- Source attempt: `a_002`
- Instruction:

> Target operation: adjust only the depth and motion cues so the scene clearly shows six glass lions chasing three red cats, and the three red cats are clearly behind the single brown donut. Spatial grounding: keep the one brown donut large in the bottom foreground, overlapping and occluding the lower front paws of the three red cats so all three cats are visibly behind the donut; place all six transparent glass lions in a rear row behind the cats, running toward the cats with forward-leaning bodies, raised paws, focused eyes, and pursuit spacing that makes the lions clearly chasing the cats from behind. Preservation lock: preserve exactly six lions total, all glass and fully visible as separate lion instances; preserve exactly three red cats total, fully visible above the donut and separated; preserve exactly one brown donut; preserve the white background and overall centered composition. Forbidden changes: do not add or remove any lions, cats, or donuts; do not change lion material from glass, cat color from red, or donut color from brown; do not place cats in front of the donut; do not crop, fuse, duplicate, reflect, or redraw unrelated objects.

**Verifier Output / Memory Reduction**

- Pass count: 8/11
- Fixed vs source/latest: none
- Regressed vs source/latest: `c_002`
- Stable pass: `c_001`, `c_003`, `c_005`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011`
- Persistent failed: `c_004`, `c_008`
- Best after this turn: `a_002`

| Atom | Status | Observed | Expected |
| --- | --- | --- | --- |
| `c_001` | `pass` | 6 | six |
| `c_002` | `fail` | no | Yes |
| `c_003` | `pass` |  yes | Yes |
| `c_004` | `fail` |  no | Yes |
| `c_005` | `pass` | 3 | three |
| `c_006` | `pass` |  yes | Yes |
| `c_007` | `pass` |  yes | Yes |
| `c_008` | `fail` |  no | Yes |
| `c_009` | `pass` | one | one |
| `c_010` | `pass` |  yes | Yes |
| `c_011` | `pass` |  yes | Yes |

### turn_010 - assistant `edit_image`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_010`
- PlannerView: `planner_views/planner_view_010.json`
- Remaining budget: 1
- Latest attempt: `a_003` edit_image pass=8 fail=3
- Best attempt: `a_002` edit_image pass=9 fail=2
- Visible images: `latest:a_003:img_003`, `best:a_002:img_002`
- Extra observations: none
- Retrieved skills in context: none
- Active compact operators: `active_skill_operator:counting_and_instance_layout`, `active_skill_operator:spatial_relation_layout`
- Latest equals best: false

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 4
- Image labels/order: `LATEST_IMAGE:a_003:img_003`, `BEST_IMAGE:a_002:img_002`

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"compact_history":[{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"generate_image","attempt_id":"a_001","failed_constraint_ids":["c_001","c_004","c_008"],"image_artifact_id":"img_001","parent_attempt_id":null,"passed_constraint_ids":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"edit_image","attempt_id":"a_003","failed_constraint_ids":["c_002","c_004","c_008"],"image_artifact_id":"img_003","parent_attempt_id":"a_002","passed_constraint_ids":["c_001","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]}],"constraint_state":{"c_001":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":"6","status":"pass"},"c_002":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":"no","status":"fail"},"c_003":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" yes","status":"pass"},"c_004":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" no","status":"fail"},"c_005":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":"3","status":"pass"},"c_006":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" yes","status":"pass"},"c_007":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" yes","status":"pass"},"c_008":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" no","status":"fail"},"c_009":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":"one","status":"pass"},"c_010":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" yes","status":"pass"},"c_011":{"attempt_ids":["a_000","a_001","a_002","a_003"],"latest_observed":" yes","status":"pass"}},"episode_id":"phase3_ep_001","latest_attempt":{"action_type":"edit_image","attempt_id":"a_003","failed_constraint_ids":["c_002","c_004","c_008"],"image_artifact_id":"img_003","parent_attempt_id":"a_002","passed_constraint_ids":["c_001","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"latest_transition":{"fixed":[],"from_attempt_id":"a_002","new_failed":[],"persistent_failed":["c_004","c_008"],"regressed":["c_002"],"stable_pass":["c_001","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],"to_attempt_id":"a_003"},"remaining_budget":1,"retrieved_experiences":[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[{"artifact_id":"img_003","attempt_id":"a_003","display_id":"IMG_003","role":"latest"},{"artifact_id":"img_002","attempt_id":"a_002","display_id":"IMG_002","role":"best"}]}

Visible image labels:

[{"artifact_id":"img_003","attempt_id":"a_003","label":"LATEST_IMAGE: attempt a_003, artifact img_003","role":"latest"},{"artifact_id":"img_002","attempt_id":"a_002","label":"BEST_IMAGE: attempt a_002, artifact img_002","role":"best"}]

Latest equals best:

false

Active Skill operators:

[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}]

Retrieved skills:

[]

Extra observations:

[]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `38dffd16e110c50079c81a962fea8d58db26d55f2a0c8739bbd2b2527428f175`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"edit_image\",\"arguments\":{\"source_attempt_id\":\"a_002\",\"edit_instruction\":\"Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap.\",\"preserve_constraint_ids\":[\"c_001\",\"c_002\",\"c_003\",\"c_005\",\"c_006\",\"c_007\",\"c_009\",\"c_010\",\"c_011\"],\"skill_ids_used\":[\"counting_and_instance_layout\",\"spatial_relation_layout\"],\"strategy_tags\":[\"localized_repair\",\"depth_layering\",\"motion_cue\"],\"target_constraint_ids\":[\"c_004\",\"c_008\"]}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_010",
  "response_metadata": {
    "created": 1784105990,
    "id": "resp_04263f300ce94c5e016a574bdfee848198bbf5dfd25e54d728",
    "raw_text_sha256": "38dffd16e110c50079c81a962fea8d58db26d55f2a0c8739bbd2b2527428f175",
    "usage": {
      "completion_tokens": 1993,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 1677,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 6574,
      "prompt_tokens_details": null,
      "total_tokens": 8567
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

```json
{
  "action": "edit_image",
  "arguments": {
    "edit_instruction": "Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap.",
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
    ],
    "skill_ids_used": [
      "counting_and_instance_layout",
      "spatial_relation_layout"
    ],
    "source_attempt_id": "a_002",
    "strategy_tags": [
      "localized_repair",
      "depth_layering",
      "motion_cue"
    ],
    "target_constraint_ids": [
      "c_004",
      "c_008"
    ]
  },
  "schema_version": "0.2"
}
```

- Action instruction:

> Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap.

**Image Tool Output**

- Attempt: `a_004`
- Parent/source attempt: `a_002`
- Image artifact: `runs/teacher_prompt_v1_validation/phase3_ep_001/images/img_004.png`
- Operation: `edit`
- Render params: steps=40, size=1024x1024, true_cfg=4.0, guidance=1.0, seed=4
- Runtime: `diffusers.QwenImageEditPlusPipeline`

**Instruction Quality**

- Verdict: `pass`
- Vague-language flags: none
- Contradiction flags: none
- Overbroad-edit flags: none
- Notes: none

**Exact Qwen-Image-Edit Input**

- Operation: `edit`
- Source attempt: `a_002`
- Instruction:

> Target operation: revise attempt a_002 so the image shows exactly six glass lions chasing exactly three red cats, and exactly one brown donut in the scene. Spatial grounding: keep the single brown donut in the foreground; place the three red cats behind the donut in a middle depth layer so the donut overlaps their lower bodies; keep all six glass lions behind the cats, oriented toward them with forward-leaning pursuit poses and heads/paws aimed at the cats. Preservation lock: preserve the six-lion count, glass material, the red cat color, the three-cat count, the single brown donut, the clean white background, and the overall centered composition. Forbidden changes: do not change the lion count, cat count, donut count, colors, or materials; do not add extra animals or objects; do not remove the donut; do not place the cats in front of the donut; do not crop, fuse, mirror, duplicate, or obscure any subject beyond the intended depth overlap.

**Verifier Output / Memory Reduction**

- Pass count: 9/11
- Fixed vs source/latest: none
- Regressed vs source/latest: none
- Stable pass: `c_001`, `c_002`, `c_003`, `c_005`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011`
- Persistent failed: `c_004`, `c_008`
- Best after this turn: `a_002`

| Atom | Status | Observed | Expected |
| --- | --- | --- | --- |
| `c_001` | `pass` | 6 | six |
| `c_002` | `pass` |  yes | Yes |
| `c_003` | `pass` |  yes | Yes |
| `c_004` | `fail` |  no | Yes |
| `c_005` | `pass` | 3 | three |
| `c_006` | `pass` |  yes | Yes |
| `c_007` | `pass` |  yes | Yes |
| `c_008` | `fail` |  no | Yes |
| `c_009` | `pass` | one | one |
| `c_010` | `pass` |  yes | Yes |
| `c_011` | `pass` |  yes | Yes |

### turn_011 - assistant `submit_attempt`

**User / PlannerView Context**

- Request: `phase3_ep_001_turn_011`
- PlannerView: `planner_views/planner_view_011.json`
- Remaining budget: 0
- Latest attempt: `a_004` edit_image pass=9 fail=2
- Best attempt: `a_002` edit_image pass=9 fail=2
- Visible images: `latest:a_004:img_004`, `best:a_002:img_002`
- Extra observations: `Budget is exhausted; submit the best available attempt with reason_code exactly best_available_under_budget. Do not use budget_exhausted_best_available.`
- Retrieved skills in context: none
- Active compact operators: `active_skill_operator:counting_and_instance_layout`, `active_skill_operator:spatial_relation_layout`
- Latest equals best: false

**Teacher Input**

- System prompt version: `teacher_system_prompt_v1`
- System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`
- Atomic constraints: 11
- Compact history length: 5
- Image labels/order: `LATEST_IMAGE:a_004:img_004`, `BEST_IMAGE:a_002:img_002`

<details>
<summary>Exact sanitized teacher text input</summary>

```text
You are the Phase 3 teacher policy for Gen-Retry v3.

System policy:

{"sha256":"864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0","version":"teacher_system_prompt_v1"}

Role:

Verifier-grounded multimodal image retry planner. Maximize the best valid attempt under the remaining budget.

Return exactly one JSON object matching action_protocol_v0_2. No markdown, no prose, no environment facts, no paths, no scores.

The top-level object must have exactly these keys: schema_version, action, arguments. Never use a top-level instructions field.

Allowed actions: query_skill, generate_image, edit_image, submit_attempt.

query_skill requires arguments.skill_ids as an array and arguments.target_constraint_ids as an array. Never use skill_id singular and never add a query field.

A query_skill action may request at most two skills. Do not request the same skill twice in one query. Do not query a Skill ID/version/hash that is already active unless the Skill changed or a required operator is demonstrably absent. A repeated failure of the same capability is not enough reason to retrieve the same Skill again. Do not emit query_skill immediately after a successful query_skill response. Apply retrieved operators in the next image action.

generate_image and edit_image instructions must be executable image instructions containing the exact text sent to Qwen-Image-Edit.

For generate_image, put the instruction in arguments.generation_instruction. For edit_image, put the instruction in arguments.edit_instruction.

Generation instructions must include relevant exact entities/counts, entity-specific attributes, layout, relation/depth cues, visibility, separation, and no extras or fused/cropped/reflected instances.

Edit instructions must include four semantic blocks: target operation, spatial grounding, preservation lock, and forbidden changes. Do not rely only on vague phrases such as 'fix the failed parts' or 'preserve all correct evidence'.

Do not put a skill ID in skill_ids_used unless that skill is present in Retrieved skills or Active Skill operators. If no relevant Skill has been retrieved or retained, use skill_ids_used: [] or choose query_skill first.

Use edit_image only with a source_attempt_id already present in compact_history. Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path string alone. Compare latest and best when they differ before choosing source_attempt_id. Do not blindly continue from the latest attempt.

If remaining_budget is 0, submit the best available attempt with reason_code exactly best_available_under_budget.

Allowed submit reason_code values are exactly: all_constraints_passed, best_available_under_budget, no_productive_action_remaining. Never use budget_exhausted_best_available.

Valid templates:

[{"action":"query_skill","arguments":{"skill_ids":["counting_and_instance_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"generate_image","arguments":{"generation_instruction":"Create exactly two red cats total behind one blue cube. Keep both cats fully visible and separated in the background, place the cube in the foreground, and do not include extra, cropped, fused, reflected, or background cats.","mode":"initial","preserve_constraint_ids":[],"skill_ids_used":[],"strategy_tags":["fresh_layout"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"edit_image","arguments":{"edit_instruction":"Edit attempt a_000 only in the cat group: remove extra cats so exactly two red cats remain, fully visible and separated behind the foreground cube. Preserve the cube color, cube position, background, and all passed non-target constraints. Do not add extra cats, redraw unrelated objects, or change the scene composition.","preserve_constraint_ids":["c_002"],"skill_ids_used":[],"source_attempt_id":"a_000","strategy_tags":["localized_repair"],"target_constraint_ids":["c_001"]},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"all_constraints_passed","selected_attempt_id":"a_000"},"schema_version":"0.2"},{"action":"submit_attempt","arguments":{"reason_code":"best_available_under_budget","selected_attempt_id":"a_000"},"schema_version":"0.2"}]

TaskSpec:

{"constraints":[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}],"episode_id":"phase3_ep_001","max_image_attempts":5,"original_prompt":"six glass lions chasing three red cats behind a brown donut","schema_version":"0.2"}

Original Prompt:

six glass lions chasing three red cats behind a brown donut

Atomic constraints:

[{"constraint_id":"c_001","constraint_type":"count","evaluator_question":"How many lions are in the image?","priority":3,"requirement":"Expected answer: six"},{"constraint_id":"c_002","constraint_type":"attribute","evaluator_question":"Are the lions glass?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_003","constraint_type":"object","evaluator_question":"Are there any lions in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_004","constraint_type":"verb","evaluator_question":"Are the lions chasing the cats?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_005","constraint_type":"count","evaluator_question":"How many cats are in the image?","priority":3,"requirement":"Expected answer: three"},{"constraint_id":"c_006","constraint_type":"attribute","evaluator_question":"Are the cats red?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_007","constraint_type":"object","evaluator_question":"Are there any cats in the image?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_008","constraint_type":"position","evaluator_question":"Are the cats behind the donut?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_009","constraint_type":"count","evaluator_question":"How many donuts are in the image?","priority":3,"requirement":"Expected answer: one"},{"constraint_id":"c_010","constraint_type":"attribute","evaluator_question":"Is the donut brown?","priority":3,"requirement":"Expected answer: Yes"},{"constraint_id":"c_011","constraint_type":"object","evaluator_question":"Are there any donuts in the image?","priority":3,"requirement":"Expected answer: Yes"}]

PlannerView:

{"best_attempt":{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"compact_history":[{"action_type":"generate_image","attempt_id":"a_000","failed_constraint_ids":["c_001","c_002","c_004","c_005","c_008"],"image_artifact_id":"img_000","parent_attempt_id":null,"passed_constraint_ids":["c_003","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"generate_image","attempt_id":"a_001","failed_constraint_ids":["c_001","c_004","c_008"],"image_artifact_id":"img_001","parent_attempt_id":null,"passed_constraint_ids":["c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"edit_image","attempt_id":"a_002","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_002","parent_attempt_id":"a_001","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"edit_image","attempt_id":"a_003","failed_constraint_ids":["c_002","c_004","c_008"],"image_artifact_id":"img_003","parent_attempt_id":"a_002","passed_constraint_ids":["c_001","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},{"action_type":"edit_image","attempt_id":"a_004","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_004","parent_attempt_id":"a_002","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]}],"constraint_state":{"c_001":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":"6","status":"pass"},"c_002":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" yes","status":"pass"},"c_003":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" yes","status":"pass"},"c_004":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" no","status":"fail"},"c_005":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":"3","status":"pass"},"c_006":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" yes","status":"pass"},"c_007":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" yes","status":"pass"},"c_008":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" no","status":"fail"},"c_009":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":"one","status":"pass"},"c_010":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" yes","status":"pass"},"c_011":{"attempt_ids":["a_000","a_001","a_002","a_003","a_004"],"latest_observed":" yes","status":"pass"}},"episode_id":"phase3_ep_001","latest_attempt":{"action_type":"edit_image","attempt_id":"a_004","failed_constraint_ids":["c_004","c_008"],"image_artifact_id":"img_004","parent_attempt_id":"a_002","passed_constraint_ids":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"]},"latest_transition":{"fixed":[],"from_attempt_id":"a_002","new_failed":[],"persistent_failed":["c_004","c_008"],"regressed":[],"stable_pass":["c_001","c_002","c_003","c_005","c_006","c_007","c_009","c_010","c_011"],"to_attempt_id":"a_004"},"remaining_budget":0,"retrieved_experiences":[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}],"schema_version":"0.2","skill_manifest":[{"description":"Exact cardinality, instance separation, full visibility, no extras or fused objects.","skill_id":"counting_and_instance_layout","version":"1.0.0"},{"description":"Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations.","skill_id":"spatial_relation_layout","version":"1.0.0"},{"description":"Bind color, material, texture, and identity attributes to the correct entity.","skill_id":"attribute_entity_binding","version":"1.0.0"},{"description":"Narrow edit scope and preserve already-correct visual evidence.","skill_id":"local_edit_preservation","version":"1.0.0"}],"task_spec_ref":"task_spec.json","tool_manifest":[{"action":"query_skill","tool_id":"query_skill"},{"action":"generate_image","tool_id":"generate_image"},{"action":"edit_image","tool_id":"edit_image"},{"action":"submit_attempt","tool_id":"submit_attempt"}],"visible_images":[{"artifact_id":"img_004","attempt_id":"a_004","display_id":"IMG_004","role":"latest"},{"artifact_id":"img_002","attempt_id":"a_002","display_id":"IMG_002","role":"best"}]}

Visible image labels:

[{"artifact_id":"img_004","attempt_id":"a_004","label":"LATEST_IMAGE: attempt a_004, artifact img_004","role":"latest"},{"artifact_id":"img_002","attempt_id":"a_002","label":"BEST_IMAGE: attempt a_002, artifact img_002","role":"best"}]

Latest equals best:

false

Active Skill operators:

[{"experience_id":"skill:counting_and_instance_layout@1.0.0:4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685","failure_signature":"active_skill_operator:counting_and_instance_layout","summary":"counting_and_instance_layout v1.0.0 hash=4e7077c86536 active operators: 1. State the exact total next to the object noun: \"exact...; 2. Use a bounded formation: row, arc, triangle, grid, or...; 3. Require full visibility and gaps; avoid piles, croppe...; 4. For edits, name the smallest operation: add, remove,...","support_count":1},{"experience_id":"skill:spatial_relation_layout@1.0.0:154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019","failure_signature":"active_skill_operator:spatial_relation_layout","summary":"spatial_relation_layout v1.0.0 hash=154561266eb9 active operators: 1. Name the relation in subject-object ord...; 2. Anchor both entities to frame/depth reg...; 3. For behind/in front, state depth and no...; 4. For left/right, use viewer-frame wording; 5. For above/below, state vertical separat...; 6. For inside/on, state containment or sup...; 7. For chasing/following/facing, state ori...","support_count":1}]

Retrieved skills:

[]

Extra observations:

["Budget is exhausted; submit the best available attempt with reason_code exactly best_available_under_budget. Do not use budget_exhausted_best_available."]
```

</details>

**Assistant Output**

- Raw teacher output SHA-256: `cee933ddc9ac6f093493845adccff35321207ef0c938a76ef53bdc45aaa8bc9b`
- Raw redacted teacher output:

```json
{
  "finish_reason": "stop",
  "model_id": "gpt-5.5",
  "raw_text": "{\"schema_version\":\"0.2\",\"action\":\"submit_attempt\",\"arguments\":{\"reason_code\":\"best_available_under_budget\",\"selected_attempt_id\":\"a_002\"}}",
  "redaction": {
    "credentials_removed": true,
    "redaction_rules": [
      "No authorization headers or API keys are persisted by the teacher client."
    ]
  },
  "request_id": "phase3_ep_001_turn_011",
  "response_metadata": {
    "created": 1784106213,
    "id": "resp_09c6a185cf9b82e7016a574ce22e8c819a92648a51d7930b35",
    "raw_text_sha256": "cee933ddc9ac6f093493845adccff35321207ef0c938a76ef53bdc45aaa8bc9b",
    "usage": {
      "completion_tokens": 88,
      "completion_tokens_details": {
        "accepted_prediction_tokens": null,
        "audio_tokens": null,
        "reasoning_tokens": 51,
        "rejected_prediction_tokens": null
      },
      "prompt_tokens": 6731,
      "prompt_tokens_details": {
        "audio_tokens": null,
        "cached_tokens": 1792
      },
      "total_tokens": 6819
    }
  },
  "schema_version": "0.2"
}
```
- Canonical action:

```json
{
  "action": "submit_attempt",
  "arguments": {
    "reason_code": "best_available_under_budget",
    "selected_attempt_id": "a_002"
  },
  "schema_version": "0.2"
}
```

**Submission Output**

- Selected attempt: `a_002`
- Reason code: `best_available_under_budget`
- Selected pass count: 9/11
- Latest at submission: `a_004`
- Best at submission: `a_002`
- Interpretation: submits historical best instead of latest.
