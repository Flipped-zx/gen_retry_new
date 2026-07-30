# Phase 7 Fresh-8 Checkpoint 80 Sol Review

## Verdict

`PASS_WITH_PROSPECTIVE_CHANGE`

## Direct Answers

1. The audited trajectories show no protocol, memory, lineage, data-integrity,
   or SFT-boundary blocker. Completion-based freezing does introduce selection
   bias: submission time favors short and successful episodes. Eight cohort
   episodes completed in one attempt, and 11/20 are in the local easy tier.
   Therefore, the audit is valid for the completed frozen cohort but is not an
   unbiased safety or incident-rate claim over all admitted work.
2. The gains, 0.53 submitted-to-peak gap, regressions, ineffective actions,
   and rejected Teacher turns do not indicate a wrong direction. Best-attempt
   reduction contains regressions, while harmful, ineffective, and invalid
   outputs remain excluded from positive SFT targets. The ten
   instruction-quality rejections warrant monitoring but are not canonical
   protocol failures or positive supervision.
3. Continue to checkpoint 100 with a prospective checkpointing correction.
   Predeclare an admission-order or episode-ID cohort and account for every
   selected episode as completed, failed, or pending/censored. Completion-order
   cohorts may still report throughput and completed-quality evidence, but not
   representative incident or safety rates without an admitted-work
   denominator.

## Blockers

None requiring stopped admission.

## Required Prospective Change

At checkpoint 100, report separately:

1. completion-conditioned quality metrics for a frozen set of valid
   trajectories;
2. status of every episode in a predeclared admission/ID cohort, including
   completed, failed, and pending/censored cases.

The checkpoint-80 metrics must be described as completion-conditioned.

## Optional Diagnostics

- Report completion latency by difficulty tier.
- Report Teacher instruction-quality rejection rate by difficulty tier.
