# Phase 3E Rollout Preparation Checkpoint

Date: 2026-07-14

## Scope

Prepared replayable run directories for the ten selected fresh Phase 3 prompts
without invoking the teacher, Qianwen-Image-Edit, or Geneval2.

## Prepared State

- Run root: `runs/phase3/`
- Prepared episodes: 10
- Episode IDs: `phase3_ep_001` through `phase3_ep_010`
- Maximum image attempts per episode: 5
- Summary artifact: `artifacts/phase3/prepared_rollouts.json`

Each run directory contains:

- `task_spec.json`
- `events.jsonl`
- `planner_views/planner_view_000.json`
- `episode_state.json`
- `manifest.json`
- empty JSONL scaffolds for future planner requests, raw teacher outputs,
  canonical actions, tool observations, and Geneval2 results
- `rollout_plan.json`
- an empty `images/` directory

## Fresh-Start Invariants

- No legacy images were imported.
- No legacy attempts were parented.
- Initial attempt history is empty.
- Initial `best_attempt_id` is null.
- Initial visible image list is empty.
- First live action must be either `query_skill` followed by fresh generation, or
  a fresh `generate_image`; it must not be `edit_image`.

## Validation

- All prepared event logs replay through the current trajectory validator and
  reducer.
- All prepared manifests are hash-closed over task spec, planner view, and event
  log artifacts.
- No image files or legacy image paths are present in prepared run state.

## Stop Condition Still Active

Live rollout execution remains blocked until the configured teacher and
Qianwen-Image endpoint environment variables are set.
