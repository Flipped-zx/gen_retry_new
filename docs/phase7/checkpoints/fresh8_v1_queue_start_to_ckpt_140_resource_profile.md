# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 140

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `11:49:53Z`, ending after the completed-quality
cohort reached 140 valid trajectories.

## Results

- Samples: 1,618 over 8,267 seconds.
- Logical episode workers: 15-16 during child replacement transitions.
- Mean active HCUs: 5.89/8.
- Median active HCUs: 6/8.
- Range: 2-8 active HCUs.
- Samples with at least six active HCUs: 1,103/1,618.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 403.44 GiB.
- OOM, API timeout, connection error, and rate-limit error: none.

## Interpretation

Resource use remains stable. The lower quality of the checkpoint-140 increment
is not accompanied by an infrastructure regression or reduced image settings;
it must be interpreted through prompt difficulty and action outcomes.
