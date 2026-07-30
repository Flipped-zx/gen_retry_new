# v0.7 Dual-Backend / PlannerContext v0.6 Five-Trajectory Analysis

## Verdict

The result is **mechanistically positive but performance-mixed**.

- Planner/reducer behavior improved in the intended direction.
- Submitted atom pass count improved slightly versus the five matched
  historical trajectories.
- Submitted Geneval2 GM and AM did not improve in aggregate.
- This five-prompt diagnostic does not support a general performance claim.

## Experimental Scope

- Prompts: four hard and one easy prompt from the frozen Flow-DPPO Geneval2
  training selection.
- Comparison: the same five prompt IDs in the completed historical v0.5 batch.
- New Agent input: PlannerContext v0.6.
- New best rule: higher pass count, then higher GM, then earlier Attempt.
- New execution profile: source-free generate through Qwen-Image-2512; edit
  through Qwen-Image-Edit-2511.
- Fixed image budget: five attempts per trajectory.
- Total new images/evaluations: 25/25.
- This is not the official 800-prompt Geneval2 benchmark protocol.

## Aggregate Result

| Metric | Historical five | New five | Delta |
| --- | ---: | ---: | ---: |
| First-attempt atom pass | 34/50 | 35/50 | +1 |
| Submitted atom pass | 39/50 | 40/50 | +1 |
| First-attempt GM | 17.41 | 7.81 | -9.60 |
| Submitted GM | 19.70 | 18.32 | -1.38 |
| Submitted AM | 77.68 | 77.33 | -0.35 |
| Retry atom gain | +5 | +5 | 0 |
| Retry GM gain | +2.30 | +10.51 | +8.21 |
| All-pass episodes | 0/5 | 0/5 | 0 |

The new system started with much lower GM but recovered more strongly during
retry. It finished one atom ahead, but the recovery was insufficient to exceed
the historical submitted GM.

## Paired Outcomes

| Episode | Tier | Old submitted | New submitted | Paired result |
| --- | --- | --- | --- | --- |
| `phase3_ep_001` | hard | 8/11, GM 5.28 | 8/11, GM 8.77 | equal atoms, higher GM |
| `phase3_ep_008` | hard | 9/11, GM 8.08 | 9/11, GM 22.80 | equal atoms, higher GM |
| `phase3_ep_010` | hard | 8/11, GM 3.34 | 9/11, GM 7.39 | more atoms |
| `phase3_ep_012` | hard | 9/11, GM 10.70 | 10/11, GM 42.69 | more atoms |
| `phase3_ep_020` | easy | 5/6, GM 71.11 | 4/6, GM 9.94 | fewer atoms |

All four hard cases improved under the hierarchical comparison. The single
easy verb/count case regressed enough to dominate the batch GM mean.

## What Actually Improved

### 1. GM Entered The Decision Loop Correctly

- GM tie-break updated best six times while pass count tied.
- In `phase3_ep_001`, `a_001` through `a_004` all remained 8/11, while GM
  rose from 3.44 to 8.77. The reducer tracked that improvement.
- In `phase3_ep_012`, source-free `a_002` remained 9/11 but raised GM from the
  previous best 8.00 to 19.01, making it the correct source for the next edit.

### 2. Pass Count Remained Primary

- Two attempts had higher GM but fewer passing atoms and were correctly
  rejected.
- The clearest case is `phase3_ep_008`: `a_002` had GM 26.16 versus `a_001`
  at 22.80, but regressed from 9/11 to 8/11. The reducer retained `a_001`.

### 3. Latest And Best Were Used As Different Facts

- Four edits used a historical source rather than the immediately preceding
  image.
- Three episodes submitted historical best rather than latest.
- `phase3_ep_012` ended with latest `a_004` at 9/11 after regressing
  `c_010`, but submitted best `a_003` at 10/11.
- `phase3_ep_020` recovered from catastrophic `a_002` by editing historical
  best `a_001`, not the broken latest image.

### 4. Generate And Edit Became Meaningfully Different Actions

- Seven source-free calls used Qwen-Image-2512.
- Eighteen source-conditioned calls used Qwen-Image-Edit-2511.
- The Agent chose two post-initial regenerations.
- In `phase3_ep_012`, an ineffective edit was followed by a source-free
  regenerate, then a productive edit that reached 10/11.

The backend remained environment-owned. The Teacher selected only the semantic
action and source; it did not learn backend/model/mode fields.

## What Did Not Improve

### 1. First-Generation GM Regressed

First-attempt atom pass increased by one, but mean GM fell by 9.60. The new
Qwen-Image route produced sharp images, yet exact count and relation confidence
was often weak.

Examples:

- `phase3_ep_001` generated two birds and eight suitcases instead of one and
  seven.
- `phase3_ep_020` produced visually plausible pursuit scenes but failed both
  exact rabbit count and the Geneval2 chasing atom.

This rules out the claim that switching source-free generation to Qwen-Image
is already a uniform metric improvement.

### 2. The Verb/Count Case Regressed

`phase3_ep_020` is the blocking counterexample:

- historical submission: 5/6, GM 71.11;
- new submission: 4/6, GM 9.94;
- one edit removed the elephant and fell to 1/6;
- rollback restored 4/6;
- final regeneration still failed rabbit count and chasing.

The image quality was not blurry. The failure was semantic and evaluator-facing:
exact count plus explicit action relation remained unresolved.

### 3. No Trajectory Reached All-Pass

Retry improved the new batch from 35/50 to 40/50, but no trajectory reached
all atoms. Repeated local edits often preserved image quality while failing to
repair the target relation, or repaired one atom and later regressed it.

## Runtime And Parallelism

- The scheduler used one sequential episode worker per physical HCU.
- Different episodes ran in parallel; attempts inside one episode remained
  sequential because each action depended on the preceding image/evaluation.
- No card hosted two simultaneous local image workers and no OOM occurred.
- Submitted trajectories were never rerun.
- `phase3_ep_001` initially stopped before image generation because runtime
  rejected a second novel Skill query. GPT-5.6 Sol confirmed this contradicted
  the accepted zero-to-N query semantics.
- The corrected runtime allows at most two successful novel Skill queries per
  image-producing round. The same immutable episode prefix resumed on the
  freed second HCU and completed with five image attempts.
- The four obsolete rejection events remain for audit and do not count as
  image attempts. Planner-call count, repair count, latency, and cost for this
  one episode are not comparable with its historical pair.

## SFT Interpretation

The batch should not be flattened into uniformly positive supervision.

Strong behavior examples:

- `phase3_ep_012` source-free regeneration after an ineffective edit;
- `phase3_ep_012` productive edit from the GM-selected best;
- `phase3_ep_008` continued branching from pass-count best despite a
  higher-GM/lower-pass latest;
- historical-best submissions after regressions.

Harmful or weak examples:

- `phase3_ep_020` edit that removed the elephant;
- repeated edits that changed GM but fixed no atom, unless explicitly used for
  tie-break policy supervision;
- the four obsolete `consecutive_query_skill` rejections;
- the remaining instruction-quality-invalid raw Teacher turn.

Environment observations, scores, Skill responses, and outcomes remain context
only rather than assistant targets.

## Claim Boundary And Next Evidence

Supported:

- PlannerContext v0.6 fields are consumed correctly.
- GM is a useful secondary selector when pass count ties.
- pass-first ordering prevents a higher-GM atom regression from replacing best.
- dual backend routing gives generate/edit genuinely different execution.
- the adaptive loop improved four of five matched cases under hierarchical
  comparison.

Not supported:

- overall Geneval2 GM improvement;
- uniform renderer improvement;
- causal attribution to Qwen-Image, GM feedback, PlannerContext, Skills, or the
  Teacher prompt separately;
- benchmark-level generalization.

The highest-value next comparison is the already prepared matched
`qwen_image_edit_only@1` PlannerContext v0.6 arm. A fixed first-instruction and
seed replay is still required to isolate renderer effects from adaptive policy
changes and generation randomness.

## References

- Validation:
  `docs/phase6/v07_dual_backend5_score_v06_validation_report.md`
- Machine summary:
  `artifacts/phase6/v07_dual_backend5_score_v06_validation_summary.json`
- Paired comparison:
  `docs/phase6/v07_dual_backend5_score_v06_paired_comparison.md`
- Machine paired data:
  `artifacts/phase6/v07_dual_backend5_score_v06_paired_comparison.json`
- Representative real I/O walkthrough:
  `docs/phase6/planner_io_v06_round_memory_walkthrough_phase3_ep012.md`
