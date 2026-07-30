# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 40/40
- PlannerContext versions: {'0.6': 40}
- Score policies: {'geneval2_pass_count_then_gm@1': 40}
- Execution profiles: {'qwen_dual_backend@1': 40}
- Image backends: {'qianwen_image_edit': 76, 'qwen_image': 47}
- Difficulty mix: {'easy': 16, 'hard': 9, 'medium': 15}
- Evaluated image attempts: 123
- Aggregate first Agent attempt atom pass rate: 232/283 (82.0%)
- Aggregate submitted reducer-best atom pass rate: 264/283 (93.3%)
- Net submitted-over-first atom gain: +32
- Geneval2 Soft-TIFA AM, first Agent attempts: 84.23
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 93.18 (+8.95)
- Geneval2 Soft-TIFA GM, first Agent attempts: 50.51
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 75.49 (+24.98)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 75.94 (+25.42)
- Submitted-to-peak GM gap: 0.44
- Episodes with all atoms passed: 26/40
- Historical-best submissions: 9/40
- Regression exposure: 13/40 episodes, 25 image actions
- Ineffective image actions: 12
- Historical edit branches: 17
- Canonical action counts: {'edit_image': 76, 'generate_image': 47, 'query_skill': 40, 'submit_attempt': 40}
- Action/backend counts: {'edit_image|qianwen_image_edit': 76, 'generate_image|qwen_image': 47}
- Scheduler profiles: 1 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 13 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 13 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 16, 'hard': 9, 'medium': 15}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_061` | medium | 5 | 6/7 | 85.37 | 11.19 | 6/7 (`a_000`) | 85.37 | 11.19 | 11.19 (`a_000`) | +0 |
| `phase3_ep_062` | medium | 5 | 5/8 | 66.72 | 8.70 | 7/8 (`a_002`) | 85.91 | 29.98 | 29.98 (`a_002`) | +2 |
| `phase3_ep_063` | hard | 5 | 8/10 | 80.23 | 23.66 | 9/10 (`a_003`) | 89.82 | 25.59 | 36.14 (`a_001`) | +1 |
| `phase3_ep_064` | hard | 5 | 7/10 | 70.00 | 2.53 | 9/10 (`a_004`) | 89.00 | 25.50 | 25.50 (`a_004`) | +2 |
| `phase3_ep_065` | easy | 1 | 4/4 | 99.82 | 99.82 | 4/4 (`a_000`) | 99.82 | 99.82 | 99.82 (`a_000`) | +0 |
| `phase3_ep_066` | easy | 3 | 5/6 | 83.33 | 6.01 | 6/6 (`a_002`) | 99.28 | 99.28 | 99.28 (`a_002`) | +1 |
| `phase3_ep_067` | easy | 4 | 5/6 | 83.33 | 6.40 | 6/6 (`a_003`) | 99.82 | 99.82 | 99.82 (`a_003`) | +1 |
| `phase3_ep_068` | medium | 5 | 4/6 | 70.40 | 27.46 | 5/6 (`a_002`) | 80.01 | 55.30 | 55.30 (`a_002`) | +1 |
| `phase3_ep_070` | medium | 5 | 6/8 | 72.04 | 0.64 | 8/8 (`a_004`) | 97.59 | 97.46 | 97.46 (`a_004`) | +2 |
| `phase3_ep_071` | hard | 3 | 9/10 | 88.89 | 66.30 | 10/10 (`a_002`) | 99.77 | 99.77 | 99.77 (`a_002`) | +1 |
| `phase3_ep_072` | hard | 5 | 7/10 | 71.38 | 11.71 | 8/10 (`a_004`) | 79.21 | 24.44 | 24.44 (`a_004`) | +1 |
| `phase3_ep_073` | easy | 2 | 3/4 | 80.31 | 71.03 | 4/4 (`a_001`) | 92.65 | 92.32 | 92.32 (`a_001`) | +1 |
| `phase3_ep_074` | easy | 1 | 6/6 | 93.30 | 91.79 | 6/6 (`a_000`) | 93.30 | 91.79 | 91.79 (`a_000`) | +0 |
| `phase3_ep_075` | easy | 5 | 4/6 | 66.67 | 0.39 | 5/6 (`a_004`) | 83.52 | 47.19 | 54.33 (`a_002`) | +1 |
| `phase3_ep_076` | medium | 4 | 5/6 | 79.51 | 74.25 | 6/6 (`a_003`) | 98.40 | 98.37 | 98.37 (`a_003`) | +1 |
| `phase3_ep_077` | medium | 2 | 7/8 | 87.50 | 34.64 | 8/8 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_078` | medium | 5 | 6/8 | 74.89 | 15.15 | 7/8 (`a_002`) | 87.47 | 33.69 | 33.69 (`a_002`) | +1 |
| `phase3_ep_079` | hard | 4 | 7/10 | 72.64 | 13.13 | 10/10 (`a_003`) | 96.02 | 95.74 | 95.74 (`a_003`) | +3 |
| `phase3_ep_080` | hard | 5 | 8/10 | 78.37 | 42.73 | 8/10 (`a_000`) | 78.37 | 42.73 | 42.73 (`a_000`) | +0 |
| `phase3_ep_081` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_082` | easy | 1 | 6/6 | 99.21 | 99.20 | 6/6 (`a_000`) | 99.21 | 99.20 | 99.20 (`a_000`) | +0 |
| `phase3_ep_083` | easy | 3 | 5/6 | 83.31 | 24.39 | 6/6 (`a_002`) | 99.85 | 99.85 | 99.85 (`a_002`) | +1 |
| `phase3_ep_084` | medium | 1 | 6/6 | 99.77 | 99.77 | 6/6 (`a_000`) | 99.77 | 99.77 | 99.77 (`a_000`) | +0 |
| `phase3_ep_085` | medium | 4 | 7/8 | 88.42 | 72.48 | 8/8 (`a_003`) | 94.30 | 92.67 | 92.67 (`a_003`) | +1 |
| `phase3_ep_086` | medium | 5 | 7/9 | 77.78 | 6.53 | 8/9 (`a_004`) | 87.90 | 24.67 | 24.67 (`a_004`) | +1 |
| `phase3_ep_087` | hard | 5 | 4/9 | 44.45 | 0.01 | 6/9 (`a_004`) | 68.76 | 1.47 | 1.47 (`a_004`) | +2 |
| `phase3_ep_088` | hard | 5 | 6/10 | 60.25 | 0.54 | 8/10 (`a_003`) | 79.45 | 29.84 | 29.84 (`a_003`) | +2 |
| `phase3_ep_089` | easy | 1 | 4/4 | 99.98 | 99.98 | 4/4 (`a_000`) | 99.98 | 99.98 | 99.98 (`a_000`) | +0 |
| `phase3_ep_090` | easy | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_091` | easy | 1 | 6/6 | 99.99 | 99.99 | 6/6 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_092` | medium | 5 | 4/6 | 67.78 | 3.11 | 5/6 (`a_003`) | 85.66 | 72.90 | 72.90 (`a_003`) | +1 |
| `phase3_ep_093` | medium | 5 | 6/8 | 74.93 | 4.17 | 7/8 (`a_003`) | 85.48 | 39.49 | 39.49 (`a_003`) | +1 |
| `phase3_ep_094` | medium | 2 | 8/9 | 92.85 | 89.19 | 9/9 (`a_001`) | 95.99 | 95.15 | 95.15 (`a_001`) | +1 |
| `phase3_ep_096` | hard | 2 | 9/10 | 92.78 | 88.86 | 10/10 (`a_001`) | 96.07 | 95.22 | 95.22 (`a_001`) | +1 |
| `phase3_ep_097` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_099` | easy | 2 | 5/6 | 83.33 | 25.28 | 6/6 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_101` | medium | 1 | 7/7 | 100.00 | 100.00 | 7/7 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_105` | easy | 1 | 4/4 | 99.94 | 99.94 | 4/4 (`a_000`) | 99.94 | 99.94 | 99.94 (`a_000`) | +0 |
| `phase3_ep_106` | easy | 1 | 4/4 | 99.64 | 99.64 | 4/4 (`a_000`) | 99.64 | 99.64 | 99.64 (`a_000`) | +0 |
| `phase3_ep_110` | medium | 1 | 8/8 | 99.97 | 99.97 | 8/8 (`a_000`) | 99.97 | 99.97 | 99.97 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_065`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 99.82.

### Observed Constraint Regression: `phase3_ep_061`

- Action: `generate_image` from `None`.
- Fixed atoms: none.
- Regressed atoms: ['c_001'].
- Reducer best after the full episode: `a_000`.
- Result `a_003`: 5/7 atoms, GM 0.38.

### Historical-Source Branch: `phase3_ep_061`

- Latest before the action was `a_001`.
- The Agent deliberately edited historical source `a_000`.
- Fixed atoms: none; regressed atoms: none.
- Result `a_002`: 6/7 atoms, GM 10.34.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_061`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: none; regressed atoms: ['c_001'].
- Result `a_003`: 5/7 atoms, GM 0.38.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
