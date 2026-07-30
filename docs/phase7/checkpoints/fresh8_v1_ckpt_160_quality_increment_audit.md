# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 10/10
- PlannerContext versions: {'0.6': 10}
- Score policies: {'geneval2_pass_count_then_gm@1': 10}
- Execution profiles: {'qwen_dual_backend@1': 10}
- Image backends: {'qianwen_image_edit': 23, 'qwen_image': 15}
- Difficulty mix: {'easy': 4, 'hard': 2, 'medium': 4}
- Evaluated image attempts: 38
- Aggregate first Agent attempt atom pass rate: 55/70 (78.6%)
- Aggregate submitted reducer-best atom pass rate: 61/70 (87.1%)
- Net submitted-over-first atom gain: +6
- Geneval2 Soft-TIFA AM, first Agent attempts: 78.72
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 85.97 (+7.26)
- Geneval2 Soft-TIFA GM, first Agent attempts: 34.18
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 59.44 (+25.26)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 60.78 (+26.60)
- Submitted-to-peak GM gap: 1.34
- Episodes with all atoms passed: 4/10
- Historical-best submissions: 5/10
- Regression exposure: 5/10 episodes, 11 image actions
- Ineffective image actions: 7
- Historical edit branches: 6
- Canonical action counts: {'edit_image': 23, 'generate_image': 15, 'query_skill': 9, 'submit_attempt': 10}
- Action/backend counts: {'edit_image|qianwen_image_edit': 23, 'generate_image|qwen_image': 15}
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
- This batch mix: {'easy': 4, 'hard': 2, 'medium': 4}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_147` | easy | 5 | 2/6 | 38.71 | 1.28 | 3/6 (`a_003`) | 50.20 | 8.95 | 8.95 (`a_003`) | +1 |
| `phase3_ep_149` | medium | 5 | 7/8 | 87.50 | 19.06 | 7/8 (`a_001`) | 87.50 | 21.59 | 21.59 (`a_001`) | +0 |
| `phase3_ep_151` | hard | 5 | 6/9 | 68.00 | 1.76 | 8/9 (`a_002`) | 93.50 | 90.84 | 90.84 (`a_002`) | +2 |
| `phase3_ep_152` | hard | 5 | 8/10 | 74.94 | 17.29 | 8/10 (`a_000`) | 74.94 | 17.29 | 30.69 (`a_003`) | +0 |
| `phase3_ep_154` | easy | 5 | 4/5 | 80.02 | 25.88 | 4/5 (`a_000`) | 80.02 | 25.88 | 25.88 (`a_000`) | +0 |
| `phase3_ep_155` | easy | 5 | 5/6 | 83.33 | 6.44 | 5/6 (`a_004`) | 78.07 | 34.51 | 34.51 (`a_004`) | +0 |
| `phase3_ep_157` | medium | 4 | 5/7 | 71.41 | 0.24 | 7/7 (`a_003`) | 99.97 | 99.97 | 99.97 (`a_003`) | +2 |
| `phase3_ep_165` | medium | 2 | 6/7 | 86.34 | 73.07 | 7/7 (`a_001`) | 98.64 | 98.58 | 98.58 (`a_001`) | +1 |
| `phase3_ep_166` | medium | 1 | 8/8 | 98.97 | 98.94 | 8/8 (`a_000`) | 98.97 | 98.94 | 98.94 (`a_000`) | +0 |
| `phase3_ep_169` | easy | 1 | 4/4 | 97.93 | 97.90 | 4/4 (`a_000`) | 97.93 | 97.90 | 97.90 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_166`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 8/8 atoms, GM 98.94.

### Observed Constraint Regression: `phase3_ep_149`

- Action: `edit_image` from `a_001`.
- Fixed atoms: ['c_004'].
- Regressed atoms: ['c_001'].
- Reducer best after the full episode: `a_001`.
- Result `a_003`: 7/8 atoms, GM 4.02.

### Historical-Source Branch: `phase3_ep_149`

- Latest before the action was `a_002`.
- The Agent deliberately edited historical source `a_001`.
- Fixed atoms: ['c_004']; regressed atoms: ['c_001'].
- Result `a_003`: 7/8 atoms, GM 4.02.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_147`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_003']; regressed atoms: none.
- Result `a_003`: 3/6 atoms, GM 8.95.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
