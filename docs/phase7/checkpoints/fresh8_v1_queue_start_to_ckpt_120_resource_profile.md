# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 120

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `11:16:24Z`, ending after the completed-quality
cohort reached 120 valid trajectories.

## Results

- Samples: 1,225 over 6,258 seconds.
- Logical episode workers: 15-16 during child replacement transitions.
- Mean active HCUs: 5.84/8.
- Median active HCUs: 6/8.
- Range: 2-8 active HCUs.
- Samples with at least six active HCUs: 803/1,225.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 403.46 GiB.
- OOM, API timeout, connection error, and rate-limit error: none.

## Interpretation

The queue remains stable with no all-idle sample. Mean utilization is slightly
lower than checkpoint 100 because more long trajectories are alternating
Teacher planning and evaluator work, but there is no memory or infrastructure
signal requiring a concurrency reduction.
