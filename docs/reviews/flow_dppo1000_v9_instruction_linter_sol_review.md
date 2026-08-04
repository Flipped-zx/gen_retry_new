# Flow-DPPO 1000 v9 Instruction Linter Sol Review

## Verdict

`PASS_WITH_REQUIRED_CHANGES`

## Answers

1. Regex-derived instruction-quality judgments should be advisory only. The
   `phase3_ep_004` bounded subset count repair is a concrete false positive;
   strict schema, references, lineage, budget, and source-selection rules
   remain suitable hard gates.
2. There is no blocking SFT inconsistency when the executed canonical Action
   remains the assistant Action, the linter report is environment metadata,
   and productive/harmful/ineffective labels come from later outcomes.
   Advisory `reject` must not automatically exclude a productive Action.
3. Resuming only `phase3_ep_004` and passing the deterministic fixed-20 audit
   is sufficient to admit IDs 021-1000. This is runtime admission evidence,
   not proof that instruction quality is universally solved.

## Required Change

Persist every prospective image-Action linter report as structured audit
metadata linked to the canonical Action. It must not create a `format_error`,
block execution, or become an SFT target.

## Resolution

Implemented in the canonical action log under `instruction_quality`, linked by
`action_event_id`, with:

- `enforcement: advisory`;
- `sft_role: environment_metadata`;
- the full deterministic report;
- `verdict: unavailable` with a sanitized exception type if the checker itself
  fails.

Planned 100/200-trajectory reviews should monitor advisory-flag rates and their
correlation with observed outcomes.
