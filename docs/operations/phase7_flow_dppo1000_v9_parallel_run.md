# Flow-DPPO 1000 v9 Fresh-8 Run Plan

Independent concurrency review:
`docs/reviews/flow_dppo1000_v9_parallel_5_5_review.md`
(`APPROVE_WITH_20_TRAJECTORY_ADMISSION_PILOT`).
API overlap review:
`docs/reviews/flow_dppo1000_v9_api_prefetch_review.md`
(`KEEP_CURRENT_CROSS_EPISODE_OVERLAP`).

## Frozen Selection

- Selection artifact:
  `artifacts/phase7/flow_dppo1000_v9_official_mix_selected_prompts.json`
- Selection SHA256:
  `9f5fca671e42bbb68577cb1513e072f7c020e59131dfa1989bb2c5c5f4fa0eba`
- Source: `Tencent-Hunyuan/UniRL@e1a814ff9de6de644b093c6ed0106869c1881e53`
- Source dataset SHA256:
  `1822f92dbf848f66d0dbe6b1f9d10114496b104d12b5c32b48e01a83e66b4fe7`
- Official Geneval2 800-row test set remains held out.
- The earlier Flow-DPPO 20 and 200 source rows are excluded: 220 rows total.
- No image outcome was used during selection.

The official test set has exactly 100 prompts at every `atom_count` from 3
through 10. The 1000-prompt selection therefore has exactly 125 prompts in
each bucket:

| Local tier | Atom count | Selected | Ratio |
|---|---:|---:|---:|
| easy | 3-5 | 375 | 37.5% |
| medium | 6-8 | 375 | 37.5% |
| hard | 9-10 | 250 | 25.0% |

These are deterministic local reporting tiers, not official Geneval2
difficulty labels. Constraint-type proportions are a soft match because the
Flow-DPPO metadata has 6,007 rows where `atom_count != len(vqa_list)`:

| Atom type | Official test | Selected | Delta |
|---|---:|---:|---:|
| attribute | 20.19% | 21.88% | +1.69 pp |
| count | 33.68% | 32.06% | -1.62 pp |
| object | 33.68% | 32.06% | -1.62 pp |
| position | 11.01% | 12.44% | +1.43 pp |
| verb | 1.43% | 1.56% | +0.13 pp |

Full rows and coverage are in
`docs/phase7/flow_dppo1000_v9_official_mix_selection_report.md`.

## Prospective Policy

This must be a new empty run root. Existing 200-trajectory artifacts are
immutable evidence and must not be copied or resumed into this batch.

- Run root: `runs/phase7_flow_dppo1000_v9_fresh8_v1`
- PlannerContext: v0.7
- Teacher: `teacher_system_prompt_v9_meaningful_retry_verb_retention`
- Action protocol: v0.5
- Skill: `action_pose_relation@2.1.0` plus the existing capability Skills
- Execution profile: `qwen_dual_backend@1`
- Generate: Qwen-Image-2512, 50 steps, 1024 x 1024
- Edit: Qwen-Image-Edit-2511, 40 steps, 1024 x 1024
- Evaluator: Geneval2 after every image Attempt
- Budget: at most five image Attempts per episode
- Best comparator: pass-count, then prompt-level GM, then earlier Attempt

Compared with the earlier 200 batch, v9 adds prior executable instructions,
hash-stable retrieved Skill observations, visible same-pass historical image
evidence, meaningful-retry checks, and delayed verb-specific repair. It is a
better specified policy, but it is still prospective until a live v9 pilot
passes.

## Admission Schedule

1. Prepare all 1000 empty directories, then validate schemas and manifests.
2. Run fixed IDs 001-020 as the live v9 admission pilot.
3. Require 20/20 valid submitted trajectories, no protocol/future-leakage
   blocker, no systematic verb-retention regression, and no stale artifact
   reuse.
4. After admission, run IDs 021-1000 as one global pending queue.
5. Run a deterministic light audit at every fixed 100-ID boundary. At every
   fixed 200-ID boundary, send that audit plus representative traces to GPT-5.6
   Sol for deep review. Reviews may run concurrently with the queue; a
   blocking verdict writes the durable stop-admission file.
6. Report both completion-conditioned quality and a fixed admitted-ID status
   denominator so short episodes do not bias checkpoint incident rates.

Do not prefetch the next action within an episode before its current image is
evaluated. The useful overlap is across episodes: Teacher/Skill/JSON/reducer
work for one episode can run while another episode owns a GPU stage.

## Eight-HCU Profile

- Eight physical HCUs.
- `--max-workers 8 --workers-per-device 2`: 16 logical episode workers.
- `--teacher-concurrency 8`.
- One Qwen/Geneval2 load-through-unload GPU stage per physical HCU, protected
  by the existing physical-device lock.
- Keep the existing scheduler lock, episode lock, atomic image validation,
  submitted-only skip, and pending-only retry behavior.
- Do not increase to three workers per HCU without a separate host-pressure
  and lock-wait experiment.

The generic scheduler already supports this layout; do not reuse the old
range-specific `051_200` wrapper or launch a second scheduler on the same run
root.

## Commands

The checked-in launcher sources the local `600`-permission Teacher environment
file without printing credential values:

```bash
scripts/run_flow_dppo1000_v9.sh dry-run
scripts/run_flow_dppo1000_v9.sh pilot
scripts/run_flow_dppo1000_v9.sh queue
scripts/audit_flow_dppo1000_v9_checkpoint.sh 20
scripts/audit_flow_dppo1000_v9_checkpoint.sh 100
```

`pilot` admits only fixed IDs 001-020. `queue` admits every remaining
non-submitted episode and is used only after the admission audit passes. The
checkpoint helper accepts 20 for admission and then fixed 100-ID boundaries.

Preparation only:

```bash
python -m gen_retry.cli.prepare_phase3_rollouts \
  --selected-prompts artifacts/phase7/flow_dppo1000_v9_official_mix_selected_prompts.json \
  --output-root runs/phase7_flow_dppo1000_v9_fresh8_v1 \
  --summary-output artifacts/phase7/flow_dppo1000_v9_fresh8_v1_prepared_rollouts.json \
  --max-image-attempts 5 \
  --execution-profile-id qwen_dual_backend \
  --execution-profile-version 1 \
  --score-policy-id geneval2_pass_count_then_gm
```

After the fixed 20-ID admission pilot, the continuous queue uses:

```bash
python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root runs/phase7_flow_dppo1000_v9_fresh8_v1 \
  --max-workers 8 \
  --workers-per-device 2 \
  --teacher-concurrency 8 \
  --image-steps 40 \
  --image-height 1024 \
  --image-width 1024 \
  --execution-profile-id qwen_dual_backend \
  --stop-admission-file runs/phase7_flow_dppo1000_v9_fresh8_v1/STOP_ADMISSION
```

The first command must refuse every non-empty target episode directory. The
second command skips canonical submitted episodes on resume and must never use
`--include-submitted` for production recovery.

## Time And Capacity

The earlier 200 fresh trajectories provide two empirical bounds:

- Complete batch: 200 trajectories, 684 evaluated images, about 6 h 49 min.
- Stable continuous queue 51-200: 150 trajectories in about 4 h 02 min,
  approximately 37.1 trajectories/hour.
- Stable queue utilization: mean 5.45/8 active HCUs, median 6/8; no OOM,
  Teacher timeout, connection error, or rate-limit event in IDs 51-200.

For the same official atom-count mix and five-attempt budget:

- P50: 27-30 hours.
- P80: 34-40 hours, including tail retries and v9 hard/verb behavior.
- All-five-attempt stress case: roughly 38-50 hours.
- Expected images at the historical mean: about 3,420; hard maximum: 5,000.
- Expected run storage from the previous 912 MiB/200 ratio: about 4.6 GiB;
  reserve at least 10 GiB for logs, audits, and retry tail.

The remembered three-hour duration is not the complete 200 run. It is closest
to the middle of the stable 150-episode continuous queue.

## Operational Monitors

- active HCU count and per-device VRAM;
- GPU-lock wait time and per-attempt latency;
- Teacher timeout/rate-limit/connection errors;
- raw Teacher format/instruction-quality rejection counts;
- pending, active, submitted, and failed-unsubmitted fixed-ID counts;
- atom/AM/GM deltas, submitted-to-peak GM gap, regression, rollback, and
  historical-source usage;
- verb Skill retrieval timing and preservation of previously passing verbs;
- artifact decode, dimensions, hash, and execution-profile provenance.

Any policy correction after admission is prospective and versioned. Completed
valid trajectories are not rewritten merely to make the batch uniform.
