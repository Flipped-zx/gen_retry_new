# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 60/60
- PlannerContext versions: {'0.6': 60}
- Score policies: {'geneval2_pass_count_then_gm@1': 60}
- Execution profiles: {'qwen_dual_backend@1': 60}
- Image backends: {'qianwen_image_edit': 114, 'qwen_image': 70}
- Difficulty mix: {'easy': 24, 'hard': 14, 'medium': 22}
- Evaluated image attempts: 184
- Aggregate first Agent attempt atom pass rate: 359/430 (83.5%)
- Aggregate submitted reducer-best atom pass rate: 402/430 (93.5%)
- Net submitted-over-first atom gain: +43
- Geneval2 Soft-TIFA AM, first Agent attempts: 83.16
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 92.39 (+9.23)
- Geneval2 Soft-TIFA GM, first Agent attempts: 46.96
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 80.85 (+33.89)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 81.38 (+34.42)
- Submitted-to-peak GM gap: 0.52
- Episodes with all atoms passed: 41/60
- Historical-best submissions: 10/60
- Regression exposure: 15/60 episodes, 27 image actions
- Ineffective image actions: 28
- Historical edit branches: 27
- Canonical action counts: {'edit_image': 114, 'generate_image': 70, 'query_skill': 57, 'submit_attempt': 60}
- Action/backend counts: {'edit_image|qianwen_image_edit': 114, 'generate_image|qwen_image': 70}
- Scheduler profiles: 6 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 37 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 37 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 24, 'hard': 14, 'medium': 22}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_001` | easy | 2 | 3/4 | 76.53 | 49.77 | 4/4 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_002` | easy | 1 | 6/6 | 99.77 | 99.77 | 6/6 (`a_000`) | 99.77 | 99.77 | 99.77 (`a_000`) | +0 |
| `phase3_ep_003` | easy | 1 | 8/8 | 100.00 | 100.00 | 8/8 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_004` | medium | 5 | 6/7 | 84.73 | 4.30 | 7/7 (`a_004`) | 95.30 | 94.50 | 94.50 (`a_004`) | +1 |
| `phase3_ep_005` | medium | 4 | 6/9 | 67.49 | 28.88 | 9/9 (`a_003`) | 92.06 | 90.78 | 90.78 (`a_003`) | +3 |
| `phase3_ep_006` | medium | 1 | 10/10 | 99.99 | 99.99 | 10/10 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_007` | hard | 2 | 9/10 | 90.12 | 65.31 | 10/10 (`a_001`) | 99.22 | 99.19 | 99.19 (`a_001`) | +1 |
| `phase3_ep_008` | hard | 1 | 10/10 | 97.60 | 97.34 | 10/10 (`a_000`) | 97.60 | 97.34 | 97.34 (`a_000`) | +0 |
| `phase3_ep_009` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_010` | easy | 5 | 4/6 | 67.87 | 2.36 | 5/6 (`a_004`) | 78.93 | 19.60 | 19.60 (`a_004`) | +1 |
| `phase3_ep_011` | easy | 5 | 4/6 | 66.79 | 4.87 | 5/6 (`a_004`) | 84.44 | 63.69 | 63.69 (`a_004`) | +1 |
| `phase3_ep_012` | medium | 3 | 4/6 | 68.26 | 2.86 | 6/6 (`a_002`) | 92.70 | 90.84 | 90.84 (`a_002`) | +2 |
| `phase3_ep_013` | medium | 3 | 7/8 | 91.43 | 87.80 | 8/8 (`a_002`) | 99.84 | 99.84 | 99.84 (`a_002`) | +1 |
| `phase3_ep_014` | medium | 5 | 6/8 | 74.77 | 4.40 | 7/8 (`a_004`) | 87.25 | 49.02 | 49.02 (`a_004`) | +1 |
| `phase3_ep_015` | hard | 1 | 10/10 | 99.97 | 99.97 | 10/10 (`a_000`) | 99.97 | 99.97 | 99.97 (`a_000`) | +0 |
| `phase3_ep_016` | hard | 1 | 10/10 | 96.56 | 95.97 | 10/10 (`a_000`) | 96.56 | 95.97 | 95.97 (`a_000`) | +0 |
| `phase3_ep_017` | easy | 2 | 3/4 | 75.01 | 15.37 | 4/4 (`a_001`) | 99.26 | 99.26 | 99.26 (`a_001`) | +1 |
| `phase3_ep_018` | easy | 1 | 6/6 | 99.99 | 99.99 | 6/6 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_019` | easy | 3 | 5/6 | 83.25 | 19.70 | 6/6 (`a_002`) | 100.00 | 100.00 | 100.00 (`a_002`) | +1 |
| `phase3_ep_020` | medium | 5 | 4/6 | 66.33 | 0.41 | 6/6 (`a_004`) | 98.06 | 97.95 | 97.95 (`a_004`) | +2 |
| `phase3_ep_021` | medium | 2 | 7/8 | 83.47 | 47.89 | 8/8 (`a_001`) | 99.11 | 99.08 | 99.08 (`a_001`) | +1 |
| `phase3_ep_022` | medium | 5 | 6/8 | 74.76 | 2.39 | 7/8 (`a_004`) | 92.25 | 88.62 | 88.62 (`a_004`) | +1 |
| `phase3_ep_023` | hard | 3 | 9/10 | 88.88 | 35.50 | 10/10 (`a_002`) | 95.45 | 94.22 | 94.22 (`a_002`) | +1 |
| `phase3_ep_024` | hard | 5 | 9/10 | 89.75 | 65.01 | 9/10 (`a_000`) | 89.75 | 65.01 | 65.01 (`a_000`) | +0 |
| `phase3_ep_025` | easy | 3 | 3/4 | 76.43 | 49.00 | 4/4 (`a_002`) | 91.79 | 90.55 | 90.55 (`a_002`) | +1 |
| `phase3_ep_026` | easy | 2 | 5/6 | 83.76 | 54.40 | 6/6 (`a_001`) | 99.87 | 99.87 | 99.87 (`a_001`) | +1 |
| `phase3_ep_027` | easy | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_028` | medium | 5 | 3/6 | 50.60 | 0.87 | 4/6 (`a_001`) | 68.48 | 17.47 | 17.47 (`a_001`) | +1 |
| `phase3_ep_029` | medium | 5 | 7/8 | 85.26 | 16.27 | 7/8 (`a_004`) | 90.94 | 88.89 | 88.89 (`a_004`) | +0 |
| `phase3_ep_030` | medium | 5 | 8/9 | 85.85 | 68.24 | 8/9 (`a_003`) | 93.07 | 89.73 | 89.73 (`a_003`) | +0 |
| `phase3_ep_031` | hard | 5 | 5/9 | 57.06 | 0.62 | 7/9 (`a_004`) | 74.05 | 16.93 | 48.25 (`a_003`) | +2 |
| `phase3_ep_032` | hard | 5 | 8/10 | 80.00 | 5.50 | 8/10 (`a_002`) | 80.43 | 43.44 | 43.44 (`a_002`) | +0 |
| `phase3_ep_033` | easy | 1 | 4/4 | 99.95 | 99.95 | 4/4 (`a_000`) | 99.95 | 99.95 | 99.95 (`a_000`) | +0 |
| `phase3_ep_034` | easy | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_035` | easy | 2 | 5/6 | 82.76 | 12.99 | 6/6 (`a_001`) | 97.44 | 97.27 | 97.27 (`a_001`) | +1 |
| `phase3_ep_036` | medium | 5 | 5/6 | 83.32 | 8.23 | 5/6 (`a_003`) | 86.37 | 75.43 | 75.43 (`a_003`) | +0 |
| `phase3_ep_037` | medium | 3 | 7/8 | 87.87 | 64.32 | 8/8 (`a_002`) | 99.71 | 99.71 | 99.71 (`a_002`) | +1 |
| `phase3_ep_038` | medium | 5 | 4/9 | 47.63 | 0.61 | 6/9 (`a_004`) | 68.88 | 17.13 | 17.13 (`a_004`) | +2 |
| `phase3_ep_039` | hard | 1 | 9/9 | 99.96 | 99.96 | 9/9 (`a_000`) | 99.96 | 99.96 | 99.96 (`a_000`) | +0 |
| `phase3_ep_040` | hard | 5 | 9/10 | 90.00 | 16.95 | 9/10 (`a_000`) | 90.00 | 16.95 | 16.95 (`a_000`) | +0 |
| `phase3_ep_041` | easy | 1 | 4/4 | 99.79 | 99.78 | 4/4 (`a_000`) | 99.79 | 99.78 | 99.78 (`a_000`) | +0 |
| `phase3_ep_042` | easy | 5 | 3/5 | 60.35 | 2.77 | 3/5 (`a_003`) | 60.59 | 6.06 | 6.06 (`a_003`) | +0 |
| `phase3_ep_043` | easy | 1 | 6/6 | 99.82 | 99.81 | 6/6 (`a_000`) | 99.82 | 99.81 | 99.81 (`a_000`) | +0 |
| `phase3_ep_044` | medium | 1 | 6/6 | 99.98 | 99.98 | 6/6 (`a_000`) | 99.98 | 99.98 | 99.98 (`a_000`) | +0 |
| `phase3_ep_045` | medium | 1 | 7/7 | 100.00 | 100.00 | 7/7 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_046` | medium | 5 | 7/8 | 87.40 | 9.31 | 8/8 (`a_004`) | 99.40 | 99.39 | 99.39 (`a_004`) | +1 |
| `phase3_ep_047` | hard | 5 | 6/9 | 64.76 | 1.04 | 7/9 (`a_004`) | 78.04 | 16.48 | 16.48 (`a_004`) | +1 |
| `phase3_ep_048` | hard | 5 | 8/10 | 77.45 | 18.19 | 10/10 (`a_004`) | 97.91 | 97.74 | 97.74 (`a_004`) | +2 |
| `phase3_ep_049` | easy | 1 | 4/4 | 87.54 | 84.15 | 4/4 (`a_000`) | 87.54 | 84.15 | 84.15 (`a_000`) | +0 |
| `phase3_ep_050` | easy | 2 | 5/6 | 83.58 | 49.56 | 6/6 (`a_001`) | 99.86 | 99.86 | 99.86 (`a_001`) | +1 |
| `phase3_ep_051` | easy | 5 | 3/5 | 55.43 | 0.41 | 3/5 (`a_003`) | 58.77 | 3.97 | 3.97 (`a_003`) | +0 |
| `phase3_ep_052` | medium | 3 | 5/6 | 83.33 | 4.63 | 6/6 (`a_002`) | 100.00 | 100.00 | 100.00 (`a_002`) | +1 |
| `phase3_ep_053` | medium | 5 | 4/7 | 61.03 | 5.40 | 6/7 (`a_002`) | 89.43 | 82.78 | 82.78 (`a_002`) | +2 |
| `phase3_ep_054` | medium | 2 | 7/8 | 87.49 | 6.94 | 8/8 (`a_001`) | 99.99 | 99.99 | 99.99 (`a_001`) | +1 |
| `phase3_ep_055` | hard | 5 | 6/9 | 69.55 | 15.63 | 8/9 (`a_004`) | 85.19 | 67.89 | 67.89 (`a_004`) | +2 |
| `phase3_ep_056` | hard | 5 | 7/10 | 70.00 | 0.21 | 10/10 (`a_004`) | 100.00 | 100.00 | 100.00 (`a_004`) | +3 |
| `phase3_ep_057` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_058` | easy | 4 | 5/6 | 89.63 | 85.03 | 6/6 (`a_003`) | 90.24 | 88.46 | 88.46 (`a_003`) | +1 |
| `phase3_ep_059` | easy | 5 | 4/6 | 64.79 | 14.16 | 4/6 (`a_000`) | 64.79 | 14.16 | 14.16 (`a_000`) | +0 |
| `phase3_ep_060` | medium | 1 | 8/8 | 93.78 | 92.76 | 8/8 (`a_000`) | 93.78 | 92.76 | 92.76 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_002`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 6/6 atoms, GM 99.77.

### Observed Constraint Regression: `phase3_ep_005`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_002', 'c_007'].
- Reducer best after the full episode: `a_003`.
- Result `a_001`: 4/9 atoms, GM 0.13.

### Historical-Source Branch: `phase3_ep_004`

- Latest before the action was `a_003`.
- The Agent deliberately edited historical source `a_002`.
- Fixed atoms: ['c_001']; regressed atoms: none.
- Result `a_004`: 7/7 atoms, GM 94.50.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_011`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_001']; regressed atoms: none.
- Result `a_003`: 5/6 atoms, GM 42.25.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
