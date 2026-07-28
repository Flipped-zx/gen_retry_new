# Structured Output Probe

Date: 2026-07-15

## GPT-5.5 Endpoint Probe

Sanitized live probe result:

- `TEACHER_API_KEY`: SET
- `TEACHER_BASE_URL`: SET
- requested model: `gpt-5.5`
- request used `response_format: {"type": "json_schema", "json_schema": ...}`
- HTTP result: `200`
- `finish_reason`: `stop`
- returned content parsed as JSON: yes
- returned object matched the probe schema:

```json
{
  "schema_version": "0.2",
  "action": "submit_attempt",
  "arguments": {
    "selected_attempt_id": "a_000",
    "reason_code": "best_available_under_budget"
  }
}
```

No credentials were printed or persisted.

## Current Gen-Retry v3 Status

`src/gen_retry/agent/teacher_client.py` currently calls `client.chat.completions.create(...)` without `response_format`.

Therefore the live trajectory currently relies on prompt-level action formatting plus post-hoc parse/schema/reference/runtime/instruction validation.

## Reference Repository Evidence

Relevant GenEvolve agent evidence:

- `/root/private_data/agentic_image/GenEvolve/genevolve/agent.py`
- `_parse_tool_call` extracts `<tool_call>{...}</tool_call>` by regex and `json.loads`.
- `_parse_answer` extracts `<answer>{...}</answer>` by regex and `json.loads`.
- the rollout loop retries by appending a format-error `<tool_response>` if no valid tag is found.

Relevant Gen-Searcher image workflow evidence:

- `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-RL/rllm/vision_deepresearch_async_workflow/gen_image_deepresearch_agent.py`
- prompt requires exactly one `<tool_call>{json}</tool_call>` or `<answer>{json}</answer>` per round.
- code detects tags by string checks/splits, parses with `json5.loads`, and adds explicit format-error observations on malformed output.
- `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-RL/rllm/vision_deepresearch_async_workflow/gen_image_deepresearch_workflow.py` extracts actions from these tags.

Conclusion: the relevant Gen-Searcher/GenEvolve image-agent trajectories use strict tagged action formats plus parser/retry feedback, not provider-level `response_format=json_schema` as the primary mechanism.

## Recommended Adaptation

For Gen-Retry v3, use both:

1. provider-level `response_format=json_schema` for `action_protocol_v0_2`;
2. existing parser/reference/runtime/instruction validators as defense in depth.

The provider schema should reduce missing-field errors such as `generate_image` without `mode`, while validators still enforce episode-specific facts that the provider schema cannot know, such as valid `source_attempt_id`, active Skill grounding, budget, and instruction quality.

## Segment Test: `phase3_ep_001_turn_001`

Test input:

- run: `runs/teacher_prompt_v1_validation/phase3_ep_001`
- request: `phase3_ep_001_turn_001`
- state: after successful `query_skill`, no image attempts yet
- original failure: Teacher emitted `generate_image` content but omitted required `arguments.mode`

Full schema attempt:

- request used the repository `schemas/action_protocol_v0_2.schema.json` as provider `response_format=json_schema`
- result: rejected by provider
- provider limitation 1: `uniqueItems` is not permitted
- provider limitation 2: after removing unsupported metadata/`uniqueItems`, `oneOf` is not permitted

Action-specific schema attempt:

- request used a provider-compatible `generate_image` schema for this step
- result: HTTP `200`
- `finish_reason`: `stop`
- returned action parsed as JSON: yes
- returned action validated locally against the full repository schema: yes

Returned action summary:

```json
{
  "schema_version": "0.2",
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
      "exact_count",
      "depth_relation",
      "motion_relation"
    ]
  }
}
```

Instruction excerpt:

```text
Create a single scene with exactly one brown donut in the foreground center. Place exactly three red cats total in the background behind the donut, fully visible and separated from each other, with the donut clearly in front of them. Place exactly six glass lions total, all fully visible and separated, arranged in a bounded arc around the cats so the group is countable. Show the six lions actively chasing the three cats...
```

Conclusion:

Provider-level structured output can fix the observed missing-`mode` class of error when the runtime supplies an action-specific schema. The full v3 discriminated-union schema still needs a provider-compatible projection because this endpoint rejects `uniqueItems` and `oneOf`.
