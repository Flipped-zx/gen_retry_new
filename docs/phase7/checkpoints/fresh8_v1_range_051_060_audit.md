# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 10/10
- PlannerContext versions: {'0.6': 10}
- Score policies: {'geneval2_pass_count_then_gm@1': 10}
- Execution profiles: {'qwen_dual_backend@1': 10}
- Image backends: {'qianwen_image_edit': 23, 'qwen_image': 13}
- Difficulty mix: {'easy': 4, 'hard': 2, 'medium': 4}
- Evaluated image attempts: 36
- Aggregate first Agent attempt atom pass rate: 53/69 (76.8%)
- Aggregate submitted reducer-best atom pass rate: 63/69 (91.3%)
- Net submitted-over-first atom gain: +10
- Geneval2 Soft-TIFA AM, first Agent attempts: 77.50
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 88.22 (+10.72)
- Geneval2 Soft-TIFA GM, first Agent attempts: 32.52
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 75.00 (+42.49)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 75.00 (+42.49)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 6/10
- Historical-best submissions: 3/10
- Regression exposure: 4/10 episodes, 11 image actions
- Ineffective image actions: 2
- Historical edit branches: 7
- Canonical action counts: {'edit_image': 23, 'generate_image': 13, 'query_skill': 10, 'submit_attempt': 10}
- Action/backend counts: {'edit_image|qianwen_image_edit': 23, 'generate_image|qwen_image': 13}
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
- This batch mix: {'easy': 4, 'hard': 2, 'medium': 4}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_051` | easy | 5 | 3/5 | 55.43 | 0.41 | 3/5 (`a_003`) | 58.77 | 3.97 | 3.97 (`a_003`) | +0 |
| `phase3_ep_052` | medium | 3 | 5/6 | 83.33 | 4.63 | 6/6 (`a_002`) | 100.00 | 100.00 | 100.00 (`a_002`) | +1 |
| `phase3_ep_053` | medium | 5 | 4/7 | 61.03 | 5.40 | 6/7 (`a_002`) | 89.43 | 82.78 | 82.78 (`a_002`) | +2 |
| `phase3_ep_054` | medium | 2 | 7/8 | 87.49 | 6.94 | 8/8 (`a_001`) | 99.99 | 99.99 | 99.99 (`a_001`) | +1 |
| `phase3_ep_055` | hard | 5 | 6/9 | 69.55 | 15.63 | 8/9 (`a_004`) | 85.19 | 67.89 | 67.89 (`a_004`) | +2 |
| `phase3_ep_056` | hard | 5 | 7/10 | 70.00 | 0.21 | 10/10 (`a_004`) | 100.00 | 100.00 | 100.00 (`a_004`) | +3 |
| `phase3_ep_057` | easy | 1 | 4/4 | 100.00 | 100.00 | 4/4 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_058` | easy | 4 | 5/6 | 89.63 | 85.03 | 6/6 (`a_003`) | 90.24 | 88.46 | 88.46 (`a_003`) | +1 |
| `phase3_ep_059` | easy | 5 | 4/6 | 64.79 | 14.16 | 4/6 (`a_000`) | 64.79 | 14.16 | 14.16 (`a_000`) | +0 |
| `phase3_ep_060` | medium | 1 | 8/8 | 93.78 | 92.76 | 8/8 (`a_000`) | 93.78 | 92.76 | 92.76 (`a_000`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Direct First-Attempt Success: `phase3_ep_057`

- The fresh generation passed every atom.
- The Agent submitted it without spending retry budget.
- Result `a_000`: 4/4 atoms, GM 100.00.

### Observed Constraint Regression: `phase3_ep_051`

- Action: `edit_image` from `a_000`.
- Fixed atoms: none.
- Regressed atoms: ['c_002', 'c_004'].
- Reducer best after the full episode: `a_003`.
- Result `a_001`: 1/5 atoms, GM 0.00.

### Historical-Source Branch: `phase3_ep_053`

- Latest before the action was `a_003`.
- The Agent deliberately edited historical source `a_002`.
- Fixed atoms: ['c_006']; regressed atoms: ['c_005'].
- Result `a_004`: 6/7 atoms, GM 71.90.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_051`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: ['c_002']; regressed atoms: none.
- Result `a_002`: 2/5 atoms, GM 0.67.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
