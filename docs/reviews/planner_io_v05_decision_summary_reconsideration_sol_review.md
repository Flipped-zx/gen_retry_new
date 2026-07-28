# Planner I/O v0.5 Decision Summary Reconsideration

Date: 2026-07-27

Reviewer: GPT-5.6 Sol

## Verdict

`REINTRODUCE_REQUIRED_TRAINABLE`

The corrected provenance changes the prior evidentiary basis: v0.4 empty
`decision_summary` values came from projecting a v0.3 trajectory, not from a
native v0.4 rollout. They therefore cannot support deleting the field.

The existing structured fields describe what the planner selected, but they do
not directly supervise why it selected generate versus edit, latest versus
historical best, or continuation versus submission. A short native summary can
provide that state-to-decision bridge without becoming a long chain of thought.

## Recommended Contract

```json
"decision_summary": {
  "type": "string",
  "minLength": 12,
  "maxLength": 200,
  "pattern": "^[^\\r\\n]+$"
}
```

- Required for `generate_image`, `edit_image`, and `submit_attempt`.
- Not present on `query_skill`.
- Exactly one sentence and at most 48 policy-tokenizer tokens.
- Explains only the current action choice.
- An edit summary must explain the source selection.
- A submit summary must explain both stopping and attempt selection.
- May reference only information visible before the action.
- Must not contain a long reasoning chain, detailed diagnosis, instruction
  restatement, or prediction of future Geneval2 results.
- Must be emitted natively by the Teacher at action time; no post-hoc labels.
- Receives loss 1 with the rest of a selected positive/recovery action.
- Must not be required with loss 0.

Example:

```text
Edit a_002 because latest a_003 regressed c_002 while a_002 remains the best repair base.
```

## Required Native Pilot

Before refreezing Gate 3, use five fixed pre-outcome PlannerContexts:

1. first generation;
2. regeneration after broad failures;
3. localized edit;
4. rollback to best after latest regresses;
5. submission after budget exhaustion.

Sample the current and candidate protocols twice per context: 20 teacher-only
calls total. Do not invoke Qwen-Image-Edit or Geneval2.

The candidate passes only if:

- 10/10 outputs are schema-valid and reference-valid;
- 10/10 action/source/submit choices are correct and no worse than control;
- 10/10 summaries agree with structured fields and contain no future leakage;
- every summary expresses visible state to decision rather than restating the
  action;
- every summary is at most 200 characters and 48 tokens.

## Gate State

Gate 3 is open pending this native pilot. This review is a recommendation, not
an implemented schema change. `action_protocol_v0_5` remains the current
runtime protocol until the pilot passes and the schema, ADR, runtime, tests,
and documentation are amended together.
