# Gate 3 Flow-DPPO 1000 v9 Selective-Skill SFT Review

Reviewer: GPT-5.6 Sol  
Date: 2026-08-04

## Verdict

`PASS_FREEZE_WITH_MONITORING`

The `flow_dppo1000_v9_selective_skill_v1` policy is approved for the formal
1000-trajectory Full SFT export and launch, subject to the ordinary frozen
export and complete LLaMA-Factory token-audit checks. No additional
`query_skill` targets should be admitted in this run.

## Questions

### 1. Utility-linked `query_skill` rule

The rule is sufficiently conservative and useful for cold-start SFT. It
requires all of the following evidence:

- the analysis record has a protocol-linked `skill_returned` event
  (`skill_grounding`);
- the first subsequent image action is labeled `trainable_positive` or
  `recovery_positive`; and
- that action's target or preserve constraint IDs overlap the query's target
  constraint IDs.

This admits 999 of 1,051 valid skill calls and keeps 52 calls context-only.
Queries without a returned Skill, without constraint overlap, or followed by a
harmful/ineffective image action should remain masked. Admitting the remaining
queries would add weak or unidentifiable action targets and is not justified
by the current evidence.

The rule is an outcome-linked utility proxy, not a causal proof that the image
instruction copied Skill content. That distinction is why post-checkpoint
monitoring is required.

### 2. Target, history, and mask contract

The contract is coherent for the Full SFT run. The reconciliation emits 4,302
targets:

- 3,303 positive/recovery `generate_image`, `edit_image`, and `submit_attempt`;
- 999 utility-linked `query_skill` actions.

The other 1,205 labeled records remain context-only: 601 harmful actions, 539
ineffective actions, 52 non-utility skill calls, and 13 raw invalid outputs.
This preserves failures in canonical history without teaching the model to
repeat them. The renderer and exporter enforce one canonical assistant action
as the only loss-bearing message; system, user, tool, evaluator, and raw
teacher observations are masked.

The audit reports zero loss-mask violations, noncanonical targets, mixed
execution profiles, mixed PlannerContext/score contracts, or prompt-group split
violations. The split is deterministic and prompt-group isolated (800/100/100
groups for train/validation/test), and each target context is rebuilt from its
temporal event prefix, so later evaluator outcomes are not visible in the
input. Image/source bindings are validated by the exporter rather than
constructed from arbitrary paths.

### 3. Leakage, split, source-image, and protocol blockers

No launch-blocking issue is present in the supplied implementation or the
1000-trajectory reconciliation audit. The remaining launch requirements are
release mechanics, not policy defects: create the Gate 3 approval receipt
bound to the exact evidence hashes, export with `release_status: frozen`, and
run the complete token-mask audit against the final runtime YAML before
starting training.

## Required Monitoring (non-blocking)

1. At the first checkpoint and on the fixed validation subset, report JSON
   schema validity, invalid-output rate, action distribution, and
   `query_skill` rate. Alert on query collapse (near-zero) or query flooding
   (most turns) relative to the frozen data distribution.
2. For sampled inferred queries, record whether the subsequent image action
   targets/preserves the queried constraints and whether the resulting
   transition improves the held-out verifier score. Treat this as an evaluation
   metric, never as a new SFT label during this run.
3. Continue ordinary loss/throughput/finite-gradient monitoring. Stop or
   investigate on NaN/Inf, mask drift, or a validation-loss increase together
   with degraded structured-action validity.

These checks can be run at checkpoint 100 or 200 without changing the frozen
dataset or protocol. They are not prerequisites for launching the Full SFT.

## Evidence Reviewed

- `runs/phase7_flow_dppo1000_v9_fresh8_v1` (1,000 submitted trajectories)
- `docs/phase7/flow_dppo1000_v9_analysis/sft_candidate_action_report.md`
- `docs/phase7/flow_dppo1000_v9_sft_reconciliation.md`
- `artifacts/phase7/flow_dppo1000_v9_sft_reconciliation/sft_dry_run_audit.json`
- `src/gen_retry/sft/supervision.py`
- `src/gen_retry/sft/llamafactory.py`
- `tests/unit/test_sft_supervision.py`

