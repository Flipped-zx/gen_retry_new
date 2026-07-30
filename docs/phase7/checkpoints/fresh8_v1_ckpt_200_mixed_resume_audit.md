# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 1/1
- PlannerContext versions: {'0.6': 1}
- Score policies: {'geneval2_pass_count_then_gm@1': 1}
- Execution profiles: {'qwen_dual_backend@1': 1}
- Image backends: {'qianwen_image_edit': 3, 'qwen_image': 2}
- Difficulty mix: {'medium': 1}
- Evaluated image attempts: 5
- Aggregate first Agent attempt atom pass rate: 7/8 (87.5%)
- Aggregate submitted reducer-best atom pass rate: 7/8 (87.5%)
- Net submitted-over-first atom gain: +0
- Geneval2 Soft-TIFA AM, first Agent attempts: 85.66
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 88.85 (+3.19)
- Geneval2 Soft-TIFA GM, first Agent attempts: 7.10
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 85.14 (+78.04)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 85.14 (+78.04)
- Submitted-to-peak GM gap: 0.00
- Episodes with all atoms passed: 0/1
- Historical-best submissions: 1/1
- Regression exposure: 0/1 episodes, 0 image actions
- Ineffective image actions: 2
- Historical edit branches: 0
- Canonical action counts: {'edit_image': 3, 'generate_image': 2, 'query_skill': 1, 'submit_attempt': 1}
- Action/backend counts: {'edit_image|qianwen_image_edit': 3, 'generate_image|qwen_image': 2}
- Scheduler profiles: 2 recorded launches
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 5 total (0 pass the corrected current validator; 0 remain protocol/reference-invalid; 5 remain instruction-quality-invalid).
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
- This batch mix: {'medium': 1}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_069` | medium | 5 | 7/8 | 85.66 | 7.10 | 7/8 (`a_003`) | 88.85 | 85.14 | 85.14 (`a_003`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Source-Free Regeneration After Prior Attempts: `phase3_ep_069`

- The Agent abandoned source-conditioned editing for one source-free root generation.
- Fixed atoms relative to the prior observation: none; regressed atoms: none.
- Result `a_002`: 7/8 atoms, GM 67.43.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
