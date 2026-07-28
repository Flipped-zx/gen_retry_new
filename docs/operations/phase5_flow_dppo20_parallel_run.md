# Phase 5 Flow-DPPO 20-Trajectory Run

## Workload

- Source: UniRL Flow-DPPO Geneval2 synthetic `train.jsonl`.
- Selection: 12 hard, 5 medium, 3 easy.
- Held-out boundary: official 800-row `test.jsonl`.
- Episode budget: at most 5 image attempts.
- Teacher: configured GPT-5.5.
- Image backend: local Qwen-Image-Edit-2511.
- Evaluator: local Geneval2.
- Quality: 40 inference steps at 1024 x 1024.

## Two-GPU Schedule

Two fixed worker loops share an episode queue. Each worker:

1. binds one physical HCU through `ROCR_VISIBLE_DEVICES`;
2. runs at most one episode child at a time;
3. preserves sequential action order inside that episode;
4. continues to the next queued episode when a child fails.

On this ROCm/HCU host, setting CUDA, HIP, and ROCR visibility variables
simultaneously caused device 1 to be filtered twice and made
`torch.cuda.is_available()` false. Only `ROCR_VISIBLE_DEVICES` is set for
`hy-smi` devices.

Qwen and Geneval2 do not remain resident together. Their model-load sections
share an inter-process file lock. This serializes transient disk/host-memory
loading but releases the lock after a model reaches its assigned GPU, allowing
the two cards to run inference concurrently.

Observed live envelope after the fix:

- GPU 0: about 85-93% VRAM during Qwen inference.
- GPU 1: about 88-93% VRAM during Qwen inference.
- Both cards reached 100% compute concurrently.

## Resume Chain

The event log is authoritative. A restart deterministically completes the first
missing suffix stage before another Teacher call:

```text
image_execution_started
-> image_execution_completed
-> geneval2_completed
-> memory_reduced
-> round_record_persisted
-> planner_context_built
```

An existing complete image is hash-checked and not regenerated. A complete
Geneval2 report is reused after constraint-coverage validation. Preparation
never overwrites a non-empty episode directory.

## Runtime Paths

- Run root: `runs/phase5_flow_dppo20`
- Selection artifact:
  `artifacts/phase5/flow_dppo_selected_20_prompts.json`
- Preparation summary:
  `artifacts/phase5/flow_dppo20_prepared_rollouts.json`
- Scheduler log: `runs/phase5_flow_dppo20/orchestrator.log`
- Per-episode logs: `runs/phase5_flow_dppo20/parallel_logs/`
- tmux session: `gen_retry_flow20_v05`

## Completion

- Scheduler status: complete; no rollout process or tmux session remains
  active.
- Submitted episodes: 20/20.
- Evaluated image attempts: 92.
- Aggregate first-attempt atom pass: 137/200.
- Aggregate best-attempt atom pass: 171/200.
- Deterministic validation: `docs/phase5/flow_dppo20_validation_report.md`
  (`PASS`).
- Final GPT-5.6 Sol review:
  `docs/reviews/gate4_flow_dppo20_final_review.md` (`PASS`).
