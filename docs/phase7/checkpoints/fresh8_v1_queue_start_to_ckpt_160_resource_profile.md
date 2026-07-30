# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 160

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `12:17:40Z`, ending immediately before the
checkpoint-160 fixed snapshot.

## Results

- Samples: 1,944 over 9,934 seconds.
- Logical episode workers: 15-16 during child replacement transitions.
- Mean active HCUs: 5.92/8.
- Median active HCUs: 6/8.
- Range: 2-8 active HCUs.
- Samples with at least six active HCUs: 1,342/1,944.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 403.48 GiB.
- OOM, API timeout, connection error, and rate-limit error in the continuous
  episode 51-200 queue: none.

The queue continues to overlap independent Teacher/API, image, evaluator, and
artifact work while keeping each episode causally sequential.
