# Fresh-8 Continuous Queue Resource Profile Through Checkpoint 80

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `10:27:30Z`, ending after the cumulative
80-trajectory cohort was frozen. Queue completion is intentionally unordered;
the cohort definition is persisted in
`artifacts/phase7/checkpoints/fresh8_v1_ckpt_080_cohort.json`.

## Results

- Samples: 651 over 3,323 seconds.
- Logical episode workers: 15-16; transitions briefly expose 15 between child
  completion and replacement process startup.
- Mean active HCUs: 6.00/8.
- Median active HCUs: 6/8.
- Range: 3-8 active HCUs.
- Samples with at least six active HCUs: 472/651.
- Samples with zero active HCUs: 0.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 402.85 GiB.
- OOM, API timeout, connection error, and rate-limit error: none.

## Interpretation

The continuous queue sustains materially better utilization than the
small-range tail while preserving one GPU stage per physical HCU. Independent
Teacher calls overlap local image/evaluator work; same-episode planning remains
blocked until its current Geneval2 observation is reduced into PlannerContext.
