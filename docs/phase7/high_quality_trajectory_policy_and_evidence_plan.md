# High-Quality Trajectory Policy And Evidence Plan

Date: 2026-08-01

## Decision

Do not freeze the final SFT export yet. Freeze and validate the rollout policy
first, because high-quality canonical trajectories are the evidence pool from
which later SFT targets will be selected.

The existing 200 trajectories remain immutable and useful. Failed or harmful
actions remain valid history; they are not automatically positive SFT targets.
No completed trajectory is rewritten by the changes below.

## What The Existing 200 Establish

| Metric | First Agent image | Submitted | Gain |
| --- | ---: | ---: | ---: |
| Passed atoms | 1159/1419 | 1301/1419 | +142 |
| Atom pass rate | 81.68 | 91.68 | +10.01 points |
| Soft-TIFA AM | 81.87 | 90.90 | +9.03 |
| Soft-TIFA GM | 42.58 | 73.50 | +30.92 |
| All-pass episodes | 51/200 | 111/200 | +60 |

Episode-level movement:

- 105 episodes improved both pass count and GM.
- 26 tied pass count and improved GM.
- 68 changed neither submitted pass count nor submitted GM.
- `phase3_ep_191` improved 8/10 to 9/10 atoms while GM fell 41.67 to
  26.08. This is the single first-to-submit atom/GM disagreement.

After the initial image there were 484 image retries:

- 129 exceeded the prior global-best pass count;
- 130 tied global-best pass count and improved GM;
- 16 had higher GM but fewer passes and were correctly rejected by the frozen
  pass-count-first selector;
- 112 made strict no progress or lowered GM;
- 59 were regression-only;
- 38 fixed and regressed different atoms in the same action.

The main content gains were count `+92` and attribute `+40`. Verb improved
only `5/22 -> 10/22`; chasing remained `2/12` at submission. Ninety-nine
episodes used all five images, including 43 with zero atom gain. The next
policy must reduce blind edit loops without blocking a changed intervention
on a persistent atom.

## What Can Be Claimed

On the fixed 200 Flow-DPPO synthetic-train prompts, the integrated retry
system strongly improves both atom-level results and local prompt-level
Soft-TIFA GM. Against the aligned user-supplied Qwen Best-of-5 file, it gains
259 passed atoms and 41.97 GM points while using 684 rather than 1000 image
calls.

This is not yet an official Geneval2 leaderboard claim and not a causal claim
for the history-aware Planner alone. The baseline lacks renderer revision,
seed, step, evaluator, and GPU-time provenance. Prompt rewrite, adaptive
selection, generation/edit routing, and history-aware planning are not
isolated.

The frozen selection rule remains:

```text
higher atom pass count -> higher prompt-level GM -> earlier Attempt
```

GM is the primary reported benchmark score, while pass count is the selection
guardrail. Changing to GM-only after observing the results would discard atom
coverage and invalidate protocol continuity. Reports should show GM, AM, atom
pass rate, all-pass rate, and image/GPU cost together.

## High-Quality Definition

Use three independent labels:

1. `trajectory_valid`: complete immutable events, point-in-time
   PlannerContext, canonical actions, images, Geneval2 reports, reducer state,
   correct lineage, and submission; no leakage and replayable.
2. `action_trainable`: reasonable from information visible before the action
   and produces a global-best atom gain or a separately accepted strong GM
   gain. This decision is deferred until the final SFT policy.
3. `trajectory_exemplary`: clearly demonstrates useful diagnosis, a changed
   intervention, edit/regenerate choice, recovery or rollback, and correct
   submit. It may contain a failed intermediate action.

Selecting only all-pass trajectories would overrepresent easy prompts and
remove the recovery behavior the Student needs to learn.

Representative existing demonstrations include:

- `phase3_ep_056`: 7/10 to 10/10, GM 0.21 to 100.00, multi-edit repair;
- `phase3_ep_108`: 3/6 to 6/6, GM 0.07 to 98.97, regenerate after edit stall;
- `phase3_ep_151`: 6/9 to 8/9, GM 1.76 to 90.84, historical-best submission;
- `phase3_ep_079`: 7/10 to 10/10, GM 13.13 to 95.74, successful hard verb
  trajectory;
- `phase3_ep_200`: 6/10 to 6/10, GM 1.08 unchanged, negative example of a
  full-budget failed route.

## Prospective Rollout Policy

The implemented candidate is:

- Action Protocol v0.5 unchanged;
- PlannerContext v0.7 for newly prepared episodes;
- Teacher `teacher_system_prompt_v9_meaningful_retry_verb_retention`;
- `action_pose_relation@2.1.0`;
- Qwen dual backend and Geneval2 unchanged;
- pass-count then GM reducer unchanged.

V0.7 retains every earlier image-action instruction. The Teacher compares a
new plan with all prior interventions. The same action/source/targets may be
used again when the instruction materially changes instance operation,
spatial anchor, separation/layout, pose/contact/motion evidence, identity
disambiguation, or regression preservation. Runtime no longer mistakes tuple
equality for semantic equivalence.

Skill contents are replayed from the retrieval-time tool observation under
the persisted content hash. Same-count historical Attempts with unique pass
evidence are now sent as visible historical candidates, so a branch such as
`phase3_ep_135` does not require the Planner to edit unseen pixels.
Planner request records now also list the Skill IDs actually retrieved for
that call, and identical latest/best images are sent only once.

This is forward-only. The completed v8.1 `phase3_ep_135` action remains valid
trajectory evidence, but its Teacher request did not contain `a_001` pixels.
That individual action must remain context-only unless the later ex-ante SFT
compatibility audit independently accepts the information boundary; its input
artifact must not be rewritten to add the image.

Two guardrails remain prospective rather than runtime-hard-coded:

- generic instruction-quality validation does not yet prove that a verb
  instruction contains the selected typed topology; the paired pilot must
  audit role order, focal pair, action corridor/contact/gap, and preservation
  adherence before deciding whether a deterministic verb validator is safe;
- Qwen image reuse is artifact-path based. Every changed experiment must use a
  new empty run directory; never rerun a changed prompt/configuration into an
  old experiment directory.

## Verb V2.1 Review

Adopt `action_pose_relation@2.1.0` prospectively, with its current scope:

- query after an evaluated verb fail/uncertain result;
- query when an explicit historical verb pass needs protection;
- do not add it as a global initial-generation prefix;
- do not adopt the rejected forced route-closure experiment.

On the ten primary failed-verb A/B prompts, Candidate B improved:

| Metric | Production A | Candidate B |
| --- | ---: | ---: |
| Atoms | 54/71 | 56/71 |
| Verb passes | 0/10 | 3/10 |
| Mean GM | 27.70 | 31.97 |
| Image calls | 50 | 50 |

This supports the combined Skill/retrieval/history policy, not any single
component. The cohort was used to develop the operator and is not independent
generalization evidence.

A visual audit of submitted Candidate-B images shows why chasing remains
hard. Many failures are frontal group motion, parallel co-running, separated
role clusters, or unclear/reversed pursuit direction. The successful
`phase3_ep_116` image has a much clearer lateral trailing horse/kangaroo pair.
`phase3_ep_098` receives a high chasing score despite a less clean frontal
composition, so VQA sensitivity also contributes. Current evidence cannot
separate renderer noncompliance from verifier error; a blinded human or
second-verifier audit is required.

## Minimum Evidence Before More Data

1. Run the predeclared ten-prompt, twenty-trajectory paired v8.1/v9 pilot with
   identical prompt set, image budget, seeds, execution profile, and evaluator.
2. Run a prospective held-out verb A/B on prompts not used to develop v2.1.
   Include every predeclared verb prompt, not only failures selected after the
   fact.
3. Build a provenance-matched, equal-five-call comparison:
   original-prompt Best-of-5; Agent first-rewrite Best-of-5 regenerate;
   fixed verifier heuristic; complete adaptive Agent.
4. Record model revisions, seeds, denoising steps, image size, evaluator
   version, wall time, GPU-seconds, and submission selector for every arm.
5. If these pass, freeze rollout policy and run an independent mixed-difficulty
   cohort. Only then rebuild final SFT eligibility.
6. An official Geneval2 claim requires one final run of the frozen system on
   the official 800-row test set; development cohorts cannot substitute for
   it.

## Deferred SFT Decisions

The current 663-target export is provisional. Do not train it as final v9
data. Still unresolved:

- whether validated `query_skill` actions receive positive loss;
- the final ex-ante semantic compatibility audit;
- the minimum GM-only gain accepted as trainable;
- final v7/v8/v9 target compatibility and weighting.

These decisions do not block preserving or analyzing canonical trajectories.
They should be frozen after the rollout and evidence policy above is stable.
