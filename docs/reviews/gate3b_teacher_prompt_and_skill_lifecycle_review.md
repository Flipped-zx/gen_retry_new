# Gate 3b Teacher Prompt and Skill Lifecycle Review

Date: 2026-07-15

Reviewer: GPT-5.6 Sol XHigh

## Final Sol Verdict

`REQUEST_CHANGES`

Sol reviewed the final three questions:

1. Does the Teacher prompt correctly separate foundational Skill operators from retry-policy decisions?
2. Is the edit/generation instruction contract concrete enough to prevent vague or contradictory rewrites before the next live trajectory?
3. Is the Skill retention/no-repeat policy efficient and auditable without changing the frozen action schema?

## Blocking Issues Reported

1. Instruction validation was pre-execution, but too lexical and still accepted omissions, incompatible counts, depth contradictions, and preserve/modify conflicts.
2. Retained Skill summaries included `preferred_action: generate_image`, which contradicted the policy boundary between foundational Skills and retry decisions.
3. Retained Skill content was reconstructed from the mutable current Skill store, and compact summaries could hard-truncate the last operator.

## Corrections Applied After Review

1. `src/gen_retry/agent/instruction_quality.py` now rejects missing required entities, missing attribute/entity bindings, missing forbidden-change wording, incompatible counts, depth contradictions, and preserve/modify conflicts.
2. `src/gen_retry/phase3/live_runner.py` no longer emits `preferred_action` for active Skill operator summaries.
3. `src/gen_retry/phase3/live_runner.py` now uses retrieval-time Skill content from `tool_observations.jsonl`, verifies the recorded content hash, and falls back only to hash-verified `content_ref` or an explicit unavailable marker.
4. Compact Skill operator summaries now allocate bounded text across all available operator bullets and avoid hard-truncating the final bullet.

## Verification After Corrections

- `python -m compileall -q src/gen_retry`
- `pytest tests/unit/test_teacher_prompt_contract.py tests/unit/test_skill_v1_runtime_policy.py -q` -> 14 passed
- `pytest tests/unit/test_teacher_prompt_contract.py tests/unit/test_export_trajectory_trace_format.py tests/unit/test_skill_v1_runtime_policy.py tests/contract/test_action_protocol.py tests/contract/test_event_schema.py tests/contract/test_planner_view_schema.py -q` -> 59 passed
- `python -m gen_retry.cli.validate_schemas` -> validated 5 schemas
- `git diff --check`
- `python -m gen_retry.cli.export_trajectory_trace --run-dir runs/skill_v1_validation_policyfix/phase3_ep_001 --output /tmp/teacher_prompt_trace_preview.md`

No live trajectory, Qwen-Image-Edit, or Geneval2 execution was run.
