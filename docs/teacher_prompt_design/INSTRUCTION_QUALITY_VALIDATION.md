# Instruction Quality Validation

Date: 2026-07-15

Implementation: `src/gen_retry/agent/instruction_quality.py`

## Purpose

The instruction-quality checker is a deterministic advisory linter for
`generate_image` and `edit_image` actions. It reports whether the exact image
instruction follows known prompt-writing heuristics.

It does not rewrite Teacher output and does not change the canonical action schema.
Its semantic checks are regex-derived and are not authoritative evidence that
an instruction is executable or useful.

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

The verdict is advisory. Live Phase 3 execution does not reject an Action or
consume a Teacher repair turn because of this verdict. Hard execution gates
remain the JSON Schema, reference validator, budget and action-order checks,
source lineage, and non-best-source evidence policy.

For prospective Actions, the linter report is persisted under
`instruction_quality` in the canonical action log, linked by `action_event_id`,
with `enforcement=advisory` and `sft_role=environment_metadata`. A checker
failure is recorded as `verdict=unavailable` and does not block execution. The
report also remains available to trace export and rollout audit. Harmful,
ineffective, vague, or semantically repetitive Actions may be excluded from
positive SFT supervision after their actual evaluator outcome is known.

This boundary avoids false rejection of bounded subset edits such as preserving
five correct kangaroos while replacing one ambiguous doubled kangaroo to repair
the total count. Entity-level noun overlap is not proof of a contradictory
instruction.

The linter must not silently mutate the action.

## Tests

Focused tests are in:

- `tests/unit/test_teacher_prompt_contract.py`
