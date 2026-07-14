# Phase 3B-C-D Checkpoint

Date: 2026-07-14

## Scope

Completed offline Phase 3 prerequisites that can run before live credentials are
available:

- Phase 3B legacy diagnostic/action analysis;
- Phase 3C fresh Geneval2 candidate-pool construction;
- Phase 3D deterministic ten-prompt selection.

No live APIs were called. No legacy images or legacy attempts were imported into
new episodes.

## Deliverables

- `artifacts/phase3/legacy_diagnostic_action_analysis.jsonl`
- `docs/phase3/legacy_edit_plausibility_analysis.md`
- `docs/phase3/legacy_failure_signature_summary.md`
- `artifacts/phase3/candidate_pool.jsonl`
- `docs/phase3/candidate_pool_report.md`
- `artifacts/phase3/selected_ten_prompts.json`
- `artifacts/phase3/constraint_coverage_matrix.json`
- `docs/phase3/prompt_selection_report.md`
- `docs/phase3/selection_provenance.md`

## Results

- Legacy counterfactual analysis records: 1,276.
- Geneval2 candidate prompts: 800.
- Historical-evidence matched candidates: 99.
- Selected prompts: 10.
- Selected aggregate constraint coverage:
  - `attribute`: 24
  - `count`: 30
  - `object`: 30
  - `position`: 10
  - `verb`: 10

## Stop Condition Still Active

Live rollout execution remains blocked until the configured teacher and
Qianwen-Image endpoint environment variables are set.

## Next Resume Action

After environment configuration is available, rerun live preflight checks and
execute ten fresh natural multi-round trajectories using only the selected prompt
artifacts committed before rollout.
