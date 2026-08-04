# Flow-DPPO 1000 v9 Parallel Execution Review

## Scope

Independent read-only GPT-5.5 XHigh review of the earlier fresh-8 scheduler,
resource profile, queue logs, retry behavior, and the proposed 1000-trajectory
scale-up. The reviewer did not run an API, GPU workload, or edit repository
files.

## Verdict

`APPROVE_WITH_20_TRAJECTORY_ADMISSION_PILOT`

The previous concurrency architecture is suitable for 1000 trajectories:
two logical episode workers per HCU, one locked GPU stage per physical HCU,
eight Teacher slots, a single global pending queue, submitted-only resume, and
pending-only retry. Do not reuse the old range-specific wrapper and do not
raise the profile to three workers per HCU without a separate pressure test.

## Evidence

- The complete earlier 200 run lasted about 6 h 49 min and produced 684
  evaluated images.
- The stable continuous 51-200 queue completed 150 trajectories in about
  4 h 02 min, or approximately 37.1 trajectories/hour.
- Its final resource profile averaged 5.45/8 active HCUs, with median 6/8 and
  no OOM, Teacher timeout, connection, or rate-limit event.
- The scheduler/device/episode locks, atomic image validation, durable stop
  admission, and final pending-only retry closed 200/200 without rerunning a
  valid submitted trajectory.

Primary evidence:

- `docs/operations/phase7_flow_dppo200_fresh8_run.md`
- `docs/reviews/phase7_api_gpu_overlap_sol_review.md`
- `docs/reviews/phase7_fresh8_ckpt_040_continuous_queue_sol_review.md`
- `docs/phase7/checkpoints/fresh8_v1_queue_final_resource_profile.md`
- `docs/phase7/checkpoints/fresh8_v1_ckpt_200_admission_status.md`

## Required Controls

- Use a new empty run root to prevent stale image-cache reuse.
- Admit v9 on fixed IDs 001-020 before opening IDs 021-1000.
- Keep fixed admitted-ID status denominators alongside completion-order
  quality cohorts.
- Monitor raw Teacher action/instruction rejection, API errors, GPU lock wait,
  active HCU count, host memory, and per-attempt latency.
- Keep same-episode decisions sequential; overlap only independent episode
  work while another episode owns a GPU stage.
- A blocking review writes the durable stop-admission flag; active episodes
  may finish and completed immutable episodes remain valid.
- Run deterministic light audits every 100 fixed IDs and GPT-5.6 Sol deep
  reviews every 200 fixed IDs; do not use the first N completions as the
  incident-rate denominator.

## Estimate

- P50: 27-30 hours.
- P80: 34-40 hours.
- All-five-attempt stress case: 38-50 hours.

The remembered three-hour duration is not the complete 200 batch; it is
closest to a partial interval within the stable continuous queue.
