# Fresh-8 Range 21-40 Resource Profile

## Scope

The monitor sampled the tail of range 21-40 every five seconds from
`2026-07-30T08:14:42Z` through `08:39:53Z`. It started after seven episodes
had already completed, so this is intentionally tail-utilization evidence, not
an estimate of whole-range average throughput.

## Results

- Samples: 297 over 1,511 seconds.
- Mean active HCUs: 3.28/8.
- Median active HCUs: 3/8.
- Range: 0-7 active HCUs.
- Samples with zero active HCUs: 37.
- Episode workers present: 1-13.
- Minimum host memory available: 409.46 GiB.
- Mean host memory available: 431.77 GiB.
- Mean one-minute load average: 6.18; maximum 30.71.
- OOM, API timeout, connection error, rate-limit error, and execution
  traceback: none.

## Interpretation

The hard physical-HCU locks prevented concurrent model residency and host
resources remained comfortable. Increasing workers per HCU would not solve the
observed tail once fewer than eight episodes remain. The lost utilization came
from the 20-episode execution barrier: episodes 41+ could not enter the queue
while one or a few long trajectories in 21-40 were still completing.

The prospective efficiency change under review is therefore a continuous
multi-episode queue with the same 16 logical workers, eight Teacher slots, and
eight physical-HCU execution slots. Checkpoint audits remain asynchronous and
do not alter episode events.

