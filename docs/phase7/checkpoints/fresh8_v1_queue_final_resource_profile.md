# Fresh-8 Continuous Queue Final Resource Profile

## Scope

The five-second monitor sampled the continuous episode 51-200 queue from
`2026-07-30T09:32:06Z` through `13:27:39Z`, immediately before the final
submission.

## Results

- Samples: 2,766 over 14,133 seconds.
- Logical episode workers: 0-16, including final drain and process exit.
- Mean active HCUs: 5.45/8.
- Median active HCUs: 6/8.
- Range: 0-8 active HCUs.
- Samples with at least six active HCUs: 1,675/2,766.
- All-idle samples: 53.
- Minimum host memory available: 396.20 GiB.
- Mean host memory available: 409.20 GiB.
- OOM, API timeout, connection error, and rate-limit error in episodes
  51-200: none.

## Tail Interpretation

There were no all-idle samples through checkpoint 180. All-idle samples began
only after `13:14Z`, when the first pass drained to a small number of legal
unfinished episodes and while the scheduler switched to the two-item
pending-only retry. There were seven zero-utilization runs; the longest was
195 seconds.

At that boundary, filling all eight HCUs would have required rerunning an
already valid trajectory or planning a same-episode action before its image
and Geneval2 result existed. The scheduler did neither. Both pending episodes
resumed on separate HCUs and all 200 fixed IDs closed.
