# Changelog

## 2026-08-04

- Enabled W&B tracking in the canonical full-SFT and LoRA recipes under the
  `Gen_retry/gen-retry-sft` project, with deterministic run/group/tag naming,
  online/offline modes, fail-fast environment checks, and `wandb==0.28.1` in
  the isolated Tsinghua-mirror bootstrap.
- Added a local SFT training report generator for `trainer_state.json` that
  emits loss/eval-loss, learning-rate, gradient, timing/ETA, and optional
  action-metric plots plus JSON/Markdown/HTML summaries without requiring
  W&B connectivity.
- Completed a W&B online connectivity smoke run; credentials remain outside
  the repository and no formal training was authorized while Gate 3 v9 is
  open.

## 2026-08-03

- Added an isolated LlamaFactory 0.9.5 SFT environment for Qwen3-VL-8B with
  full-SFT/ZeRO-3 and LoRA/ZeRO-2 baselines, a Tsinghua-mirror bootstrap, and a
  version-locked image-only torchaudio compatibility patch for the vendor
  Torch stack.
- Added a strict Gen-Retry-to-ShareGPT exporter, provenance manifest, image
  path/hash and placeholder audit, prompt-group split checks, Gate 3 training
  guard, runtime-config materializer, and real LLaMA-Factory token-label audit.
- Converted the existing checkpoint-200 663-target dataset only as a
  `provisional`, `training_authorized=false` smoke artifact; final v9 Gate 3
  remains open and no supervision semantics changed.
- Hardened the adapter after independent review: positive targets are bound to
  the policy/decision/audit hashes, duplicate prompts are split as one group,
  images are copied content-addressed into the dataset and rehashed, and a
  frozen launch requires a structured Gate 3 receipt plus a complete token
  audit bound to the exact dataset/config. Provisional execution is forbidden.
- Replaced the system-site overlay with a clean venv that snapshots only the
  vendor Torch/torchvision/DeepSpeed/FA2 distributions, excludes
  vLLM/CuPy/Megatron, passes `pip check`, records dependency/patch manifests,
  and exposes a separate allocated-HCU smoke for bf16, FA2, and ZeRO-2.
- Closed the final independent-review blockers by deriving authorization again
  inside the library training entrypoint and comparing real tokenized labels
  against the exact per-split target sequence, SHA-256 multiset, and action
  counts. The final read-only re-review returned `PASS`.

## 2026-08-01

- Demoted regex-derived instruction-quality verdicts from a live Qwen
  execution gate to advisory audit metadata after a bounded subset count repair
  in `phase3_ep_004` was falsely rejected four times.
- Kept Action schema/reference, budget, source lineage, and non-best-source
  evidence checks as hard runtime gates.
- Persisted prospective image-Action linter reports in the canonical action log
  as `enforcement=advisory`, `sft_role=environment_metadata`; checker failures
  record a sanitized `unavailable` verdict and cannot block execution.
- Updated checkpoint format-error classification to separate current runtime
  validity from advisory linter findings.

## 2026-08-01

- Selected a fresh 1000-prompt Flow-DPPO cohort with 125 prompts at every
  official Geneval2 `atom_count` from 3 through 10, local tier counts
  375/375/250, official-test semantic-family exclusion, and all 220 earlier
  selected source rows excluded.
- Added the prospective v9 fresh-8 run plan, including a 20-trajectory
  admission pilot, 16 logical workers over eight physical HCU locks, eight
  Teacher slots, fixed-denominator checkpoint reporting, resume rules, and
  empirical P50/P80 estimates of 27-30/34-40 hours.
- Optimized the deterministic official-mix selector by incrementally caching
  selected feature sets. Regenerating the earlier 200 selection remains
  byte-identical with SHA256
  `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`.
- Deferred the final v9 SFT export until the rollout policy and equal-budget
  evidence are frozen; retained all 200 completed trajectories as immutable
  evidence.
- Added PlannerContext v0.7. New prepared primary-score episodes retain the
  full executable instruction in every prior image Round; historical v0.6
  episodes remain valid replay/resume inputs.
- Replaced the v8 tuple hard rejection with
  `teacher_system_prompt_v9_meaningful_retry_verb_retention`: repeated
  action/source/targets are allowed only with a concrete new visual
  intervention.
- Retained `action_pose_relation@2.1.0`, delayed verb retrieval, and historical
  verb-pass preservation without changing Action Protocol, Qwen, Geneval2,
  reducer, budget, or submit semantics.
- Restored Skill guidance from retrieval-time tool observations under the
  persisted content hash. Verified all 13 PlannerContexts in the earlier
  `verb_multiround_teacher_v2` runs rebuild exactly after the Skill upgrade.
- Exposed same-pass historical Attempts with unique atom-pass evidence as
  visible Teacher image candidates and stopped sending duplicate latest/best
  pixels when both IDs are equal.
- Added ADR-0008, a v0.7 fixture/schema, compatibility tests, and the
  consolidated trajectory-quality, score-claim, verb-adoption, and next
  evidence plan.

## 2026-07-31

- Added a paired analysis of the user-supplied original-prompt Qwen-Image
  Best-of-5 results against all 200 fixed retry trajectories.
- Verified exact prompt/VQA alignment for 200/200 rows. Best-of-5 reaches
  1042/1419 atoms, Soft-TIFA GM 31.53, and 42/200 all-pass prompts; the Agent
  leads by 259 atoms, 41.97 GM points, and 69 all-pass prompts.
- Added a pass-count-first selector sensitivity check, difficulty and
  atom-type breakdowns, paired bootstrap intervals, a Best-of-K prefix curve,
  per-prompt failure cases, a reproducible CLI, and focused unit tests.
- Kept the claim integrated and descriptive because the baseline file omits
  execution-profile provenance and does not normalize generate/edit cost.
- Completed a two-HCU, artifact-backed prompt-composition experiment over all
  12 `chasing` prompts from the final Flow-DPPO 200 cohort.
- Evaluated six verb formulations and selected `focal_action_anchor`: 3/12
  chasing passes versus 0/12 initial and 2/12 current submitted.
- Recorded a paired same-seed improvement on `phase3_ep_098` from 4/5 to 5/5
  atoms, with chasing confidence 0.002505 -> 0.996891 and no regression.
- Replayed observed candidates through the frozen comparator; the compatible
  historical-best result is 1303/1419 atoms, 11/22 verbs, and 112/200
  all-pass trajectories. This is explicitly not a fresh full-policy rollout.
- Promoted `action_pose_relation` to `2.0.0` with a targeted chasing focal
  action anchor, preservation checks, and reducer-best fallback. No protocol,
  memory, score, or SFT semantics changed.
- Added a resumable experiment runner, deterministic strategy composition and
  summaries, unit coverage, and the verb experiment report.
- Completed two fresh GPT-5.5 Teacher multi-round trajectories on preselected
  `chasing` failures. Both autonomously retrieved
  `action_pose_relation@2.0.0`.
- Improved the paired submitted result from 11/13 to 12/13 atoms, 0/2 to 1/2
  verb passes, and 0/2 to 1/2 all-pass episodes, using nine images versus the
  historical ten. `phase3_ep_098` reached 5/5; `phase3_ep_014` tied at 7/8
  and still failed chasing.
- Tested and rejected an experiment-only forced verb-route closure: it made
  `phase3_ep_098` all-pass in three images but regressed `phase3_ep_014` to
  5/8. The production Teacher remains v8.
- Added deterministic audits, trajectory analyses, a machine-readable paired
  comparison, and the multi-round pilot report.
- Froze the complete 12-episode official-current verb-nonpass cohort and ran a
  fresh two-HCU multi-round Production-A control plus Candidate-B experiment.
- On the ten primary episodes, Candidate B improved 54/71 to 56/71 atoms,
  0/10 to 3/10 verb passes, and mean GM 27.70 to 31.97 with the same 50 image
  attempts. Across all twelve, it improved Production A from 66/84 and 1/12
  verbs to 67/84 and 4/12.
- Promoted `action_pose_relation@2.1.0` with typed chasing, playing-with, and
  jumping-over action topologies, explicit no-storyboard/no-role-reversal
  constraints, and verb-pass preservation during peripheral repairs.
- Promoted
  `teacher_system_prompt_v8_1_verb_evidence_retention`: action-pose retrieval
  now occurs after evaluated verb failure/uncertainty, and a same-count
  historical verb-pass source may be used for local non-verb repair.
- Verified delayed retrieval in 12/12 Candidate-B episodes versus pre-image
  retrieval in 12/12 Production-A episodes. `phase3_ep_135` branched from a
  historical verb-pass source after reducer-best regressed the verb and
  recovered reducer-best to verb-pass evidence.
- Added failed-12 rollout audits, trajectory analyses, a machine-readable
  comparison, and the multi-round A/B report. No action schema, reducer,
  score, memory, or SFT semantics changed.

## 2026-07-30

- Completed all 200 fixed fresh trajectories with 684 evaluated images; the
  continuous first pass closed 198 and a pending-only resume closed the final
  two without rerunning any valid trajectory.
- Improved submitted atom pass from 1159/1419 to 1301/1419, Soft-TIFA AM from
  81.87 to 90.90, Soft-TIFA GM from 42.58 to 73.50, and all-pass trajectories
  from 51/200 to 111/200.
- Recorded final easy/medium/hard and atom-type results. Count gained 92 atoms
  and attribute gained 40; verb remained weakest at 10/22, including chasing
  at 2/12.
- Separated 162 v7-only, 37 v8-only, and one mixed-resume trajectory. v8-only
  produced zero equivalent failed-route repeats across 32 closure
  opportunities; this is descriptive mechanism evidence only.
- Reconciled final SFT supervision to 663 canonical targets and 496
  context-only records with no mask, canonical-target, profile,
  context/score-contract, or prompt-split violation.
- Added the final 200-trajectory report and a real v8 round-by-round Planner
  I/O walkthrough for `phase3_ep_176`.
- Recorded GPT-5.6 Sol's final verdict `PASS_FINAL`: no blocker remains and the
  dataset may proceed to the next SFT supervision gate.
- Completed the checkpoint-180 light audit: the 20-trajectory increment used
  64 evaluated images, improved submitted atom pass from 109/130 to 122/130,
  improved Soft-TIFA GM from 49.10 to 80.41, and produced 13/20 all-pass
  submissions with zero submitted-to-peak GM gap.
- Separated five v7 and 15 v8 trajectories by persisted Teacher system-prompt
  version. Across six v8 post-regression/strict-no-progress opportunities,
  zero subsequent actions repeated the same action/source/target tuple.
- Recorded GPT-5.6 Sol's checkpoint-180 verdict `PASS_CONTINUE_QUEUE`: the v8
  evidence supports retry-closure mechanism consistency, not causal
  performance improvement.
- Predeclared the final checkpoint-200 cohort as all fixed IDs 1-200 with no
  completion-conditioned substitution.
- Completed the checkpoint-160 light audit: the 10-trajectory increment used
  38 evaluated images, improved submitted atom pass from 55/70 to 61/70,
  improved Soft-TIFA GM from 34.18 to 59.44, and produced 4/10 all-pass
  submissions.
- Separated the increment into seven v7 and three v8 trajectories by persisted
  Teacher system-prompt version. The three v8 trajectories provide only early
  compatibility evidence, not an aggregate performance claim.
- Recorded GPT-5.6 Sol's checkpoint-160 verdict `PASS_CONTINUE_QUEUE`; missing
  closure-rejection coverage is an evidence gap rather than a blocker.
- Predeclared checkpoint-180 quality, fixed-admission, and Teacher-version
  cohorts before checkpoint completion.
- Completed the checkpoint-150 deep audit: the 10-trajectory increment used 38
  evaluated images, improved submitted atom pass from 51/66 to 61/66,
  improved Soft-TIFA GM from 32.50 to 76.17, and produced 6/10 all-pass
  submissions.
- Reconciled cumulative checkpoint-150 SFT supervision: 490 canonical targets
  and 357 context-only records, with no masking, canonical-target, profile,
  context/score-contract, or prompt-split violation.
- Froze checkpoint 150 as the final all-v7 baseline, predeclared checkpoint
  160, and required future v8 evidence to be grouped by persisted Teacher
  system-prompt version.
- Recorded GPT-5.6 Sol's checkpoint-150 verdict `PASS_CONTINUE_QUEUE`; v8
  continues unchanged and asynchronous admission remains valid under frozen
  cohort boundaries.
- Completed the checkpoint-140 quality audit: the 20-trajectory increment used
  79 evaluated images, improved submitted atom pass from 124/148 to 135/148,
  improved Soft-TIFA GM from 30.63 to 58.59, and produced 7/20 all-pass
  submissions.
- Recorded the fixed ID 121-140 admission snapshot with 18 completed, two
  active, and zero failed episodes.
- Recorded GPT-5.6 Sol's checkpoint-140 verdict
  `PASS_WITH_PROSPECTIVE_CHANGE`: no validity blocker was found, but the 23/79
  regressive-action concentration required a forward-only retry closure
  policy.
- Added Teacher policy v8 and runtime checks that reject an identical
  action/source/target retry after regression or strict no-progress, default
  edits to reducer-best, and require relevant constraint-pass evidence before
  editing from another historical source.
- Kept Action Protocol 0.5, PlannerContext 0.6, the score policy, execution
  profile, completed trajectories, and SFT ownership unchanged; post-change
  evidence is separated by persisted Teacher system-prompt version.
- Validated the v8 policy with 79 contract tests, 133 unit tests, 12 schemas,
  104 fixture records, and the deterministic historical replay.
- Completed the checkpoint-50 boundary with 50/50 valid submissions and 148
  evaluated images: submitted atom pass 339/361, Soft-TIFA GM 82.02, and
  35/50 all-pass episodes.
- Recorded GPT-5.6 Sol's checkpoint-50 verdict
  `PASS_WITH_PROSPECTIVE_CHANGE`; no rollout blocker was found.
- Reconciled cumulative 1-50 supervision: 164 canonical SFT dry-run targets,
  117 context-only records, and no mask, profile, score-contract, or
  prompt-split violation.
- Started the continuous 51-200 queue with 16 logical workers, eight Teacher
  slots, interleaved HCU assignment, asynchronous audits, and five-second
  resource sampling.
- Completed and audited episodes 51-60: 36 evaluated images, submitted atom
  pass 63/69, Soft-TIFA GM 75.00, and zero submitted-to-peak GM gap.
- Recorded GPT-5.6 Sol's checkpoint-60 verdict `PASS_CONTINUE_QUEUE`.
- Measured the continuous queue at 5.92/8 mean active HCUs with 16 workers
  always present and no all-idle sample through checkpoint 60.
- Audited a completion-conditioned checkpoint-80 cohort: 55 evaluated images,
  submitted atom pass 126/131, Soft-TIFA GM 81.33, and 15/20 all-pass
  episodes.
- Recorded GPT-5.6 Sol's checkpoint-80 verdict
  `PASS_WITH_PROSPECTIVE_CHANGE`: completion-order quality evidence remains
  valid but cannot estimate admitted-work incident rates.
- Predeclared checkpoint-100 completed-quality and fixed admission-status
  cohorts so pending, failed, active, and completed work use an explicit
  denominator.
- Completed the checkpoint-100 deep audit: 100 valid quality trajectories,
  307 evaluated images, submitted atom pass 666/713, Soft-TIFA GM 78.71, and
  67/100 all-pass episodes.
- Recorded the fixed ID 61-100 admission snapshot with 36 completed, one
  failed-unsubmitted, and three active episodes.
- Reconciled 100-trajectory SFT supervision to 328 canonical targets and 226
  context-only records with all mask and contract invariants passing.
- Recorded GPT-5.6 Sol's final checkpoint-100 verdict `PASS_CONTINUE_QUEUE`;
  the reviewer withdrew an initial routing blocker after reading accepted
  ADR-0006.
- Completed checkpoint 120 with a 20-trajectory quality increment: 65
  evaluated images, submitted atom pass 123/136, Soft-TIFA GM 76.37, and zero
  submitted-to-peak GM gap.
- Recorded the fixed ID 101-120 admission snapshot with 16 completed and four
  active episodes, then recorded Sol's `PASS_CONTINUE_QUEUE` light review.
- Predeclared checkpoint-140 quality and fixed ID 121-140 admission cohorts.
- Completed and audited the first 40 fresh 8-HCU official-mix trajectories:
  121 evaluated images, submitted atom pass 278/296, Soft-TIFA GM 82.45, and
  27/40 all-pass episodes.
- Corrected post-hoc supervision labeling to use the frozen pass-count/GM
  ordering, so equal-pass GM improvements are not mislabeled ineffective.
- Recorded GPT-5.6 Sol checkpoint verdicts `PASS_CONTINUE` at 20 and
  `PASS_CONTINUE_QUEUE` at 40.
- Added a continuous global episode queue for 51-200 with two workers per HCU,
  atomic durable stop admission, canonical submitted-only skipping, five-pass
  pending-only retry, interleaved device assignment, and scheduler provenance.
- Added deterministic Flow-DPPO selection that exactly matches the official
  GenEval2 atomicity marginal: 25 prompts for every `atom_count` from 3
  through 10, with easy/medium/hard explicitly labeled as local reporting
  tiers.
- Soft-balanced skill coverage toward the official aggregate, excluded the
  official exact/family boundary and all 20 prior source rows, persisted the
  actual VQA-count histogram, and added same-input determinism tests.
- Froze 200 unique prompts under selection SHA
  `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`
  and locked the SHA into the batch summary and each episode rollout plan.
- Prepared 200 fresh PlannerContext v0.6 / `qwen_dual_backend@1` rollout
  directories and recorded 2/4/8-card execution estimates.
- Recorded GPT-5.6 Sol's focused data-distribution verdict: `PASS`.
- Launched the resumable 200-trajectory queue from commit `3a6ef8f` with one
  fixed sequential episode worker on each of two HCUs.
- Completed five fresh `qwen_dual_backend@1` / PlannerContext v0.6
  trajectories with 25 local 1024 x 1024 images and complete Geneval2
  evaluation.
- Used one sequential episode worker per HCU, parallelized independent
  episodes across two cards, and completed without OOM or rerunning submitted
  trajectories.
- Corrected the runtime mismatch that unconditionally rejected a second novel
  `query_skill`: each image-producing Round now permits at most two successful
  novel Skill queries and idempotently resumes a validated query missing its
  tool response.
- Extended rollout auditing for dynamic execution-profile provenance,
  PlannerContext v0.6 score visibility, corrected current-validator
  classification, and subset selection by prompt ID.
- Added deterministic paired comparison reporting with per-Attempt
  action/source/backend/outcome tables, GM tie-break updates, pass-first
  rejections, rollbacks, and post-initial regenerations.
- Recorded the matched result: submitted atom pass 39/50 to 40/50, GM 19.70 to
  18.32, and AM 77.68 to 77.33. Four pairs improved under hierarchical
  ordering; one easy verb/count pair regressed.
- Added a real v0.6 Round-by-Round walkthrough for `phase3_ep_012` and recorded
  GPT-5.6 Sol's final `PASS` for the bounded claim "mechanistically positive
  but performance-mixed."
- Accepted ADR-0007 and added PlannerContext v0.6 while keeping Action Protocol
  v0.5 unchanged.
- Added the environment-owned
  `geneval2_soft_tifa_gm@flow_dppo_v1` aggregate with one shared deterministic
  implementation and exact event recomputation.
- Changed new-episode best selection to higher pass-count, then higher GM, then
  earlier Attempt; historical scoreless episodes retain legacy replay order.
- Added latest/best GM, source-aware round GM delta, score-policy resume locks,
  and homogeneous temporal-prefix-verified SFT export.
- Reprepared the five matched dual-backend and five edit-only diagnostic
  scaffolds with PlannerContext v0.6 and the explicit score policy; no live
  model or evaluator calls were made.
- Recorded GPT-5.6 Sol's final `APPROVE` after numeric, comparator, delta,
  policy-lock, and SFT leakage amendments.

## 2026-07-29

- Accepted ADR-0006 and introduced independently versioned
  `qwen_dual_backend@1` execution while keeping Planner Action and
  PlannerContext schemas at v0.5.
- Routed source-free `generate_image` to local Qwen-Image-2512 and
  source-conditioned `edit_image` to local Qwen-Image-Edit-2511 without adding
  backend, model, or mode fields to the SFT target.
- Added complete profile/model/pipeline/sampling/source/output provenance,
  profile-locked resume, trajectory validation, and homogeneous-profile SFT
  export enforcement.
- Retained the legacy edit-only configuration as historical provenance; old
  trajectories and completed artifacts were not rewritten.
- Froze five diagnostic Flow-DPPO prompts with known legacy failure modes and
  prepared matched fresh dual-profile and edit-only run directories without
  making live model or evaluator calls.
- Recorded GPT-5.6 Sol's final `APPROVE` after its requested execution-profile,
  provenance, resume, SFT-separation, and matched-comparison amendments.

## 2026-07-27

- Added optional loading of Git-ignored `.env.teacher.local` credentials while
  preserving shell-export precedence.
- Added a resumable, sanitized GPT-5.5 teacher-only A/B pilot for bounded
  `decision_summary` supervision across five fixed PlannerContext cases.
- Recorded the final Sol verdict `FAIL_KEEP_V05`: two broad-failure
  regeneration summaries did not justify generate-over-edit selection, so the
  canonical v0.5 action schema remains unchanged.
- Added deterministic hard-heavy selection of 20 Flow-DPPO Geneval2 synthetic
  training prompts while excluding the official 800-row test set and
  overlapping semantic families.
- Added a two-device rollout scheduler with one child per physical HCU,
  serialized local model loading, failure isolation, and resumable
  image/evaluator/memory/RoundRecord/context suffix recovery.
- Completed 20 native PlannerContext v0.5 trajectories with 92 local
  1024 x 1024, 40-step Qwen-Image-Edit attempts and complete Geneval2 atom
  evaluation.
- Added batch closure/future-leakage auditing, cross-trajectory analysis, and a
  readable complete-success trace for `phase3_ep_011`.
- Corrected SFT candidate reporting so `query_skill` remains loss 0 and only
  positive/recovery native v0.5 generate/edit/submit actions are candidates.
- Made SFT request indexing deduplicate only identical interrupted retries and
  reject conflicting duplicate request IDs.
- Completed a v0.5 SFT export dry run with 59 loss-bearing targets and 105
  context-only records.
- Recorded the final GPT-5.6 Sol Gate 4 verdict `PASS`.
- Added a consolidated Planner I/O v0.5 architecture document separating Agent
  input/action fields from environment-owned updates and records.
- Added a native v0.5 round-by-round walkthrough for Flow-DPPO
  `phase3_ep_011`, including Skill retrieval, an ineffective edit, a branch
  from historical best, and the all-pass submission.
- Extended the 20-trajectory validation report with deterministic difficulty
  rules, five real strategy case studies, and Flow-DPPO-compatible Geneval2
  Soft-TIFA GM for first, submitted, and peak attempts.
- Added Geneval2 Soft-TIFA AM as the reproducible atom-level continuous metric;
  the 20-trajectory first-to-submitted result is 69.38 to 84.70 (+15.32).

## 2026-07-26

- Added Planner Action Protocol v0.5 with one strict action and a shared
  `instruction` field for generate/edit actions.
- Removed `decision_summary`, `diagnosis_summary`, and legacy planning fields
  from canonical v0.5 image actions.
- Added PlannerContext v0.5 with `latest_attempt`,
  `last_completed_image_round`, `prior_image_rounds`, and deduplicated
  `best_attempt` state.
- Kept nested v0.2-v0.4 actions valid in historical event envelopes while
  making v0.5 the default parser/runtime protocol.
- Changed v0.5 SFT supervision so `query_skill` remains a real action with loss
  0 until Skill utility is validated.
- Upgraded count-edit and local-preservation Skills, added action-pose and
  object-identity Skills, and deprecated overlapping placeholder IDs.

## 2026-07-14

- Added the v0.2 artifact manifest schema for environment-owned artifact refs.
- Tightened the v0.2 episode event schema with payload contracts for canonical
  actions, skill returns, image execution, Geneval2 observations, reducer output,
  submission, and invalid-action observations.
- Tightened the v0.2 planner view schema so planner-visible image references,
  attempts, transitions, tool manifests, and skill manifests are structured and
  exclude raw model output text.
- Addressed Gate 1 requested changes:
  - `action_validated` and `task_created` event payloads now reference the
    canonical action and TaskSpec schemas directly.
  - image execution start/completion payloads are separated, with completed
    events requiring replayable attempt and artifact identity fields.
  - generate execution payloads cannot carry source attempts; edit payloads must
    carry source attempts.
  - `skill_returned` payloads require a query action reference.
  - semantic trajectory validation rejects duplicate constraint IDs, duplicate
    artifact IDs, duplicate per-attempt Geneval2 observations, unknown edit
    sources, and mismatched or unlinked skill returns.
- Addressed Gate 1 second-cycle requested changes:
  - trajectory validation now requires a single episode identity, a first
    `task_created` event, and matching envelope/TaskSpec episode IDs.
  - actions before `task_created` are rejected.
  - image starts must reference exactly one validated image action.
  - image completions must match a prior start by request ID and reference that
    start event.
  - image artifact IDs and Geneval2 results are unique per trajectory/attempt.
- Addressed the user-authorized extra Gate 1 correction cycle:
  - image execution start events can no longer declare attempt lineage fields,
    so completion events are the single source for attempt/parent IDs.
  - each `query_skill` action can have at most one `skill_returned` event.
  - each `geneval2_completed` event must cover every TaskSpec constraint exactly
    once.
  - each `attempt_submitted` event must link to a validated `submit_attempt`
    action with matching selected attempt and reason code.
