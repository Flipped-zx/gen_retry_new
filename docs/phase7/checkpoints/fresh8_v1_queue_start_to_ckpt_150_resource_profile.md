# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 150

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `12:07:17Z`, ending immediately before the
checkpoint-150 fixed snapshot.

## Results

- Samples: 1,822 over 9,310 seconds.
- Logical episode workers: 15-16 during child replacement transitions.
- Mean active HCUs: 5.92/8.
- Median active HCUs: 6/8.
- Range: 2-8 active HCUs.
- Samples with at least six active HCUs: 1,262/1,822.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 403.34 GiB.
- OOM, API timeout, connection error, and rate-limit error in the continuous
  episode 51-200 queue: none.

## Interpretation

The queue continues to overlap independent Teacher/API, image, evaluator, and
artifact work without violating within-episode causality. An HCU can be idle
while its assigned episode waits for Teacher or Geneval2, but no sample shows
all eight HCUs idle.
