# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 100

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `10:50:46Z`, ending after the completed-quality
cohort reached 100 valid trajectories.

## Results

- Samples: 924 over 4,719 seconds.
- Logical episode workers: 15-16, with brief child replacement transitions.
- Mean active HCUs: 5.94/8.
- Median active HCUs: 6/8.
- Range: 3-8 active HCUs.
- Samples with at least six active HCUs: 639/924.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 403.73 GiB.
- Mean one-minute load average: 14.30; maximum 41.39.
- OOM, API timeout, connection error, and rate-limit error: none.

## Interpretation

The queue continues to overlap independent Teacher calls with local GPU work
without admitting same-episode future planning. Resource use is stable and
there is no infrastructure signal requiring a throughput reduction.
