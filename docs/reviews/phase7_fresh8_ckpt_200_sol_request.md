# Phase 7 Fresh-8 Checkpoint 200 Final Sol Review Request

## Gate

`Final 200-trajectory deep review`

## Scope

Review final all-ID validity, claim boundaries, SFT ownership, resume
semantics, and v8 mechanism evidence. Do not edit files, invoke live
Teacher/Qwen/Geneval2, inspect credentials, or reinterpret the nonrandom
version split as a causal ablation.

## Frozen Contracts

- PlannerContext `0.6`
- Action Protocol `0.5`
- Score policy `geneval2_pass_count_then_gm@1`
- Execution profile `qwen_dual_backend@1`
- At most five image attempts
- Accepted routing:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`

## Evidence

- Final all-ID audit:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_200_final_audit.md`
- Final report:
  `docs/phase7/flow_dppo200_final_report.md`
- Fixed admission closure:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_200_admission_status.md`
- Version stratification:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_200_version_stratified_note.md`
- Final SFT reconciliation:
  `docs/phase7/checkpoints/fresh8_v1_ckpt_200_sft_reconciliation.md`
- Final resource profile:
  `docs/phase7/checkpoints/fresh8_v1_queue_final_resource_profile.md`
- Real v8 Planner I/O walkthrough:
  `docs/phase7/planner_io_v06_v8_round_memory_walkthrough_phase3_ep176.md`
- Final behavior labels:
  `docs/phase7/checkpoints/ckpt_200_final_analysis/sft_candidate_action_report.md`
- Accepted routing decision:
  `docs/decisions/ADR-0006-qwen-dual-backend-execution-profile.md`
- Current module contracts:
  `docs/architecture/MODULE_CONTRACTS.md`

## Final Evidence Summary

- 200/200 fixed IDs have valid submissions; 684 image attempts.
- Atom pass: 1159/1419 -> 1301/1419.
- Soft-TIFA AM: 81.87 -> 90.90.
- Soft-TIFA GM: 42.58 -> 73.50.
- All-pass: 51/200 -> 111/200.
- Submitted-to-peak GM gap: 0.75; all nine higher-GM rejected images passed
  one fewer atom.
- Tier counts: 75 easy, 75 medium, 50 hard, assigned before rollout.
- Final atom pass: object 455/459, attribute 282/304, count 395/459,
  position 159/175, verb 10/22.
- Chasing remains 2/12 at submission.

Resume and version boundary:

- 198 episodes closed in continuous pass one.
- `phase3_ep_069` and `phase3_ep_184` resumed only their pending state and
  completed; no valid trajectory reran.
- Version groups: 162 v7-only, 37 v8-only, one mixed resume.
- v7-only equivalent repeats: 65/148 closure opportunities.
- v8-only equivalent repeats: 0/32 closure opportunities.
- No causal v8 performance claim is made.

SFT reconciliation:

- 1,159 labeled records.
- 663 canonical targets and 496 context-only records.
- 193 query-Skill, 106 harmful, 115 ineffective, and 82 raw rejected records
  remain context-only.
- Zero mask, canonical-target, execution-profile, context/score-contract, or
  prompt-group split violation.

Infrastructure:

- Mean 5.45/8 active HCUs and median six over the full queue.
- All 53 zero-HCU samples occurred only in final queue drain/retry windows;
  no all-idle sample occurred through checkpoint 180.
- No episode 51-200 OOM, API timeout, connection error, or rate limit.

## Questions

1. Is there any final data-validity, routing, evaluator, memory, resume,
   SFT-boundary, score-selection, cohort, or future-leakage blocker?
2. Are the supported claims appropriately limited to this fixed synthetic
   batch and descriptive v8 mechanism evidence, with leaderboard and causal
   claims excluded?
3. Is the completed dataset ready to proceed to the next SFT supervision gate,
   or is a blocking prospective fix required first?

## Expected Response

Return one of:

- `PASS_FINAL`
- `FAIL_BLOCKING`

Answer all three questions directly. Separate blocking validity issues from
optional future experiments.
