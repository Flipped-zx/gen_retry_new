# Phase 7 Flow-DPPO 200-Trajectory Run

## Workload

- Source: UniRL Flow-DPPO Geneval2 synthetic `train.jsonl`.
- Selection: 200 unique non-test prompts.
- Hard distribution: 25 prompts for each `atom_count` from 3 through 10.
- Local reporting tiers: 75 easy, 75 medium, 50 hard.
- Episode budget: at most 5 image attempts, or at most 1,000 images total.
- Planner: GPT-5.5 with Action Protocol v0.5 and PlannerContext v0.6.
- Execution: `qwen_dual_backend@1`.
- Evaluator: local Geneval2 with pass-count then GM best selection.
- Quality: 40 edit steps, 50 generation steps, 1024 x 1024.

The official 800-row Geneval2 file is held out. These are synthetic training
prompts with an official-like atomicity distribution, not an official
benchmark evaluation.

## Parallelism

One fixed worker owns one physical HCU. Episodes are parallel across cards;
attempts remain sequential inside an episode because every next PlannerContext
depends on the preceding image and Geneval2 result. A submitted episode is
skipped on resume.

The existing global model-load lock remains enabled to avoid transient
host-memory and storage spikes. This is safe but means 8-card scaling will be
less than perfectly linear.

## Time Estimate

Five completed v0.7 trajectories took 21.64-26.42 minutes each, with a mean of
23.62 minutes for five attempts. The 200-episode upper-budget workload is
therefore about 78.7 GPU-hours.

| Cards | Ideal compute time | Operational planning window |
| ---: | ---: | ---: |
| 2 | 39.4 h | 43-48 h |
| 4 | 19.7 h | 22-26 h |
| 8 | 9.8 h | 12-16 h |

The wider 8-card window accounts for serialized model loading, shared storage,
Teacher API concurrency, evaluator variance, and tail episodes. Early
all-constraint submissions can reduce these times; interruptions and retries
can increase them.

## Runtime Paths

- Run root: `runs/phase7_flow_dppo200_official_mix_v07_score_v06`
- Selection:
  `artifacts/phase7/flow_dppo200_official_mix_selected_prompts.json`
- Selection report:
  `docs/phase7/flow_dppo200_official_mix_selection_report.md`
- Preparation summary:
  `artifacts/phase7/flow_dppo200_official_mix_prepared_rollouts.json`
- Scheduler log:
  `runs/phase7_flow_dppo200_official_mix_v07_score_v06/orchestrator.log`
- Per-episode logs:
  `runs/phase7_flow_dppo200_official_mix_v07_score_v06/parallel_logs/`
- tmux session: `gen_retry_phase7_flow200`

## Resume Contract

- Preparation refuses to overwrite any non-empty episode directory.
- Immutable events are authoritative.
- Complete images and Geneval2 reports are hash-checked and reused.
- A restarted scheduler skips submitted episodes and resumes incomplete
  suffixes.
- No legacy image or attempt is imported.

## Live Status

- Selection SHA:
  `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`.
- Prepared fresh episodes: 200/200.
- Dry-run workers: 2 HCUs, one worker per card.
- GPT-5.6 Sol distribution review: `PASS`.
- Scheduler launch: pending the pre-launch Git commit.
