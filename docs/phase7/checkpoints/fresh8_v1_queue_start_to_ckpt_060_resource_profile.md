# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 60

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `10:05:31Z`, ending just after episodes 51-60
all had valid submissions. Later episode IDs were already running during this
window because queue admission is continuous and completion order is not
forced.

## Results

- Samples: 393 over 2,004 seconds.
- Logical episode workers: 16 in every sample.
- Mean active HCUs: 5.92/8.
- Median active HCUs: 6/8.
- Range: 3-8 active HCUs.
- Samples with at least six active HCUs: 271/393.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.35 GiB.
- Mean host memory available: 402.49 GiB.
- Mean one-minute load average: 13.55; maximum 34.18.
- OOM, API timeout, connection error, and rate-limit error: none.

## Interpretation

Cross-episode Teacher prefetch and two logical workers per HCU removed the
small-range tail barrier. An HCU can be idle briefly while both assigned
episodes are in Teacher, Skill, or transition work, but no sample showed the
whole queue idle and the median sample kept six cards in GPU execution.

Same-episode planning remains causal: the next Teacher call is made only after
the current image and Geneval2 outcome have updated PlannerContext. Only
independent episodes overlap.
