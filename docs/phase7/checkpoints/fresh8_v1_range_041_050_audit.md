# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 10/10
- PlannerContext versions: {'0.6': 10}
- Score policies: {'geneval2_pass_count_then_gm@1': 10}
- Execution profiles: {'qwen_dual_backend@1': 10}
- Image backends: {'qianwen_image_edit': 14, 'qwen_image': 13}
- Difficulty mix: {'easy': 5, 'hard': 2, 'medium': 3}
- Evaluated image attempts: 27
- Aggregate first Agent attempt atom pass rate: 56/65 (86.2%)
- Aggregate submitted reducer-best atom pass rate: 61/65 (93.8%)
- Net submitted-over-first atom gain: +5
- Geneval2 Soft-TIFA AM, first Agent attempts: 86.07
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 92.29 (+6.23)
- Geneval2 Soft-TIFA GM, first Agent attempts: 56.46
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 80.33 (+23.87)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 80.33 (+23.87)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 8/10
- Historical-best submissions: 1/10
- Regression exposure: 2/10 episodes, 2 image actions
- Ineffective image actions: 5
- Historical edit branches: 2
- Canonical action counts: {'edit_image': 14, 'generate_image': 13, 'query_skill': 9, 'submit_attempt': 10}
- Action/backend counts: {'edit_image|qianwen_image_edit': 14, 'generate_image|qwen_image': 13}
- Scheduler profiles: 2 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 11 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 11 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 5, 'hard': 2, 'medium': 3}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_041`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 99.78.

### Observed Constraint Regression: `phase3_ep_046`

- Action: `edit_image` from `a_001`.
- Fixed atoms: none.
- Regressed atoms: ['c_001'].
- Reducer best after the full episode: `a_004`.
- Result `a_002`: 6/8 atoms, GM 29.83.

### Historical-Source Branch: `phase3_ep_042`

- Latest before the action was `a_001`.
- The Agent deliberately edited historical source `a_000`.
- Fixed atoms: none; regressed atoms: none.
- Result `a_002`: 3/5 atoms, GM 0.71.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_042`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: none; regressed atoms: none.
- Result `a_003`: 3/5 atoms, GM 6.06.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
