# Muse Image-Informed Ablation Design — Sol Review

Reviewer: GPT-5.6 Sol

Verdict: `PASS_WITH_REQUIRED_CHANGES`

## Decision

The staged design can isolate adaptive retry value. No additional baseline is
blocking. The shared-initial-image four-arm pilot is sufficient if Best-of-K
and the fixed heuristic use the same attempt cap, evaluator schedule, action
availability where applicable, and terminal selector as the full planner.

Single-shot is the cost anchor, Best-of-K controls additional sampling, and the
fixed heuristic controls verifier-guided edit capability without learned
planning.

## Required Changes

1. Freeze the selector and estimand before live data. Keep the current
   pass-count reducer as operational `submitted`/`best_by_pass`, use
   prompt-level submitted Soft-TIFA GM as primary, and report
   `best_by_gm@K` only as a post-hoc oracle secondary. Do not silently switch to
   GM-only or pass-count/GM lexicographic selection; either changes protocol
   semantics and requires ADR/revalidation. Claim improvement in submitted GM,
   not that the system directly optimizes GM.
2. If atom-level grounding remains a contribution claim, planner-only
   differences are insufficient. Confirmatory live outcomes must include full
   versus aggregate-only feedback and full versus no-verifier. Aggregate-only
   versus no-verifier is interpretive enrichment rather than separately
   blocking.
3. A blinded human or genuinely independent evaluator audit on a frozen
   confirmatory subset is mandatory for a general image-quality claim and must
   not feed planning or selection. Without it, conclusions must be restricted
   to the Geneval2-defined objective.
4. Information ablations must be orthogonal. `-V` removes all verifier
   derivatives, including best labels, fixed/regressed/persistent transitions,
   and score-encoding metadata. Aggregate-only cannot leak atom identities or
   expected/observed text. `-I` removes captions, descriptions, filenames, and
   other visual-content metadata. Planner-only labels come from event prefixes,
   never later outcomes.
5. Equal image calls are not necessarily equal total compute. Report
   generation/edit cost, evaluator calls, planner tokens, early submission,
   GPU-seconds, and logical charging of the shared initial image. Use the term
   `equal image-call budget` unless total compute is actually matched. Original
   prompt is the independent unit; prefixes, attempts, atoms, and seeds are
   repeated measurements, with seeds nested under prompt.

## Review Boundary

This review approves the experiment ordering after the required clarifications.
It does not approve a schema, reducer, selector, PlannerContext, or supervision
change, and it does not constitute a protocol gate.
