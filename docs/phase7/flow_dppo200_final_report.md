# Flow-DPPO Geneval2 200-Trajectory Final Report

## Scope

This report covers the fixed fresh batch
`runs/phase7_flow_dppo200_fresh8_v1/`.

- Teacher/Planner: GPT-5.5.
- PlannerContext: `0.6`.
- Action Protocol: `0.5`.
- `generate_image`: local Qwen-Image-2512.
- `edit_image`: local Qwen-Image-Edit-2511.
- Evaluator: Geneval2 on every image attempt.
- Image budget: at most five attempts per trajectory.
- Resolution: 1024 x 1024.
- Final denominator: all 200 fixed episode IDs.

This is held-out-safe Flow-DPPO synthetic-train evidence. The official
Geneval2 800-row test set was excluded. The reported Soft-TIFA GM is the
formal local Flow-DPPO-compatible Geneval2 score, not an official leaderboard
submission.

## Prompt Selection And Difficulty

Selection artifact:
`artifacts/phase7/flow_dppo200_official_mix_selected_prompts.json`

- Selection SHA:
  `25fd84df1e4aba81c3511bc71ef54d0bb6d061a23a166c82032dca3747b287e8`
- Exactly 25 prompts for each `atom_count` from 3 through 10.
- Easy: atom count 3-5, 75 prompts.
- Medium: atom count 6-8, 75 prompts.
- Hard: atom count 9-10, 50 prompts.
- Ratio: 37.5% easy, 37.5% medium, 25% hard.

Difficulty is assigned from committed prompt metadata before rollout. It is
not inferred from success, latency, or image quality.

## Final Metrics

| Metric | First Agent image | Submitted image | Change |
| --- | ---: | ---: | ---: |
| Passed atoms | 1159/1419 | 1301/1419 | +142 |
| Atom pass rate | 81.68% | 91.68% | +10.01 points |
| Soft-TIFA AM | 81.87 | 90.90 | +9.03 |
| Soft-TIFA GM | 42.58 | 73.50 | +30.92 |
| All-pass trajectories | 51/200 | 111/200 | +60 |

There were 684 evaluated images. The mean per-trajectory peak GM was 74.25,
so submitted GM was 0.75 lower. Nine trajectories had a higher-GM image than
the submitted image; in all nine, that image passed one fewer atom. This is
the expected result of the frozen comparator:

`higher pass count -> higher GM -> earlier attempt`

## Difficulty Results

| Tier | Episodes | Attempts | Initial atoms | Submitted atoms | Initial GM | Submitted GM | All pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Easy | 75 | 191 | 318/374 | 346/374 | 57.49 | 80.19 | 55/75 |
| Medium | 75 | 283 | 447/556 | 516/556 | 33.02 | 73.05 | 39/75 |
| Hard | 50 | 210 | 394/489 | 439/489 | 34.55 | 64.15 | 17/50 |

Medium gained the most atoms (+69). Hard prompts consumed the most images per
episode (4.20) and retained the lowest GM and all-pass rate.

## Atom-Type Results

| Atom type | Total | Initial pass | Submitted pass | Gain | Final pass rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Object | 459 | 454 | 455 | +1 | 99.13% |
| Attribute | 304 | 242 | 282 | +40 | 92.76% |
| Count | 459 | 303 | 395 | +92 | 86.06% |
| Position | 175 | 155 | 159 | +4 | 90.86% |
| Verb | 22 | 5 | 10 | +5 | 45.45% |

Most improvement came from exact count (+92) and attribute binding (+40).
Verb relations remain the clear bottleneck:

- `playing with`: 3/6 -> 5/6.
- `jumping over`: 2/4 -> 3/4.
- `chasing`: 0/12 -> 2/12.

The weak chasing result is not explained by a missing Geneval2 atom: every
chasing prompt has an explicit VQA atom and every attempt was evaluated.
The evidence is compatible with both generator difficulty and VQA sensitivity;
this batch does not isolate those causes.

## What Produced The Gains

The 684 image actions consist of 253 source-free generations and 431 edits.
The source-free total includes 200 initial generations and 53 later
regenerations.

| Outcome signal | Generate | Edit |
| --- | ---: | ---: |
| Became reducer-best | 229 | 230 |
| Fixed at least one atom | 34 | 160 |
| Regressed at least one atom | 14 | 117 |
| Strictly ineffective after first image | 10 | 105 |

Edits supplied most atom repairs, but also most regressions and ineffective
actions. Regeneration was useful when a local edit path stalled. Sixty
episodes submitted an earlier historical best rather than blindly submitting
the latest image.

Representative trajectories:

- `phase3_ep_056`: hard prompt, four edits, +3 atoms, GM 0.21 -> 100.00,
  all-pass `a_004`.
- `phase3_ep_108`: an edit did not close the task, then source-free
  regeneration reached all-pass, +3 atoms and GM 0.07 -> 98.97.
- `phase3_ep_053`: later edits regressed; the Agent submitted historical
  `a_002` instead of latest `a_004`, preserving +2 atoms and GM 82.78.
- `phase3_ep_176`: v8 observed a no-progress edit, changed from edit to
  source-free regeneration, and reached 10/10 atoms.
- `phase3_ep_184`: resumed from two persisted attempts, completed the
  five-attempt trajectory, and submitted historical `a_003`.
- `phase3_ep_200`: count/object/position mostly held, but the chasing verb
  remained failed after five attempts.

The per-trajectory table is in
`docs/phase7/checkpoints/ckpt_200_final_analysis/trajectory_comparison.md`.

## Why Improvement Was Not Larger

1. Verb relations remained weak, especially chasing at 2/12.
2. Count repair improved strongly but still ended at 395/459.
3. Edit actions caused 117 atom regressions and 105 strict ineffective
   outcomes.
4. Eighty-nine trajectories still had at least one failed/uncertain atom at
   submission.
5. Pass-count-first selection correctly rejected nine higher-GM images that
   passed one fewer atom; this accounts for the 0.75 submitted-to-peak GM gap.

## v8 Retry Closure

Teacher policy v8 was introduced prospectively after checkpoint 140 without
changing the Action schema, PlannerContext, score policy, backends, or
completed trajectories.

- v7-only: 65 equivalent repeats across 148 closure opportunities.
- v8-only: zero equivalent repeats across 32 closure opportunities.
- One resumed trajectory is mixed-version and reported separately.

This supports a mechanism-consistency claim, not a causal performance claim.
See
`docs/phase7/checkpoints/fresh8_v1_ckpt_200_version_stratified_note.md`.

## SFT Boundary

The final dry run contains:

- 1,159 labeled action/raw records.
- 663 canonical positive or recovery targets.
- 496 context-only records.
- Target actions: 229 generate, 234 edit, 200 submit.
- Context-only: 193 query-Skill, 106 harmful, 115 ineffective, and 82 raw
  rejected records.
- Split: 160 train, 20 validation, 20 test.

There are zero loss-mask, noncanonical-target, execution-profile,
PlannerContext/score-contract, or prompt-group split violations.

Query-Skill remains a real Planner action in the trajectory, but remains
loss-zero until Skill utility is separately accepted.

## Claim Boundary

Supported:

- all 200 fixed fresh trajectories are complete and resumable;
- retries improve atom pass, AM, and GM within this batch;
- latest/best separation prevents many harmful final submissions;
- v8 removes observed equivalent failed-route repeats;
- the normalized records satisfy the frozen SFT ownership contract.

Not supported:

- official Geneval2 leaderboard performance;
- causal superiority over equal-compute Best-of-K or a fixed retry heuristic;
- causal v8 performance improvement;
- generalization to arbitrary complex prompts outside this distribution.
