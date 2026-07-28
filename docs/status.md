# Status

## Current Phase

The Flow-DPPO 20-trajectory native Planner I/O v0.5 batch is complete and
passed deterministic validation plus final GPT-5.6 Sol review. No rollout
process is active. Phase 5 dataset assembly may use the 59 accepted
generate/edit/submit candidate actions; `query_skill` remains masked at loss 0.

## Gate State

- Gate 1 Protocol Freeze: APPROVED after user-authorized extra final correction cycle
- Gate 2 Five-Trajectory Pilot Review: APPROVED
- Gate 3 SFT Supervision Freeze: APPROVED
- PlannerContext / Round Memory final review: APPROVED
- Planner I/O v0.5 Sol amendment: IMPLEMENTED
- Gate 4 Flow-DPPO 20-Trajectory Final Review: PASS

## Protocol

- Current action protocol: v0.5 for new rollout/SFT records; v0.2-v0.4 remain valid historical event schemas.
- Current planner input: `PlannerContext` v0.5; the builder retains an explicit v0.4 compatibility mode.
- Live APIs run: yes
- Teacher policy: GPT-5.5 through `TEACHER_API_KEY` and `TEACHER_BASE_URL`
- Image backend: local Qwen-Image-Edit direct runtime through configured `model_path`
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

## Active Risks

- External source roots have pre-existing dirty working trees; reuse decisions must rely on recorded commit/path/license evidence.
- Legacy Gen-Retry has no root license found, so copying code remains disallowed until file-level license evidence is recorded.
- Geneval2 is CC BY-NC 4.0 and should remain an external evaluator/runtime unless licensing is explicitly reviewed.
- The 20-trajectory batch is not evidence of model-level improvement. Verb
  atoms remain the weakest category at 7/15 best-attempt passes.
- Eligible actions span rollout-only Teacher prompt v4/v5 provenance. Exact
  version/hash metadata is retained; SFT rendering uses one frozen v0.5
  training system contract.
- Reducer best is currently ordered by thresholded passed-atom count with
  earlier-attempt tie breaking, not by Soft-TIFA GM. The submitted 20-image GM
  is 47.25 while the per-trajectory peak-GM selection would be 53.33.
- Edit supervision is thin in the Phase 4 freeze: 2 `edit_image` targets versus 16 `generate_image` and 10 `submit_attempt`.
- Under v0.5, `query_skill` and its linked Skill response both have loss 0
  until capability-isolated utility validation is accepted.
- Phase 4 truncation policy is documented but unexercised because no dry-run record required truncation.
- Phase 5 must use the same renderer and policy shape documented in `docs/phase4/sft_supervision_freeze.md`.
- The ten Phase 3 images were rendered with low-quality pilot parameters (`4` steps, `512 x 512`); do not use their visual sharpness to judge Qwen-Image-Edit capability.
- The high-quality `runs/phase3_hq5/phase3_ep_004` directory contains an interrupted `image_execution_started` event without an image, evaluator result, or submission; do not count it as a valid trajectory until it is deliberately resumed and completed.
- `docs/phase3/planner_io_v04_sft_message_view_phase3_ep001.json` is a human display artifact only; it contains notes and old empty `decision_summary` values and must not be used as trainable data.
- `query_skill` remains context-only for SFT until skill utility is accepted, despite being a real planner action in the trajectory protocol.

## Unresolved Decisions

- Whether future capability-isolated Skill utility evidence is sufficient to
  promote selected `query_skill` actions from loss 0 to positive supervision.

## Last Reviewer Verdict

Planner I/O native `decision_summary` pilot verdict is `FAIL_KEEP_V05`: two
broad-failure regeneration summaries did not explain generate-over-edit
selection, so canonical v0.5 remains unchanged and Gate 3 is closed on this
question. Gate 3a Skill-v1 Trace I/O Clarity remains `APPROVE`; Skill utility
remains `REQUEST_CHANGES`.

## Next Autonomous Action

If collecting more live evidence before Phase 5, resume the high-quality batch from `runs/phase3_hq5/` using the state in `docs/operations/phase3_hq5_interruption_status.md`: keep `phase3_ep_001`, `phase3_ep_002`, and `phase3_ep_003` as valid completed trajectories, exclude `phase3_ep_004` until deliberately completed, and finish two more valid submissions to reach five HQ trajectories. Use the policy in `docs/operations/qwen_rendering_quality_baseline.md`: no standalone image smoke by default, `40` steps at `1024 x 1024`, no legacy image reuse, and episode-level parallelism whenever resources allow. Within each episode, preserve sequential canonical history.

Otherwise, proceed toward Phase 5 using native v0.5 records. Before writing the
final dataset, run an export invariant test confirming exactly one schema-valid
generate/edit/submit assistant action with loss 1 per target sample,
`query_skill` and all tool/evaluator/raw records with loss 0, no raw rejected
output, no future outcome leakage, no `_note` fields in assistant targets, and
split assignments matching the final split manifest.
