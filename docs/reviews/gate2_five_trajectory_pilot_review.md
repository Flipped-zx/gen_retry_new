# Gate 2 Review — Five-Trajectory Pilot

## Verdict

`APPROVE`

## Blocking Issues

None.

## Reviewer Summary

The completed Phase 3 evidence supports proceeding to Phase 4: ten fresh live trajectories, 49 image attempts, 49 Geneval2 normalized evaluations, 69 canonical actions, 9 rejected raw turns excluded from SFT, and 38 positive/recovery candidate actions.

No mismatch was found in best-so-far submission, edit source validity, max-attempt budget, atom normalization, or SFT candidate masking.

## Risks To Carry Into Phase 4

- `query_skill -> skill_returned` interactions are real, but returned skill files are placeholder-level. Phase 4 must explicitly decide whether query-skill actions are trainable.
- Behavior distribution is skewed toward regressions and budget-exhausted recovery, with weak direct-success coverage.
- Older Phase 3 preflight docs mention the superseded endpoint blocker; the live checkpoint supersedes them.

## Minimal Validation Experiment

Run a Phase 4 export dry run over all 78 labeled records and assert that loss is applied only to canonical assistant actions labeled `trainable_positive` or `recovery_positive`; raw teacher outputs, format errors, tool responses, Geneval2 observations, harmful/ineffective actions, and environment-owned facts must be context-only.
