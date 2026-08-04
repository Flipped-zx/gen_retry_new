# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 10/10
- PlannerContext versions: {'0.6': 10}
- Score policies: {'geneval2_pass_count_then_gm@1': 10}
- Execution profiles: {'qwen_dual_backend@1': 10}
- Image backends: {'qianwen_image_edit': 32, 'qwen_image': 18}
- Difficulty mix: {'easy': 5, 'hard': 3, 'medium': 2}
- Evaluated image attempts: 50
- Aggregate first Agent attempt atom pass rate: 47/71 (66.2%)
- Aggregate submitted reducer-best atom pass rate: 54/71 (76.1%)
- Net submitted-over-first atom gain: +7
- Geneval2 Soft-TIFA AM, first Agent attempts: 65.00
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 73.65 (+8.64)
- Geneval2 Soft-TIFA GM, first Agent attempts: 11.00
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 27.70 (+16.69)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 27.79 (+16.78)
- Submitted-to-peak GM gap: 0.09
- Episodes with all atoms passed: 0/10
- Historical-best submissions: 6/10
- Regression exposure: 8/10 episodes, 14 image actions
- Ineffective image actions: 11
- Historical edit branches: 11
- Canonical action counts: {'edit_image': 32, 'generate_image': 18, 'query_skill': 11, 'submit_attempt': 10}
- Action/backend counts: {'edit_image|qianwen_image_edit': 32, 'generate_image|qwen_image': 18}
- Scheduler profiles: 1 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 2 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 2 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 5, 'hard': 3, 'medium': 2}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_032` | hard | 5 | 5/10 | 53.77 | 0.30 | 8/10 (`a_004`) | 79.82 | 18.69 | 18.69 (`a_004`) | +3 |
| `phase3_ep_042` | easy | 5 | 3/5 | 60.17 | 0.88 | 4/5 (`a_004`) | 80.30 | 43.09 | 43.09 (`a_004`) | +1 |
| `phase3_ep_051` | easy | 5 | 2/5 | 45.75 | 1.92 | 4/5 (`a_003`) | 69.43 | 26.20 | 26.20 (`a_003`) | +2 |
| `phase3_ep_107` | easy | 5 | 2/5 | 43.01 | 2.31 | 2/5 (`a_000`) | 43.01 | 2.31 | 2.31 (`a_000`) | +0 |
| `phase3_ep_116` | medium | 5 | 6/8 | 75.03 | 11.71 | 7/8 (`a_004`) | 88.82 | 75.49 | 75.49 (`a_004`) | +1 |
| `phase3_ep_135` | hard | 5 | 7/10 | 71.16 | 13.36 | 7/10 (`a_000`) | 71.16 | 13.36 | 13.36 (`a_000`) | +0 |
| `phase3_ep_154` | easy | 5 | 4/5 | 79.96 | 9.43 | 4/5 (`a_004`) | 80.02 | 27.41 | 27.41 (`a_004`) | +0 |
| `phase3_ep_163` | easy | 5 | 3/5 | 56.06 | 1.91 | 3/5 (`a_001`) | 58.81 | 2.21 | 2.21 (`a_001`) | +0 |
| `phase3_ep_181` | medium | 5 | 7/8 | 87.73 | 62.59 | 7/8 (`a_000`) | 87.73 | 62.59 | 62.59 (`a_000`) | +0 |
| `phase3_ep_200` | hard | 5 | 8/10 | 77.36 | 5.64 | 8/10 (`a_000`) | 77.36 | 5.64 | 6.54 (`a_003`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Observed Constraint Regression: `phase3_ep_032`

- Action: `edit_image` from `a_003`.
- Fixed atoms: ['c_001'].
- Regressed atoms: ['c_009'].
- Reducer best after the full episode: `a_004`.
- Result `a_004`: 8/10 atoms, GM 18.69.

### Historical-Source Branch: `phase3_ep_107`

- Latest before the action was `a_002`.
- The Agent deliberately edited historical source `a_000`.
- Fixed atoms: none; regressed atoms: none.
- Result `a_003`: 2/5 atoms, GM 1.49.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_032`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_005', 'c_008', 'c_009']; regressed atoms: none.
- Result `a_003`: 8/10 atoms, GM 18.25.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
