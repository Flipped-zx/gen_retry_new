# v0.7 Dual-Backend Diagnostic Prompt Selection

## Purpose

This is a small diagnostic comparison set for the proposed v0.7 execution
profile. It is not a benchmark sample and must not be used to claim aggregate
Geneval2 improvement.

The five primary prompts are frozen Flow-DPPO synthetic training prompts that
already have complete legacy edit-only trajectories. The official Geneval2
800-row test set remains held out.

Structured manifest:
`artifacts/phase6/v07_dual_backend_selected_prompts.json`.

Fresh comparison rollout directories:

- `runs/phase6_v07_dual_backend5_score_v06/`
- `runs/phase6_v07_legacy_edit_only5_score_v06/`

Preparation summaries:

- `artifacts/phase6/v07_dual_backend_score_v06_prepared_rollouts.json`
- `artifacts/phase6/v07_legacy_edit_only_score_v06_prepared_rollouts.json`

These directories contain only task, initial PlannerContext, immutable setup
events, and their respective execution-profile lock. No Teacher, image model,
or Geneval2 call has been made.

## Selected failure cases

| Legacy episode | Difficulty | Legacy pass | Legacy submitted GM | Why selected |
|---|---:|---:|---:|---|
| `phase3_ep_001` | hard | 8 -> 8 / 11 | 0.0528 | Three global count/attribute failures survived four edits. Tests whether a real T2I restart is preferable to continued local editing. |
| `phase3_ep_008` | hard | 9 -> 9 / 11 | 0.0808 | Chasing and cat count persisted; the legacy source-free regenerate collapsed to 7/11. Directly tests the new Qwen-Image regeneration route. |
| `phase3_ep_010` | hard | 7 -> 8 / 11 | 0.0334 | Bagel identity/count/color stayed unresolved after repeated replacement edits. Tests object identity repair versus complete regeneration. |
| `phase3_ep_012` | hard | 5 -> 9 / 11 | 0.1070 | Atom pass count improved, but support relation and candle count kept GM low. Tests whether productive editing should continue or switch to a fresh layout. |
| `phase3_ep_020` | easy | 5 -> 5 / 6 | 0.7111 | Only the `chasing` relation remained failed through four edits. Isolates verb/action evidence from global complexity. |

Optional regression control:

- `phase3_ep_011` reached 11/11 and submitted GM 0.9464 after branching back
  to the first image for a second edit. Run it only when one additional prompt
  is affordable; it checks that dual routing does not damage a known successful
  edit workflow.

## Comparison questions

Each selected failure case answers a different question:

1. Does Qwen-Image produce a stronger first scene than white-canvas
   Qwen-Image-Edit generation?
2. When the Planner chooses a later `generate_image`, does a true source-free
   T2I backend avoid the legacy regeneration collapse?
3. Does the Planner naturally switch between edit and restart when the two
   operations have genuinely different effects?
4. Are persistent verb failures caused by action selection, edit capability,
   or Geneval2 evidence sensitivity?
5. Does submitted GM improve without sacrificing submitted AM or atom pass
   count?

## Frozen comparison controls

- Same original prompts and atom constraints.
- Same GPT-5.5 Teacher policy and prompt contract.
- Same maximum of five image attempts.
- Same Geneval2 evaluator and normalization.
- Same `geneval2_pass_count_then_gm@1` reducer and submission semantics:
  pass-count first, prompt-level GM only as a tie-break.
- Same image resolution and quality-oriented inference defaults per backend.
- Fresh run directories; no legacy image reuse.
- Persist action type, source, backend/model ID, seed, inference parameters,
  GPU-seconds, evaluator results, transitions, best, and submission.

The existing legacy trajectories provide a first reference arm. Any causal
claim about renderer effects additionally requires a fixed-action matched
replay because an adaptive Planner may choose different later actions after
seeing different first images.

## Later execution

On a two-device host, run one sequential episode worker per eligible device:

Dual profile:

```bash
python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root runs/phase6_v07_dual_backend5_score_v06 \
  --execution-profile-id qwen_dual_backend \
  --max-workers 2
```

Matched legacy profile:

```bash
python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root runs/phase6_v07_legacy_edit_only5_score_v06 \
  --execution-profile-id qwen_image_edit_only \
  --max-workers 2
```

Each episode remains sequential because its next Planner action depends on the
preceding image and Geneval2 observation. The scheduler parallelizes different
episodes, serializes simultaneous model-load peaks, isolates worker logs, and
resumes each episode from immutable events.
