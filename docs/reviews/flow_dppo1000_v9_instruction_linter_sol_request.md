# Flow-DPPO 1000 v9 Instruction Linter Sol Review Request

This request is the frozen copy of
`docs/templates/SOL_REVIEW_REQUEST.md` for the fixed-20 admission repair.

## Decision

Demote `src/gen_retry/agent/instruction_quality.py` from a live execution gate
to an advisory, deterministic audit. JSON Schema, constraint/attempt/Skill
reference validation, runtime budget, source lineage, and non-best-source
evidence validation remain hard gates.

The linter continues to report `pass`, `warn`, or `reject` and all detailed
flags for post-hoc filtering. Its regex-derived semantic verdict no longer
causes a Teacher repair turn or prevents Qwen execution.

## Evidence

- Fixed pilot IDs 001-020 produced 19 valid submissions.
- `phase3_ep_004` reached four evaluated Attempts with one image call left.
- Its next count-repair Action preserved five correct kangaroos and replaced
  one ambiguous doubled/ghost cluster to obtain six clear kangaroos.
- The linter rejected four semantically reasonable variants because the noun
  `kangaroos` appeared under both bounded preservation and modification.
- Strict Action/reference validation already rejects unknown constraints,
  target/preserve ID overlap, and unknown edit sources.
- Completed valid trajectories will not be rerun; only `phase3_ep_004` resumes.

## Questions

1. Is advisory-only treatment of regex-derived instruction quality the right
   boundary for rollout collection, given strict schema/reference/runtime
   validation and post-hoc trajectory filtering remain in force?
2. Does this change introduce any blocking SFT inconsistency if canonical
   history retains the executed Action and later supervision filters harmful
   or meaningless retries by observed outcome?
3. Is one resumed `phase3_ep_004` plus the deterministic fixed-20 audit
   sufficient admission evidence before IDs 021-1000 are started?

## Non-goals

- No Action schema, PlannerContext, reducer, Geneval2, Qwen, or score-policy
  change.
- No modification or rerun of completed trajectory artifacts.
- No claim that an advisory linter proves semantic instruction quality.

## Expected Verdict

`PASS`, `PASS_WITH_REQUIRED_CHANGES`, or `FAIL`, with required changes separated
from optional future analysis.
