# ADR-0009: Advisory Instruction-Quality Linter

- Status: Accepted after focused GPT-5.6 Sol review
- Action protocol: `0.5` unchanged
- PlannerContext: `0.7` unchanged
- Teacher policy: `teacher_system_prompt_v9_meaningful_retry_verb_retention`

## Context

The instruction-quality checker combines deterministic facts with regex-based
prompt-writing heuristics. In the fixed-20 Flow-DPPO v9 admission pilot,
`phase3_ep_004` attempted to preserve five correct kangaroos while replacing
one ambiguous doubled cluster to obtain exactly six. Four reasonable variants
were rejected because the same entity noun appeared in bounded preservation
and modification language. The rejection consumed all format-repair turns and
stopped an otherwise resumable episode with one image Attempt remaining.

JSON Schema and reference validation already reject malformed Actions, unknown
constraint IDs, target/preserve constraint-ID overlap, and unknown source
Attempts. Runtime checks separately enforce budget, action order, source
lineage, and evidence for editing from a non-best historical Attempt.

## Decision

1. Instruction-quality `pass`, `warn`, and `reject` verdicts are advisory.
2. Live execution does not reject or repair an Action based on regex-derived
   instruction-quality findings.
3. The linter and detailed flags remain available to trace export, checkpoint
   audit, and post-hoc SFT candidate filtering. Prospective reports are stored
   in the canonical action log with their `action_event_id`, explicitly marked
   as advisory environment metadata.
4. Schema, reference, runtime, lineage, budget, and future-leakage checks remain
   hard gates.
5. Completed valid trajectories are not rerun. Only the interrupted
   `phase3_ep_004` is resumed before the fixed-20 admission audit.

## Consequences

- A semantic linter can no longer substitute for the Planner or waste an image
  opportunity indirectly through repeated Teacher repair calls.
- Weak or meaningless retries may exist in canonical history, where their real
  Geneval2 outcome can label them harmful or ineffective.
- Positive SFT supervision still requires the separate outcome and
  compatibility policy; an executed Action is not automatically a target.
- No Action schema, PlannerContext, Qwen, Geneval2, reducer, score policy, or
  image budget semantics change.

## Review

GPT-5.6 Sol returned `PASS_WITH_REQUIRED_CHANGES`. The required change was to
persist each prospective report as structured audit metadata linked to the
canonical image Action, while keeping it out of SFT targets and ensuring a
checker failure cannot block execution. The implementation includes that
change. Sol accepted one resumed `phase3_ep_004` plus the deterministic
fixed-20 audit as sufficient admission evidence for IDs 021-1000.
