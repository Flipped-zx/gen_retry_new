# MASTER CONTINUATION GOAL — Phase 3 Ten Fresh Natural Rollouts

Repository:

`/root/private_data/agentic_image/gen_retry_new`

Legacy repository:

`/root/private_data/agentic_image/gen-retry`

The legacy repository and all other configured external repositories are strictly read-only.

## Current State

- Gate 1 is approved.
- Phase 2 is complete and committed.
- Do not repeat Phase 0, Gate 1, or Phase 2 audits unless a concrete live incompatibility is found.
- This file replaces all earlier unexecuted Phase 3 plans.

## Core Experimental Decision

All ten Phase 3 trajectories must start from a fresh initial generation.

Do not:

- import legacy images as current attempts;
- continue editing a legacy image;
- construct a canonical episode from a legacy image;
- treat a legacy attempt as the parent of a new action;
- use legacy actions as current-protocol SFT targets.

Legacy Gen-Retry data may be used only as read-only analytical evidence:

- prior prompt records;
- prior Geneval2 diagnostic records;
- prior action records;
- prior fixed / regressed / unresolved outcomes;
- prior difficulty evidence.

The purpose of legacy analysis is to answer:

> Given the historical diagnosis and action outcome, would an edit action have been plausible or potentially preferable?

This is a counterfactual analysis only. It must not be presented as executed ground truth.

Every live trajectory in Phase 3 must follow:

`fresh prompt → fresh initial generation → Geneval2 → natural multi-round retry`

---

# Model and Role Policy

## Main executor

Use Codex 5.5 High/XHigh for:

- implementation;
- repository inspection;
- tests;
- prompt selection;
- trajectory execution;
- adapter work;
- artifact management;
- trajectory analysis;
- SFT design.

## Source researcher

Use the source researcher only for focused, read-only inspection of:

- legacy Gen-Retry;
- Gen-Searcher;
- GenEvolve;
- Geneval2;
- existing source evidence recorded in `docs/SOURCE_LEDGER.md`.

Do not repeat broad searches when grounded evidence already exists.

## High-level reviewer

Use 5.6/Sol only at Gate 2 and Gate 3, or for a genuinely high-level unresolved design conflict.

The reviewer is read-only and receives a compact packet with no more than three core questions.

---

# Phase 3 Research Principle

Do not pre-script trajectory stories.

The experiment is:

> Select ten real, high-difficulty Geneval2 prompts with balanced atomic-constraint coverage, start all episodes from fresh generation, allow the teacher Agent to choose actions naturally, and analyze which retry strategies emerge.

Controlled before execution:

- prompt difficulty;
- constraint-type coverage;
- semantic diversity;
- prompt provenance;
- attempt budget.

Observed after execution:

- direct success;
- regeneration;
- local edit;
- constraint repair;
- regression;
- historical branching within the new episode;
- persistent failure;
- historical-best submission within the new episode.

These are non-exclusive post-hoc labels, not per-episode requirements.

Do not fabricate evaluator outcomes, force a particular action sequence, or select prompts after seeing live outcomes to manufacture desired coverage.

---

# Phase 3A — Preflight

Before any live or paid call:

1. Read:
   - `AGENTS.md`
   - `DEVELOPMENT_BLUEPRINT.md`
   - `docs/status.md`
   - accepted ADRs
   - frozen schemas
   - Phase 2 reports and follow-ups
   - `docs/SOURCE_LEDGER.md`

2. Verify:
   - GPT-5.5 teacher configuration;
   - Qianwen-Image-Edit configuration;
   - Geneval2 environment;
   - isolated run directories;
   - retry budgets;
   - caching and resume behavior;
   - secret redaction;
   - artifact manifests.

3. Never print, persist, or commit:
   - API keys;
   - authorization headers;
   - private endpoint credentials;
   - secret-bearing provider payloads.

4. Resolve ordinary adapter issues with 5.5 High/XHigh.

5. Stop only when:
   - a required credential or endpoint is absent;
   - Geneval2 cannot run or normalize into the frozen atom schema;
   - Qianwen-Image-Edit cannot satisfy the frozen generate/edit contract;
   - an external read-only repository would need modification;
   - a core research decision requires user choice.

Do not redesign the frozen protocol for provider-specific request differences. Handle them in adapters.

---

# Phase 3B — Legacy Diagnostic and Action Analysis

Before selecting the ten prompts, inspect the legacy Gen-Retry repository only as an evidence source.

Do not load legacy images into new episodes.

Build an analysis set from available historical records containing, when traceable:

- original prompt;
- historical atomic constraints;
- historical Geneval2 diagnosis;
- historical action type;
- historical action instruction or prompt;
- fixed constraints;
- regressed constraints;
- persistent failures;
- retry depth;
- final unresolved status.

For every analyzable historical transition, produce a compact record:

- `legacy_record_id`
- `prompt_id`
- `constraint_signature`
- `pre_action_failed_constraints`
- `pre_action_passed_constraints`
- `historical_action`
- `historical_strategy_tags`
- `post_action_fixed_constraints`
- `post_action_regressed_constraints`
- `post_action_persistent_constraints`
- `edit_plausibility`
- `edit_plausibility_evidence`
- `counterfactual_edit_strategy`
- `confidence`
- `limitations`

Allowed `edit_plausibility` values:

- `high`
- `medium`
- `low`
- `undetermined`

The analysis may infer that an edit could have been plausible when grounded evidence shows, for example:

- a small number of localized failed constraints;
- a high pass ratio;
- a usable global layout;
- repeated failure under regeneration;
- target constraints that map to plausible local modifications.

The analysis must explicitly state that this is counterfactual and not experimentally verified.

Do not use these records as positive SFT targets.

Allowed uses:

- difficulty estimation;
- prompt selection evidence;
- identifying failure signatures;
- defining strategy taxonomy;
- defining skills;
- designing analysis rubrics;
- generating hypotheses to test in fresh rollouts.

Required artifacts:

- `artifacts/phase3/legacy_diagnostic_action_analysis.jsonl`
- `docs/phase3/legacy_edit_plausibility_analysis.md`
- `docs/phase3/legacy_failure_signature_summary.md`

---

# Phase 3C — Fresh Candidate Pool Construction

Construct the live candidate pool from Geneval2 prompts.

Legacy prompt text may be reused only when it is part of the Geneval2 task pool or can be mapped to a current Geneval2 task with traceable constraints.

Even when a prompt originally appeared in legacy Gen-Retry:

- ignore the legacy image;
- ignore the legacy attempt state;
- start a completely fresh episode;
- create a new initial generation.

For every candidate, normalize:

- `candidate_id`
- `prompt_id`
- `original_prompt`
- `atomic_constraints`
- `constraint_count`
- `constraint_type_histogram`
- `constraint_type_combination`
- `baseline_difficulty_evidence`
- `historical_difficulty_evidence`
- `historical_unresolved_evidence`
- `semantic_duplication_group`
- `provenance`
- `selection_eligibility`

Use the actual Geneval2 taxonomy. Do not invent unsupported constraint categories.

Historical evidence may inform difficulty, but must not carry historical images or attempt states into the new episode.

Required artifacts:

- `artifacts/phase3/candidate_pool.jsonl`
- `docs/phase3/candidate_pool_report.md`

---

# Phase 3D — Deterministic Ten-Prompt Selection

Select exactly ten high-difficulty prompts using a deterministic and documented method.

Optimize for:

1. high difficulty;
2. broad constraint-type coverage;
3. balanced aggregate occurrence of major constraint types;
4. difficult multi-type combinations;
5. low semantic duplication;
6. inclusion of historically difficult or unresolved prompt patterns when grounded records exist.

Difficulty signals may include:

- number of atomic constraints;
- baseline failed-atom evidence;
- baseline pass ratio evidence;
- historical retry depth;
- historical unresolved status;
- difficult constraint-type combinations;
- rare constraint types.

Do not claim unavailable signals.

A deterministic greedy selector is acceptable.

Conceptual objective:

`difficulty + new_coverage + rare_combination_bonus - imbalance_penalty - semantic_duplication_penalty`

Before live execution, create:

- `artifacts/phase3/selected_ten_prompts.json`
- `artifacts/phase3/constraint_coverage_matrix.json`
- `docs/phase3/prompt_selection_report.md`
- `docs/phase3/selection_provenance.md`

The report must explain:

- why each prompt was selected;
- grounded difficulty evidence;
- constraint coverage contribution;
- duplication control;
- limitations.

Commit the selection artifacts before the first live rollout.

---

# Phase 3E — Ten Fresh Natural Multi-Round Rollouts

Execute one fresh episode for each selected prompt.

## Components

- Teacher policy: GPT-5.5
- Image backend: Qianwen-Image-Edit
- Evaluator: Geneval2
- Protocol: frozen current protocol
- Maximum attempts: explicitly configured and recorded

Every episode must begin with:

- original prompt;
- atomic constraints;
- empty attempt history;
- no source image;
- `best_attempt_id = null`;
- a fresh `generate_image` action or an allowed skill query followed by fresh generation.

No episode may begin with an edit action.

Qianwen-Image-Edit remains the unified backend:

- `generate_image`: fresh generation without a source image;
- `edit_image`: edit a source attempt created earlier in the same new episode.

The teacher may choose only:

- `query_skill`
- `generate_image`
- `edit_image`
- `submit_attempt`

After the initial generation, the teacher receives:

- current image;
- Geneval2 atom results;
- new-episode attempt history;
- fixed / regressed / persistent / stable-pass states;
- best attempt from the same new episode;
- strategy history from the same new episode;
- retrieved skills;
- tool capabilities;
- remaining budget.

Do not tell the teacher that an episode must demonstrate a predetermined behavior.

Each episode ends when:

- all constraints pass and an attempt is submitted;
- the budget is exhausted and a valid attempt is submitted;
- or a documented infrastructure failure invalidates the episode.

Do not silently replace valid but uninteresting trajectories.

Replacement is allowed only for an invalid infrastructure run, not to manufacture missing strategy coverage.

---

# Phase 3F — Traceability Requirements

For every decision, persist:

1. episode ID;
2. round ID;
3. planner request ID;
4. exact PlannerView;
5. image references visible to the teacher;
6. retrieved skills;
7. raw teacher output;
8. redaction record;
9. validation result;
10. canonical action;
11. rejected or repaired output;
12. action type;
13. source attempt ID when applicable;
14. focus constraint IDs;
15. preserve constraint IDs;
16. strategy tags;
17. exact generation or edit instruction;
18. normalized Qianwen-Image-Edit request metadata;
19. image artifact;
20. Geneval2 raw-result reference;
21. normalized atom results;
22. attempt transition;
23. fixed constraints;
24. regressed constraints;
25. persistent failures;
26. latest attempt;
27. best attempt;
28. remaining budget;
29. final submission;
30. termination reason.

Every episode must replay from its immutable event log.

Suggested structure:

```text
runs/phase3/<episode_id>/
  task_spec.json
  events.jsonl
  planner_requests.jsonl
  raw_teacher_outputs.jsonl
  canonical_actions.jsonl
  tool_observations.jsonl
  geneval2_results.jsonl
  episode_state.json
  submission.json
  manifest.json
  images/
  trajectory_analysis.md
```

---

# Phase 3G — Post-Hoc Behavioral Labels

Assign non-exclusive labels from actual new-episode events only:

- `direct_success`
- `regeneration_used`
- `local_edit_used`
- `target_constraint_fixed`
- `constraint_regression`
- `persistent_failure`
- `repeated_ineffective_strategy`
- `historical_branch`
- `best_so_far_recovery`
- `historical_best_submission`
- `all_constraints_passed`
- `budget_exhausted`
- `invalid_infrastructure_run`

Here, `historical_branch` means branching from an earlier attempt within the same newly generated episode.

Do not use legacy attempts to satisfy any behavioral label.

Do not fabricate missing coverage.

---

# Phase 3H — Per-Trajectory Quality Analysis

For each new trajectory, analyze:

- what the teacher did well;
- what it did poorly;
- whether the action was justified by the available state;
- whether edit versus regenerate was distinguishable;
- whether the selected source attempt was appropriate;
- whether the instruction operationalized failed constraints;
- whether stable passes were preserved;
- which constraints were fixed;
- which constraints regressed;
- whether an ineffective strategy was repeated;
- whether memory changed the decision;
- whether best-so-far changed the decision;
- whether the final submission was correct;
- whether the action has sufficient evidence for SFT supervision.

Classify every new-protocol assistant action as exactly one of:

- `trainable_positive`
- `recovery_positive`
- `history_only_harmful`
- `history_only_ineffective`
- `excluded_ambiguous`
- `excluded_invalid`

Do not classify an action as positive solely because the episode eventually succeeded.

Use direct action-outcome evidence.

For each decision, add:

- plausible alternative action;
- whether the available state favored the chosen action;
- whether branch execution would be needed for stronger counterfactual evidence.

Legacy counterfactual analysis must remain separate from these SFT supervision labels.

---

# Phase 3I — Cross-Trajectory Analysis

After ten valid fresh episodes, report:

- prompt difficulty distribution;
- constraint-type coverage;
- semantic diversity;
- action distribution;
- behavioral-label coverage;
- edit versus regenerate frequency;
- target fixes;
- regressions;
- branches from earlier attempts in the same episode;
- persistent failures;
- all-pass submissions;
- historical-best submissions within the same episode;
- repeated ineffective strategies;
- trainable-positive action count;
- recovery-positive action count;
- harmful/ineffective history-only count;
- ambiguous action count;
- context-length statistics;
- instruction-length statistics;
- unused protocol fields;
- missing fields;
- ambiguous fields;
- adapter failures;
- evaluator-normalization failures;
- prompt-policy failures.

Compare fresh live trajectories with the legacy counterfactual edit-plausibility analysis:

- Which historically observed failure signatures actually led to edit in fresh runs?
- Which edit hypotheses were supported?
- Which were contradicted?
- Which remain untested?

Required artifacts:

- `docs/phase3/ten_trajectory_comparison.md`
- `docs/phase3/behavior_coverage_report.md`
- `docs/phase3/legacy_vs_fresh_strategy_analysis.md`
- `docs/phase3/sft_candidate_action_report.md`
- `artifacts/phase3/trajectory_index.json`
- `artifacts/phase3/action_supervision_labels.jsonl`

If a desired behavior does not appear naturally, record zero coverage and propose an optional later coverage-completion set.

Do not execute additional paid episodes without user approval.

---

# Gate 2 — Automatic Review

After Phase 3:

1. build a compact Gate 2 packet;
2. include:
   - one-page experiment brief;
   - ten-prompt selection summary;
   - legacy diagnostic/action analysis summary;
   - fresh rollout behavioral coverage;
   - trajectory-quality summary;
   - SFT candidate-action summary;
   - test and replay summary;
   - no more than three high-level questions;
3. invoke Sol automatically.

Require one verdict:

- `APPROVE`
- `REQUEST_CHANGES`
- `BLOCKED`

Gate 2 reviews:

1. whether all ten rollouts were fresh and unscripted;
2. whether prompt selection and provenance are defensible;
3. whether legacy evidence was used only analytically;
4. whether action-outcome traces support supervision labels;
5. whether the evidence is sufficient for Phase 4 SFT design.

Gate 2 must not require every desired behavior to occur naturally.

Missing behavior coverage is a limitation, not automatically a blocker.

If `REQUEST_CHANGES`:

- use 5.5 High/XHigh for scoped corrections;
- rerun only affected tests or invalid infrastructure runs;
- do not rerun valid episodes merely to obtain preferred behavior;
- allow at most two correction cycles.

After `APPROVE`:

- update `docs/status.md`;
- commit Phase 3 and Gate 2;
- immediately begin Phase 4;
- do not return merely because Phase 3 is complete.

---

# Phase 4 — SFT Design Based on Fresh Trajectories

The SFT scheme must be derived primarily from the ten fresh trajectories and their action-outcome evidence.

Legacy diagnostic/action records may contribute:

- failure-signature taxonomy;
- difficulty analysis;
- skill hypotheses;
- negative or ambiguous examples for analysis.

Legacy records must not become positive current-protocol action targets unless they independently satisfy the frozen protocol and were executed under the current environment, which is not expected in this phase.

Freeze:

- multimodal message format;
- system prompt;
- user observation format;
- tool observation format;
- assistant canonical action target;
- image placement;
- loss mask;
- target selection;
- harmful-action handling;
- ineffective-action handling;
- recovery-action handling;
- context compression;
- token budget;
- truncation behavior;
- train/validation/test split;
- action balance;
- schema validation;
- train/inference consistency.

The principal target is:

`canonical assistant action JSON`

Do not train on:

- environment-computed state;
- Geneval2 output tokens;
- raw tool observations;
- raw legacy assistant JSON;
- counterfactual legacy edit hypotheses;
- harmful actions as positive targets;
- unverifiable free-form chain-of-thought.

Harmful and ineffective actions may appear only as history when needed to supervise a later recovery decision.

Prepare Gate 3 and invoke Sol automatically.

---

# Autonomous Continuation Policy

After each subphase:

1. validate its Done Definition;
2. update `docs/status.md`;
3. write an internal checkpoint report;
4. commit when appropriate;
5. immediately continue.

Do not issue a final user-facing response after an intermediate subphase.

Return only when:

- a documented stop condition occurs;
- user approval is required for additional paid episodes;
- credentials or endpoints are missing;
- the live backend violates a frozen semantic contract;
- two reviewer correction cycles fail;
- or Phase 4 and Gate 3 are complete.

Begin by reading the current repository state and executing Phase 3A preflight, followed by legacy diagnostic/action analysis and fresh candidate-pool construction.
