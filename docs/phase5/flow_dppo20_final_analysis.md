# Flow-DPPO 20-Trajectory Final Analysis

## Batch Result

- Source: UniRL Flow-DPPO Geneval2 synthetic training split at commit
  `e1a814ff9de6de644b093c6ed0106869c1881e53`.
- Selection: 12 hard, 5 medium, 3 easy; the official 800-row test set and
  overlapping semantic families were excluded.
- Execution: 20/20 fresh native PlannerContext/action v0.5 episodes submitted.
- Images: 92 local Qwen-Image-Edit attempts, all 1024 x 1024 at 40 steps.
- Evaluation: every attempt has complete Geneval2 coverage for its frozen VQA
  atom rubric.
- Aggregate first Agent attempt pass: 137/200 atoms (68.5%).
- Aggregate submitted reducer-best pass: 171/200 atoms (85.5%).
- Net gain: +34 atoms; 13/20 trajectories improved over their first image.
- Geneval2 Soft-TIFA AM: first Agent attempts 69.38; submitted reducer-best
  attempts 84.70; gain +15.32.
- Geneval2 Soft-TIFA GM: first Agent attempts 20.99; submitted reducer-best
  attempts 47.25; per-trajectory peak attempts 53.33.
- Complete success: 4/20 trajectories.
- Historical best submitted after later exploration: 13/20 trajectories.

## Difficulty

| Tier | Episodes | Attempts | Initial Pass | Best Pass | All-Pass Episodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| hard | 12 | 58 | 92/133 (69.2%) | 111/133 (83.5%) | 1 |
| medium | 5 | 25 | 31/48 (64.6%) | 42/48 (87.5%) | 1 |
| easy | 3 | 9 | 14/19 (73.7%) | 18/19 (94.7%) | 2 |

The tier labels describe static Flow-DPPO/VQA complexity, not measured model
difficulty. This small batch is architecture and supervision evidence, not an
unbiased benchmark estimate.

The AM and GM values are actual scores recomputed from persisted local
evaluator correct-answer probabilities. AM measures atom-level continuous
correctness; GM measures prompt-level joint correctness and is the primary
Flow-DPPO reporting metric. They are not official 800-prompt leaderboard
results because prompt split, generator, resolution, and trajectory selection
protocol differ. Reducer best currently uses thresholded pass count and keeps
the earlier attempt on ties, so submitted GM can be lower than trajectory peak
GM.

## Capability Result

| Atom type | Slots | Initial Pass | Best Pass | Net Gain |
| --- | ---: | ---: | ---: | ---: |
| object | 57 | 48 (84.2%) | 55 (96.5%) | +7 |
| attribute | 49 | 40 (81.6%) | 45 (91.8%) | +5 |
| position | 22 | 15 (68.2%) | 20 (90.9%) | +5 |
| count | 57 | 32 (56.1%) | 44 (77.2%) | +12 |
| verb | 15 | 2 (13.3%) | 7 (46.7%) | +5 |

Retry behavior materially improves count, position, and verb atoms, but action
relations remain the dominant unresolved weakness. The current foundational
`action_pose_relation` Skill gives relevant planning context; this batch does
not prove that querying it causes the improvement, so `query_skill` remains
loss 0.

## Action And Supervision Result

Canonical history contains 24 `query_skill`, 29 `generate_image`, 63
`edit_image`, and 20 `submit_attempt` actions.

The post-hoc labels contain:

- 59 candidate v0.5 targets: 23 generation, 16 edit, and 20 submit actions;
- 24 valid `query_skill` actions retained only as loss-0 context;
- 24 harmful and 29 ineffective image actions retained in history, not as
  positive targets;
- 28 rejected raw Teacher turns retained only as audit evidence.

The actual v0.5 SFT renderer dry run emits exactly those 59 targets and masks
105 records. Its report is
`docs/phase5/flow_dppo20_sft_dry_run_report.md`.

Of the 28 rejected raw turns, 18 pass the corrected current validator. The
remaining 10 comprise 5 invalid Skill references and 5 instruction-quality
failures. No rejected raw turn enters canonical action history or the positive
SFT target set.

All canonical image and submit targets use action protocol v0.5. Teacher
requests span system prompt v4 and v5 because the static Skill catalog was
added while the resumable batch was running; the exact version is persisted
per request. The final SFT renderer uses the single frozen v0.5 training system
contract rather than copying either rollout-only Teacher prompt.

## Representative Trajectory

`phase3_ep_011` is the clearest successful multi-round example:

1. It queries count, static spatial-relation, and attribute-binding Skills.
2. Fresh generation produces `a_000` with 10/11 atoms passed; only “flowers
   under pigs” fails.
3. Editing `a_000` produces `a_001` with no atom gain.
4. The next PlannerContext exposes latest `a_001`, best `a_000`, and the
   ineffective prior edit. The Planner branches from historical best `a_000`
   instead of blindly editing latest.
5. The second edit produces `a_002`, fixes `c_008`, preserves the other ten
   atoms, and reaches 11/11.
6. The Planner submits `a_002` with `all_constraints_passed`.

The complete actual PlannerContext, sanitized Teacher input, raw redacted
output, canonical action, tool response, image/Geneval2 observation, transition,
and submission are rendered in
`docs/phase5/flow_dppo20_analysis/trajectory_trace_phase3_ep_011.md`.

A shorter round-by-round field walkthrough, showing the actual changing Agent
input, visible images, canonical output, and environment update, is
`docs/phase5/planner_io_v05_round_memory_walkthrough_flow_dppo_ep011.md`.

## Validation Boundary

The deterministic batch audit passed for all 20 trajectories:

- selection prompt and frozen atom rubric match;
- schemas and manifest hashes close;
- the first image action is a source-free fresh generation;
- edit lineage uses the declared `source_attempt_id`;
- every image and Geneval2 report is present;
- every image round has memory, RoundRecord, and next-context suffix events;
- each PlannerContext snapshot matches the point-in-time latest, best, and
  remaining budget, with no future attempt state;
- submission selects reducer best;
- persisted Teacher outputs are sanitized and contain no credential-like key.

Machine-readable evidence is
`artifacts/phase5/flow_dppo20_validation_summary.json`. Per-action labels are
`artifacts/phase5/flow_dppo20_analysis/action_supervision_labels.jsonl`; each
run directory also contains its own `trajectory_analysis.md`.
