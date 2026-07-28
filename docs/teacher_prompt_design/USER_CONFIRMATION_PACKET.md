# User Confirmation Packet: Teacher Prompt + Skill Lifecycle v1

Date: 2026-07-15

## 1. Main Defects Found

Audit file: `docs/teacher_prompt_design/CURRENT_EDIT_INSTRUCTION_AUDIT.md`

- Initial generation was usable but risky because it weakened the required `behind` relation with `above or beside`.
- First edit was contradictory: `forward toward/behind` mixed incompatible depth/motion wording.
- Second edit was too vague: `modify only the failed parts` and `preserve all correct evidence` did not name target objects, operations, or locks.
- Third edit was overbroad for a local edit and risked global scene reconstruction.
- Best-branch edit was the strongest instruction, but still did not improve the best attempt.

## 2. Final Teacher System-Prompt Rules

File: `docs/teacher_prompt_design/TEACHER_SYSTEM_PROMPT_V1.md`

- Teacher is a verifier-grounded multimodal retry planner.
- Goal is to maximize the best valid attempt under remaining image-attempt budget.
- Output exactly one canonical action JSON object, with no prose or chain-of-thought.
- Skills provide generation/edit instruction operators only.
- Skills do not decide generate versus edit, branch versus latest, continue, or submit.
- Teacher must use visible images and Geneval2 atom feedback together.
- Teacher must compare latest and best images when they differ.
- Teacher must use fixed, regressed, persistent, stable-pass, and repeated-strategy history.
- Teacher must not repeat a materially equivalent ineffective instruction without a concrete change.

System prompt version: `teacher_system_prompt_v1`

System prompt SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`

## 3. Final Edit-Instruction Four-Block Contract

File: `docs/teacher_prompt_design/IMAGE_INSTRUCTION_CONTRACT_V1.md`

Every `edit_instruction` must include:

1. Target operation: exact object or region, exact add/remove/reposition/attribute operation, exact final state.
2. Spatial grounding: bounded region or relative position, orientation, depth, occlusion when relevant.
3. Preservation lock: stable passed constraints, preserved entities/counts/materials/colors/relations/background/composition, and source attempt identity.
4. Forbidden changes: no extras, no unrelated object changes, no background redraw unless required, no broad scene reconstruction for a local edit.

The deterministic linter now rejects missing required entities, missing attribute/entity bindings, missing no-extra/forbidden-change wording, incompatible counts, depth contradictions, preserve/modify conflicts, overbroad local edits, unsupported content, and unknown source attempts.

## 4. Skill No-Repeat and Retention Policy

File: `docs/teacher_prompt_design/SKILL_LIFECYCLE_POLICY_V1.md`

- Full Skill Markdown is returned only after `query_skill`.
- Same Skill identity `(skill_id, version, content_sha256)` may be retrieved at most once per episode by default.
- At most two Skills may be queried at once.
- Consecutive query-only loops are forbidden.
- Repeated failure alone is not enough reason to query the same Skill again.
- Changed Skill version/hash is treated as a new identity.
- Compact active operator summaries persist in PlannerView after the full Markdown turn.
- Active summaries do not include `preferred_action`.
- Active summaries are built from retrieval-time Skill content in `tool_observations.jsonl`, hash-verified against the recorded event identity.

## 5. Files Changed

Design/review docs:

- `docs/teacher_prompt_design/CURRENT_EDIT_INSTRUCTION_AUDIT.md`
- `docs/teacher_prompt_design/TEACHER_MULTIMODAL_INPUT_CONTRACT.md`
- `docs/teacher_prompt_design/TEACHER_SYSTEM_PROMPT_V1.md`
- `docs/teacher_prompt_design/SKILL_LIFECYCLE_POLICY_V1.md`
- `docs/teacher_prompt_design/IMAGE_INSTRUCTION_CONTRACT_V1.md`
- `docs/teacher_prompt_design/INSTRUCTION_QUALITY_VALIDATION.md`
- `docs/teacher_prompt_design/HUMAN_READABLE_TRACE_FORMAT.md`
- `docs/teacher_prompt_design/USER_CONFIRMATION_PACKET.md`
- `docs/reviews/gate3b_teacher_prompt_and_skill_lifecycle_packet.md`
- `docs/reviews/gate3b_teacher_prompt_and_skill_lifecycle_review.md`

Runtime/code/tests:

- `src/gen_retry/agent/teacher_client.py`
- `src/gen_retry/agent/instruction_quality.py`
- `src/gen_retry/runtime/planner_view.py`
- `src/gen_retry/phase3/live_runner.py`
- `src/gen_retry/cli/export_trajectory_trace.py`
- `tests/unit/test_teacher_prompt_contract.py`
- `tests/unit/test_skill_v1_runtime_policy.py`
- `tests/unit/test_export_trajectory_trace_format.py`

## 6. Tests Run

- `python -m compileall -q src/gen_retry`
- `pytest tests/unit/test_teacher_prompt_contract.py tests/unit/test_skill_v1_runtime_policy.py -q` -> 14 passed
- `pytest tests/unit/test_teacher_prompt_contract.py tests/unit/test_export_trajectory_trace_format.py tests/unit/test_skill_v1_runtime_policy.py tests/contract/test_action_protocol.py tests/contract/test_event_schema.py tests/contract/test_planner_view_schema.py -q` -> 59 passed
- `python -m gen_retry.cli.validate_schemas` -> validated 5 schemas
- `git diff --check`
- `python -m gen_retry.cli.export_trajectory_trace --run-dir runs/skill_v1_validation_policyfix/phase3_ep_001 --output /tmp/teacher_prompt_trace_preview.md`

No live trajectory, Qwen-Image-Edit, or Geneval2 execution was run.

## 7. Sol Verdict

Final GPT-5.6 Sol verdict: `REQUEST_CHANGES`

Reported blockers:

1. Instruction validation was pre-execution but too weak.
2. Active Skill summaries carried `preferred_action: generate_image`.
3. Skill retention reread mutable current Skill content and could truncate the last operator mid-sentence.

Corrections applied after that verdict:

- linter now rejects the missing/contradictory cases Sol named;
- active Skill summaries no longer carry `preferred_action`;
- retained Skill content is retrieval-time and hash-verified;
- operator summaries allocate bounded text across all available operator bullets.

No third Sol review was invoked because the goal allowed only a scoped correction cycle.

## 8. Selected Fresh Validation Task

Use the first already-selected Phase 3 prompt as a fresh validation task:

- prompt source: `artifacts/phase3/selected_ten_prompts.json`
- new run root after approval: `runs/teacher_prompt_v1_validation`
- episode: `phase3_ep_001`
- prompt: `six glass lions chasing three red cats behind a brown donut`
- start state: empty attempt history and fresh generation

## 9. Exact Live Calls After Approval

After your approval, run:

```bash
mkdir -p artifacts/teacher_prompt_v1_validation
PYTHONPATH=src python -m gen_retry.cli.prepare_phase3_rollouts --selected-prompts artifacts/phase3/selected_ten_prompts.json --output-root runs/teacher_prompt_v1_validation --summary-output artifacts/teacher_prompt_v1_validation/rollout_prep_summary.json --max-image-attempts 5 --limit 1
PYTHONPATH=src python -m gen_retry.cli.run_phase3_rollouts_parallel --run-root runs/teacher_prompt_v1_validation --episode-id phase3_ep_001 --image-steps 40 --image-height 1024 --image-width 1024 --max-workers 1
PYTHONPATH=src python -m gen_retry.cli.export_trajectory_trace --run-dir runs/teacher_prompt_v1_validation/phase3_ep_001 --output docs/teacher_prompt_design/validation_trace_phase3_ep_001.md
```

The rollout command will invoke GPT-5.5 Teacher, local Qwen-Image-Edit, and Geneval2 through the existing runner.

## 10. Maximum Image Attempts

`max_image_attempts=5`

## 11. Unresolved Risks

- The instruction-quality validator is still deterministic and lexical; it is stronger, but not a semantic proof system.
- The final Sol verdict remains `REQUEST_CHANGES`; the named blockers were fixed locally but not re-reviewed by Sol.
- Historical Skill events without retrieval-time content can only fall back to hash-verified `content_ref` content or an unavailable marker.
- The next live trajectory may still fail on image-model capability or evaluator noise even if the Teacher input/output structure is correct.

## 12. Confirmation Request

Please answer yes or no:

Approve running the fresh validation trajectory above with Teacher prompt v1, Skill lifecycle v1, and instruction-quality gate enabled?
