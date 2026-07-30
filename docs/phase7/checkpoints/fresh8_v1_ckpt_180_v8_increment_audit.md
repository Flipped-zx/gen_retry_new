# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 15/15
- PlannerContext versions: {'0.6': 15}
- Score policies: {'geneval2_pass_count_then_gm@1': 15}
- Execution profiles: {'qwen_dual_backend@1': 15}
- Image backends: {'qianwen_image_edit': 21, 'qwen_image': 18}
- Difficulty mix: {'easy': 8, 'hard': 4, 'medium': 3}
- Evaluated image attempts: 39
- Aggregate first Agent attempt atom pass rate: 84/98 (85.7%)
- Aggregate submitted reducer-best atom pass rate: 96/98 (98.0%)
- Net submitted-over-first atom gain: +12
- Geneval2 Soft-TIFA AM, first Agent attempts: 86.45
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 96.87 (+10.42)
- Geneval2 Soft-TIFA GM, first Agent attempts: 54.17
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 95.26 (+41.09)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 95.26 (+41.09)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 13/15
- Historical-best submissions: 2/15
- Regression exposure: 3/15 episodes, 4 image actions
- Ineffective image actions: 4
- Historical edit branches: 2
- Canonical action counts: {'edit_image': 21, 'generate_image': 18, 'query_skill': 13, 'submit_attempt': 15}
- Action/backend counts: {'edit_image|qianwen_image_edit': 21, 'generate_image|qwen_image': 18}
- Scheduler profiles: 1 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 4 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 4 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 8, 'hard': 4, 'medium': 3}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_164` | medium | 4 | 4/6 | 66.63 | 17.43 | 6/6 (`a_003`) | 96.33 | 96.08 | 96.08 (`a_003`) | +2 |
| `phase3_ep_167` | hard | 3 | 8/9 | 84.43 | 30.39 | 9/9 (`a_002`) | 96.93 | 96.64 | 96.64 (`a_002`) | +1 |
| `phase3_ep_168` | hard | 5 | 7/10 | 71.94 | 17.23 | 9/10 (`a_003`) | 86.30 | 69.48 | 69.48 (`a_003`) | +2 |
| `phase3_ep_170` | easy | 4 | 3/4 | 74.99 | 22.87 | 4/4 (`a_003`) | 97.61 | 97.52 | 97.52 (`a_003`) | +1 |
| `phase3_ep_171` | easy | 5 | 5/6 | 78.61 | 11.81 | 5/6 (`a_003`) | 88.11 | 82.11 | 82.11 (`a_003`) | +0 |
| `phase3_ep_172` | medium | 1 | 8/8 | 96.64 | 96.45 | 8/8 (`a_000`) | 96.64 | 96.45 | 96.45 (`a_000`) | +0 |
| `phase3_ep_173` | medium | 4 | 6/7 | 83.14 | 42.98 | 7/7 (`a_003`) | 98.92 | 98.88 | 98.88 (`a_003`) | +1 |
| `phase3_ep_175` | hard | 2 | 9/10 | 92.69 | 87.68 | 10/10 (`a_001`) | 99.69 | 99.69 | 99.69 (`a_001`) | +1 |
| `phase3_ep_176` | hard | 3 | 8/10 | 79.85 | 1.66 | 10/10 (`a_002`) | 96.21 | 95.83 | 95.83 (`a_002`) | +2 |
| `phase3_ep_177` | easy | 1 | 4/4 | 99.55 | 99.55 | 4/4 (`a_000`) | 99.55 | 99.55 | 99.55 (`a_000`) | +0 |
| `phase3_ep_179` | easy | 2 | 5/6 | 87.82 | 80.35 | 6/6 (`a_001`) | 99.93 | 99.93 | 99.93 (`a_001`) | +1 |
| `phase3_ep_185` | easy | 1 | 4/4 | 99.55 | 99.55 | 4/4 (`a_000`) | 99.55 | 99.55 | 99.55 (`a_000`) | +0 |
| `phase3_ep_186` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_187` | easy | 2 | 5/6 | 83.25 | 7.01 | 6/6 (`a_001`) | 99.56 | 99.56 | 99.56 (`a_001`) | +1 |
| `phase3_ep_193` | easy | 1 | 4/4 | 97.72 | 97.64 | 4/4 (`a_000`) | 97.72 | 97.64 | 97.64 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_172`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 8/8 atoms, GM 96.45.

### Observed Constraint Regression: `phase3_ep_167`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_001'].
- Reducer best after the full episode: `a_002`.
- Result `a_001`: 7/9 atoms, GM 24.21.

### Historical-Source Branch: `phase3_ep_167`

- Latest before the action was `a_001`.
- The Agent deliberately edited historical source `a_000`.
- Fixed atoms: ['c_004']; regressed atoms: none.
- Result `a_002`: 9/9 atoms, GM 96.64.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_170`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: none; regressed atoms: none.
- Result `a_002`: 3/4 atoms, GM 65.39.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
