# Checkpoint 80 Scope Qualification

The checkpoint-80 cohort was selected from valid trajectories by
`attempt_submitted.created_at`. Its quality metrics are therefore
**completion-conditioned**: they accurately describe the 20 frozen completed
trajectories, but they are not an unbiased estimate of quality, failure rate,
or incident rate over all episodes admitted by the scheduler.

In particular, incomplete or instruction-quality-failed episodes could not
enter the completed cohort. The queue and completed artifacts remain valid;
the limitation concerns only the population to which checkpoint-80 aggregate
claims may be generalized.

Checkpoint 100 prospectively separates:

1. completed-trajectory quality metrics;
2. a fixed admission/ID cohort with every episode classified as completed,
   failed, or pending/censored.

The prospective definition is frozen in
`artifacts/phase7/checkpoints/fresh8_v1_ckpt_100_predeclared_cohorts.json`.
