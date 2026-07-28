# Skill-v1 Validation Analysis

Date: 2026-07-15

## Run Summary

- Run root: `runs/skill_v1_validation_policyfix`
- Episode: `phase3_ep_001`
- Prompt: `six glass lions chasing three red cats behind a brown donut`
- Rendering: local Qwen-Image-Edit, `40` steps, `1024 x 1024`
- Teacher: GPT-5.5
- Evaluator: Geneval2, every image attempt
- Final state: submitted `a_000` with `best_available_under_budget`
- Counts: 56 events, 10 canonical actions, 5 image attempts, 5 Geneval2 reports
- Readable trace: `docs/skills/validation/trajectory_trace_skill_v1_policyfix_ep_001.md`

This is a valid completed fresh-start trajectory. The interrupted foreground/tmux handoff exposed a resume bug around an unfinished `image_execution_started` event. The invalid tail was backed up under `runs/skill_v1_validation_policyfix/phase3_ep_001/recovery_backup_after_duplicate_start_20260715T1445Z`, the valid prefix was restored to the pending-start boundary, and the repaired runner resumed from the same episode state.

## Action-Level Behavior

| Turn | Action | Input context | Output/action form | Outcome |
| --- | --- | --- | --- | --- |
| `turn_000` | `query_skill` | Empty history, atom rubric, no images, Skill summaries only | Requests `counting_and_instance_layout` + `spatial_relation_layout` for count/relation atoms | Full Markdown Skills returned as tool observation |
| `turn_001` | `generate_image` | Retrieved Skill Markdown in immediate context | Fresh generation instruction uses exact totals, bounded layout, visibility gaps, depth relation, chase cues | `a_000`, 8/11 pass; fails chasing, cat count, cats behind donut |
| `turn_002` | `query_skill` | Geneval2 failure state for `a_000`, no Skill content retained | Re-queries count + spatial Skills for failed atoms | Allowed because new evaluator observation exists |
| `turn_003` | `edit_image` | Retrieved Skill Markdown + image refs for latest/best `a_000` | Local edit targeting failed count/relation atoms, preserving passed atoms | `a_001`, 8/11 pass; cat count becomes uncertain, relation still fails |
| `turn_004` | `query_skill` | New Geneval2 state after edit | Re-queries spatial + count Skills for persistent failed atoms | Tool response correctly tied to `evt_0026` |
| `turn_005` | `edit_image` | Retrieved Skill Markdown + latest/best image refs | Edits from `a_001`, targets cats/chasing/behind relation | `a_002`, 7/11 pass; regresses glass-lion attribute |
| `turn_006` | `query_skill` | New Geneval2 state after regression | Re-queries count + spatial Skills | Tool response correctly tied to `evt_0037` |
| `turn_007` | `edit_image` | Retrieved Skill Markdown + latest/best image refs | Edits from `a_002`, targets regressed glass plus persistent relation/count atoms | `a_003`, 7/11 pass; same major failures persist |
| `turn_008` | `edit_image` | No retrieved Skill content; latest `a_003`, best `a_000` | Branches from historical best `a_000`, repairs failed atoms while preserving passed atoms | `a_004`, 8/11 pass; returns to best-equivalent score but does not improve |
| `turn_009` | `submit_attempt` | Budget exhausted; best-so-far and latest visible | Submits historical best `a_000` with required reason code | Correct best-so-far recovery |

## Skill Use Assessment

The Skill mechanism now matches the desired GenSearcher/GenEvolve-style interaction shape:

- the planner first sees Skill summaries, not full content;
- `query_skill` is an explicit assistant action;
- the local tool returns full `SKILL.md` Markdown content with version/hash metadata;
- the retrieved Markdown enters the next teacher request exactly once;
- the next generation/edit action can cite `skill_ids_used` only for retrieved Skills;
- repeated retrieval is allowed only after a new image/evaluator observation, not as a query-only loop.

The content is no longer placeholder. The generation/edit instructions show direct uptake of the Skill operators: exact totals, bounded formations, full visibility, separated instances, foreground/background anchoring, occlusion/depth cues, chase direction, and preservation of already-passing atoms.

## Main Weakness

The trajectory proves the interaction structure and traceability, but not strong visual repair effectiveness. The hard atoms `c_004` chasing, `c_005` exactly three cats, and `c_008` cats behind donut remain failed through all five attempts. Later edits repeat the same count/spatial repair family and sometimes regress a passed atom (`c_002` glass lions).

This means:

- the trace is suitable as a clear demonstration of the agent loop and Skill-conditioned action format;
- the initial `generate_image` and final `submit_attempt` are behaviorally strong;
- the repeated Skill queries should remain context/audit evidence, not automatic SFT targets;
- the unsuccessful edit actions are useful negative or history-only examples;
- one successful structure-valid trajectory is not enough to approve Skill-v1 as producing materially better outcomes.

## Recommendation For Sol Review

Ask Sol to judge whether this validation is sufficient to accept the Skill-v1 interaction standard, not whether the image task was solved. The likely decision boundary is:

- approve the protocol shape if explicit query/tool-response/action use and resume semantics are sufficient;
- request changes if repeated re-querying the same two Skills after each failed edit is considered too weak or too repetitive;
- keep `query_skill` context-only for SFT until at least one additional trajectory shows retrieved Skills materially improve an image outcome.

## Sol Review Result

Review file: `docs/reviews/gate3a_skill_v1_validation_sol_review.md`

Verdict: `REQUEST_CHANGES`

Sol accepted the retrieval plumbing and readable trace format, but did not accept Skill-v1 utility. The blocking issue is that the Skill-conditioned edits did not fix any targeted constraints, one edit regressed a preserved atom, and only two of the four Skills were exercised.

Required minimal follow-up: run one fresh, capability-isolated episode with at most three attempts, targeting an attribute/local-preservation failure. It should retrieve `attribute_entity_binding` and `local_edit_preservation`, immediately edit with concrete uptake of both Skills, fix at least one targeted failed or uncertain atom, and avoid regressions among preserved atoms.

Follow-up scoped review: `docs/reviews/gate3a_skill_v1_trace_io_clarity_review.md`

Verdict: `APPROVE` for trace/I/O clarity.

This approval separates foundational Skill interaction from downstream utility. The trajectory is accepted as a clear GenSearcher/GenEvolve-style input-output trace: PlannerView context, `query_skill`, full Markdown tool response, immediate grounded action, image artifact, Geneval2 result, memory transition, and best-so-far state are all visible. The unresolved issues are about later utility, Skill coverage, SFT targetability, and future generate/edit repair-strategy Skills.
