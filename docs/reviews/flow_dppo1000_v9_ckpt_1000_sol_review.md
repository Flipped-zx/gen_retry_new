# Flow-DPPO 1000 v9 Final Sol Review

## Verdict

`PASS_WITH_BLOCKED_SFT_EXPORT`

## Trajectory Pool

The immutable canonical pool is accepted. All 1000 episodes are submitted and
closed, and all 3443 image executions have matching start, completion, image,
Attempt, and Geneval2 records. Source lineage, point-in-time PlannerContext,
reducer-best submission, resume integrity, manifest closure, and credential
scans pass.

The quality direction is useful and internally coherent:

- atom pass: `79.86% -> 90.85%`;
- Soft-TIFA AM: `80.60 -> 90.25`;
- submitted Soft-TIFA GM: `40.32 -> 71.14`;
- all-pass episodes: `260 -> 552`;
- post-hoc GM peak: `72.30`, only `1.16` above submitted GM.

Hard prompts and verb atoms remain weak, but this is valuable failure coverage
rather than evidence of dataset corruption. The 749 regression Actions and 547
strict no-progress Actions are valid observed outcomes. They belong in history
but are not automatically positive supervision.

## Protocol And Resume

No blocking protocol or data-integrity issue was found. The resumed 83
episodes created no orphan images or half-written Attempts. The 13 early raw
Teacher rejections do not invalidate canonical trajectories; episodes 021-1000
created zero linter-triggered repair turns.

Linter verdicts must remain advisory. At least 169 canonical image Actions
with `reject` verdicts produced an initial or new-best result, so linter output
cannot define SFT inclusion.

## SFT Boundary

Positive SFT export remains blocked because action-level v9 compatibility and
outcome eligibility have not been frozen. Executed, schema-valid, or
reducer-best-producing Actions are not automatically valid imitation targets.

Required before Gate 3:

1. Run the outcome-blind compatibility audit from each exact point-in-time
   PlannerContext, including semantic comparison with earlier failed
   instructions.
2. Independently label outcomes against `best_before`: atom-best gain, strong
   GM-only gain, marginal gain, local-only progress, harmful, ineffective, and
   submit-best.
3. Apply loss only to compatible first generations, qualifying retries, and
   correct reducer-best submissions. Keep harmful and ineffective Actions as
   context.
4. Keep `query_skill`, tool responses, evaluator observations, raw Teacher
   errors, linter metadata, and images outside assistant loss until Skill
   timing and utility receive separate approval.
5. Verify one frozen v9 training system policy, no future leakage, full
   provenance, and the final linter-verdict by outcome-tier by SFT-inclusion
   report.
6. Complete or formally resolve the predeclared equal-budget paired-policy
   validation, then perform Gate 3 supervision freeze.

## Claim Limits

This batch supports claims about trajectory integrity, retry coverage, and
within-trajectory initial-to-submitted improvement. It does not establish an
official Geneval2 leaderboard score, adaptive-policy superiority over an
equal-compute Best-of-K baseline, generator-level improvement, or readiness of
every canonical Action for positive SFT.
