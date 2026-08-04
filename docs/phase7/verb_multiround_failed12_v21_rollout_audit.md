# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 12/12
- PlannerContext versions: {'0.6': 12}
- Score policies: {'geneval2_pass_count_then_gm@1': 12}
- Execution profiles: {'qwen_dual_backend@1': 12}
- Image backends: {'qianwen_image_edit': 43, 'qwen_image': 17}
- Difficulty mix: {'easy': 6, 'hard': 3, 'medium': 3}
- Evaluated image attempts: 60
- Aggregate first Agent attempt atom pass rate: 59/84 (70.2%)
- Aggregate submitted reducer-best atom pass rate: 67/84 (79.8%)
- Net submitted-over-first atom gain: +8
- Geneval2 Soft-TIFA AM, first Agent attempts: 68.81
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 80.00 (+11.19)
- Geneval2 Soft-TIFA GM, first Agent attempts: 12.87
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 37.51 (+24.64)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 38.17 (+25.30)
- Submitted-to-peak GM gap: 0.66
- Episodes with all atoms passed: 1/12
- Historical-best submissions: 5/12
- Regression exposure: 11/12 episodes, 16 image actions
- Ineffective image actions: 5
- Historical edit branches: 8
- Canonical action counts: {'edit_image': 43, 'generate_image': 17, 'query_skill': 23, 'submit_attempt': 12}
- Action/backend counts: {'edit_image|qianwen_image_edit': 43, 'generate_image|qwen_image': 17}
- Scheduler profiles: 1 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 7 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 7 remain instruction-quality-invalid).
- Credential-like text in audited outputs: 0 files

## Score Semantics

For each image, Geneval2 Soft-TIFA derives AM and GM from the VQA correct-answer probabilities:

```text
image_AM = mean(atom_probability)
image_GM = exp(mean(log(max(atom_probability, 1e-300))))
batch_AM = 100 * mean(image_AM)
batch_GM = 100 * mean(image_GM)
```

AM is the atom-level continuous score; GM is the prompt-level score and the primary Flow-DPPO reporting metric. Both differ from thresholded atom pass rate. Gen-Retry selects best by passed-atom count, then higher Soft-TIFA GM, then the earlier Attempt. A trajectory's submitted GM can still be lower than its peak GM when the peak-GM image passes fewer atoms.

PlannerContext v0.6 exposed the environment-owned GM scalar for latest/best plus source-aware GM deltas. The Planner did not see raw confidence vectors or AM; it saw GM together with normalized atom statuses and observed answers.

When the fifth image both exhausts the image budget and reaches all constraints, runtime control requires the terminal reason `best_available_under_budget`. The episode still counts as all-pass; the reason records why submission became mandatory, not the quality of the selected image.

These are actual Soft-TIFA AM/GM scores recomputed from the persisted local Qwen3-VL correct-answer probabilities. They are not official leaderboard scores: this batch uses Flow-DPPO training prompts, profile-routed local image generation at 1024 x 1024, and one trajectory-selected image per prompt rather than the official 800-prompt benchmark generation protocol.

## Difficulty Policy

The tiers are a deterministic local grouping over committed Flow-DPPO training metadata, scaled from the official Geneval2 atom-count distribution. They are not official Geneval2 difficulty labels and do not use post-hoc image outcomes:

- **Hard:** source `atom_count` 9-10.
- **Medium:** source `atom_count` 6-8.
- **Easy:** source `atom_count` 3-5.
- This batch mix: {'easy': 6, 'hard': 3, 'medium': 3}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_014` | medium | 5 | 6/8 | 74.91 | 2.05 | 6/8 (`a_004`) | 74.01 | 33.50 | 33.50 (`a_004`) | +0 |
| `phase3_ep_032` | hard | 5 | 8/10 | 80.00 | 6.55 | 8/10 (`a_004`) | 80.99 | 26.56 | 26.56 (`a_004`) | +0 |
| `phase3_ep_042` | easy | 5 | 3/5 | 60.25 | 1.99 | 4/5 (`a_003`) | 81.43 | 59.03 | 59.03 (`a_003`) | +1 |
| `phase3_ep_051` | easy | 5 | 2/5 | 40.01 | 0.07 | 4/5 (`a_002`) | 78.93 | 12.10 | 12.10 (`a_002`) | +2 |
| `phase3_ep_098` | easy | 5 | 4/5 | 80.65 | 50.35 | 5/5 (`a_004`) | 97.06 | 96.87 | 96.87 (`a_004`) | +1 |
| `phase3_ep_107` | easy | 5 | 2/5 | 45.19 | 0.26 | 3/5 (`a_004`) | 61.18 | 7.72 | 7.72 (`a_004`) | +1 |
| `phase3_ep_116` | medium | 5 | 7/8 | 84.73 | 20.70 | 7/8 (`a_004`) | 90.94 | 87.61 | 87.61 (`a_004`) | +0 |
| `phase3_ep_135` | hard | 5 | 7/10 | 72.55 | 8.89 | 8/10 (`a_003`) | 77.87 | 11.21 | 11.21 (`a_003`) | +1 |
| `phase3_ep_154` | easy | 5 | 4/5 | 80.04 | 29.65 | 4/5 (`a_001`) | 80.32 | 48.55 | 48.55 (`a_001`) | +0 |
| `phase3_ep_163` | easy | 5 | 3/5 | 60.00 | 1.02 | 4/5 (`a_004`) | 80.00 | 8.85 | 8.85 (`a_004`) | +1 |
| `phase3_ep_181` | medium | 5 | 7/8 | 87.50 | 31.36 | 7/8 (`a_001`) | 87.58 | 53.68 | 53.68 (`a_001`) | +0 |
| `phase3_ep_200` | hard | 5 | 6/10 | 59.91 | 1.50 | 7/10 (`a_004`) | 69.69 | 4.39 | 12.34 (`a_001`) | +1 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Observed Constraint Regression: `phase3_ep_014`

- Action: `edit_image` from `a_002`.
- Fixed atoms: none.
- Regressed atoms: ['c_004'].
- Reducer best after the full episode: `a_004`.
- Result `a_003`: 5/8 atoms, GM 13.21.

### Historical-Source Branch: `phase3_ep_014`

- Latest before the action was `a_003`.
- The Agent deliberately edited historical source `a_002`.
- Fixed atoms: none; regressed atoms: none.
- Result `a_004`: 6/8 atoms, GM 33.50.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_032`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_004', 'c_009']; regressed atoms: ['c_008'].
- Result `a_002`: 8/10 atoms, GM 9.14.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
