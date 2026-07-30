# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 5/5
- PlannerContext versions: {'0.6': 5}
- Score policies: {'geneval2_pass_count_then_gm@1': 5}
- Execution profiles: {'qwen_dual_backend@1': 5}
- Image backends: {'qianwen_image_edit': 15, 'qwen_image': 10}
- Difficulty mix: {'easy': 3, 'hard': 2}
- Evaluated image attempts: 25
- Aggregate first Agent attempt atom pass rate: 25/32 (78.1%)
- Aggregate submitted reducer-best atom pass rate: 26/32 (81.2%)
- Net submitted-over-first atom gain: +1
- Geneval2 Soft-TIFA AM, first Agent attempts: 78.26
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 80.01 (+1.74)
- Geneval2 Soft-TIFA GM, first Agent attempts: 33.88
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 35.86 (+1.98)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 35.86 (+1.98)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 0/5
- Historical-best submissions: 5/5
- Regression exposure: 2/5 episodes, 7 image actions
- Ineffective image actions: 9
- Historical edit branches: 5
- Canonical action counts: {'edit_image': 15, 'generate_image': 10, 'query_skill': 5, 'submit_attempt': 5}
- Action/backend counts: {'edit_image|qianwen_image_edit': 15, 'generate_image|qwen_image': 10}
- Scheduler profiles: 1 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 1 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 1 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 3, 'hard': 2}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_159` | hard | 5 | 6/9 | 69.54 | 4.04 | 7/9 (`a_002`) | 77.78 | 8.03 | 8.03 (`a_002`) | +1 |
| `phase3_ep_160` | hard | 5 | 9/10 | 81.55 | 64.29 | 9/10 (`a_000`) | 81.55 | 64.29 | 64.29 (`a_000`) | +0 |
| `phase3_ep_161` | easy | 5 | 3/4 | 85.76 | 80.99 | 3/4 (`a_000`) | 85.76 | 80.99 | 80.99 (`a_000`) | +0 |
| `phase3_ep_162` | easy | 5 | 3/4 | 74.98 | 3.93 | 3/4 (`a_003`) | 75.00 | 6.74 | 6.74 (`a_003`) | +0 |
| `phase3_ep_163` | easy | 5 | 4/5 | 79.48 | 16.15 | 4/5 (`a_001`) | 79.94 | 19.24 | 19.24 (`a_001`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Observed Constraint Regression: `phase3_ep_160`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_008'].
- Reducer best after the full episode: `a_000`.
- Result `a_001`: 8/10 atoms, GM 56.17.

### Historical-Source Branch: `phase3_ep_159`

- Latest before the action was `a_003`.
- The Agent deliberately edited historical source `a_002`.
- Fixed atoms: none; regressed atoms: none.
- Result `a_004`: 7/9 atoms, GM 5.25.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_160`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: none; regressed atoms: ['c_001', 'c_004', 'c_005', 'c_006', 'c_007'].
- Result `a_003`: 3/10 atoms, GM 0.01.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
