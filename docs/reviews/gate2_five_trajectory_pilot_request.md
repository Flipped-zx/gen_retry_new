# SOL_REVIEW_REQUEST

## Gate

`Five-Trajectory Pilot`

## Decision to review

Approve the completed ten fresh Phase 3 live trajectories and post-hoc labels as sufficient evidence to proceed to Phase 4 SFT supervision freeze work.

## Current evidence

- Relevant schema/ADR:
  - `schemas/action_protocol_v0_2.schema.json`
  - `schemas/episode_event_v0_2.schema.json`
  - `schemas/planner_view_v0_2.schema.json`
  - `docs/architecture/MODULE_CONTRACTS.md`
  - Gate 1 Protocol Freeze was approved in `docs/status.md`.
- Minimal test/pilot summary:
  - Live preflight passed and is recorded in `docs/checkpoints/phase3_live_preflight.md` and `artifacts/phase3/live_preflight_summary.json`.
  - Ten selected prompt rollout directories already existed before live execution.
  - Ten fresh live trajectories completed under `runs/phase3/phase3_ep_001` through `runs/phase3/phase3_ep_010`.
  - Every valid trajectory starts from empty attempt history and a fresh generation path; smoke tests are not counted.
  - GPT-5.5 teacher policy used `TEACHER_API_KEY` and `TEACHER_BASE_URL`; local Qwen-Image-Edit direct runtime used configured `model_path`; Geneval2 atom normalization was run for every image attempt.
  - Cross-trajectory reports:
    - `docs/phase3/ten_trajectory_comparison.md`
    - `docs/phase3/behavior_coverage_report.md`
    - `docs/phase3/legacy_vs_fresh_strategy_analysis.md`
    - `docs/phase3/sft_candidate_action_report.md`
  - Machine-readable outputs:
    - `artifacts/phase3/trajectory_index.json`
    - `artifacts/phase3/action_supervision_labels.jsonl`
  - Summary: 10 valid episodes, 49 image attempts, 69 canonical actions, 9 rejected raw turns, 38 positive/recovery SFT candidate actions.
- Conflicting evidence, if any:
  - One earlier invalid infrastructure run was archived under `runs/phase3_invalid/` and is explicitly excluded from Phase 3 episode counts and SFT candidates.
  - Two valid episodes include rejected raw teacher turns before canonical recovery; these are labeled `excluded_invalid`.
  - Many edit actions regressed constraints; these are retained as history-only negative evidence, not positive SFT targets.

## Questions（最多 3 个）

1. Does the evidence satisfy Gate 2 for proceeding beyond the fresh live pilot without rerunning valid trajectories?
2. Are the Phase 3 action labels and SFT inclusion/exclusion choices defensible under the frozen v0.2 protocol?
3. Is any blocking issue visible in the history, branching, best-so-far, or atom-normalization evidence that would weaken the claimed contribution?

## Explicit non-goals

- Do not re-review Gate 1 schema semantics unless a Gate 2 blocker depends on them.
- Do not request more live rollouts merely to improve behavior distribution.
- Do not inspect credentials, raw API headers, or local model weights.
- Do not implement Phase 4.

## Expected response

- blocking issues only;
- recommended decision;
- risks and one minimal validation experiment;
- no code implementation.
