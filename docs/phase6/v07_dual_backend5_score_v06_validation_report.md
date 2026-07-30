# Flow-DPPO Rollout Validation

- Status: **PASS**
- Validated episodes: 5/5
- PlannerContext versions: {'0.6': 5}
- Score policies: {'geneval2_pass_count_then_gm@1': 5}
- Execution profiles: {'qwen_dual_backend@1': 5}
- Image backends: {'qianwen_image_edit': 18, 'qwen_image': 7}
- Difficulty mix: {'easy': 1, 'hard': 4}
- Evaluated image attempts: 25
- Aggregate first Agent attempt atom pass rate: 35/50 (70.0%)
- Aggregate submitted reducer-best atom pass rate: 40/50 (80.0%)
- Net submitted-over-first atom gain: +5
- Geneval2 Soft-TIFA AM, first Agent attempts: 69.21
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 77.33 (+8.12)
- Geneval2 Soft-TIFA GM, first Agent attempts: 7.81
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 18.32 (+10.51)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 18.99 (+11.18)
- Episodes with all atoms passed: 0/5
- Historical-best submissions: 3/5
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 5 total (4 pass the corrected current validator; 0 remain protocol/reference-invalid; 1 remain instruction-quality-invalid).
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

These are actual Soft-TIFA AM/GM scores recomputed from the persisted local Qwen3-VL correct-answer probabilities. They are not official leaderboard scores: this batch uses Flow-DPPO training prompts, profile-routed local image generation at 1024 x 1024, and one trajectory-selected image per prompt rather than the official 800-prompt benchmark generation protocol.

## Difficulty Policy

The tiers are a deterministic local sampling policy over committed Flow-DPPO training metadata, not official Geneval2 difficulty labels and not post-hoc image outcomes:

- **Hard:** `atom_count >= 9`, actual `len(vqa_list) >= 10`, and at least one relation/action phrase.
- **Medium:** `atom_count` 7-8, actual VQA count 8-10, and at least one relation/action phrase.
- **Easy:** `atom_count <= 5`, actual VQA count <= 7, and at least one relation/action phrase.
- This batch mix: {'easy': 1, 'hard': 4}.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_001` | hard | 5 | 7/11 | 61.62 | 0.87 | 8/11 (`a_004`) | 72.70 | 8.77 | 8.77 (`a_004`) | +1 |
| `phase3_ep_008` | hard | 5 | 8/11 | 73.54 | 22.34 | 9/11 (`a_001`) | 78.31 | 22.80 | 26.16 (`a_002`) | +1 |
| `phase3_ep_010` | hard | 5 | 7/11 | 59.86 | 0.89 | 9/11 (`a_002`) | 80.41 | 7.39 | 7.39 (`a_002`) | +2 |
| `phase3_ep_012` | hard | 5 | 9/11 | 83.53 | 8.00 | 10/11 (`a_003`) | 88.46 | 42.69 | 42.69 (`a_003`) | +1 |
| `phase3_ep_020` | easy | 5 | 4/6 | 67.50 | 6.95 | 4/6 (`a_004`) | 66.76 | 9.94 | 9.94 (`a_004`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### GM Tie-Break Across Stable Atom States: `phase3_ep_001`

- `a_001` reached 8/11 at GM 3.44.
- `a_002`, `a_003`, and `a_004` retained the same 8/11 atom count while increasing GM at each step.
- Final `a_004` remained 8/11 but reached GM 8.77 and was submitted.

### Pass-Count Primary Rejects Higher-GM Regression: `phase3_ep_008`

- `a_001` became best at 9/11, GM 22.80.
- `a_002` had higher GM (26.16) but only 8/11 after regressing `c_001`.
- Reducer retained `a_001`; the next two edits branched from `a_001`, and submission protected it.

### Ineffective Edit, Regenerate, Productive Edit: `phase3_ep_012`

- Local edit `a_001` stayed 9/11 and fell to GM 5.94.
- Source-free `generate_image` produced `a_002` at 9/11, GM 19.01, becoming best by GM.
- Editing `a_002` fixed `c_010`; `a_003` reached 10/11, GM 42.69.
- Final `a_004` regressed `c_010` to 9/11, so submission returned `a_003`.

### Catastrophic Edit, Rollback, Then Regenerate: `phase3_ep_020`

- `a_001` was best at 4/6, GM 7.38.
- Editing it produced `a_002` at only 1/6 and regressed three preserved atoms.
- The next edit rolled back to `a_001`; `a_003` restored 4/6 but did not become best.
- Final source-free regeneration `a_004` remained 4/6 at GM 9.94.


## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, profile-specific local image-backend provenance and 1024x1024 artifact checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
