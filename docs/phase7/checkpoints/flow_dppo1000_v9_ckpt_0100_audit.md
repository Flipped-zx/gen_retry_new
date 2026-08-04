# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 100/100
- PlannerContext versions: {'0.7': 100}
- Score policies: {'geneval2_pass_count_then_gm@1': 100}
- Execution profiles: {'qwen_dual_backend@1': 100}
- Image backends: {'qianwen_image_edit': 221, 'qwen_image': 116}
- Difficulty mix: {'easy': 39, 'hard': 24, 'medium': 37}
- Evaluated image attempts: 337
- Aggregate first Agent attempt atom pass rate: 556/696 (79.9%)
- Aggregate submitted reducer-best atom pass rate: 634/696 (91.1%)
- Net submitted-over-first atom gain: +78
- Geneval2 Soft-TIFA AM, first Agent attempts: 81.08
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 91.32 (+10.24)
- Geneval2 Soft-TIFA GM, first Agent attempts: 36.09
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 73.12 (+37.03)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 74.27 (+38.18)
- Submitted-to-peak GM gap: 1.15
- Episodes with all atoms passed: 59/100
- Historical-best submissions: 24/100
- Regression exposure: 27/100 episodes, 56 image actions
- Ineffective image actions: 58
- Historical edit branches: 60
- Canonical action counts: {'edit_image': 221, 'generate_image': 116, 'query_skill': 106, 'submit_attempt': 100}
- Action/backend counts: {'edit_image|qianwen_image_edit': 221, 'generate_image|qwen_image': 116}
- Scheduler profiles: 3 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 13 total (13 pass the current runtime contract; 0 remain protocol/reference-invalid; 13 contract-passing image actions carry advisory linter flags).
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
- This batch mix: {'easy': 39, 'hard': 24, 'medium': 37}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_001` | easy | 4 | 3/4 | 75.00 | 7.96 | 4/4 (`a_003`) | 99.87 | 99.87 | 99.87 (`a_003`) | +1 |
| `phase3_ep_002` | easy | 4 | 3/4 | 75.00 | 0.71 | 4/4 (`a_003`) | 100.00 | 100.00 | 100.00 (`a_003`) | +1 |
| `phase3_ep_003` | easy | 5 | 6/7 | 84.93 | 11.25 | 6/7 (`a_001`) | 89.76 | 83.53 | 83.53 (`a_001`) | +0 |
| `phase3_ep_004` | medium | 5 | 7/8 | 87.50 | 41.70 | 7/8 (`a_002`) | 93.11 | 90.47 | 90.47 (`a_002`) | +0 |
| `phase3_ep_005` | medium | 5 | 8/9 | 88.70 | 22.58 | 8/9 (`a_002`) | 93.57 | 91.04 | 91.04 (`a_002`) | +0 |
| `phase3_ep_006` | medium | 2 | 9/10 | 88.47 | 47.48 | 10/10 (`a_001`) | 95.76 | 94.95 | 94.95 (`a_001`) | +1 |
| `phase3_ep_007` | hard | 3 | 5/10 | 50.20 | 1.47 | 10/10 (`a_002`) | 99.82 | 99.82 | 99.82 (`a_002`) | +5 |
| `phase3_ep_008` | hard | 5 | 8/10 | 79.13 | 10.46 | 8/10 (`a_003`) | 79.13 | 14.47 | 14.47 (`a_003`) | +0 |
| `phase3_ep_009` | easy | 1 | 4/4 | 99.98 | 99.98 | 4/4 (`a_000`) | 99.98 | 99.98 | 99.98 (`a_000`) | +0 |
| `phase3_ep_010` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_011` | easy | 2 | 5/6 | 83.33 | 14.71 | 6/6 (`a_001`) | 99.89 | 99.89 | 99.89 (`a_001`) | +1 |
| `phase3_ep_012` | medium | 5 | 5/6 | 77.17 | 3.12 | 5/6 (`a_000`) | 77.17 | 3.12 | 3.12 (`a_000`) | +0 |
| `phase3_ep_013` | medium | 5 | 7/8 | 87.50 | 19.71 | 7/8 (`a_000`) | 87.50 | 19.71 | 19.71 (`a_000`) | +0 |
| `phase3_ep_014` | medium | 2 | 5/8 | 63.57 | 20.47 | 8/8 (`a_001`) | 93.89 | 93.53 | 93.53 (`a_001`) | +3 |
| `phase3_ep_015` | hard | 5 | 8/10 | 80.85 | 52.31 | 9/10 (`a_003`) | 87.30 | 15.70 | 52.31 (`a_000`) | +1 |
| `phase3_ep_016` | hard | 2 | 9/10 | 90.58 | 88.04 | 10/10 (`a_001`) | 96.18 | 95.32 | 95.32 (`a_001`) | +1 |
| `phase3_ep_017` | easy | 1 | 4/4 | 98.60 | 98.58 | 4/4 (`a_000`) | 98.60 | 98.58 | 98.58 (`a_000`) | +0 |
| `phase3_ep_018` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_019` | easy | 2 | 5/6 | 86.93 | 77.44 | 6/6 (`a_001`) | 97.77 | 97.64 | 97.64 (`a_001`) | +1 |
| `phase3_ep_020` | medium | 5 | 4/6 | 65.13 | 10.33 | 5/6 (`a_004`) | 82.26 | 61.18 | 61.18 (`a_004`) | +1 |
| `phase3_ep_021` | medium | 5 | 6/8 | 76.92 | 10.42 | 6/8 (`a_004`) | 75.24 | 14.47 | 14.47 (`a_004`) | +0 |
| `phase3_ep_022` | medium | 5 | 6/8 | 72.73 | 11.37 | 7/8 (`a_001`) | 87.42 | 25.74 | 25.74 (`a_001`) | +1 |
| `phase3_ep_023` | hard | 5 | 7/10 | 70.00 | 3.16 | 8/10 (`a_004`) | 80.01 | 36.86 | 36.86 (`a_004`) | +1 |
| `phase3_ep_024` | hard | 5 | 7/10 | 66.68 | 7.72 | 7/10 (`a_004`) | 71.04 | 31.55 | 31.55 (`a_004`) | +0 |
| `phase3_ep_025` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_026` | easy | 3 | 3/4 | 74.80 | 23.03 | 4/4 (`a_002`) | 91.22 | 90.13 | 90.13 (`a_002`) | +1 |
| `phase3_ep_027` | easy | 3 | 5/6 | 83.33 | 18.28 | 6/6 (`a_002`) | 99.99 | 99.99 | 99.99 (`a_002`) | +1 |
| `phase3_ep_028` | medium | 1 | 6/6 | 99.83 | 99.83 | 6/6 (`a_000`) | 99.83 | 99.83 | 99.83 (`a_000`) | +0 |
| `phase3_ep_029` | medium | 5 | 6/8 | 75.00 | 1.26 | 7/8 (`a_002`) | 87.49 | 32.14 | 32.14 (`a_002`) | +1 |
| `phase3_ep_030` | medium | 5 | 7/9 | 77.79 | 14.72 | 7/9 (`a_004`) | 77.99 | 32.62 | 32.62 (`a_004`) | +0 |
| `phase3_ep_031` | hard | 3 | 7/9 | 77.07 | 4.16 | 9/9 (`a_002`) | 98.15 | 98.07 | 98.07 (`a_002`) | +2 |
| `phase3_ep_032` | hard | 5 | 6/10 | 58.18 | 0.84 | 9/10 (`a_004`) | 88.83 | 70.71 | 70.71 (`a_004`) | +3 |
| `phase3_ep_033` | easy | 1 | 4/4 | 90.13 | 88.44 | 4/4 (`a_000`) | 90.13 | 88.44 | 88.44 (`a_000`) | +0 |
| `phase3_ep_034` | easy | 4 | 2/4 | 59.71 | 13.68 | 4/4 (`a_003`) | 99.55 | 99.54 | 99.54 (`a_003`) | +2 |
| `phase3_ep_035` | easy | 4 | 4/6 | 66.67 | 1.33 | 6/6 (`a_003`) | 100.00 | 100.00 | 100.00 (`a_003`) | +2 |
| `phase3_ep_036` | medium | 4 | 5/6 | 88.47 | 82.53 | 6/6 (`a_003`) | 95.37 | 94.75 | 94.75 (`a_003`) | +1 |
| `phase3_ep_037` | medium | 2 | 7/8 | 87.50 | 19.09 | 8/8 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_038` | medium | 1 | 9/9 | 99.87 | 99.87 | 9/9 (`a_000`) | 99.87 | 99.87 | 99.87 (`a_000`) | +0 |
| `phase3_ep_039` | hard | 5 | 6/9 | 67.99 | 1.99 | 7/9 (`a_004`) | 77.27 | 49.06 | 49.06 (`a_004`) | +1 |
| `phase3_ep_040` | hard | 4 | 7/10 | 70.13 | 7.25 | 10/10 (`a_003`) | 95.99 | 95.71 | 95.71 (`a_003`) | +3 |
| `phase3_ep_041` | easy | 5 | 3/4 | 70.58 | 7.45 | 3/4 (`a_004`) | 86.07 | 81.60 | 81.60 (`a_004`) | +0 |
| `phase3_ep_042` | easy | 2 | 4/5 | 73.23 | 8.78 | 5/5 (`a_001`) | 91.22 | 89.09 | 89.09 (`a_001`) | +1 |
| `phase3_ep_043` | easy | 1 | 6/6 | 95.90 | 95.40 | 6/6 (`a_000`) | 95.90 | 95.40 | 95.40 (`a_000`) | +0 |
| `phase3_ep_044` | medium | 2 | 5/6 | 83.48 | 45.24 | 6/6 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_045` | medium | 2 | 6/7 | 85.69 | 7.52 | 7/7 (`a_001`) | 94.51 | 93.37 | 93.37 (`a_001`) | +1 |
| `phase3_ep_046` | medium | 5 | 6/8 | 74.62 | 0.88 | 7/8 (`a_002`) | 86.95 | 8.59 | 8.59 (`a_002`) | +1 |
| `phase3_ep_047` | hard | 5 | 7/9 | 78.05 | 7.51 | 8/9 (`a_004`) | 88.87 | 45.93 | 45.93 (`a_004`) | +1 |
| `phase3_ep_048` | hard | 2 | 9/10 | 89.34 | 51.84 | 10/10 (`a_001`) | 99.30 | 99.28 | 99.28 (`a_001`) | +1 |
| `phase3_ep_049` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_050` | easy | 4 | 3/4 | 75.00 | 9.90 | 4/4 (`a_003`) | 94.43 | 93.90 | 93.90 (`a_003`) | +1 |
| `phase3_ep_051` | easy | 5 | 3/5 | 59.99 | 2.76 | 4/5 (`a_001`) | 71.59 | 28.82 | 28.82 (`a_001`) | +1 |
| `phase3_ep_052` | medium | 4 | 5/6 | 80.85 | 42.24 | 6/6 (`a_003`) | 89.10 | 87.52 | 87.52 (`a_003`) | +1 |
| `phase3_ep_053` | medium | 2 | 6/7 | 87.10 | 72.04 | 7/7 (`a_001`) | 99.99 | 99.99 | 99.99 (`a_001`) | +1 |
| `phase3_ep_054` | medium | 5 | 7/8 | 93.02 | 90.32 | 7/8 (`a_000`) | 93.02 | 90.32 | 90.32 (`a_000`) | +0 |
| `phase3_ep_055` | hard | 5 | 7/9 | 77.76 | 2.48 | 7/9 (`a_004`) | 77.66 | 8.28 | 8.28 (`a_004`) | +0 |
| `phase3_ep_056` | hard | 4 | 8/10 | 83.28 | 52.92 | 10/10 (`a_003`) | 99.96 | 99.96 | 99.96 (`a_003`) | +2 |
| `phase3_ep_057` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_058` | easy | 3 | 3/4 | 74.66 | 1.15 | 4/4 (`a_002`) | 99.63 | 99.63 | 99.63 (`a_002`) | +1 |
| `phase3_ep_059` | easy | 5 | 5/6 | 83.79 | 55.54 | 5/6 (`a_001`) | 83.83 | 55.69 | 55.69 (`a_001`) | +0 |
| `phase3_ep_060` | medium | 5 | 6/8 | 74.93 | 10.20 | 7/8 (`a_004`) | 87.73 | 66.15 | 66.15 (`a_004`) | +1 |
| `phase3_ep_061` | medium | 5 | 5/7 | 69.10 | 6.66 | 5/7 (`a_000`) | 69.10 | 6.66 | 6.66 (`a_000`) | +0 |
| `phase3_ep_062` | medium | 3 | 7/8 | 84.13 | 8.94 | 8/8 (`a_002`) | 99.85 | 99.85 | 99.85 (`a_002`) | +1 |
| `phase3_ep_063` | hard | 5 | 8/10 | 77.50 | 0.87 | 9/10 (`a_003`) | 89.55 | 10.90 | 74.46 (`a_004`) | +1 |
| `phase3_ep_064` | hard | 5 | 8/10 | 81.45 | 17.99 | 9/10 (`a_003`) | 88.45 | 14.98 | 17.99 (`a_000`) | +1 |
| `phase3_ep_065` | easy | 1 | 4/4 | 98.18 | 98.12 | 4/4 (`a_000`) | 98.18 | 98.12 | 98.12 (`a_000`) | +0 |
| `phase3_ep_066` | easy | 1 | 4/4 | 99.77 | 99.77 | 4/4 (`a_000`) | 99.77 | 99.77 | 99.77 (`a_000`) | +0 |
| `phase3_ep_067` | easy | 1 | 6/6 | 99.99 | 99.99 | 6/6 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_068` | medium | 5 | 5/6 | 83.56 | 49.18 | 6/6 (`a_004`) | 99.99 | 99.99 | 99.99 (`a_004`) | +1 |
| `phase3_ep_069` | medium | 2 | 7/8 | 87.50 | 5.82 | 8/8 (`a_001`) | 99.96 | 99.96 | 99.96 (`a_001`) | +1 |
| `phase3_ep_070` | medium | 5 | 4/8 | 57.93 | 20.00 | 5/8 (`a_004`) | 64.64 | 21.66 | 21.66 (`a_004`) | +1 |
| `phase3_ep_071` | hard | 5 | 9/10 | 89.96 | 16.53 | 9/10 (`a_004`) | 90.93 | 79.03 | 79.03 (`a_004`) | +0 |
| `phase3_ep_072` | hard | 5 | 8/10 | 80.02 | 5.89 | 9/10 (`a_002`) | 89.54 | 27.81 | 27.81 (`a_002`) | +1 |
| `phase3_ep_073` | easy | 2 | 3/4 | 74.90 | 1.11 | 4/4 (`a_001`) | 99.55 | 99.55 | 99.55 (`a_001`) | +1 |
| `phase3_ep_074` | easy | 4 | 2/4 | 50.29 | 0.53 | 4/4 (`a_003`) | 99.78 | 99.78 | 99.78 (`a_003`) | +2 |
| `phase3_ep_075` | easy | 5 | 4/6 | 68.16 | 5.77 | 5/6 (`a_003`) | 73.78 | 13.66 | 16.75 (`a_001`) | +1 |
| `phase3_ep_076` | medium | 3 | 4/6 | 66.81 | 1.43 | 6/6 (`a_002`) | 92.66 | 91.79 | 91.79 (`a_002`) | +2 |
| `phase3_ep_077` | medium | 3 | 6/8 | 79.69 | 3.77 | 8/8 (`a_002`) | 99.20 | 99.18 | 99.18 (`a_002`) | +2 |
| `phase3_ep_078` | medium | 5 | 5/8 | 62.50 | 0.16 | 5/8 (`a_003`) | 62.55 | 0.96 | 0.96 (`a_003`) | +0 |
| `phase3_ep_079` | hard | 5 | 7/10 | 70.14 | 3.01 | 9/10 (`a_003`) | 89.87 | 63.54 | 63.54 (`a_003`) | +2 |
| `phase3_ep_080` | hard | 5 | 6/10 | 57.54 | 1.09 | 7/10 (`a_004`) | 69.67 | 2.25 | 2.25 (`a_004`) | +1 |
| `phase3_ep_081` | easy | 1 | 4/4 | 99.99 | 99.99 | 4/4 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_082` | easy | 1 | 4/4 | 99.94 | 99.94 | 4/4 (`a_000`) | 99.94 | 99.94 | 99.94 (`a_000`) | +0 |
| `phase3_ep_083` | easy | 1 | 6/6 | 99.99 | 99.99 | 6/6 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_084` | medium | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_085` | medium | 1 | 8/8 | 99.77 | 99.77 | 8/8 (`a_000`) | 99.77 | 99.77 | 99.77 (`a_000`) | +0 |
| `phase3_ep_086` | medium | 5 | 7/9 | 78.41 | 27.24 | 7/9 (`a_002`) | 79.06 | 41.78 | 41.78 (`a_002`) | +0 |
| `phase3_ep_087` | hard | 5 | 7/9 | 77.78 | 0.46 | 7/9 (`a_002`) | 77.75 | 0.78 | 0.78 (`a_002`) | +0 |
| `phase3_ep_088` | hard | 5 | 7/10 | 63.29 | 17.14 | 7/10 (`a_000`) | 63.29 | 17.14 | 21.94 (`a_002`) | +0 |
| `phase3_ep_089` | easy | 1 | 4/4 | 94.02 | 93.40 | 4/4 (`a_000`) | 94.02 | 93.40 | 93.40 (`a_000`) | +0 |
| `phase3_ep_090` | easy | 2 | 3/4 | 75.00 | 0.47 | 4/4 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_091` | easy | 2 | 5/6 | 83.33 | 2.23 | 6/6 (`a_001`) | 99.42 | 99.41 | 99.41 (`a_001`) | +1 |
| `phase3_ep_092` | medium | 4 | 4/6 | 66.70 | 2.67 | 6/6 (`a_003`) | 99.33 | 99.32 | 99.32 (`a_003`) | +2 |
| `phase3_ep_093` | medium | 5 | 5/8 | 71.55 | 34.11 | 7/8 (`a_004`) | 87.60 | 83.66 | 83.66 (`a_004`) | +2 |
| `phase3_ep_094` | medium | 2 | 7/9 | 78.43 | 39.24 | 9/9 (`a_001`) | 91.23 | 89.56 | 89.56 (`a_001`) | +2 |
| `phase3_ep_095` | hard | 5 | 8/9 | 88.89 | 9.48 | 8/9 (`a_001`) | 88.89 | 20.84 | 20.84 (`a_001`) | +0 |
| `phase3_ep_096` | hard | 5 | 6/10 | 64.42 | 7.65 | 7/10 (`a_004`) | 66.84 | 3.35 | 7.65 (`a_000`) | +1 |
| `phase3_ep_097` | easy | 1 | 4/4 | 97.44 | 97.36 | 4/4 (`a_000`) | 97.44 | 97.36 | 97.36 (`a_000`) | +0 |
| `phase3_ep_098` | easy | 5 | 4/5 | 80.00 | 18.03 | 5/5 (`a_004`) | 97.03 | 96.84 | 96.84 (`a_004`) | +1 |
| `phase3_ep_099` | easy | 5 | 5/6 | 83.33 | 11.80 | 5/6 (`a_004`) | 86.91 | 77.77 | 77.77 (`a_004`) | +0 |
| `phase3_ep_100` | medium | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_009`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 99.98.

### Observed Constraint Regression: `phase3_ep_003`

- Action: `edit_image` from `a_000`.
- Fixed atoms: ['c_003'].
- Regressed atoms: ['c_004'].
- Reducer best after the full episode: `a_001`.
- Result `a_001`: 6/7 atoms, GM 83.53.

### Historical-Source Branch: `phase3_ep_001`

- Latest before the action was `a_002`.
- The Agent deliberately edited historical source `a_001`.
- Fixed atoms: ['c_003']; regressed atoms: none.
- Result `a_003`: 4/4 atoms, GM 99.87.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_002`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_001']; regressed atoms: none.
- Result `a_003`: 4/4 atoms, GM 100.00.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
