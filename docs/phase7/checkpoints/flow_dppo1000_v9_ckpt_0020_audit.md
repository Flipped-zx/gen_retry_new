# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 20/20
- PlannerContext versions: {'0.7': 20}
- Score policies: {'geneval2_pass_count_then_gm@1': 20}
- Execution profiles: {'qwen_dual_backend@1': 20}
- Image backends: {'qianwen_image_edit': 41, 'qwen_image': 24}
- Difficulty mix: {'easy': 9, 'hard': 4, 'medium': 7}
- Evaluated image attempts: 65
- Aggregate first Agent attempt atom pass rate: 113/138 (81.9%)
- Aggregate submitted reducer-best atom pass rate: 129/138 (93.5%)
- Net submitted-over-first atom gain: +16
- Geneval2 Soft-TIFA AM, first Agent attempts: 83.13
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 93.58 (+10.45)
- Geneval2 Soft-TIFA GM, first Agent attempts: 41.42
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 77.94 (+36.52)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 79.77 (+38.35)
- Submitted-to-peak GM gap: 1.83
- Episodes with all atoms passed: 12/20
- Historical-best submissions: 7/20
- Regression exposure: 4/20 episodes, 9 image actions
- Ineffective image actions: 16
- Historical edit branches: 13
- Canonical action counts: {'edit_image': 41, 'generate_image': 24, 'query_skill': 21, 'submit_attempt': 20}
- Action/backend counts: {'edit_image|qianwen_image_edit': 41, 'generate_image|qwen_image': 24}
- Scheduler profiles: 2 recorded launches
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
- This batch mix: {'easy': 9, 'hard': 4, 'medium': 7}.

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
