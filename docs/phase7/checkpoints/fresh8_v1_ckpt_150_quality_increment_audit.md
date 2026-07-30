# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 10/10
- PlannerContext versions: {'0.6': 10}
- Score policies: {'geneval2_pass_count_then_gm@1': 10}
- Execution profiles: {'qwen_dual_backend@1': 10}
- Image backends: {'qianwen_image_edit': 26, 'qwen_image': 12}
- Difficulty mix: {'easy': 3, 'hard': 2, 'medium': 5}
- Evaluated image attempts: 38
- Aggregate first Agent attempt atom pass rate: 51/66 (77.3%)
- Aggregate submitted reducer-best atom pass rate: 61/66 (92.4%)
- Net submitted-over-first atom gain: +10
- Geneval2 Soft-TIFA AM, first Agent attempts: 78.02
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 90.21 (+12.19)
- Geneval2 Soft-TIFA GM, first Agent attempts: 32.50
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 76.17 (+43.67)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 76.37 (+43.87)
- Submitted-to-peak GM gap: 0.20
- Episodes with all atoms passed: 6/10
- Historical-best submissions: 3/10
- Regression exposure: 3/10 episodes, 6 image actions
- Ineffective image actions: 5
- Historical edit branches: 5
- Canonical action counts: {'edit_image': 26, 'generate_image': 12, 'query_skill': 9, 'submit_attempt': 10}
- Action/backend counts: {'edit_image|qianwen_image_edit': 26, 'generate_image|qwen_image': 12}
- Scheduler profiles: 1 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 3 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 3 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 3, 'hard': 2, 'medium': 5}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_138` | easy | 5 | 2/4 | 55.31 | 1.70 | 2/4 (`a_001`) | 51.11 | 2.35 | 2.35 (`a_001`) | +0 |
| `phase3_ep_140` | medium | 5 | 4/6 | 66.63 | 1.83 | 6/6 (`a_004`) | 99.38 | 99.37 | 99.37 (`a_004`) | +2 |
| `phase3_ep_142` | medium | 5 | 6/8 | 74.53 | 4.58 | 7/8 (`a_004`) | 84.70 | 7.89 | 9.91 (`a_002`) | +1 |
| `phase3_ep_143` | hard | 5 | 9/10 | 92.23 | 86.06 | 9/10 (`a_003`) | 95.00 | 93.30 | 93.30 (`a_003`) | +0 |
| `phase3_ep_144` | hard | 5 | 8/10 | 83.79 | 20.42 | 9/10 (`a_003`) | 85.73 | 73.97 | 73.97 (`a_003`) | +1 |
| `phase3_ep_146` | easy | 5 | 3/4 | 75.00 | 4.65 | 4/4 (`a_004`) | 94.45 | 93.91 | 93.91 (`a_004`) | +1 |
| `phase3_ep_148` | medium | 2 | 5/6 | 87.13 | 81.48 | 6/6 (`a_001`) | 94.74 | 94.17 | 94.17 (`a_001`) | +1 |
| `phase3_ep_153` | easy | 1 | 4/4 | 99.84 | 99.84 | 4/4 (`a_000`) | 99.84 | 99.84 | 99.84 (`a_000`) | +0 |
| `phase3_ep_156` | medium | 2 | 5/6 | 83.32 | 24.25 | 6/6 (`a_001`) | 99.99 | 99.99 | 99.99 (`a_001`) | +1 |
| `phase3_ep_158` | medium | 3 | 5/8 | 62.44 | 0.17 | 8/8 (`a_002`) | 97.15 | 96.86 | 96.86 (`a_002`) | +3 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_153`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 99.84.

### Observed Constraint Regression: `phase3_ep_140`

- Action: `edit_image` from `a_002`.
- Fixed atoms: ['c_005'].
- Regressed atoms: ['c_002'].
- Reducer best after the full episode: `a_004`.
- Result `a_003`: 5/6 atoms, GM 67.45.

### Historical-Source Branch: `phase3_ep_138`

- Latest before the action was `a_002`.
- The Agent deliberately edited historical source `a_001`.
- Fixed atoms: none; regressed atoms: none.
- Result `a_003`: 2/4 atoms, GM 1.77.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_138`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: none; regressed atoms: none.
- Result `a_002`: 2/4 atoms, GM 0.62.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
