# Fresh-8 Range 41-50 Resource Profile

## Scope

The monitor sampled the initial 41-50 scheduler every five seconds from
`2026-07-30T08:43:15Z` through `09:12:31Z`. It covers the ten-episode range
through its first failed exit, before the isolated resume of `phase3_ep_046`.
The completed range has 10 valid submissions; the resume reused existing
events and did not rerun the other nine episodes.

## Results

- Samples: 345 over 1,756 seconds.
- Mean active HCUs: 1.63/8.
- Median active HCUs: 1/8.
- Range: 0-5 active HCUs.
- Samples with zero active HCUs: 39.
- Episode workers present: 1-10.
- Minimum host memory available: 423.93 GiB.
- Mean host memory available: 448.48 GiB.
- Mean one-minute load average: 6.02; maximum 24.42.
- OOM, API timeout, connection error, and rate-limit error: none.
- `phase3_ep_046` exited after repeated instruction-quality rejection; its
  subsequent resume completed from canonical history and submitted an
  all-pass fifth image.

## Interpretation

The low utilization is the expected small-range tail: only ten episodes were
admitted and the final recovery held the run-root scheduler while one episode
remained. This is not evidence that two workers per HCU are ineffective.

Starting with episode 51, the scheduler uses one continuous 150-episode queue,
interleaved device assignment, 16 logical workers, eight Teacher slots, and
eight physical-HCU execution locks. Independent Teacher calls can overlap
another episode's image/evaluator stage; no episode can plan past its own
unevaluated image attempt.
