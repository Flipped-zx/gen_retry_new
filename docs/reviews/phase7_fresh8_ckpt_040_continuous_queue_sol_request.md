# Phase 7 Checkpoint 40 And Continuous Queue Sol Review Request

## Gate

`40-trajectory light review plus prospective scheduler-boundary review`

Episodes 41-50 are already running under the accepted two-workers-per-HCU
profile. Do not edit files or invoke live services.

## Validity Evidence

- Range 21-40 audit:
  `docs/phase7/checkpoints/fresh8_v1_range_021_040_audit.md`
- Cumulative 1-40 audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_040_cumulative_audit.md`
- Range behavior and SFT labels:
  `docs/phase7/checkpoints/ckpt_040_analysis/`
- Tail resource profile:
  `docs/phase7/checkpoints/fresh8_v1_range_021_040_resource_profile.md`
- Accepted backend decision:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`
  (`Accepted`, supersedes ADR-0001)
- Current adapter contract:
  `docs/architecture/MODULE_CONTRACTS.md`, section 6

Range 21-40:

- 20/20 submitted; 69/69 complete Geneval2 evaluations.
- Atom pass: 125/152 first to 137/152 submitted.
- Soft-TIFA AM: 82.37 to 90.88.
- Soft-TIFA GM: 42.44 to 75.01.
- Per-trajectory peak GM: 76.58; submitted gap 1.57.
- 10/20 all-pass; 6 historical-best submissions.
- 11 regressive and 16 strictly ineffective image actions.
- 12 instruction-quality rejected Teacher turns; zero protocol/reference
  invalid turns and zero rejected SFT targets.
- All schema, lineage, point-in-time context, backend, evaluator, manifest,
  submission, and credential checks passed.

Cumulative 1-40:

- Atom pass: 250/296 first to 278/296 submitted.
- Soft-TIFA GM: 48.19 to 82.45.
- 27/40 all-pass.

## Prospective Scheduler Change

After the already-running 41-50 range, replace the remaining small execution
ranges with one continuous pending-episode queue:

- Keep two logical workers per HCU: 16 total.
- Keep eight Teacher slots and eight physical-HCU GPU slots.
- Keep all Planner, Skill, Qwen, Geneval2, score, seed, and event semantics.
- Queue only episodes 51-200; submitted episodes are skipped on resume.
- A worker that completes or fails one child continues to the next pending
  episode, preserving per-episode causal sequencing.
- Run asynchronous deterministic audits after each additional 20 submitted
  episodes and deep reviews at cumulative 50-episode boundaries.
- If a review finds a blocker, request a graceful stop of new episode starts;
  active episodes remain artifact-backed and resumable.
- After the initial queue drains, rerun only still-unsubmitted episodes, up to
  the existing five orchestration passes.

This removes the measured 20-episode range tail while preserving hard
concurrency limits. Scheduler profile boundaries remain persisted.

## Questions

1. Does checkpoint 40 expose any data-validity, SFT-boundary, evaluator, or
   wrong-direction blocker?
2. Is the lower all-pass rate and higher regression/ineffective-action
   exposure acceptable training evidence, or does it require a prospective
   policy correction before continuing?
3. Is the continuous 51-200 queue safe and comparable under the frozen locks
   and semantics, and what minimum graceful-stop/retry condition is required?

## Expected Response

Return `PASS_CONTINUE_QUEUE`, `PASS_CONTINUE_RANGES`, or `STOP_BLOCKING`.
Separate validity blockers from policy-quality observations and scheduler
requirements.
