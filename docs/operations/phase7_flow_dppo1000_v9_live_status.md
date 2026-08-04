# Flow-DPPO 1000 v9 Live Status

## Current State

- Selection: 1000/1000 frozen prompts.
- Prepared episodes: 1000/1000 fresh PlannerContext v0.7 directories.
- Selection SHA256:
  `9f5fca671e42bbb68577cb1513e072f7c020e59131dfa1989bb2c5c5f4fa0eba`.
- Fixed-ID admission pilot: PASS, 20/20 valid submissions and 65 image
  Attempts.
- Pilot metrics: best atom pass rate `93.48%`; submitted Soft-TIFA GM `77.94`
  from initial `41.42`.
- `phase3_ep_004` alone was resumed after its regex-derived instruction linter
  false positive; the other 19 valid trajectories were not rerun.
- Active stage: complete; final deterministic audit and Sol review finished.
- Valid submissions: `1000/1000`; incomplete or failed episodes: `0`.
- Image Attempts: `3443`; image start, completion, image-file, and Geneval2
  counts all equal `3443`.
- The first queue stopped at `917/1000` after sanitized Teacher `403
  insufficient balance` responses. The remaining 83 requests resumed once
  from persisted state after Teacher and GPU recovery.
- Resume scheduler exit: `0`; active rollout workers: `0`; no
  `STOP_ADMISSION` file.
- Interruption integrity: no orphan image, half-written Attempt, duplicated
  existing Attempt, or rerun submitted trajectory.
- Final audit: `PASS: 1000 episodes, 3443 attempts`.
- Final quality: atom pass `79.86% -> 90.85%`, Soft-TIFA AM `80.60 -> 90.25`,
  submitted Soft-TIFA GM `40.32 -> 71.14`, and `552/1000` all-pass.
- GPT-5.6 Sol verdict: `PASS_WITH_BLOCKED_SFT_EXPORT`. The canonical pool is
  accepted; Gate-3 positive supervision remains open.
- Queue start: `2026-08-01T08:28:42Z`.
- Resume log:
  `runs/phase7_flow_dppo1000_v9_fresh8_v1/queue_resume_0917_1000.log`.
- Scheduler: 16 logical workers, two per physical HCU, eight Teacher slots.
- Instruction-quality verdicts are advisory environment metadata under
  ADR-0009; schema/reference/runtime/source validation remains blocking.

## Policy Lock

- Action Protocol v0.5.
- PlannerContext v0.7.
- Teacher prompt:
  `teacher_system_prompt_v9_meaningful_retry_verb_retention`.
- Skill: `action_pose_relation@2.1.0` plus the existing capability Skills.
- Execution: `qwen_dual_backend@1`.
- Score policy: `geneval2_pass_count_then_gm@1`.
- Maximum image Attempts: five.

## Commands

Verify the completed resume scheduler:

```bash
cat runs/phase7_flow_dppo1000_v9_fresh8_v1/queue_resume_0917_1000.exit
find runs/phase7_flow_dppo1000_v9_fresh8_v1 \
  -mindepth 2 -maxdepth 2 -name submission.json | wc -l
```

Reproduce the final deterministic audit:

```bash
scripts/audit_flow_dppo1000_v9_checkpoint.sh 1000
```

Result: `PASS: 1000 episodes, 3443 attempts`.

## Review Cadence

- Fixed IDs 001-020: admission gate.
- Every fixed 100-ID boundary: deterministic light audit.
- Every fixed 200-ID boundary: GPT-5.6 Sol deep review with at most three
  questions and representative traces.
- Review can overlap active work. A blocking verdict creates
  `runs/phase7_flow_dppo1000_v9_fresh8_v1/STOP_ADMISSION`; active episodes may
  finish but no new episode is claimed.

Checkpoint reports must separate the fixed admitted-ID status denominator
from completion-conditioned quality. Completed valid trajectories are never
rerun to obtain preferred behavior.

## Checkpoint 100

- Audit: PASS, 100/100 fixed IDs and 337 image Attempts.
- Best atom pass rate: `91.09%`, up from initial `79.89%`.
- Submitted Soft-TIFA GM: `73.12`, up from initial `36.09`.
- All-pass episodes: `59/100`.
- Runtime status at audit completion: 119/1000 submitted, 16 active, no
  `STOP_ADMISSION` file.
- Report:
  `docs/phase7/checkpoints/flow_dppo1000_v9_ckpt_0100_audit.md`.

## Checkpoint 200

- Audit: PASS, 200/200 fixed IDs and 665 image Attempts.
- Best atom pass rate: `91.55%`, up from initial `80.46%`.
- Submitted Soft-TIFA GM: `72.40`, up from initial `38.86`.
- All-pass episodes: `120/200`; submitted-to-peak GM gap: `1.47`.
- Regression exposure: 66 episodes and 128 image Actions; strict ineffective
  Actions: 107.
- Sol verdict: `PASS_CONTINUE_WITH_MONITORING`; no `STOP_ADMISSION`.
- Required before checkpoint 400: linter/outcome/SFT cross-tab and explicit
  regression/no-progress recovery analysis.
- Review:
  `docs/reviews/flow_dppo1000_v9_ckpt_0200_sol_review.md`.

## Final Checkpoint 1000

- Audit: PASS, 1000/1000 fixed IDs and 3443 image Attempts.
- Best/submitted atom pass rate: `90.85%`, up from `79.86%` initially.
- Submitted Soft-TIFA GM: `71.14`, up from `40.32`; post-hoc peak GM is
  `72.30`, a `1.16` point gap.
- All-pass episodes: `552/1000`; historical-best submissions: `316/1000`.
- Regression exposure: 383 episodes and 749 image Actions; strict ineffective
  Actions: 547.
- Resume integrity: 83 interrupted Teacher requests resumed with zero orphan
  images or partial Attempts.
- Sol verdict: `PASS_WITH_BLOCKED_SFT_EXPORT`.
- Reports:
  `docs/phase7/flow_dppo1000_v9_final_analysis_report.md` and
  `docs/reviews/flow_dppo1000_v9_ckpt_1000_sol_review.md`.
