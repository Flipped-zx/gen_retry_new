# HQ5 Completed Trajectory Behavior Analysis

Date: 2026-07-15

Scope: completed high-quality trajectories under `runs/phase3_hq5/`.

Related trace: `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md`.

## Completed Trajectories

| Episode | Prompt | Attempts | Submitted | Outcome pattern |
| --- | --- | ---: | --- | --- |
| `phase3_ep_001` | `six glass lions chasing three red cats behind a brown donut` | 5 | `a_003` | Multi-step improvement, final edit regressed, submitted historical best |
| `phase3_ep_002` | `seven purple flamingos playing with a green sheep behind five metal croissants` | 5 | `a_000` | Initial attempt stayed best; repeated edits did not beat it |
| `phase3_ep_003` | `a yellow violin to the right of a purple rabbit chasing five sparkling turtles` | 2 | `a_001` | One targeted edit fixed the remaining failed atom, then all-pass submit |

## Behavioral Features Observed

1. Strict action protocol held.
   Each assistant turn produced exactly one executable canonical action: `query_skill`, `generate_image`, `edit_image`, or `submit_attempt`.

2. Teacher behavior was image-aware through environment-owned context.
   The teacher did not receive mutable hidden memory. It received a `PlannerView` with remaining budget, latest attempt, best attempt, visible image references, retrieved skills, and atom-level evaluator state.

3. Retry behavior was history-aware.
   `phase3_ep_001` submitted `a_003` even though the latest image was `a_004`, because `a_004` regressed. `phase3_ep_002` repeatedly edited from `a_000`, the historical best, after edits failed to improve the score.

4. Edit targets were mostly verifier-grounded.
   The edit actions usually targeted non-passing atom IDs and listed passing atom IDs under `preserve_constraint_ids`.

5. The system captured non-monotonic editing.
   Edits can improve one atom while regressing another. This is visible in `phase3_ep_001`: `a_004` tried to fix lion count but regressed the chasing relation.

6. Fresh generation was used when appropriate.
   `phase3_ep_001` used a second fresh `generate_image` after the first attempt had broad structural/count failures.

7. The image backend quality configuration was high quality.
   Completed image attempts used local Qwen-Image-Edit direct runtime with `40` steps and `1024 x 1024`, recorded in image tool observations.

## Fit Against Intended Design

Overall: yes, these trajectories look like the intended verifier-grounded retry agent behavior.

Strong matches:

- Single canonical action per assistant turn.
- Empty history at episode start.
- Fresh generation before edits.
- Geneval2 evaluates every generated/edited attempt.
- PlannerView uses canonical attempt history, not raw scratch output.
- Best-so-far is environment-owned and can differ from latest.
- Submission can select historical best rather than latest.
- Raw teacher outputs are persisted with redaction metadata; canonical actions are separately parsed and stored.

Weak or incomplete parts:

- The `query_skill` mechanism does retrieve local Markdown skill documents and passes them back into later teacher context, but the current skill Markdown contents are placeholders (`- TODO`). The protocol shape is correct; the missing part is substantive skill guidance.
- `phase3_ep_002` shows safe retry behavior but weak effectiveness: edits repeatedly failed to improve the persistent interaction/count failures.
- Count and relation atoms remain the hardest cases. `phase3_ep_001` improved from 6/11 to 10/11, but never reached an all-pass count on lions.
- The agent sometimes spends the final budget trying to fix one uncertain/failing atom and can regress. This is useful training evidence, but it is not the cleanest success story.

## Best Trajectory To Explain

Use `phase3_ep_001` as the primary readable trajectory.

Why:

- It includes the full loop: skill query, fresh generation, fresh regeneration, targeted edits, verifier transitions, best-so-far tracking, and final submit.
- It has clear before/after improvements:
  - `a_000`: 6 pass / 5 fail / 0 uncertain
  - `a_001`: 8 pass / 2 fail / 1 uncertain
  - `a_002`: 9 pass / 2 fail / 0 uncertain
  - `a_003`: 10 pass / 0 fail / 1 uncertain
  - `a_004`: 9 pass / 2 fail / 0 uncertain
- It demonstrates an important agentic behavior: the last action produced a worse image, but submission selected the historical best `a_003`.

`phase3_ep_003` is the cleanest success, but it is too short to show the full retry loop. `phase3_ep_002` is useful as a failure/recovery case, but less suitable as the main narrative because the initial image remained best.

## Input And Output Forms

Task input:

- File: `runs/phase3_hq5/phase3_ep_001/task_spec.json`
- Shape: original prompt, atom constraints, max image attempts.
- Example fields: `original_prompt`, `constraints[].constraint_id`, `constraints[].constraint_type`, `constraints[].requirement`, `constraints[].evaluator_question`.

Planner input to teacher:

- Files:
  - `runs/phase3_hq5/phase3_ep_001/planner_requests.jsonl`
  - `runs/phase3_hq5/phase3_ep_001/planner_views/planner_view_*.json`
- Shape: request metadata plus immutable planner view.
- Important fields: `remaining_budget`, `latest_attempt`, `best_attempt`, `visible_images`, `extra_observations`, `retrieved_skill_ids`, atom results, transitions.

Assistant output:

- Files:
  - `runs/phase3_hq5/phase3_ep_001/raw_teacher_outputs.jsonl`
  - `runs/phase3_hq5/phase3_ep_001/canonical_actions.jsonl`
- Shape:
  - raw teacher output is stored as raw JSON text plus redaction metadata and SHA-256;
  - canonical action is the parsed executable action used by the environment.
- Important fields: `action`, `arguments`, `target_constraint_ids`, `preserve_constraint_ids`, `source_attempt_id`, instruction text.

Tool output for `query_skill`:

- File: `runs/phase3_hq5/phase3_ep_001/tool_observations.jsonl`
- Shape: `skill_returned` observation with skill IDs, summaries, content refs, and hashes.

Image tool output:

- Files:
  - `runs/phase3_hq5/phase3_ep_001/tool_observations.jsonl`
  - `runs/phase3_hq5/phase3_ep_001/images/img_*.png`
- Shape: `image_execution_completed` observation plus image artifact.
- Important fields: `attempt_id`, `image_artifact_id`, `request_id`, render metadata such as `num_inference_steps`, `width`, `height`, `seed`, `local_runtime`.

Verifier output:

- File: `runs/phase3_hq5/phase3_ep_001/geneval2_results.jsonl`
- Shape: one record per attempt with normalized atom results.
- Important fields: `attempt_id`, `constraint_results[].constraint_id`, `constraint_results[].status`, `observed`, `expected`, `confidence`.

Memory/reducer output:

- Files:
  - `runs/phase3_hq5/phase3_ep_001/events.jsonl`
  - `runs/phase3_hq5/phase3_ep_001/episode_state.json`
- Shape: immutable events plus reduced state. The reducer owns latest attempt, best attempt, transitions, budget, and submission state.

Submission output:

- File: `runs/phase3_hq5/phase3_ep_001/submission.json`
- Shape: selected attempt, best attempt, attempt order, reason code.

## Phase3 EP001 Turn Narrative

Turn `000`: `query_skill`

- Input: empty attempt history, no visible images, remaining budget 5, observation says not to edit or submit.
- Assistant action: query `counting_layout` and `spatial_relation` for count/action/position atoms.
- Output: local skill store returned two skill records. Their content is placeholder, but the tool interaction exists in canonical history.

Turn `001`: `generate_image`

- Input: no image attempts yet, retrieved skills in context.
- Assistant action: initial generation instruction for exactly six glass lions, three red cats behind one brown donut, and a chasing relation.
- Image output: `a_000`, `img_000.png`, local Qwen runtime, 40 steps, 1024 x 1024.
- Verifier output: 6/11 pass. Failed lion count, glass material, chasing relation, cat count, and cat/donut position.
- Memory output: best becomes `a_000`.

Turn `002`: `generate_image`

- Input: latest/best `a_000`, visible image `img_000`, remaining budget 4, atom failures from `a_000`.
- Assistant action: fresh regeneration with stronger layout/count constraints.
- Image output: `a_001`, `img_001.png`.
- Verifier output: 8/11 pass plus 1 uncertain. Cat count and cat-behind-donut position were fixed; lion count, glass material, and chasing remained non-passing.
- Memory output: best becomes `a_001`.

Turn `003`: `edit_image`

- Input: source/best `a_001`, remaining budget 3.
- Assistant action: edit from `a_001`, target lion count, glass material, and chasing; preserve already-passing cat/donut atoms.
- Image output: `a_002`, `img_002.png`.
- Verifier output: 9/11 pass. Glass material fixed; lion count and chasing still failed.
- Memory output: best becomes `a_002`.

Turn `004`: `edit_image`

- Input: source/best `a_002`, remaining budget 2.
- Assistant action: edit from `a_002`, target lion count and chasing; preserve glass, cats, donut, and position atoms.
- Image output: `a_003`, `img_003.png`.
- Verifier output: 10/11 pass plus 1 uncertain. Chasing fixed; lion count remained uncertain.
- Memory output: best becomes `a_003`.

Turn `005`: `edit_image`

- Input: source/best `a_003`, remaining budget 1.
- Assistant action: edit from `a_003`, target only lion count; preserve all other atoms.
- Image output: `a_004`, `img_004.png`.
- Verifier output: 9/11 pass. Lion count failed and chasing regressed.
- Memory output: best remains `a_003`, not latest `a_004`.

Turn `006`: `submit_attempt`

- Input: budget exhausted, latest `a_004`, best `a_003`.
- Assistant action: submit `a_003` with `reason_code=best_available_under_budget`.
- Output: `submission.json` records `submitted_attempt_id=a_003`, `best_attempt_id=a_003`, and full attempt order.

## Recommendation

For a GenSearcher/GenEvolve-style explanation, present `phase3_ep_001` using:

- `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md` as the full readable trace;
- this report for the behavior-level interpretation;
- the five image artifacts under `runs/phase3_hq5/phase3_ep_001/images/` for visual evidence;
- `geneval2_results.jsonl` for the atom-level verifier table.
