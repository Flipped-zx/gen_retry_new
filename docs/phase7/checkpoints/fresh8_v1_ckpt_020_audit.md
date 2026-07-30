# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 20/20
- PlannerContext versions: {'0.6': 20}
- Score policies: {'geneval2_pass_count_then_gm@1': 20}
- Execution profiles: {'qwen_dual_backend@1': 20}
- Image backends: {'qianwen_image_edit': 31, 'qwen_image': 21}
- Difficulty mix: {'easy': 9, 'hard': 4, 'medium': 7}
- Evaluated image attempts: 52
- Aggregate first Agent attempt atom pass rate: 125/144 (86.8%)
- Aggregate submitted reducer-best atom pass rate: 141/144 (97.9%)
- Net submitted-over-first atom gain: +16
- Geneval2 Soft-TIFA AM, first Agent attempts: 85.32
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 96.05 (+10.72)
- Geneval2 Soft-TIFA GM, first Agent attempts: 53.95
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 89.89 (+35.93)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 89.89 (+35.93)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 17/20
- Historical-best submissions: 0/20
- Regression exposure: 3/20 episodes, 3 image actions
- Ineffective image actions: 5
- Historical edit branches: 5
- Canonical action counts: {'edit_image': 31, 'generate_image': 21, 'query_skill': 18, 'submit_attempt': 20}
- Action/backend counts: {'edit_image|qianwen_image_edit': 31, 'generate_image|qwen_image': 21}
- Scheduler profiles: 2 recorded launches
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
- This batch mix: {'easy': 9, 'hard': 4, 'medium': 7}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_001` | easy | 2 | 3/4 | 76.53 | 49.77 | 4/4 (`a_001`) | 100.00 | 100.00 | 100.00 (`a_001`) | +1 |
| `phase3_ep_002` | easy | 1 | 6/6 | 99.77 | 99.77 | 6/6 (`a_000`) | 99.77 | 99.77 | 99.77 (`a_000`) | +0 |
| `phase3_ep_003` | easy | 1 | 8/8 | 100.00 | 100.00 | 8/8 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_004` | medium | 5 | 6/7 | 84.73 | 4.30 | 7/7 (`a_004`) | 95.30 | 94.50 | 94.50 (`a_004`) | +1 |
| `phase3_ep_005` | medium | 4 | 6/9 | 67.49 | 28.88 | 9/9 (`a_003`) | 92.06 | 90.78 | 90.78 (`a_003`) | +3 |
| `phase3_ep_006` | medium | 1 | 10/10 | 99.99 | 99.99 | 10/10 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_007` | hard | 2 | 9/10 | 90.12 | 65.31 | 10/10 (`a_001`) | 99.22 | 99.19 | 99.19 (`a_001`) | +1 |
| `phase3_ep_008` | hard | 1 | 10/10 | 97.60 | 97.34 | 10/10 (`a_000`) | 97.60 | 97.34 | 97.34 (`a_000`) | +0 |
| `phase3_ep_009` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_010` | easy | 5 | 4/6 | 67.87 | 2.36 | 5/6 (`a_004`) | 78.93 | 19.60 | 19.60 (`a_004`) | +1 |
| `phase3_ep_011` | easy | 5 | 4/6 | 66.79 | 4.87 | 5/6 (`a_004`) | 84.44 | 63.69 | 63.69 (`a_004`) | +1 |
| `phase3_ep_012` | medium | 3 | 4/6 | 68.26 | 2.86 | 6/6 (`a_002`) | 92.70 | 90.84 | 90.84 (`a_002`) | +2 |
| `phase3_ep_013` | medium | 3 | 7/8 | 91.43 | 87.80 | 8/8 (`a_002`) | 99.84 | 99.84 | 99.84 (`a_002`) | +1 |
| `phase3_ep_014` | medium | 5 | 6/8 | 74.77 | 4.40 | 7/8 (`a_004`) | 87.25 | 49.02 | 49.02 (`a_004`) | +1 |
| `phase3_ep_015` | hard | 1 | 10/10 | 99.97 | 99.97 | 10/10 (`a_000`) | 99.97 | 99.97 | 99.97 (`a_000`) | +0 |
| `phase3_ep_016` | hard | 1 | 10/10 | 96.56 | 95.97 | 10/10 (`a_000`) | 96.56 | 95.97 | 95.97 (`a_000`) | +0 |
| `phase3_ep_017` | easy | 2 | 3/4 | 75.01 | 15.37 | 4/4 (`a_001`) | 99.26 | 99.26 | 99.26 (`a_001`) | +1 |
| `phase3_ep_018` | easy | 1 | 6/6 | 99.99 | 99.99 | 6/6 (`a_000`) | 99.99 | 99.99 | 99.99 (`a_000`) | +0 |
| `phase3_ep_019` | easy | 3 | 5/6 | 83.25 | 19.70 | 6/6 (`a_002`) | 100.00 | 100.00 | 100.00 (`a_002`) | +1 |
| `phase3_ep_020` | medium | 5 | 4/6 | 66.33 | 0.41 | 6/6 (`a_004`) | 98.06 | 97.95 | 97.95 (`a_004`) | +2 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_002`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 6/6 atoms, GM 99.77.

### Observed Constraint Regression: `phase3_ep_005`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_002', 'c_007'].
- Reducer best after the full episode: `a_003`.
- Result `a_001`: 4/9 atoms, GM 0.13.

### Historical-Source Branch: `phase3_ep_004`

- Latest before the action was `a_003`.
- The Agent deliberately edited historical source `a_002`.
- Fixed atoms: ['c_001']; regressed atoms: none.
- Result `a_004`: 7/7 atoms, GM 94.50.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_011`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_001']; regressed atoms: none.
- Result `a_003`: 5/6 atoms, GM 42.25.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
