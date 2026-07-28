# Phase 3 HQ5 Interruption Status

Date: 2026-07-15

This note records the live high-quality five-trajectory batch state after user interruption.

## Batch Configuration

- Run root: `runs/phase3_hq5/`
- Teacher policy: GPT-5.5 through environment-provided `TEACHER_API_KEY` and `TEACHER_BASE_URL`
- Image backend: local Qwen-Image-Edit direct runtime
- Rendering parameters: `40` steps, `1024 x 1024`
- Parallelism: one active local image worker on the available GPU, selected from `hy-smi`
- Standalone image smoke: skipped

## Episode State

| Episode | State | Image attempts | Submitted | Best | Reason |
| --- | --- | ---: | --- | --- | --- |
| `phase3_ep_001` | valid submitted | 5 | `a_003` | `a_003` | `best_available_under_budget` |
| `phase3_ep_002` | valid submitted | 5 | `a_000` | `a_000` | `best_available_under_budget` |
| `phase3_ep_003` | valid submitted | 2 | `a_001` | `a_001` | `all_constraints_passed` |
| `phase3_ep_004` | partial, not countable | 0 | none | none | interrupted after `image_execution_started` |
| `phase3_ep_005` | prepared only | 0 | none | none | not started |

## Geneval2 Summary

| Episode | Attempt scores |
| --- | --- |
| `phase3_ep_001` | `a_000` 6 pass / 5 fail / 0 uncertain; `a_001` 8 / 2 / 1; `a_002` 9 / 2 / 0; `a_003` 10 / 0 / 1; `a_004` 9 / 2 / 0 |
| `phase3_ep_002` | `a_000` 9 pass / 2 fail / 0 uncertain; `a_001` 9 / 2 / 0; `a_002` 9 / 2 / 0; `a_003` 8 / 2 / 1; `a_004` 9 / 1 / 1 |
| `phase3_ep_003` | `a_000` 10 pass / 1 fail / 0 uncertain; `a_001` 11 / 0 / 0 |

## Resume Guidance

- Count only `phase3_ep_001`, `phase3_ep_002`, and `phase3_ep_003` as valid trajectories.
- Do not rerun those three valid trajectories merely to obtain a preferred behavior.
- `phase3_ep_004` has teacher/action records but no image, no Geneval2 result, and no submission. It must remain excluded until deliberately resumed and completed.
- `phase3_ep_005` is prepared-only and safe to start later.
- To collect exactly five valid HQ trajectories under this run root, complete two more valid submissions from the remaining prepared/partial episodes.
