# SOL_REVIEW_REQUEST

## Gate

`SFT Supervision Freeze`

## Decision to review

Decide whether the completed native GPT-5.5 teacher-only A/B pilot is sufficient
to reintroduce required trainable `decision_summary` into the next canonical
Planner Action protocol.

## Current evidence

- Prior reconsideration:
  - `docs/reviews/planner_io_v05_decision_summary_reconsideration_sol_review.md`
  - verdict: `REINTRODUCE_REQUIRED_TRAINABLE`, conditional on a native pilot.
- Pilot implementation:
  - `src/gen_retry/cli/run_decision_summary_teacher_pilot.py`
- Sanitized pilot artifacts:
  - `artifacts/phase4/decision_summary_teacher_pilot/summary.json`
  - `artifacts/phase4/decision_summary_teacher_pilot/control__*.json`
  - `artifacts/phase4/decision_summary_teacher_pilot/candidate__*.json`
- Fixed pre-outcome PlannerContext cases:
  - first generation;
  - regeneration after broad failure;
  - localized edit;
  - rollback to historical best after latest regressed;
  - submit historical best after budget exhaustion.
- Sampling:
  - GPT-5.5 Teacher;
  - two control and two candidate samples per case;
  - 20 calls total;
  - no Qwen-Image-Edit or Geneval2 calls.
- Automatic results:
  - control: 10/10 schema-valid, reference-valid, and decision-correct;
  - candidate: 10/10 schema-valid, reference-valid, decision-correct, and
    summary length/format compliant;
  - candidate: 0/10 future-leakage regex matches;
  - candidate: 5/10 causal-connector heuristic matches;
  - heuristic false negatives include summaries using `so`, which was absent
    from the regex.
- The candidate artifacts contain the complete native summaries and no
  credentials.

## Questions

1. Manually inspect all ten candidate summaries. Does each express enough
   visible-state-to-decision rationale for its structured action, source, or
   submit selection without becoming chain-of-thought or instruction
   duplication? Identify any failing sample exactly.
2. Is the candidate protocol no worse than control on action correctness and
   sufficiently better in planner supervision to pass the conditional pilot?
   Return one final verdict: `PASS_REINTRODUCE` or `FAIL_KEEP_V05`.
3. If the verdict is `PASS_REINTRODUCE`, state the final field contract and
   whether `so` should be accepted as a valid causal connector. If it is
   `FAIL_KEEP_V05`, state the one minimal blocking defect; do not propose a
   broad redesign.

## Explicit non-goals

- Do not edit code, schema, ADR, artifacts, or completed trajectories.
- Do not run additional Teacher, Qwen-Image-Edit, or Geneval2 calls.
- Do not reopen PlannerContext, Skill, or other action-field decisions.
- Do not inspect or report credentials.

## Expected response

- exactly one final verdict: `PASS_REINTRODUCE` or `FAIL_KEEP_V05`;
- failing sample IDs, if any;
- concise rationale;
- final field contract if passed;
- no implementation.
