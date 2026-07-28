# Instruction Quality Validation

Date: 2026-07-15

Implementation: `src/gen_retry/agent/instruction_quality.py`

## Purpose

The instruction-quality validator is a deterministic linter for `generate_image` and `edit_image` actions. It reports whether the exact image instruction is concrete enough to send to Qwen-Image-Edit.

It does not rewrite Teacher output and does not change the canonical action schema.

## Report Fields

For each image action, the linter reports:

- target constraints referenced;
- preservation constraints referenced;
- exact count coverage;
- required entity coverage;
- attribute/entity binding coverage;
- spatial grounding coverage;
- semantic block coverage;
- forbidden-change coverage;
- vague-language flags;
- contradiction flags;
- incompatible count flags;
- overbroad-edit flags;
- unsupported-content flags;
- preserve/modify conflict flags;
- source-attempt consistency;
- final verdict: `pass`, `warn`, or `reject`.

## Verdict Policy

- `pass`: required entity, attribute, count, spatial, semantic-block, and forbidden-change coverage are present; no contradiction, incompatible count, overbroad edit, preserve/modify conflict, unsupported critical content, or unknown source.
- `warn`: instruction is otherwise executable but contains vague language.
- `reject`: instruction has missing required entity/attribute/count/prohibition coverage, contradiction, incompatible count, overbroad local edit, preserve/modify conflict, unsupported critical content, missing edit semantic block, or unknown `source_attempt_id`.

In live Phase 3 runtime, every `generate_image` and `edit_image` action must receive `pass` before `action_validated` and before image execution. A `warn` or `reject` verdict produces a structured `instruction_quality_rejected` validation observation through the same repair path as schema/runtime validation failures.

The linter must not silently mutate the action.

## Tests

Focused tests are in:

- `tests/unit/test_teacher_prompt_contract.py`
