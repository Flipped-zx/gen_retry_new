# Checkpoint 100 Fixed Admission-Cohort Status

## Frozen Denominator

- Episode IDs: `phase3_ep_061` through `phase3_ep_100`
- Count: 40
- Snapshot: `2026-07-30T10:45:53Z`
- Selection: fixed prospectively before checkpoint completion

## Status

| Status | Count | Episode IDs |
| --- | ---: | --- |
| Completed | 36 | `061-068`, `070-094`, `096-097`, `099` |
| Failed unsubmitted | 1 | `069` |
| Active | 3 | `095`, `098`, `100` |
| Not yet admitted | 0 | none |

`phase3_ep_069` retained two evaluated image attempts and ended its current
worker on an instruction-quality `format_error`; it remains eligible for the
pending-only resume pass. It is not included in completed-quality metrics and
is explicitly present in this operational denominator.

The active episodes had canonical event histories and in-flight image or
evaluation work at the snapshot. No episode in this fixed cohort was omitted
because it was slow, failed, or incomplete.

## Claim Boundary

The separate completed-quality cohort measures quality among 100 valid
trajectories. This fixed status table measures admission and operational
closure. Neither table is substituted for the other.
