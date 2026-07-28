# SKILL V1 FOUNDATIONAL CAPABILITIES DESIGN GOAL
## Stop before live trajectory execution and ask for user confirmation

Repository:

`/root/private_data/agentic_image/gen_retry_new`

Legacy repository:

`/root/private_data/agentic_image/gen-retry`

All external repositories are strictly read-only.

---

# 0. Current project state

The project already has:

- an approved canonical action protocol;
- deterministic event replay;
- a working `query_skill -> LocalSkillStore -> SKILL.md -> tool observation -> next PlannerView` chain;
- ten completed fresh Phase 3 trajectories;
- approved Gate 2 and Gate 3;
- a frozen Phase 4 SFT supervision design;
- placeholder Markdown skills whose retrieval mechanism is correct but whose content is not operational.

The previous Skill design goals were not executed.

This file replaces all earlier unexecuted Skill-v1 goals.

Do not repeat Phase 0–4 work.

Do not modify completed Phase 3 trajectories or their labels.

---

# 1. Objective

Design a minimal, grounded Skill Catalog v1 that teaches stable image-generation and image-editing capabilities.

The Skill system must answer:

> How should a visual constraint be operationalized in a generation or editing instruction?

The Skill system must not answer:

> Should the Agent edit, regenerate, branch from an earlier attempt, continue, or submit?

High-level action selection remains the responsibility of the retry policy, using:

- current image;
- Geneval2 atom feedback;
- attempt history;
- fixed / regressed / persistent states;
- best-so-far;
- strategy history;
- remaining budget.

Do not encode retry-policy decisions into static Skill Markdown.

---

# 2. Mandatory role split

## 2.1 Main executor: GPT-5.5 High/XHigh

Use GPT-5.5 High/XHigh for:

- repository inspection;
- evidence extraction;
- implementation feasibility analysis;
- drafting Skill documents;
- manifest and retrieval policy design;
- persistent-worker and concurrency design;
- static validation and tests;
- preparing the user confirmation packet.

## 2.2 Source researcher: GPT-5.5 High, read-only

Use a focused read-only researcher for the minimum necessary evidence from:

### Current repository

- `skills/*/SKILL.md`
- `src/gen_retry/tools/skill_store.py`
- `src/gen_retry/agent/teacher_client.py`
- `docs/phase3/hq5_completed_trajectory_behavior_analysis.md`
- `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md`
- all per-trajectory Phase 3 analyses
- `artifacts/phase3/action_supervision_labels.jsonl`
- `docs/phase4/sft_supervision_freeze.md`
- `docs/status.md`
- `docs/SOURCE_LEDGER.md`

### Legacy Gen-Retry

Use only:

- historical Prompt records;
- historical Geneval2 diagnoses;
- historical actions;
- fixed / regressed / persistent outcomes;
- unresolved failure patterns.

Do not use:

- legacy images as new trajectory inputs;
- legacy attempt states as parents;
- legacy actions as current-protocol positive SFT targets.

### Grounded external evidence already available locally or in the Source Ledger

Inspect only the relevant files or sections from:

- GEMS: Markdown Skill format and on-demand loading;
- GenEvolve: productive-versus-harmful / best-versus-worst trajectory experience distillation;
- Gen-Searcher: persistent heavy-model service organization;
- official Qwen-Image-Edit usage guidance for instruction construction and persistent loading.

Do not repeat broad repository or paper searches when grounded evidence already exists.

## 2.3 High-level reviewer: GPT-5.6 Sol XHigh, read-only

Invoke Sol only after GPT-5.5 has completed the draft design packet.

Sol reviews exactly these three questions:

1. Is the Skill Catalog minimal, non-overlapping, and aligned with the actual Geneval2 failure evidence?
2. Is each Skill operational, concise, grounded, and clearly separated from retry-policy decisions?
3. Is the proposed persistent Qwen-Image-Edit worker and concurrency design technically appropriate?

Sol must return exactly one verdict:

- `APPROVE`
- `REQUEST_CHANGES`
- `BLOCKED`

If `REQUEST_CHANGES`:

- allow one scoped GPT-5.5 correction cycle;
- run one final Sol review;
- do not expand the review scope.

---

# 3. Skill versus Policy boundary

Use this rule:

## Put knowledge in Skill when it answers:

- How do I express an exact count?
- How do I make multiple instances separately visible?
- How do I express left/right, front/behind, containment, facing, chasing, or following?
- How do I bind color or material to the correct entity?
- How do I write a local edit instruction that preserves already-correct content?

## Keep knowledge in retry policy / future experience system when it answers:

- Should I edit or regenerate?
- Should I use the latest image or branch from best-so-far?
- Should I continue or submit?
- How should remaining budget change the action?
- Should a repeated ineffective strategy be abandoned?
- Which action is preferable in the current episode state?

Do not add numeric pass-ratio thresholds, budget rules, or edit-versus-regenerate heuristics to `SKILL.md`.

A Skill may declare:

- supported action modes;
- applicability to a constraint type;
- how to construct the instruction after an action mode has been chosen.

A Skill may not choose the high-level action for the Agent.

---

# 4. Part A — Audit actual capability failures

Inspect the completed ten fresh trajectories and available historical diagnosis/action records.

Produce an evidence table with:

- actual Geneval2 constraint type;
- representative failure signature;
- frequency;
- representative episode/action IDs;
- target fixed count;
- regression count;
- repeated ineffective strategy count;
- common instruction defect;
- capability knowledge that could address the defect;
- whether evidence is evaluator-grounded, trajectory-derived, or hypothetical.

Separate:

- evaluator-grounded facts;
- trajectory-derived observations;
- counterfactual hypotheses.

Do not invent taxonomy categories not present in the actual evaluator data.

Required output:

`docs/skills/design_review/FOUNDATIONAL_CAPABILITY_EVIDENCE.md`

---

# 5. Part B — Propose a minimal Skill Catalog v1

Start from exactly these four candidate Skills:

## 5.1 `counting_and_instance_layout`

Purpose:

- operationalize exact cardinality;
- keep every instance fully visible;
- separate instances with visible gaps;
- prevent extras, duplicates, fusion, and cropped objects;
- place an instance group in a bounded region when relevant.

Supported action modes:

- `generate_image`
- `edit_image`

This Skill must not decide whether edit or generate is preferable.

## 5.2 `spatial_relation_layout`

Purpose:

- operationalize left/right, above/below, front/behind, inside/on;
- operationalize directional or verb relations such as facing, chasing, and following when present;
- use explicit frame regions, orientation, visible gaps, depth cues, and occlusion control;
- keep both subject and object visible and identifiable.

Supported action modes:

- `generate_image`
- `edit_image`

## 5.3 `attribute_entity_binding`

Purpose:

- bind color, material, texture, identity, and other attributes to the correct object;
- prevent entity swaps, attribute leakage, and ambiguous shared descriptions;
- use separate entity descriptions and spatial anchors.

Supported action modes:

- `generate_image`
- `edit_image`

## 5.4 `local_edit_preservation`

Purpose:

- construct a narrow edit instruction after `edit_image` has already been selected;
- identify the exact object or region to change;
- list stable passed constraints that must remain unchanged;
- preserve unrelated objects, background, composition, attributes, counts, and relations;
- avoid broad instructions such as “fix the image”.

Supported action mode:

- `edit_image`

Do not add a fifth Skill unless actual failure evidence demonstrates a frequent, non-overlapping foundational capability that cannot be represented cleanly by these four.

Explicitly prohibited Skill:

- `retry_action_selection`

Do not encode edit-versus-regenerate, branch-versus-latest, or continue-versus-submit policy in Skill v1.

Required output:

`docs/skills/design_review/SKILL_CATALOG_V1_PROPOSAL.md`

For each Skill include:

- `skill_id`
- one-sentence manifest summary
- actual constraint types covered
- supported action modes
- applicable failure signatures
- non-applicable conditions
- overlap analysis
- evidence references
- expected token size
- useful retrieval pairings

---

# 6. Part C — Draft exact Skill Markdown

Use this outer format for compatibility with the existing store and GEMS-style Markdown Skills:

```markdown
# Skill: <Name>

## Description
<one concise paragraph>

## Instructions

### Applicable when
...

### Do not use when
...

### Operators
...

### Preservation checks
...

### Avoid
...

### Minimal instruction pattern
...
```

`### Preservation checks` may be omitted only when genuinely irrelevant.

Each Skill should be approximately 180–350 English tokens unless evidence requires otherwise.

Skill content must be:

- operational;
- reusable;
- concise;
- expressed as instruction-construction operators;
- grounded in sources or trajectory evidence.

Skill content must not contain:

- chain-of-thought;
- long background essays;
- duplicated full rubrics;
- hard-coded episode IDs;
- unsupported causal claims;
- provider secrets;
- high-level retry policy;
- unbounded examples.

Draft files under:

- `docs/skills/design_review/drafts/counting_and_instance_layout/SKILL.md`
- `docs/skills/design_review/drafts/spatial_relation_layout/SKILL.md`
- `docs/skills/design_review/drafts/attribute_entity_binding/SKILL.md`
- `docs/skills/design_review/drafts/local_edit_preservation/SKILL.md`

Do not overwrite active files under `skills/` yet.

---

# 7. Part D — Provenance and authoring method

Explain how Skill v1 was authored from evidence rather than intuition.

Combine:

1. grounded prior work and repository conventions;
2. official Qwen-Image-Edit operational guidance;
3. current ten-trajectory instruction/outcome evidence;
4. historical diagnosis/action outcome evidence;
5. productive-versus-harmful transition comparisons.

For every substantive instruction inside each Skill, record one provenance category:

- `repository_grounded`
- `paper_grounded`
- `trajectory_grounded`
- `backend_documentation_grounded`
- `our_hypothesis`

Every `our_hypothesis` item must include a validation plan.

Required output:

`docs/skills/design_review/SKILL_PROVENANCE_LEDGER.md`

---

# 8. Part E — Manifest and retrieval policy

Design the Skill manifest so the planner sees a short summary before retrieval.

Each manifest item must include:

- `skill_id`
- `version`
- `summary`
- `constraint_types`
- `supported_action_modes`
- `content_hash`

Full Markdown content must be returned only after `query_skill`.

Freeze these initial retrieval rules:

1. One `query_skill` action may request at most two Skills.
2. The same Skill version may be retrieved at most once per episode by default.
3. Consecutive `query_skill`-only loops are forbidden.
4. After a successful Skill query, the next canonical action should normally be:
   - `generate_image`
   - `edit_image`
   - or `submit_attempt`
5. Retrieved Skill content must enter the next PlannerView exactly once unless explicitly retained by the current reducer policy.
6. Version and content hash must be logged.
7. Skill text is a tool observation and does not receive SFT loss.
8. `query_skill` remains context-only until fresh action-outcome evidence shows that retrieval was relevant, used, and materially helpful.

Decide whether Skill utilization should initially be:

- inferred from downstream instruction/operator matching;
- or explicitly recorded in a separate analysis record.

Do not modify the canonical action schema solely for easier Skill auditing unless a concrete traceability failure is demonstrated.

Required output:

`docs/skills/design_review/SKILL_FORMAT_AND_RETRIEVAL_POLICY.md`

---

# 9. Part F — Persistent Qwen-Image-Edit runtime design

Design the runtime so Qwen-Image-Edit is not reloaded for every image action.

Required architecture:

```text
Episode scheduler
  -> teacher API request queue
  -> persistent Qwen-Image-Edit worker
  -> Geneval2 evaluation queue
  -> reducer
  -> next PlannerView
```

Requirements:

1. Qwen-Image-Edit loads exactly once per worker process.
2. One worker owns one configured GPU or GPU group.
3. The same loaded backend handles both:
   - `generate_image`
   - `edit_image`
4. Every image job has:
   - job ID;
   - episode ID;
   - action ID;
   - idempotency key;
   - deterministic artifact destination;
   - resume/cache status.
5. Completed expensive jobs must not be repeated after resume.
6. Within one episode, dependent rounds remain sequential:
   - image execution;
   - Geneval2 evaluation;
   - state reduction;
   - next planner decision.
7. Across episodes, teacher API work, image execution, and evaluation may be pipelined.
8. Geneval2 and Qwen may run concurrently only when:
   - they use separate hardware or services;
   - profiling confirms no harmful contention.
9. If they share a GPU:
   - default to serialized GPU execution;
   - do not assume concurrent execution improves throughput.
10. For the first Skill-v1 validation trajectory:
   - prioritize correctness;
   - use one persistent in-process worker;
   - run only one fresh episode.

Compare:

## Option A — in-process long-lived worker

Assess:

- implementation effort;
- model-load lifetime;
- failure isolation;
- resume behavior;
- suitability for one fresh trajectory.

## Option B — local persistent service worker

Assess:

- implementation effort;
- process isolation;
- queueing;
- multi-episode throughput;
- suitability for later batch construction.

Recommend:

- one immediate implementation for the first validation trajectory;
- one later-scale implementation.

Required output:

`docs/skills/design_review/PERSISTENT_WORKER_AND_CONCURRENCY_DESIGN.md`

Do not implement the worker in this design-review task.

---

# 10. Part G — Select one first validation trajectory

Select exactly one task specification from the completed Phase 3 set for a fresh Skill-v1 validation episode.

Default candidate:

`phase3_ep_001`

Use it only if evidence confirms that it tests several of:

- Skill retrieval;
- counting;
- spatial or verb relation;
- instruction construction;
- local-edit preservation;
- repeated editing;
- regression;
- best-so-far submission.

The new validation trajectory must later:

- start from empty history;
- use a fresh initial generation;
- reuse no old images;
- reuse no old attempt states;
- use the same original Prompt and atomic constraints;
- use the accepted Skill Catalog v1;
- use the same teacher, Qwen-Image-Edit, and Geneval2 versions;
- use at most five image attempts unless explicitly approved otherwise;
- preserve full traceability.

Define falsifiable success criteria:

1. The Agent queries a relevant Skill or correctly decides no Skill is needed.
2. The next generation/edit instruction visibly uses concrete operators from the retrieved Skill.
3. The query does not create a redundant query-only loop.
4. Skill use does not worsen action selection or context cost without benefit.
5. The resulting trajectory is sufficiently traceable to judge whether Skill retrieval helped, was ignored, or was harmful.

Also define:

- what counts as Skill failure;
- what result would justify running two additional fresh trajectories;
- what result would justify revising Skill content before further runs.

Required output:

`docs/skills/design_review/FIRST_SKILL_V1_TRAJECTORY_PLAN.md`

---

# 11. Part H — Sol review

Create:

`docs/reviews/gate3a_foundational_skill_design_packet.md`

The packet must include only:

- one-page decision brief;
- proposed four-Skill catalog;
- one representative drafted Skill;
- provenance summary;
- retrieval policy;
- persistent-worker recommendation;
- first validation trajectory plan;
- no more than three questions.

Invoke GPT-5.6 Sol.

Apply at most one scoped correction cycle.

Do not let Sol reopen:

- the canonical event protocol;
- completed Phase 3 trajectories;
- Gate 2;
- the general Phase 4 SFT schema;
- unrelated runtime modules.

---

# 12. Part I — User confirmation packet

After the final Sol verdict, create:

`docs/skills/design_review/USER_CONFIRMATION_PACKET.md`

It must contain:

1. final proposed Skill IDs;
2. one-line purpose of each Skill;
3. exact Markdown template;
4. Skill token lengths;
5. retrieval limits;
6. provenance summary;
7. explicit statement that high-level retry policy is not encoded in Skills;
8. persistent-worker recommendation;
9. Geneval2/Qwen concurrency policy;
10. selected first validation trajectory;
11. files that will be activated after approval;
12. live calls that will occur after approval;
13. expected maximum image attempts;
14. unresolved risks;
15. a clear yes/no confirmation request.

STOP after producing this packet.

Do not:

- overwrite active `skills/*/SKILL.md`;
- activate Skill Catalog v1;
- modify the frozen SFT policy;
- run GPT-5.5 teacher rollout calls;
- run Qwen-Image-Edit;
- run Geneval2;
- execute the validation trajectory.

Return the confirmation packet to the user.

---

# 13. Completion report

At completion, report:

- files added;
- sources inspected;
- Skill catalog proposed;
- Sol verdict;
- unresolved issues;
- exact path to `USER_CONFIRMATION_PACKET.md`.

Do not continue beyond user confirmation.
