# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 20/20
- PlannerContext versions: {'0.6': 20}
- Score policies: {'geneval2_pass_count_then_gm@1': 20}
- Execution profiles: {'qwen_dual_backend@1': 20}
- Image backends: {'qianwen_image_edit': 37, 'qwen_image': 28}
- Difficulty mix: {'easy': 8, 'hard': 7, 'medium': 5}
- Evaluated image attempts: 65
- Aggregate first Agent attempt atom pass rate: 111/136 (81.6%)
- Aggregate submitted reducer-best atom pass rate: 123/136 (90.4%)
- Net submitted-over-first atom gain: +12
- Geneval2 Soft-TIFA AM, first Agent attempts: 81.07
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 89.84 (+8.77)
- Geneval2 Soft-TIFA GM, first Agent attempts: 53.10
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 76.37 (+23.27)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 76.37 (+23.27)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 11/20
- Historical-best submissions: 6/20
- Regression exposure: 6/20 episodes, 15 image actions
- Ineffective image actions: 13
- Historical edit branches: 10
- Canonical action counts: {'edit_image': 37, 'generate_image': 28, 'query_skill': 17, 'submit_attempt': 20}
- Action/backend counts: {'edit_image|qianwen_image_edit': 37, 'generate_image|qwen_image': 28}
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
- This batch mix: {'easy': 8, 'hard': 7, 'medium': 5}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_095` | hard | 5 | 8/9 | 87.89 | 18.71 | 8/9 (`a_003`) | 89.50 | 81.58 | 81.58 (`a_003`) | +0 |
| `phase3_ep_098` | easy | 5 | 4/5 | 79.94 | 30.15 | 4/5 (`a_000`) | 79.94 | 30.15 | 30.15 (`a_000`) | +0 |
| `phase3_ep_100` | medium | 5 | 5/6 | 81.51 | 76.06 | 5/6 (`a_001`) | 87.20 | 82.88 | 82.88 (`a_001`) | +0 |
| `phase3_ep_102` | medium | 5 | 4/8 | 51.02 | 8.64 | 7/8 (`a_004`) | 87.19 | 26.83 | 26.83 (`a_004`) | +3 |
| `phase3_ep_103` | hard | 5 | 5/9 | 56.66 | 2.54 | 6/9 (`a_004`) | 71.51 | 8.43 | 8.43 (`a_004`) | +1 |
| `phase3_ep_104` | hard | 5 | 9/10 | 90.38 | 72.14 | 9/10 (`a_000`) | 90.38 | 72.14 | 72.14 (`a_000`) | +0 |
| `phase3_ep_107` | easy | 5 | 2/5 | 41.34 | 0.41 | 2/5 (`a_002`) | 49.77 | 7.26 | 7.26 (`a_002`) | +0 |
| `phase3_ep_108` | medium | 3 | 3/6 | 50.13 | 0.07 | 6/6 (`a_002`) | 99.00 | 98.97 | 98.97 (`a_002`) | +3 |
| `phase3_ep_109` | medium | 5 | 5/7 | 69.49 | 13.49 | 6/7 (`a_004`) | 89.51 | 82.83 | 82.83 (`a_004`) | +1 |
| `phase3_ep_111` | hard | 5 | 8/9 | 90.01 | 78.79 | 8/9 (`a_000`) | 90.01 | 78.79 | 78.79 (`a_000`) | +0 |
| `phase3_ep_112` | hard | 5 | 8/10 | 79.65 | 2.63 | 10/10 (`a_004`) | 95.27 | 94.71 | 94.71 (`a_004`) | +2 |
| `phase3_ep_113` | easy | 1 | 4/4 | 89.05 | 86.58 | 4/4 (`a_000`) | 89.05 | 86.58 | 86.58 (`a_000`) | +0 |
| `phase3_ep_114` | easy | 1 | 4/4 | 93.10 | 92.25 | 4/4 (`a_000`) | 93.10 | 92.25 | 92.25 (`a_000`) | +0 |
| `phase3_ep_115` | easy | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_120` | hard | 3 | 9/10 | 89.93 | 15.91 | 10/10 (`a_002`) | 99.63 | 99.62 | 99.62 (`a_002`) | +1 |
| `phase3_ep_121` | easy | 2 | 3/4 | 83.88 | 77.41 | 4/4 (`a_001`) | 98.27 | 98.24 | 98.24 (`a_001`) | +1 |
| `phase3_ep_122` | easy | 1 | 4/4 | 99.99 | 99.99 | 4/4 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_124` | medium | 1 | 6/6 | 92.52 | 91.70 | 6/6 (`a_000`) | 92.52 | 91.70 | 91.70 (`a_000`) | +0 |
| `phase3_ep_128` | hard | 1 | 10/10 | 95.97 | 95.58 | 10/10 (`a_000`) | 95.97 | 95.58 | 95.58 (`a_000`) | +0 |
| `phase3_ep_129` | easy | 1 | 4/4 | 98.95 | 98.93 | 4/4 (`a_000`) | 98.95 | 98.93 | 98.93 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_113`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 86.58.

### Observed Constraint Regression: `phase3_ep_095`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_004'].
- Reducer best after the full episode: `a_003`.
- Result `a_001`: 7/9 atoms, GM 12.74.

### Historical-Source Branch: `phase3_ep_095`

- Latest before the action was `a_001`.
- The Agent deliberately edited historical source `a_000`.
- Fixed atoms: none; regressed atoms: ['c_004'].
- Result `a_002`: 7/9 atoms, GM 8.65.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_098`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_003']; regressed atoms: none.
- Result `a_003`: 4/5 atoms, GM 25.85.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
