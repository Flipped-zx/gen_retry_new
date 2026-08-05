# Status

## Current Phase

The `research/hpsv3-quality-guard` branch proposes an additive HPSv3
auxiliary-quality observation and PlannerContext v0.8. This is an experiment
branch only: Geneval2 remains the sole best/submission comparator, v0.7 replay
is unchanged, and no hidden source filter is introduced. The first GPT-5.6 Sol
review returned `FAIL_STOP_PILOT`; its event-order, missing-value, anchor,
fingerprint, policy-isolation, and admission-design blockers have now been
implemented. The second GPT-5.6 Sol review returned `PASS` for the documented
GPT-5.5 Teacher paired pilot only. The 18-episode calibration cohort and a
disjoint 60-episode confirmation manifest are frozen without reading HPS
results. No live `G+H` pilot, v0.8 SFT use, SFT export, or policy promotion has
occurred.

The six-trajectory HPSv3 mini-pilot decision probe is now complete. The offline
HPS diagnostic produced a negative child-minus-parent delta for all six selected
edit pairs (U mean -1.177195, D mean -0.806923, N mean -0.073430). A
counterfactual GPT-5.5 Teacher call under each arm produced 6/6 parseable
actions for both `G` and `G+H`; three exact action objects differed, but only
one changed action type. The clearest mechanism case changed a high-risk U
continuation from `edit_image` to `query_skill(local_edit_preservation)`;
the other two differences retained `edit_image` and refined the instruction.
No image action was executed, so this is decision feasibility evidence rather
than mitigation evidence. Calls were separate unsampled API requests, so
action differences also contain Teacher sampling variation. Report:
`docs/phase7/hpsv3_teacher_decision_probe_report.md`; artifact:
`artifacts/phase7/hpsv3_teacher_decision_probe_v1.json`.

The formal Flow-DPPO 1000 v9 cold-start SFT is complete. Gate 3 returned
`PASS_FREEZE_WITH_MONITORING`, and the frozen export contains 4302 positive
targets split by trajectory into 3450 train, 438 validation, and 414 test
rows. Positive targets include 1191 `edit_image`, 1112 `generate_image`, 999
validated `query_skill`, and 1000 `submit_attempt` actions. Another 1205
harmful, ineffective, invalid, tool-response, or otherwise context-only
records retain zero loss; this includes 52 unvalidated Skill calls.

The main run fine-tuned Qwen3-VL-8B-Instruct with full SFT while freezing the
vision tower and projector. It used BF16, FlashAttention-2, ZeRO-3, global
batch size 32, two epochs, and eight 64 GiB HCUs. All 216 optimizer steps
completed in 2492.6 seconds with no NaN/Inf or stability failure. Final train
loss was 0.3071 and final validation loss was 0.2712. The output is
`runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42`, with resumable
checkpoints at steps 100, 200, and 216.

W&B online monitoring completed under entity `Gen_retry`, project
`gen-retry-sft`, group `v9-cold-start`, and run
`gen-retry-flow1000-v9-selective-skill-full-s42`. Local curve/HTML/Markdown
reports are under
`artifacts/sft/flow1000_v9_selective_skill_full_s42_monitor`.
The read-only W&B API check reports state `finished`; run URL:
`https://wandb.ai/Gen_retry/gen-retry-sft/runs/kf975j1w`.

A fixed 16-row balanced validation probe compared checkpoint 100 with the
final model. Both produced 16/16 schema-valid actions and the expected 4/16
`query_skill` rate. Action-type accuracy improved from 15/16 to 16/16; target
and preserve-constraint overlap improved to 1.0; attempt-reference accuracy
remained 1.0. This is a policy-format sanity check, not image execution or a
Geneval2 quality claim. Results are under
`artifacts/sft/checkpoint_eval/flow1000_v9_full_s42`.

The final checkpoint has now completed a production-path rollout on 20 frozen
SFT-test episodes under `runs/phase7_sft_frozen_test20_v2`. The run used the
training system prompt, PlannerContext v0.7, action protocol v0.5, the existing
Qwen generation/edit and Geneval2 adapters, 50 generation steps, 40 edit
steps, 1024 x 1024 images, and at most five image calls. It produced 108/108
schema-valid planner outputs, 20/20 matched Skill queries/tool responses, and
20/20 submissions with no Teacher fallback. Across 68 image calls, submitted
atoms improved from 121/146 to 134/146 and mean Soft-TIFA GM from 46.43 to
69.14; 11/20 submissions were all-pass. Canonical history was actively used:
17 edits branched from a non-latest `source_attempt_id`, five submissions
selected a historical attempt, and seven episodes recovered after regression.
There were six successful same-request transport retries during the fully
concurrent run, with no duplicate successful outputs or canonical actions.
Formal report: `docs/phase7/sft_frozen_test20_v2_report.md`; machine-readable
artifact: `artifacts/phase7/sft_frozen_test20_v2_report.json`.

A paired raw-original-prompt baseline is prepared but not yet executed for the
same frozen 20 TaskSpecs. Its new root is
`runs/phase7_sft_frozen_test20_qwen_raw_b5_v1`; the frozen plan contains 20
episodes x 5 variants using seeds 0--4, the existing Qwen-Image generate route,
50 steps, 1024 x 1024, and the existing Geneval2 adapter. The single-image arm
is seed 0; both highest-GM and pass-count-first Best-of-5 selectors will be
reported. Preparation imported only TaskSpecs and produced no image,
Geneval2, or result artifact. Launch and resume instructions:
`docs/operations/sft_frozen_test20_qwen_raw_baseline.md`.

The official-atomicity-matched Flow-DPPO 200-trajectory batch is complete
under `runs/phase7_flow_dppo200_fresh8_v1`: 1301/1419 submitted atoms,
Soft-TIFA GM 73.50, and 111/200 all-pass trajectories.

A paired comparison with the user-supplied original-prompt Qwen-Image
Best-of-5 baseline is complete. The aligned baseline reaches 1042/1419 atoms,
Soft-TIFA GM 31.53, and 42/200 all-pass prompts; the Agent leads by 259 atoms,
41.97 GM points, and 69 all-pass prompts while using 684 versus 1000 image
calls. A pass-count-first baseline sensitivity check still leaves a
229-atom and 42.36-GM-point Agent lead. This is integrated-system evidence,
not a compute-normalized causal policy ablation.

The public trajectory showcase was refreshed on 2026-08-02 to foreground the
trajectory evidence itself. The first viewport now presents four canonical
episodes at once, supports dimension filters and two four-item batches, and
opens the selected episode into the existing full Attempt strip and prompt
comparison. The archive contains eight grounded examples spanning count,
attribute, spatial, action, and history-recovery behavior. This was a
frontend-only presentation change; protocol semantics and review gates were
not affected. Public site:
`https://gen-retry-trajectories.ryuuikujyunn.chatgpt.site/`.

The follow-up two-HCU verb generation study is also complete. It evaluated six
prompt-composition formulations against the complete 12-prompt `chasing`
cohort. `focal_action_anchor` was selected as a targeted retry technique: it
reached 3/12 chasing passes versus the current submitted 2/12, and produced a
paired 5/5 result on `phase3_ep_098` without regressing any previously passed
atom. Replaying observed candidates through the frozen historical-best
comparator yields 1303/1419 atoms, 11/22 verbs, and 112/200 all-pass
trajectories. This is a counterfactual compatibility result, not a fresh
200-episode rollout.

The earlier `action_pose_relation@2.0.0` pilot introduced a targeted focal
operator rather than a global prompt prefix. Full methodology and limitations
are recorded in
`docs/phase7/verb_generation_technique_experiment.md`.

A fresh two-episode multi-round Teacher pilot has now validated the operator
inside the actual retry loop. Both episodes autonomously queried the Skill.
`phase3_ep_098` improved from the historical 4/5 verb-fail submission to 5/5
all-pass after four image attempts; `phase3_ep_014` tied its historical 7/8
atom result and still failed chasing. Across the frozen pair, submitted atoms
improved 11/13 -> 12/13, verb passes 0/2 -> 1/2, all-pass episodes 0/2 -> 1/2,
and image attempts fell 10 -> 9. An experiment-only forced verb-route closure
improved retry diversity but regressed the hard episode to 5/8, so it was
rejected and removed; it is not part of the promoted policy. Details:
`docs/phase7/verb_multiround_teacher_pilot.md`.

The complete official-current verb-nonpass cohort has now been rerun as a
two-HCU multi-round A/B. On the ten primary episodes not used in the earlier
pilot, Candidate B improved 54/71 -> 56/71 submitted atoms, 0/10 -> 3/10 verb
passes, and mean GM 27.70 -> 31.97 with the same 50 image attempts. Across all
twelve failures it improved Production A from 66/84 atoms and 1/12 verbs to
67/84 and 4/12; relative to official current it improved 64/84 and 0/12 to
67/84 and 4/12. The predeclared promotion rule passed.

The prospective rollout policy now uses `action_pose_relation@2.1.0` and
`teacher_system_prompt_v9_meaningful_retry_verb_retention`. The action Skill is
retrieved only after an evaluated verb failure or uncertainty, exposes typed
chasing/playing/jumping topologies, and preserves historical verb-pass
evidence during non-verb repair. Candidate B delayed action-Skill retrieval in
12/12 episodes; Production A retrieved it before the first image in 12/12.
`phase3_ep_135` verified the intended history-aware behavior by branching from
a non-reducer-best verb-pass attempt after a same-count higher-GM edit
regressed the verb, then recovering reducer-best to a verb-pass attempt.
The v9 merge adds PlannerContext v0.7 prior instructions, removes the coarse
runtime tuple rejection, restores Skill guidance from hash-verified immutable
tool observations, and exposes same-count historical evidence images. The
action schema, reducer, score, Qwen, Geneval2, and SFT inclusion policy remain
unchanged. Details:
`docs/phase7/verb_failed12_multiround_experiment.md`.

The meaningful-retry v9 design completed Sol design review with `PASS`, and
the rollout-side Teacher/PlannerContext/runtime changes were implemented.
Its formerly open SFT requirements were subsequently resolved by the formal
Gate 3 freeze described above.

A new prospective 1000-prompt Flow-DPPO batch has been selected and its fixed
20-ID admission pilot has passed. It exactly mirrors the official Geneval2
test-set atom-count marginal
with 125 prompts at every `atom_count` from 3 through 10, yielding local
easy/medium/hard counts of 375/375/250. It excludes the 220 source rows used
by the earlier 20- and 200-prompt batches and keeps the official 800 rows held
out. The frozen selection SHA256 is
`9f5fca671e42bbb68577cb1513e072f7c020e59131dfa1989bb2c5c5f4fa0eba`.
All 1000 fresh PlannerContext v0.7 directories are prepared. The fixed pilot
has 20/20 valid submissions and 65 Attempts; best atom pass rate is 93.48%,
and submitted Soft-TIFA GM improves from 41.42 initially to 77.94. A
regex-derived instruction-quality false positive stopped `phase3_ep_004`;
ADR-0009 now makes the linter advisory while retaining schema, reference,
budget, lineage, and source-selection hard gates. Only `phase3_ep_004` was
resumed, and the deterministic fixed-20 audit passed. Empirical timing puts
1000 trajectories at 27-30 hours P50 and 34-40 hours P80. The continuous
`phase3_ep_021` through `phase3_ep_1000` queue started at
`2026-08-01T08:28:42Z` in tmux session `flow1000_v9_queue`. Details:
`docs/operations/phase7_flow_dppo1000_v9_parallel_run.md`. Independent
parallel review:
`docs/reviews/flow_dppo1000_v9_parallel_5_5_review.md`
(`APPROVE_WITH_20_TRAJECTORY_ADMISSION_PILOT`).
Live status: `docs/operations/phase7_flow_dppo1000_v9_live_status.md`.

The Flow-DPPO 1000 v9 fixed-ID checkpoint 100 audit has passed with 337 image
Attempts. Best atom pass rate is 91.09% versus 79.89% initially; submitted
Soft-TIFA GM is 73.12 versus 36.09 initially, and 59/100 episodes are all-pass.
At audit completion 119/1000 trajectories were submitted, 16 were active, and
no admission stop was present.

The fixed-ID checkpoint 200 audit also passed with 665 image Attempts. Best
atom pass rate is 91.55% versus 80.46% initially, submitted Soft-TIFA GM is
72.40 versus 38.86 initially, and 120/200 episodes are all-pass. GPT-5.6 Sol
returned `PASS_CONTINUE_WITH_MONITORING`: 128 regressive and 107 ineffective
Actions require monitoring but are not a direction blocker because reducer
rollback keeps the submitted-to-peak GM gap to 1.47 points. Before checkpoint
400, report linter verdict by outcome/SFT inclusion and explicit recovery after
regression/no-progress.

The Flow-DPPO 1000 v9 batch is complete. The first queue stopped at 917/1000
after sanitized Teacher `403 insufficient balance` responses; the remaining
83 requests resumed once from persisted PlannerContext state. Existing
Attempts and submitted trajectories were reused. The resume scheduler exited
with code 0, and final event/file reconciliation found zero orphan images,
half-written Attempts, or duplicate image executions.

The final deterministic audit passed with 1000 submitted episodes and 3443
image Attempts. Atom pass improved from 5540/6937 (79.86%) to 6302/6937
(90.85%), Soft-TIFA AM from 80.60 to 90.25, and submitted Soft-TIFA GM from
40.32 to 71.14. There are 552 all-pass episodes. The post-hoc GM peak is 72.30,
so the actual submission gap is 1.16 points. At that stage GPT-5.6 Sol returned
`PASS_WITH_BLOCKED_SFT_EXPORT`; the later compatibility, labeling, and Gate 3
work resolved that historical block. Details:
`docs/phase7/flow_dppo1000_v9_final_analysis_report.md`.

## Gate State

- Gate 1 Protocol Freeze: APPROVED after user-authorized extra final correction cycle
- Gate 2 Five-Trajectory Pilot Review: APPROVED
- Gate 3 legacy SFT Supervision Freeze: APPROVED; v9 re-freeze:
  PASS_FREEZE_WITH_MONITORING; formal SFT complete
- PlannerContext / Round Memory final review: APPROVED
- Planner I/O v0.5 Sol amendment: IMPLEMENTED
- Gate 4 Flow-DPPO 20-Trajectory Final Review: PASS
- Qwen dual-backend execution-profile review: APPROVE
- PlannerContext v0.6 score-policy review: APPROVE
- v0.7 / PlannerContext v0.6 five-trajectory final review: PASS
- Flow-DPPO 200 official-mix distribution review: PASS
- Flow-DPPO fresh-8 checkpoint 20 light review: PASS_CONTINUE
- Flow-DPPO 1000 v9 fixed-20 admission audit: PASS
- Flow-DPPO 1000 v9 final trajectory pool: PASS; positive SFT export frozen
  and formal 8-HCU SFT complete
- Advisory instruction-quality boundary: PASS_WITH_REQUIRED_CHANGES,
  required metadata persistence implemented
- Flow-DPPO fresh-8 checkpoint 40 / continuous queue review:
  PASS_CONTINUE_QUEUE
- Muse Image-informed ablation claim-sufficiency review:
  PASS_WITH_REQUIRED_CHANGES (not a protocol gate)

## Protocol

- Current action protocol: v0.5 for new rollout/SFT records; v0.2-v0.4 remain valid historical event schemas.
- Current planner input: `PlannerContext` v0.7 for newly prepared score-policy
  episodes; v0.6 remains a compatible immutable replay/resume mode and
  v0.4/v0.5 remain historical replay modes.
- Live APIs run: yes
- Teacher policy: GPT-5.5 through `TEACHER_API_KEY` and `TEACHER_BASE_URL`;
  prospective prompt version `teacher_system_prompt_v9_meaningful_retry_verb_retention`
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

- Reference evidence governance reorganized:
  - external sources now have a repository-local index under `references/`;
  - `paper/` is reserved for Gen-Retry-authored manuscript assets;
  - the user-supplied Generation Navigator v1 PDF is an ignored local cache
    with a versioned URL/hash manifest, section-level ledger entry, and
    Gen-Retry comparison in `docs/research/related_work_evidence_map.md`;
  - Gen-Searcher, GenEvolve, and GEMS now have versioned paper manifests;
    Gen-Searcher and GEMS were promoted to section-level paper evidence;
  - Gen-Searcher and GenEvolve remain read-only evidence roots, while sibling
    Gen-Retry versions remain excluded;
  - historical Phase 0 architecture reports now identify their superseded
    status instead of competing with current ADR-0006 semantics;
  - no Action, schema, reducer, score, backend, or SFT rule changed.
- GenEvolve evaluation reference complete:
  - formal benchmark contains 594 prompt/ground-truth pairs, split into 335
    Knowledge-Anchored and 259 Quality-Anchored cases;
  - training reward, formal image KScore, and qualitative gallery evidence are
    recorded as three distinct evidence layers;
  - KScore is documented as `0.1 F + 0.4 V + 0.4 T + 0.1 A`, so aggregate
    improvement cannot establish aesthetics or texture preservation;
  - released no-text scoring conflicts with the paper's renormalization rule
    and remains explicitly unresolved;
  - GenEvolve's open Qwen path is confirmed as one reference-conditioned final
    render rather than edit-on-edit retry;
  - local design lessons preserve separate semantic and quality views, require
    per-edit source/output quality auditing, and treat edit-depth limits as a
    secondary guard;
  - reference: `docs/research/genevolve_evaluation_reference.md`;
  - provenance: `docs/SOURCE_LEDGER.md`.
- Canonical trajectory web showcase complete:
  - private Sites deployment: `https://gen-retry-trajectories.ryuuikujyunn.chatgpt.site`;
  - source surface: `showcase/`;
  - four grounded examples cover count/layout repair, attribute binding,
    action/spatial repair, and non-monotonic historical recovery;
  - image comparison, attempt lineage, atom pass progression, and exact
    initial/final canonical instructions are displayed without reading raw
    teacher output at runtime;
  - vinext build, rendered-HTML tests, and TypeScript checks pass.
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
- Qwen-Image Best-of-5 paired baseline analysis:
  - exact prompt and ordered VQA alignment passed for 200/200 rows;
  - highest-GM baseline: 1042/1419 atoms, Soft-TIFA AM 74.32, GM 31.53,
    and 42/200 all-pass prompts;
  - Agent delta: +259 atoms, +16.58 AM, +41.97 GM, and +69 all-pass prompts;
  - protocol-selector sensitivity baseline: 1072/1419 atoms and GM 31.14,
    leaving the Agent +229 atoms and +42.36 GM;
  - report: `docs/phase7/qwen_best_of_5_baseline_comparison.md`;
  - artifact: `artifacts/phase7/qwen_best_of_5_baseline_comparison.json`.
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
- Fresh 8-HCU checkpoint-160 light review:
  - checkpoint increment — 10 valid trajectories and 38 evaluated images,
    submitted atom pass 61/70, Soft-TIFA GM 59.44, and 4/10 all-pass
    submissions;
  - version split — seven v7 trajectories with 34 attempts and all 11
    regressive actions; three v8 trajectories with four attempts, all 19
    atoms passed, and no regression;
  - the v8 subgroup is limited to early compatibility evidence because it is
    small, easier, and contains no closure-rejection example;
  - fixed ID 151-160 admission snapshot — eight completed, two active, zero
    failed;
  - GPT-5.6 Sol verdict — `PASS_CONTINUE_QUEUE`; continue unchanged to the
    predeclared checkpoint 180.
- Fresh 8-HCU checkpoint-180 light review:
  - checkpoint increment — 20 valid trajectories and 64 evaluated images,
    submitted atom pass 122/130, Soft-TIFA GM 80.41, and 13/20 all-pass
    submissions;
  - version split — five v7 and 15 v8 trajectories; the v8 group had six
    post-regression/strict-no-progress decisions and zero equivalent
    action/source/target repeats;
  - fixed ID 161-180 admission snapshot — 17 completed, three active, zero
    failed;
  - cumulative quality cohort — 180 valid trajectories and 591 evaluated
    images, submitted atom pass 1168/1263 and Soft-TIFA GM 75.19;
  - GPT-5.6 Sol verdict — `PASS_CONTINUE_QUEUE`; v8 supports descriptive
    retry-closure consistency but no causal performance claim.
- Fresh 8-HCU final checkpoint-200 review:
  - 200/200 fixed IDs completed with 684 evaluated images; no valid trajectory
    was rerun;
  - submitted atom pass 1301/1419, Soft-TIFA AM 90.90, Soft-TIFA GM 73.50,
    and 111/200 all-pass trajectories;
  - 162 v7-only, 37 v8-only, and one mixed-resume trajectory; v8-only had zero
    equivalent repeats across 32 retry-closure opportunities;
  - final SFT reconciliation — 663 canonical targets and 496 context-only
    records with all ownership, profile, score-contract, and split invariants
    passing;
  - `pytest tests/contract -q` — passed, 79 tests;
  - `pytest tests/unit -q` — passed, 133 tests;
  - schema validation — passed, 12 schemas;
  - fixture validation — passed, 104 records;
  - historical replay — passed;
  - GPT-5.6 Sol verdict — `PASS_FINAL`; the dataset may proceed to the next
    SFT supervision gate.
- Meaningful-retry v9 SFT design review:
  - same action/source/targets is no longer treated as proof of an equivalent
    retry strategy;
  - PlannerContext v0.7 retains prior instructions from past-only events;
  - compatibility review is outcome-blind and outcome tiers compare with
    `best_before`;
  - candidate full-weight retry rules retain 124/129 atom-gain and 73/130
    GM-only provisional targets before semantic review;
  - Sol design verdict — `PASS`;
  - this was a design-stage verdict; the later implementation and Gate 3
    review are now complete.

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
- The paired Qwen-Image Best-of-5 result establishes integrated-system
  improvement but still does not isolate adaptive planner value from prompt
  rewriting, verifier selection, editing, or stochastic resampling. The
  baseline file omits renderer/model/evaluator provenance, and generate/edit
  costs are not normalized. A provenance-matched, compute-normalized
  Best-of-K and fixed-heuristic comparison is still required.
- Eligible actions span rollout-only Teacher prompt v4/v5 provenance. Exact
  version/hash metadata is retained; SFT rendering uses one frozen v0.5
  training system contract.
- Completed v0.5 trajectories retain the old earlier-Attempt tie rule and must
  not be relabeled as v0.6. New v0.6 trajectories may therefore not be mixed
  into one SFT export with those historical contexts.
- Edit supervision is thin in the Phase 4 freeze: 2 `edit_image` targets versus 16 `generate_image` and 10 `submit_attempt`.
- Under the formal v9 freeze, 999 validated productive `query_skill` actions
  receive positive supervision. Skill/tool responses and 52 unvalidated Skill
  calls remain context-only with loss zero.
- Phase 4 truncation policy is documented but unexercised because no dry-run record required truncation.
- Phase 5 must use the same renderer and policy shape documented in `docs/phase4/sft_supervision_freeze.md`.
- The ten Phase 3 images were rendered with low-quality pilot parameters (`4` steps, `512 x 512`); do not use their visual sharpness to judge Qwen-Image-Edit capability.
- The high-quality `runs/phase3_hq5/phase3_ep_004` directory contains an interrupted `image_execution_started` event without an image, evaluator result, or submission; do not count it as a valid trajectory until it is deliberately resumed and completed.
- `docs/phase3/planner_io_v04_sft_message_view_phase3_ep001.json` is a human display artifact only; it contains notes and old empty `decision_summary` values and must not be used as trainable data.
- The checkpoint action probe covers only 16 balanced validation targets. It
  establishes schema/action/constraint behavior, but not downstream image or
  Geneval2 improvement; that must be measured in the later policy evaluation.
- Checkpoint 140 exposed 23 regressive image actions in 79 attempts. The v8
  retry closure policy is prospective, so its effect must be measured only on
  requests that persist `teacher_system_prompt_v8_retry_closure_policy`; v7
  and v8 episodes must not be pooled as if all received the change.
- The final batch is held-out-safe Flow-DPPO synthetic-train evidence, not an
  official Geneval2 800-row leaderboard result.
- The 20-episode frozen-test SFT rollout establishes executable closed-loop
  behavior and within-episode improvement, but its sample is too small for an
  official 800-row claim and it is not a causal SFT-versus-Teacher ablation.
- Verb atoms remain the main content limitation: 10/22 passed at submission,
  with chasing at 2/12. The targeted failed-12 rerun raises the observed
  replacement counterfactual to 14/22 but is not a fresh 200-episode rerun;
  seven Candidate-B submitted chasing atoms still fail. The evidence does not
  isolate generator difficulty from VQA sensitivity.
- The 663-target checkpoint-200 SFT dry run is provisional under the new
  meaningful-retry policy. Its source trajectories use PlannerContext v0.6
  and v7/v8 Teacher provenance, and its exporter predates the final v9
  compatibility audit. Do not train it as the final v9 dataset.
- Verb topology is currently enforced by Teacher/Skill guidance, not by a
  dedicated runtime instruction validator. Audit typed-operator adherence in
  the paired pilot before adding a hard validator.
- Qwen cache reuse is artifact-path based. Changed prompt/config experiments
  must always use new empty run directories; do not reuse an experiment path.

## Unresolved Decisions

- Model-level image execution must determine whether the accepted selective
  `query_skill` supervision improves downstream generation quality; the
  16-row action probe cannot establish that claim.

## Last Reviewer Verdict

The latest review is the HPSv3 auxiliary quality guard review. GPT-5.6 Sol
returned `PASS` for the GPT-5.5 Teacher `G`/`G+H` paired pilot. The verdict does
not approve PlannerContext v0.8 for the frozen SFT planner, SFT export, or
policy promotion. The reviewed protocol requires the 18-row calibration,
disjoint 60-row confirmation set, conjunctive Geneval2/HPS/human gates, and
episode-cluster analysis.

The earlier Flow-DPPO 1000 v9 selective-Skill SFT Gate 3 review returned
`PASS_FREEZE_WITH_MONITORING`. The reviewed frozen export was used unchanged
for the completed formal run.

Earlier active verdicts remain unchanged. Planner I/O native
`decision_summary` is `FAIL_KEEP_V05`; Gate 3a Skill-v1 Trace I/O Clarity is
`APPROVE`. The older general Skill-attribution review remains
`REQUEST_CHANGES`, while the later Gate 3 freeze accepts only the 999
validated productive Skill calls for this run.

## Next Autonomous Action

Preserve the completed trajectories, frozen SFT export, formal full-SFT
checkpoints, and frozen-test-20 production rollout unchanged. The immediate
paired-evidence step is the prepared same-20 Qwen raw-prompt single/Best-of-5
baseline. The later model-level scale step is a separately named official
Geneval2 800-row run; do not mix its official prompts with the frozen SFT-test
episode report.

If prioritizing ablation evidence, first run the zero-image-call Stage 0
analysis and planner-only Stage 1 screen in
`docs/research/muse_image_selective_lessons_and_ablation_plan.md`. Before any
live ablation, satisfy the selector/estimand, live feedback-granularity,
independent-audit, information-isolation, and cost-accounting requirements in
the Sol review. Do not change selector semantics without a separate ADR and
protocol validation.

The older Phase 3 HQ5 resume instructions remain archived in
`docs/operations/phase3_hq5_interruption_status.md`; they are not part of the
current Phase 7 autonomous action.
