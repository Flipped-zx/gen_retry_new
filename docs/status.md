# Status

## Current Phase

The official-atomicity-matched Flow-DPPO 200-trajectory batch has restarted
from 200 empty episode states under
`runs/phase7_flow_dppo200_fresh8_v1`. Eight fixed HCU workers are processing
the batch in tmux session
`gen_retry_fresh8_001_020`. The frozen pool still has 25 prompts for every
`atom_count` from 3 through 10; local reporting tiers are 75 easy, 75 medium,
and 50 hard. The earlier interrupted run root remains untouched and is not
reused. Checkpoints use a 20-episode light audit and a 50-episode GPT-5.6 Sol
deep review, overlapped with subsequent generation unless a blocking issue is
found. Range 1-20 uses eight logical workers; later ranges use the Sol-reviewed
Teacher/GPU overlap profile with sixteen logical episode workers, eight
Teacher slots, and one complete local GPU stage per physical HCU.
Episodes 1-40 are complete and passed deterministic audit plus Sol light
reviews. Episodes 41-50 are running under the overlap profile. Sol approved a
continuous global queue for episodes 51-200 with the same hard concurrency
limits, durable admission stop, canonical resume, and five-pass retry bound.

## Gate State

- Gate 1 Protocol Freeze: APPROVED after user-authorized extra final correction cycle
- Gate 2 Five-Trajectory Pilot Review: APPROVED
- Gate 3 SFT Supervision Freeze: APPROVED
- PlannerContext / Round Memory final review: APPROVED
- Planner I/O v0.5 Sol amendment: IMPLEMENTED
- Gate 4 Flow-DPPO 20-Trajectory Final Review: PASS
- Qwen dual-backend execution-profile review: APPROVE
- PlannerContext v0.6 score-policy review: APPROVE
- v0.7 / PlannerContext v0.6 five-trajectory final review: PASS
- Flow-DPPO 200 official-mix distribution review: PASS
- Flow-DPPO fresh-8 checkpoint 20 light review: PASS_CONTINUE
- Flow-DPPO fresh-8 checkpoint 40 / continuous queue review:
  PASS_CONTINUE_QUEUE
- Muse Image-informed ablation claim-sufficiency review:
  PASS_WITH_REQUIRED_CHANGES (not a protocol gate)

## Protocol

- Current action protocol: v0.5 for new rollout/SFT records; v0.2-v0.4 remain valid historical event schemas.
- Current planner input: `PlannerContext` v0.6 for new score-policy episodes;
  v0.4/v0.5 remain historical replay modes.
- Live APIs run: yes
- Teacher policy: GPT-5.5 through `TEACHER_API_KEY` and `TEACHER_BASE_URL`
- Current image execution profile: `qwen_dual_backend@1`
- `generate_image`: local Qwen-Image-2512 direct runtime, source-free root Attempt
- `edit_image`: local Qwen-Image-Edit-2511 direct runtime, declared-source child Attempt
- Backend/model/mode remain environment-owned and are not Planner/SFT fields
- New score policy: higher atom pass-count, then higher
  `geneval2_soft_tifa_gm@flow_dppo_v1`, then earlier Attempt
- Geneval2 score and score deltas are environment/context-only, never Action fields
- Rendering quality baseline: `docs/operations/qwen_rendering_quality_baseline.md`
- External roots configured: yes
- Active completion record: `docs/checkpoints/phase4_sft_supervision_freeze.md`

## Completed Deliverables

- Phase 0 repository archaeology complete.
- Phase 1 protocol implementation and Gate 1 approval complete.
- Phase 2 deterministic mock replay runtime complete.
- Phase 3 offline prerequisites complete:
  - legacy diagnostic/action counterfactual analysis;
  - fresh Geneval2 candidate pool from 800 prompt rows;
  - exactly ten high-difficulty, constraint-balanced prompt selections;
  - ten prepared fresh-start rollout directories.
- Phase 3 live preflight complete:
  - teacher credentials were visible as SET without printing values;
  - GPT-5.5 teacher smoke test passed;
  - local Qwen-Image-Edit model path existed;
  - `provider=local` adapter used direct local inference, not an HTTP endpoint;
  - generation, edit, and Geneval2 atom-normalization smoke tests passed.
- Future live rendering policy updated:
  - default rollout rendering is 40 steps at 1024 x 1024;
  - standalone image smoke is disabled by default;
  - if rendering parameters are uncertain, use `docs/operations/qwen_rendering_quality_baseline.md` and the Gen-Searcher/GenEvolve evidence in `docs/SOURCE_LEDGER.md`.
- Additional high-quality live batch `runs/phase3_hq5/` is partially complete:
  - valid submitted trajectories: `phase3_ep_001`, `phase3_ep_002`, `phase3_ep_003`;
  - partial, not countable: `phase3_ep_004`;
  - prepared only: `phase3_ep_005`;
  - current interruption/resume details: `docs/operations/phase3_hq5_interruption_status.md`.
  - completed trajectory behavior analysis: `docs/phase3/hq5_completed_trajectory_behavior_analysis.md`;
  - readable GenSearcher-style trace for the recommended example: `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md`.
- Phase 3 ten fresh live trajectories complete:
  - ten valid submitted trajectories under `runs/phase3/`;
  - 49 image attempts evaluated with Geneval2;
  - smoke tests and one archived invalid infrastructure run excluded from Phase 3 episode counts.
- Phase 3 post-hoc analysis complete:
  - `docs/phase3/ten_trajectory_comparison.md`
  - `docs/phase3/behavior_coverage_report.md`
  - `docs/phase3/legacy_vs_fresh_strategy_analysis.md`
  - `docs/phase3/sft_candidate_action_report.md`
  - `artifacts/phase3/trajectory_index.json`
  - `artifacts/phase3/action_supervision_labels.jsonl`
- Flow-DPPO official-mix 200-prompt batch prepared:
  - exact official atomicity marginal: 25 prompts for every `atom_count`
    from 3 through 10;
  - local reporting tiers: easy=75, medium=75, hard=50;
  - official 800 prompts and conservative semantic-family overlaps remain
    held out;
  - all 20 earlier Flow-DPPO source rows are excluded;
  - frozen selection SHA:
    `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`;
  - 200/200 fresh v0.6 dual-backend rollout directories prepared;
  - selection report:
    `docs/phase7/flow_dppo200_official_mix_selection_report.md`;
  - parallel run plan and 2/4/8-card estimates:
    `docs/operations/phase7_flow_dppo200_parallel_run.md`;
  - final focused Sol review:
    `docs/reviews/flow_dppo200_official_mix_sol_review.md` (`PASS`).
- Flow-DPPO official-mix fresh 8-HCU execution:
  - 200 new empty PlannerContext v0.6 / `qwen_dual_backend@1` episode
    directories prepared under `runs/phase7_flow_dppo200_fresh8_v1`;
  - no old image, Attempt, evaluator result, or submission was imported;
  - range 1-20 completed with 20/20 valid submissions, 52 image attempts, and
    52 complete Geneval2 evaluations;
  - submitted atom pass improved from 125/144 to 141/144; Soft-TIFA AM from
    85.32 to 96.05; Soft-TIFA GM from 53.95 to 89.89;
  - 17/20 reached all atoms and submitted-to-peak GM gap was 0.00;
  - checkpoint-20 audit:
    `docs/phase7/checkpoints/fresh8_v1_ckpt_020_audit.md` (`PASS`);
  - checkpoint-20 Sol light review:
    `docs/reviews/phase7_fresh8_ckpt_020_sol_review.md`
    (`PASS_CONTINUE`);
  - range 21-40 completed with 20/20 valid submissions and 69 evaluated image
    attempts;
  - range 21-40 submitted atom pass improved from 125/152 to 137/152,
    Soft-TIFA AM from 82.37 to 90.88, and Soft-TIFA GM from 42.44 to 75.01;
  - cumulative 1-40 submitted atom pass is 278/296 and GM is 82.45, with 27/40
    all-pass episodes;
  - checkpoint-40 cumulative audit:
    `docs/phase7/checkpoints/fresh8_v1_ckpt_040_cumulative_audit.md`
    (`PASS`);
  - checkpoint-40 Sol review:
    `docs/reviews/phase7_fresh8_ckpt_040_continuous_queue_sol_review.md`
    (`PASS_CONTINUE_QUEUE`);
  - range 41-50 completed with 10/10 valid submissions and 27 evaluated image
    attempts; submitted atom pass improved from 56/65 to 61/65 and Soft-TIFA
    GM from 56.46 to 80.33;
  - cumulative 1-50 submitted atom pass is 339/361 and GM is 82.02, with 35/50
    all-pass episodes and a submitted-to-peak GM gap of 0.63;
  - checkpoint-50 cumulative audit:
    `docs/phase7/checkpoints/fresh8_v1_ckpt_050_cumulative_audit.md`
    (`PASS`);
  - checkpoint-50 Sol deep review:
    `docs/reviews/phase7_fresh8_ckpt_050_sol_review.md`
    (`PASS_WITH_PROSPECTIVE_CHANGE`, cumulative SFT reconciliation completed);
  - cumulative SFT dry-run reconciliation emitted 164 canonical targets,
    retained 117 context-only records, and passed all mask and contract
    invariants:
    `docs/phase7/checkpoints/fresh8_v1_ckpt_050_sft_reconciliation.md`;
  - range 51-60 completed with 10/10 valid submissions and 36 evaluated image
    attempts; submitted atom pass improved from 53/69 to 63/69 and Soft-TIFA
    GM from 32.52 to 75.00;
  - cumulative 1-60 submitted atom pass is 402/430 and GM is 80.85, with 41/60
    all-pass episodes;
  - checkpoint-60 Sol light review:
    `docs/reviews/phase7_fresh8_ckpt_060_sol_review.md`
    (`PASS_CONTINUE_QUEUE`);
  - continuous-queue startup resource evidence averaged 5.92/8 active HCUs
    with 16 workers always present and no all-idle sample:
    `docs/phase7/checkpoints/fresh8_v1_queue_start_to_ckpt_060_resource_profile.md`;
  - checkpoint-80 completion-conditioned cohort passed with 20/20 valid
    submissions, submitted atom pass 126/131, Soft-TIFA GM 81.33, and 15/20
    all-pass episodes;
  - checkpoint-80 Sol light review:
    `docs/reviews/phase7_fresh8_ckpt_080_sol_review.md`
    (`PASS_WITH_PROSPECTIVE_CHANGE`);
  - completion-order selection is explicitly qualified as unsuitable for
    representative incident-rate claims:
    `docs/phase7/checkpoints/fresh8_v1_ckpt_080_scope_note.md`;
  - checkpoint 100 prospectively separates a completed quality cohort from the
    fixed ID 61-100 admission-status denominator:
    `artifacts/phase7/checkpoints/fresh8_v1_ckpt_100_predeclared_cohorts.json`;
  - checkpoint-100 completed-quality cohort passed with 100/100 valid
    trajectories and 307 evaluated images; submitted atom pass is 666/713,
    Soft-TIFA GM is 78.71, and 67/100 episodes are all-pass;
  - fixed ID 61-100 admission snapshot recorded 36 completed, one
    failed-unsubmitted, three active, and zero not-yet-admitted episodes:
    `docs/phase7/checkpoints/fresh8_v1_ckpt_100_admission_status.md`;
  - cumulative checkpoint-100 SFT reconciliation emitted 328 targets, retained
    226 context-only records, and passed all mask and contract invariants;
  - checkpoint-100 Sol deep review:
    `docs/reviews/phase7_fresh8_ckpt_100_sol_review.md`
    (`PASS_CONTINUE_QUEUE`; an initial routing blocker was withdrawn after the
    reviewer read accepted ADR-0006);
  - checkpoint-120 completed-quality increment passed with 20/20 valid
    trajectories and 65 evaluated images; submitted atom pass improved from
    111/136 to 123/136 and Soft-TIFA GM from 53.10 to 76.37;
  - cumulative 120-trajectory quality is 789/849 submitted atoms, GM 78.32,
    and 78/120 all-pass episodes;
  - fixed ID 101-120 admission snapshot recorded 16 completed and four active
    episodes, with no failed or unadmitted episode;
  - checkpoint-120 Sol light review:
    `docs/reviews/phase7_fresh8_ckpt_120_sol_review.md`
    (`PASS_CONTINUE_QUEUE`);
  - one global continuous queue for episodes 51-200 is active, with checkpoint
    audits running asynchronously;
  - the continuous queue preserves two workers per HCU, eight Teacher slots,
    physical-HCU and episode locks, and adds atomic stop-admission checks plus
    canonical pending-only retries;
  - checkpoint audit supports explicit episode subsets and inclusive ranges;
  - prospective 2-workers-per-HCU scheduling is protected by physical-HCU,
    scheduler, and episode locks, bounded Teacher slots, atomic image writes,
    and scheduler provenance;
  - concurrency review:
    `docs/reviews/phase7_api_gpu_overlap_sol_review.md`
    (`APPROVE_WITH_REQUIRED_CHANGES`, implemented);
  - run and 20-light/50-deep review policy:
    `docs/operations/phase7_flow_dppo200_fresh8_run.md`.
- Gate 2 review approved in `docs/reviews/gate2_five_trajectory_pilot_review.md`.
- Phase 4 SFT supervision freeze complete:
  - `docs/decisions/ADR-0005-sft-supervision-freeze.md`
  - `docs/phase4/sft_supervision_freeze.md`
  - `docs/checkpoints/phase4_sft_supervision_freeze.md`
  - `artifacts/phase4/sft_supervision_policy.json`
  - `artifacts/phase4/sft_dry_run_decisions.jsonl`
  - `artifacts/phase4/sft_dry_run_records.jsonl`
  - `artifacts/phase4/sft_split_manifest.json`
  - `artifacts/phase4/sft_dry_run_audit.json`
- Gate 3 review approved in `docs/reviews/gate3_sft_supervision_freeze_review.md`.
- Skill-v1 validation run complete:
  - activated four non-placeholder Skill files under `skills/`;
  - completed one fresh 40-step, 1024 x 1024 validation trajectory under `runs/skill_v1_validation_policyfix/phase3_ep_001`;
  - produced 5 image attempts, 5 Geneval2 evaluations, and a valid best-so-far submission;
  - readable trace: `docs/skills/validation/trajectory_trace_skill_v1_policyfix_ep_001.md`;
  - validation analysis: `docs/skills/validation/SKILL_V1_VALIDATION_ANALYSIS.md`;
  - fixed live resume handling for interrupted `image_execution_started` events before continuing the run.
- Gate 3a Skill-v1 validation Sol review complete:
  - review: `docs/reviews/gate3a_skill_v1_validation_sol_review.md`;
  - verdict: `REQUEST_CHANGES`;
  - Sol accepted retrieval mechanics and trace format, but not Skill-v1 utility;
  - `query_skill` remains context-only for SFT;
  - next required validation is one capability-isolated attribute/local-preservation episode with at least one targeted fix and no preserved-atom regression.
- Gate 3a Skill-v1 trace/I/O clarity review complete:
  - review: `docs/reviews/gate3a_skill_v1_trace_io_clarity_review.md`;
  - verdict: `APPROVE` for foundational Skill trace/I/O clarity;
  - this approval is scoped to clear PlannerView/action/tool/evaluator input-output structure, not downstream repair utility.
- PlannerContext / Planning Round / Episode Memory upgrade complete:
  - action schema: `schemas/action_protocol_v0_3.schema.json`;
  - planner input schema: `schemas/planner_context_v0_3.schema.json`;
  - deterministic builder: `src/gen_retry/runtime/planner_context.py`;
  - live runner integration: `src/gen_retry/phase3/live_runner.py`;
  - `strategy_tags` removed from v0.3 actions and replaced by `interventions[].operation`;
  - `query_skill`, `generate_image`, `edit_image`, and `submit_attempt` are explicit Planner Actions;
  - `query_skill` is part of the active Planning Round and does not create an Attempt;
  - completed RoundRecords align query actions, image action plan, final prompt, result attempt, source-based outcome, best/latest update, and value;
  - edit transition comparison uses the action's `source_attempt_id`, not latest by default;
  - new live trajectory: `runs/planner_context_v0_3/phase3_ep_001`;
  - persisted RoundRecords: `runs/planner_context_v0_3/phase3_ep_001/round_records/`;
  - readable trace: `docs/phase3/trajectory_trace_planner_context_v0_3_ep_001.md`;
  - new/old comparison: `docs/phase3/planner_context_round_memory_comparison.md`;
  - design: `docs/phase3/planner_context_round_memory_design.md`;
  - final 5.6sol review: `docs/reviews/planner_context_round_memory_final_review.md` (`PASS`).
- Planner I/O v0.4 migration progress:
  - source of truth: `gen_retry_planner_io_v04_codex_reference.md`;
  - action schema: `schemas/action_protocol_v0_4.schema.json`;
  - planner input schema: `schemas/planner_context_v0_4.schema.json`;
  - teacher prompt, provider schema, parser, reference validation, replay builder, and SFT renderer default to v0.4;
  - PlannerContext exposes only `task_context`, `latest_observation`, `skill_context`, `episode_memory`, and `runtime_state`;
  - visible latest/best image bindings are passed outside PlannerContext;
  - normalized v0.4 replay trace: `docs/phase3/trajectory_trace_planner_io_v0_4_phase3_ep_001.md`;
  - Sol review: `docs/reviews/planner_io_v04_sol_review.md`.
- Planner I/O v0.5 field/SFT review:
  - Sol review request: `docs/reviews/planner_io_v05_field_sft_review_request.md`;
  - Sol review summary: `docs/reviews/planner_io_v05_field_sft_review.md`;
  - proposed v0.5 field packet: `docs/phase3/planner_io_v05_field_design_packet.md`;
  - real-trajectory round/memory walkthrough: `docs/phase3/planner_io_v05_round_memory_walkthrough_phase3_ep001.md`;
  - result: v0.4 is a usable base, but v0.5 must clarify latest/last/best semantics, update ADR/schema consistency, and ensure display JSON is not used as trainable SFT data.
- Planner I/O v0.5 implementation:
  - action schema: `schemas/action_protocol_v0_5.schema.json`;
  - planner input schema: `schemas/planner_context_v0_5.schema.json`;
  - canonical generate/edit actions use only target/preserve IDs, edit source
    when applicable, and one executable `instruction`;
  - Sol-rejected `decision_summary` and `diagnosis_summary` are absent from
    canonical v0.5 actions rather than required with zero loss;
  - PlannerContext uses `latest_attempt`, `last_completed_image_round`,
    `prior_image_rounds`, and a reference-only best record when best equals latest;
  - parser, provider schema, teacher contract, live runner, instruction quality,
    replay/trace helpers, and SFT renderer default to v0.5;
  - `query_skill` remains a canonical Planner Action but is context-only with
    loss 0 under v0.5 SFT supervision;
  - event envelopes and fixture validation retain v0.2-v0.4 action compatibility.
- Skill catalog v0.5:
  - `counting_and_instance_layout` and `local_edit_preservation` upgraded to v2;
  - static-only `spatial_relation_layout` upgraded to v2;
  - `action_pose_relation` and `object_identity_presence` added at v1;
  - overlapping placeholder IDs are deprecated and excluded from the default manifest;
  - LocalSkillStore versions and content hashes are checked against the manifest.
- Geneval2 skill coverage review:
  - report: `docs/skills/geneval2_skill_coverage_review.md`;
  - missing skill content proposal: `docs/skills/geneval2_missing_skill_content_proposal_sol.md`;
  - result: current four real skills partially cover Geneval2 but do not yet justify positive `query_skill` SFT targets.
- Flow-DPPO 20-trajectory batch:
  - selected 12 hard, 5 medium, and 3 easy prompts from the UniRL Flow-DPPO
    Geneval2 synthetic training split;
  - excluded the official 800-row test set and deterministic overlapping
    semantic families;
  - completed 20/20 fresh native v0.5 trajectories with 92 local
    Qwen-Image-Edit images and 92 complete Geneval2 evaluations;
  - aggregate atom pass improved from 137/200 on first attempts to 171/200 on
    best attempts; 4/20 trajectories reached all atoms;
  - deterministic validation:
    `docs/phase5/flow_dppo20_validation_report.md`;
  - explicit Agent input/action/environment field architecture:
    `docs/phase5/planner_io_v05_agent_environment_architecture.md`;
  - representative native v0.5 round/memory walkthrough:
    `docs/phase5/planner_io_v05_round_memory_walkthrough_flow_dppo_ep011.md`;
  - final analysis:
    `docs/phase5/flow_dppo20_final_analysis.md`;
  - representative actual trace:
    `docs/phase5/flow_dppo20_analysis/trajectory_trace_phase3_ep_011.md`;
  - final Sol review:
    `docs/reviews/gate4_flow_dppo20_final_review.md` (`PASS`);
  - accepted SFT boundary: 59 native v0.5 image/submit targets, with
    `query_skill`, harmful/ineffective actions, and rejected raw turns masked.
  - Geneval2 Soft-TIFA GM recomputed from persisted correct-answer
    probabilities: first Agent attempts 20.99, submitted reducer-best 47.25,
    per-trajectory peak 53.33;
  - Geneval2 Soft-TIFA AM recomputed from the same probabilities: first Agent
    attempts 69.38, submitted reducer-best 84.70, gain +15.32;
  - SFT export dry run:
    `docs/phase5/flow_dppo20_sft_dry_run_report.md` (`PASS`, 59 targets and
    105 context-only records).
- Muse Image related-work and ablation-design package:
  - corrected source identity: the 2026 agentic Muse Image release is from
    Meta Superintelligence Labs, not Google's 2023 Muse generator;
  - source record:
    `references/web/muse_image_meta_2026-07-07/technical_blog_snapshot.md`;
  - selective lessons and staged comparison/ablation plan:
    `docs/research/muse_image_selective_lessons_and_ablation_plan.md`;
  - the design prioritizes zero-GPU trajectory analysis, a planner-only
    `V x I x H` screen, matched one-step mechanism tests, and an
    equal-image-call-budget four-arm live pilot before any full factorial;
  - Muse Image remains related-work motivation rather than an executable or
    numerically comparable baseline because no public reproducible protocol was
    found;
  - Google RichHF + Muse was added as the closer verifier-guided precedent,
    motivating a nested atom-level versus aggregate-only versus no-verifier
    feedback ablation without importing RAHF into the runtime;
  - GPT-5.6 Sol claim-sufficiency review:
    `docs/reviews/muse_image_ablation_design_sol_review.md`
    (`PASS_WITH_REQUIRED_CHANGES`);
  - required pre-live decisions are to keep operational pass-count selection,
    use submitted GM as primary, keep best-by-GM as a post-hoc oracle, run live
    atom-level versus aggregate/no-verifier outcomes for the grounding claim,
    and require an independent blinded audit for any general image-quality
    claim.
- Qwen dual-backend execution profile:
  - accepted ADR:
    `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`;
  - design and final GPT-5.6 Sol review:
    `docs/architecture/planner_execution_v0_7_dual_backend.md` and
    `docs/reviews/planner_execution_v07_dual_backend_review.md`;
  - Action Protocol remains v0.5; new diagnostic runs use PlannerContext v0.6;
    `v0.7` is an experiment design label, while the serialized environment
    profile is `qwen_dual_backend@1`;
  - image execution events now persist route/model/pipeline/sampling/source and
    output provenance and reject resume under a different profile;
  - SFT dry-run export rejects mixed execution profiles;
  - five failure-diverse Flow-DPPO prompts are frozen in
    `artifacts/phase6/v07_dual_backend_selected_prompts.json`;
  - five dual-backend trajectories completed at
    `runs/phase6_v07_dual_backend5_score_v06/`;
  - the matched edit-only v0.6 arm remains prepared and unexecuted at
    `runs/phase6_v07_legacy_edit_only5_score_v06/`.
- PlannerContext v0.6 Geneval2 score policy:
  - accepted ADR:
    `docs/decisions/ADR-0007-geneval2-primary-score-selection.md`;
  - frozen design and GPT-5.6 Sol final `APPROVE`:
    `docs/architecture/planner_score_semantics_v0_6.md` and
    `docs/reviews/planner_score_v06_sol_review_request.md`;
  - new Geneval2 events persist a recomputable prompt-level GM;
  - reducer ranking is pass-count first and GM only on ties;
  - historical Flow-DPPO20 counterfactual changes 8/20 selected Attempts and
    raises mean GM from 47.25 to 53.33 without reducing pass-count;
  - SFT exports group the full context/score tuple and rebuild each context
    from the exact pre-action event prefix.
- v0.7 / PlannerContext v0.6 five-trajectory diagnostic:
  - five valid submitted trajectories and 25 complete Geneval2 evaluations;
  - 7 source-free Qwen-Image generations and 18 Qwen-Image-Edit edits;
  - first-to-submitted atom pass improved 35/50 to 40/50;
  - first-to-submitted GM improved 7.81 to 18.32 and AM 69.21 to 77.33;
  - versus the same five historical prompts, submitted atom pass improved
    39/50 to 40/50, while GM fell 19.70 to 18.32 and AM 77.68 to 77.33;
  - four paired trajectories improved under pass-first/GM-second ordering and
    one easy verb/count trajectory regressed;
  - GM triggered six best updates, pass-first rejected two higher-GM
    lower-pass attempts, four edits branched from historical sources, and two
    post-initial source-free regenerations occurred;
  - bounded runtime correction now permits at most two successful novel
    `query_skill` interactions per image-producing Round and resumes an
    interrupted Skill response idempotently;
  - validation:
    `docs/phase6/v07_dual_backend5_score_v06_validation_report.md`;
  - paired and final analysis:
    `docs/phase6/v07_dual_backend5_score_v06_paired_comparison.md` and
    `docs/phase6/v07_dual_backend5_score_v06_final_analysis.md`;
  - representative real I/O walkthrough:
    `docs/phase6/planner_io_v06_round_memory_walkthrough_phase3_ep012.md`;
  - final Sol verdict:
    `docs/reviews/v07_dual_backend5_score_v06_final_sol_review.md` (`PASS`).

## Tests And Results

- Phase 3 live preflight:
  - `python -m gen_retry.cli.phase3_live_preflight --image-steps 2 --image-height 512 --image-width 512` — passed
- Phase 3 live rollouts:
  - `python -m gen_retry.cli.run_phase3_rollouts --image-steps 4 --image-height 512 --image-width 512` — completed ten submitted trajectories
- Phase 3 analysis:
  - `python -m gen_retry.cli.analyze_phase3_rollouts` — passed, 10 episodes and 78 labeled records
- Phase 4:
  - `python -m gen_retry.cli.phase4_sft_dry_run` — passed, 28 targets and 50 context-only records
- Skill-v1 validation:
  - `pytest tests/unit/test_skill_v1_runtime_policy.py tests/contract/test_action_protocol.py tests/contract/test_event_schema.py -q` — passed, 42 tests
  - `python -m gen_retry.cli.run_phase3_rollouts_parallel --run-root runs/skill_v1_validation_policyfix --episode-id phase3_ep_001 --image-steps 40 --image-height 1024 --image-width 1024 --max-workers 1` — completed, submitted `a_000`
  - `python -m gen_retry.cli.export_trajectory_trace --run-dir runs/skill_v1_validation_policyfix/phase3_ep_001 --output docs/skills/validation/trajectory_trace_skill_v1_policyfix_ep_001.md` — passed
  - `python -m gen_retry.cli.analyze_phase3_rollouts --run-root runs/skill_v1_validation_policyfix --invalid-run-root runs/skill_v1_validation_policyfix_invalid --artifact-root artifacts/skill_v1_validation_policyfix --docs-root docs/skills/validation --expected-count 1` — passed, 1 episode and 10 labeled actions
- Final validation:
  - `pytest tests/contract -q` — passed, 58 tests
  - `pytest tests/unit -q` — passed, 43 tests
  - `python -m gen_retry.cli.validate_schemas` — passed, 7 schemas
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records
  - `python -m gen_retry.cli.replay_episode examples/one_episode_trajectory.jsonl --planner-context` — passed
  - `python -m gen_retry.cli.export_trajectory_trace --run-dir runs/planner_context_v0_3/phase3_ep_001 --output docs/phase3/trajectory_trace_planner_context_v0_3_ep_001.md` — passed
  - `git diff --check` — passed
- Planner I/O v0.4 validation:
  - `pytest tests/contract/test_action_protocol.py tests/contract/test_provider_action_schema.py tests/unit/test_planner_context_round_memory.py -q` — passed, 40 tests
  - `pytest tests/unit -q` — passed, 43 tests
  - `pytest tests/contract -q` — passed, 67 tests
  - `python -m gen_retry.cli.validate_schemas` — passed, 9 schemas
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records
  - `python -m gen_retry.cli.replay_episode examples/one_episode_trajectory.jsonl --planner-context` — passed and emitted PlannerContext v0.4
  - `git diff --check` — passed
- Planner I/O v0.5 validation:
  - focused protocol/runtime/SFT/teacher suite — passed, 63 tests;
  - `pytest tests/contract -q` — passed, 74 tests;
  - `pytest tests/unit -q` — passed, 50 tests;
  - `python -m gen_retry.cli.validate_schemas` — passed, 11 schemas;
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records.
- Decision-summary teacher-only pilot:
  - GPT-5.5 control: 10/10 valid and decision-correct;
  - GPT-5.5 candidate: 10/10 valid and decision-correct, 10/10 format-valid,
    with no detected future leakage;
  - Sol final review: `FAIL_KEEP_V05` because 2/10 broad-failure regeneration
    summaries did not explain generate-over-edit selection;
  - no Qwen-Image-Edit or Geneval2 calls were made.
- Flow-DPPO 20-trajectory validation:
  - `python -m gen_retry.cli.audit_phase5_rollouts ...` — passed, 20 episodes
    and 92 attempts;
  - `pytest tests/contract -q` — passed, 74 tests;
  - `pytest tests/unit -q` — passed, 76 tests;
  - `python -m gen_retry.cli.validate_schemas` — passed, 11 schemas;
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records;
  - `python -m gen_retry.cli.replay_episode
    examples/one_episode_trajectory.jsonl --planner-context` — passed;
  - `git diff --check` — passed.
  - `python -m gen_retry.cli.phase4_sft_dry_run ...` — passed, 59 targets and
    105 context-only records.
  - `pytest tests/unit/test_phase5_rollout_audit.py -q` — passed, 11 tests for
    Geneval2-compatible Soft-TIFA AM/GM calculation and input validation.
- Qwen dual-backend execution-profile validation:
  - `pytest tests/contract -q` — passed, 77 tests;
  - `pytest tests/unit -q` — passed, 91 tests;
  - `python -m gen_retry.cli.validate_schemas` — passed, 11 schemas;
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records;
  - `python -m gen_retry.cli.replay_episode
    examples/one_episode_trajectory.jsonl --planner-context` — passed;
  - ten selected fresh run scaffolds validate with zero attempts: five lock
    `qwen_dual_backend@1` and five lock `qwen_image_edit_only@1`;
  - `git diff --check` — passed;
  - no Teacher, Qwen, or Geneval2 live call was made.
- PlannerContext v0.6 score-policy validation:
  - `pytest tests/contract -q` — passed, 79 tests;
  - `pytest tests/unit -q` — passed, 103 tests;
  - `python -m gen_retry.cli.validate_schemas` — passed, 12 schemas;
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records;
  - historical example replay — passed with legacy v0.5 ordering;
  - Flow-DPPO20 counterfactual — 8/20 best selections changed, 47.25 to
    53.33 mean GM, zero pass-count regressions;
  - historical 59-target SFT dry run — passed with exact temporal-prefix
    reconstruction and homogeneous context/score contract;
  - ten fresh comparison scaffolds validate with PlannerContext v0.6 and zero
    image attempts;
  - `git diff --check` — passed;
  - no Teacher, Qwen, or Geneval2 live call was made.
- v0.7 / PlannerContext v0.6 five-trajectory live validation:
  - `python -m gen_retry.cli.audit_phase5_rollouts ... --expected-count 5`
    — passed, 5 episodes and 25 attempts;
  - `python -m gen_retry.cli.compare_paired_rollouts ...`
    — passed, atom delta +1 and GM delta -1.38;
  - `pytest tests/contract -q` — passed, 79 tests;
  - `pytest tests/unit -q` — passed, 108 tests;
  - `python -m gen_retry.cli.validate_schemas` — passed, 12 schemas;
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records;
  - `git diff --check` — passed.
- Fresh 8-HCU checkpoint-140 and retry-closure validation:
  - cumulative completed-quality cohort — 140 valid trajectories and 451
    evaluated images, submitted atom pass 924/997, Soft-TIFA GM 75.50, and
    85/140 all-pass submissions;
  - checkpoint-140 increment — 79 evaluated images, submitted atom pass
    135/148, Soft-TIFA GM 58.59, and 7/20 all-pass submissions;
  - fixed ID 121-140 admission snapshot — 18 completed, two active, zero
    failed;
  - resource samples through checkpoint 140 — 5.89/8 mean active HCUs,
    median six, and no all-idle sample;
  - GPT-5.6 Sol verdict — `PASS_WITH_PROSPECTIVE_CHANGE`, with no validity
    blocker and a required forward-only retry closure policy;
  - Teacher policy v8 rejects equivalent retries after regression or strict
    no-progress, defaults edits to reducer-best, and requires relevant
    constraint evidence for another historical source;
  - `pytest tests/contract -q` — passed, 79 tests;
  - `pytest tests/unit -q` — passed, 133 tests;
  - `python -m gen_retry.cli.validate_schemas` — passed, 12 schemas;
  - `python -m gen_retry.cli.validate_fixtures` — passed, 104 fixture records;
  - historical example replay — passed.
- Fresh 8-HCU checkpoint-150 deep review:
  - checkpoint increment — 10 valid trajectories and 38 evaluated images,
    submitted atom pass 61/66, Soft-TIFA GM 76.17, and 6/10 all-pass
    submissions;
  - cumulative quality cohort — 150 valid trajectories and 489 evaluated
    images, submitted atom pass 985/1063, Soft-TIFA GM 75.55, and 91/150
    all-pass submissions;
  - fixed ID 141-150 admission snapshot — nine completed, one active, zero
    failed;
  - cumulative SFT reconciliation — 490 canonical targets and 357
    context-only records, with all ownership, profile, context/score-contract,
    and split invariants passing;
  - checkpoint 150 is frozen as an all-v7 baseline; the first valid v8
    submission occurred outside that cohort;
  - GPT-5.6 Sol verdict — `PASS_CONTINUE_QUEUE`, with v8 unchanged and
    asynchronous admission accepted under immutable predeclared cohorts.

## Active Risks

- External source roots have pre-existing dirty working trees; reuse decisions must rely on recorded commit/path/license evidence.
- Legacy Gen-Retry has no root license found, so copying code remains disallowed until file-level license evidence is recorded.
- Geneval2 is CC BY-NC 4.0 and should remain an external evaluator/runtime unless licensing is explicitly reviewed.
- The 20-trajectory batch is not evidence of model-level improvement. Verb
  atoms remain the weakest category at 7/15 best-attempt passes.
- The five-trajectory dual-backend diagnostic is not evidence of aggregate
  Geneval2 improvement: submitted GM and AM both fell slightly, and
  `phase3_ep_020` regressed from 5/6 to 4/6 despite sharper rendering.
- `phase3_ep_001` contains four obsolete pre-image
  `consecutive_query_skill` rejection events. Its image/score/submission
  comparison is valid, but planner-call count, repair count, latency, and cost
  are not directly comparable.
- The current first-to-best gains do not isolate adaptive planner value from
  extra image calls, verifier selection, or stochastic resampling. A
  equal-image-call-budget Best-of-K and fixed-heuristic comparison is still
  required, with total compute reported separately.
- Eligible actions span rollout-only Teacher prompt v4/v5 provenance. Exact
  version/hash metadata is retained; SFT rendering uses one frozen v0.5
  training system contract.
- Completed v0.5 trajectories retain the old earlier-Attempt tie rule and must
  not be relabeled as v0.6. New v0.6 trajectories may therefore not be mixed
  into one SFT export with those historical contexts.
- Edit supervision is thin in the Phase 4 freeze: 2 `edit_image` targets versus 16 `generate_image` and 10 `submit_attempt`.
- Under v0.5, `query_skill` and its linked Skill response both have loss 0
  until capability-isolated utility validation is accepted.
- Phase 4 truncation policy is documented but unexercised because no dry-run record required truncation.
- Phase 5 must use the same renderer and policy shape documented in `docs/phase4/sft_supervision_freeze.md`.
- The ten Phase 3 images were rendered with low-quality pilot parameters (`4` steps, `512 x 512`); do not use their visual sharpness to judge Qwen-Image-Edit capability.
- The high-quality `runs/phase3_hq5/phase3_ep_004` directory contains an interrupted `image_execution_started` event without an image, evaluator result, or submission; do not count it as a valid trajectory until it is deliberately resumed and completed.
- `docs/phase3/planner_io_v04_sft_message_view_phase3_ep001.json` is a human display artifact only; it contains notes and old empty `decision_summary` values and must not be used as trainable data.
- `query_skill` remains context-only for SFT until skill utility is accepted, despite being a real planner action in the trajectory protocol.
- Checkpoint 140 exposed 23 regressive image actions in 79 attempts. The v8
  retry closure policy is prospective, so its effect must be measured only on
  requests that persist `teacher_system_prompt_v8_retry_closure_policy`; v7
  and v8 episodes must not be pooled as if all received the change.

## Unresolved Decisions

- Whether future capability-isolated Skill utility evidence is sufficient to
  promote selected `query_skill` actions from loss 0 to positive supervision.

## Last Reviewer Verdict

The latest review is the fresh 8-HCU checkpoint-150 deep review:
`PASS_CONTINUE_QUEUE`. It found no cohort, evaluator, lineage, routing, memory,
SFT-masking, or future-leakage blocker. Checkpoint 150 is accepted as the final
all-v7 baseline; v8 continues unchanged and must be evaluated separately by
persisted Teacher system-prompt version. Asynchronous admission during review
is accepted because cohort boundaries are predeclared and immutable.

Earlier active verdicts remain unchanged. Planner I/O native
`decision_summary` is `FAIL_KEEP_V05`; Gate 3a Skill-v1 Trace I/O Clarity is
`APPROVE`; Skill utility remains `REQUEST_CHANGES`.

## Next Autonomous Action

Continue the fresh 8-HCU queue through checkpoint 160 using the predeclared
completion-quality and fixed-admission cohorts. Report v7 and v8 regressions,
strict no-progress retries, quality, and throughput separately using each
sanitized Planner request's persisted system-prompt version and hash. Do not
rerun valid v7 trajectories to manufacture a post-change comparison.

If prioritizing ablation evidence, first run the zero-image-call Stage 0
analysis and planner-only Stage 1 screen in
`docs/research/muse_image_selective_lessons_and_ablation_plan.md`. Before any
live ablation, satisfy the selector/estimand, live feedback-granularity,
independent-audit, information-isolation, and cost-accounting requirements in
the Sol review. Do not change selector semantics without a separate ADR and
protocol validation.

If collecting more live evidence before Phase 5, resume the high-quality batch from `runs/phase3_hq5/` using the state in `docs/operations/phase3_hq5_interruption_status.md`: keep `phase3_ep_001`, `phase3_ep_002`, and `phase3_ep_003` as valid completed trajectories, exclude `phase3_ep_004` until deliberately completed, and finish two more valid submissions to reach five HQ trajectories. Use the policy in `docs/operations/qwen_rendering_quality_baseline.md`: no standalone image smoke by default, `40` steps at `1024 x 1024`, no legacy image reuse, and episode-level parallelism whenever resources allow. Within each episode, preserve sequential canonical history.

Otherwise, proceed toward Phase 5 using native v0.5 records. Before writing the
final dataset, run an export invariant test confirming exactly one schema-valid
generate/edit/submit assistant action with loss 1 per target sample,
`query_skill` and all tool/evaluator/raw records with loss 0, no raw rejected
output, no future outcome leakage, no `_note` fields in assistant targets, and
split assignments matching the final split manifest.
