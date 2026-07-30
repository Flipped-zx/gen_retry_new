# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 180

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `12:47:08Z`, ending immediately before the
checkpoint-180 fixed snapshot.

## Results

- Samples: 2,290 over 11,702 seconds.
- Logical episode workers: 15-16 during child replacement transitions.
- Mean active HCUs: 5.91/8.
- Median active HCUs: 6/8.
- Range: 2-8 active HCUs.
- Samples with at least six active HCUs: 1,591/2,290.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 403.70 GiB.
- OOM, API timeout, connection error, and rate-limit error in the continuous
  episode 51-200 queue: none.

Independent Teacher/API, image, evaluator, and artifact work remains
overlapped while each episode stays causally sequential.
