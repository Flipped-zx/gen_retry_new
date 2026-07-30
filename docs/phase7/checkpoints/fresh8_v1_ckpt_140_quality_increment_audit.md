# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 20/20
- PlannerContext versions: {'0.6': 20}
- Score policies: {'geneval2_pass_count_then_gm@1': 20}
- Execution profiles: {'qwen_dual_backend@1': 20}
- Image backends: {'qianwen_image_edit': 54, 'qwen_image': 25}
- Difficulty mix: {'easy': 6, 'hard': 4, 'medium': 10}
- Evaluated image attempts: 79
- Aggregate first Agent attempt atom pass rate: 124/148 (83.8%)
- Aggregate submitted reducer-best atom pass rate: 135/148 (91.2%)
- Net submitted-over-first atom gain: +11
- Geneval2 Soft-TIFA AM, first Agent attempts: 82.75
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 89.18 (+6.43)
- Geneval2 Soft-TIFA GM, first Agent attempts: 30.63
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 58.59 (+27.96)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 60.60 (+29.97)
- Submitted-to-peak GM gap: 2.01
- Episodes with all atoms passed: 7/20
- Historical-best submissions: 9/20
- Regression exposure: 10/20 episodes, 23 image actions
- Ineffective image actions: 12
- Historical edit branches: 16
- Canonical action counts: {'edit_image': 54, 'generate_image': 25, 'query_skill': 21, 'submit_attempt': 20}
- Action/backend counts: {'edit_image|qianwen_image_edit': 54, 'generate_image|qwen_image': 25}
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
- This batch mix: {'easy': 6, 'hard': 4, 'medium': 10}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_116` | medium | 5 | 7/8 | 87.28 | 18.34 | 7/8 (`a_000`) | 87.28 | 18.34 | 18.34 (`a_000`) | +0 |
| `phase3_ep_117` | medium | 5 | 5/7 | 71.43 | 0.31 | 6/7 (`a_002`) | 78.47 | 4.09 | 4.09 (`a_002`) | +1 |
| `phase3_ep_118` | medium | 5 | 7/8 | 86.31 | 24.97 | 7/8 (`a_002`) | 87.56 | 51.86 | 51.86 (`a_002`) | +0 |
| `phase3_ep_119` | hard | 5 | 8/10 | 79.32 | 16.37 | 9/10 (`a_004`) | 85.03 | 45.46 | 45.46 (`a_004`) | +1 |
| `phase3_ep_123` | easy | 5 | 5/6 | 81.76 | 25.07 | 5/6 (`a_001`) | 83.29 | 28.86 | 28.86 (`a_001`) | +0 |
| `phase3_ep_125` | medium | 5 | 5/8 | 62.56 | 1.62 | 7/8 (`a_003`) | 83.47 | 52.47 | 52.47 (`a_003`) | +2 |
| `phase3_ep_126` | medium | 5 | 7/8 | 87.35 | 18.76 | 7/8 (`a_003`) | 87.39 | 37.91 | 37.91 (`a_003`) | +0 |
| `phase3_ep_127` | hard | 5 | 8/10 | 79.06 | 15.81 | 9/10 (`a_004`) | 88.24 | 79.48 | 79.48 (`a_004`) | +1 |
| `phase3_ep_130` | easy | 5 | 3/4 | 67.21 | 28.83 | 3/4 (`a_000`) | 67.21 | 28.83 | 29.94 (`a_003`) | +0 |
| `phase3_ep_131` | easy | 4 | 5/6 | 82.73 | 10.92 | 6/6 (`a_003`) | 94.88 | 94.11 | 94.11 (`a_003`) | +1 |
| `phase3_ep_132` | medium | 5 | 4/6 | 64.77 | 4.00 | 5/6 (`a_004`) | 82.51 | 8.98 | 8.98 (`a_004`) | +1 |
| `phase3_ep_133` | medium | 5 | 7/8 | 87.32 | 12.89 | 7/8 (`a_004`) | 82.03 | 20.76 | 59.90 (`a_002`) | +0 |
| `phase3_ep_134` | medium | 3 | 6/8 | 74.60 | 1.77 | 8/8 (`a_002`) | 98.31 | 98.25 | 98.25 (`a_002`) | +2 |
| `phase3_ep_135` | hard | 5 | 9/10 | 92.52 | 90.10 | 9/10 (`a_000`) | 92.52 | 90.10 | 90.10 (`a_000`) | +0 |
| `phase3_ep_136` | hard | 5 | 9/10 | 89.03 | 16.37 | 9/10 (`a_000`) | 89.03 | 16.37 | 16.37 (`a_000`) | +0 |
| `phase3_ep_137` | easy | 1 | 4/4 | 99.99 | 99.99 | 4/4 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_139` | easy | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_141` | medium | 2 | 7/8 | 87.04 | 19.04 | 8/8 (`a_001`) | 96.87 | 96.47 | 96.47 (`a_001`) | +1 |
| `phase3_ep_145` | easy | 2 | 3/4 | 74.94 | 7.73 | 4/4 (`a_001`) | 99.73 | 99.72 | 99.72 (`a_001`) | +1 |
| `phase3_ep_150` | medium | 1 | 9/9 | 99.71 | 99.71 | 9/9 (`a_000`) | 99.71 | 99.71 | 99.71 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_137`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 99.99.

### Observed Constraint Regression: `phase3_ep_116`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_006', 'c_007', 'c_008'].
- Reducer best after the full episode: `a_000`.
- Result `a_001`: 4/8 atoms, GM 0.03.

### Historical-Source Branch: `phase3_ep_116`

- Latest before the action was `a_001`.
- The Agent deliberately edited historical source `a_000`.
- Fixed atoms: none; regressed atoms: ['c_006', 'c_007', 'c_008'].
- Result `a_002`: 4/8 atoms, GM 0.04.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_116`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_006', 'c_008']; regressed atoms: none.
- Result `a_003`: 6/8 atoms, GM 9.41.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
