# Phase 7 Fresh-8 Checkpoint 140 Sol Review

## Verdict

`PASS_WITH_PROSPECTIVE_CHANGE`

## Direct Answers

1. No validity blocker was found. Routing, lineage, evaluator coverage, memory
   ownership, SFT masking, and future-leakage checks pass. The fixed admission
   denominator remains intact: 18/20 completed, two active, zero failed or
   omitted.
2. Difficulty alone does not fully explain the decline. All-pass fell within
   every tier, though all 13 failures were exactly one atom short and submitted
   quality still gained 11 atoms and 27.96 GM. The 2.01 GM gap is concentrated
   in two episodes and remains compliant with pass-count-first selection. The
   stronger signal is regression concentration: 23/79 image actions versus
   67/372 previously. This is a retry-policy closure problem, not invalid data
   or a wrong overall direction.
3. Continue admission with a forward-only, versioned planner-policy
   correction. After a regressive or no-progress result, do not repeat the
   same source/action/target strategy. Source-conditioned retries default to
   reducer-best unless a historical source has explicit relevant constraint
   evidence. Keep schemas, scoring, routing, completed history, and SFT labels
   unchanged, and report post-change episodes separately.

## Blockers

None.

## Required Prospective Change

- Version the Teacher policy.
- Reject an identical action/source/target tuple after regression or strict
  no-progress.
- Default edit source to reducer-best.
- Permit a non-best source only when its persisted constraint results contain
  relevant pass evidence absent from best.
- Do not rewrite completed trajectories.
- Separate v8 post-change evidence at checkpoint 150/160.
