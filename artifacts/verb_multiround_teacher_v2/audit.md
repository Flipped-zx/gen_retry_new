# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 2/2
- PlannerContext versions: {'0.6': 2}
- Score policies: {'geneval2_pass_count_then_gm@1': 2}
- Execution profiles: {'qwen_dual_backend@1': 2}
- Image backends: {'qianwen_image_edit': 7, 'qwen_image': 2}
- Difficulty mix: {'easy': 1, 'medium': 1}
- Evaluated image attempts: 9
- Aggregate first Agent attempt atom pass rate: 8/13 (61.5%)
- Aggregate submitted reducer-best atom pass rate: 12/13 (92.3%)
- Net submitted-over-first atom gain: +4
- Geneval2 Soft-TIFA AM, first Agent attempts: 61.44
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 93.68 (+32.25)
- Geneval2 Soft-TIFA GM, first Agent attempts: 3.18
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 69.38 (+66.20)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 69.38 (+66.20)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 1/2
- Historical-best submissions: 1/2
- Regression exposure: 1/2 episodes, 1 image actions
- Ineffective image actions: 0
- Historical edit branches: 0
- Canonical action counts: {'edit_image': 7, 'generate_image': 2, 'query_skill': 2, 'submit_attempt': 2}
- Action/backend counts: {'edit_image|qianwen_image_edit': 7, 'generate_image|qwen_image': 2}
- Scheduler profiles: 0 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 0 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 0 remain instruction-quality-invalid).
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
- This batch mix: {'easy': 1, 'medium': 1}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_014` | medium | 5 | 5/8 | 62.52 | 1.65 | 7/8 (`a_003`) | 87.40 | 38.80 | 38.80 (`a_003`) | +2 |
| `phase3_ep_098` | easy | 4 | 3/5 | 60.35 | 4.71 | 5/5 (`a_003`) | 99.96 | 99.96 | 99.96 (`a_003`) | +2 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Observed Constraint Regression: `phase3_ep_014`

- Action: `edit_image` from `a_003`.
- Fixed atoms: none.
- Regressed atoms: ['c_007'].
- Reducer best after the full episode: `a_003`.
- Result `a_004`: 6/8 atoms, GM 11.46.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
