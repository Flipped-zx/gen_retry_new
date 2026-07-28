# Flow-DPPO 20 Rollout Validation

- Status: **PASS**
- Native v0.5 episodes: 20/20
- Difficulty mix: {'easy': 3, 'hard': 12, 'medium': 5}
- Evaluated image attempts: 92
- Aggregate first Agent attempt atom pass rate: 137/200 (68.5%)
- Aggregate submitted reducer-best atom pass rate: 171/200 (85.5%)
- Net submitted-over-first atom gain: +34
- Geneval2 Soft-TIFA AM, first Agent attempts: 69.38
- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: 84.70 (+15.32)
- Geneval2 Soft-TIFA GM, first Agent attempts: 20.99
- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: 47.25 (+26.26)
- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: 53.33 (+32.34)
- Episodes with all atoms passed: 4/20
- Historical-best submissions: 13/20
- Teacher model IDs: ['gpt-5.5']
- Rejected raw Teacher turns: 28 total (18 pass the corrected current validator; 5 remain protocol/reference-invalid; 5 remain instruction-quality-invalid).
- Credential-like text in audited outputs: 0 files

## Score Semantics

For each image, Geneval2 Soft-TIFA derives AM and GM from the VQA correct-answer probabilities:

```text
image_AM = mean(atom_probability)
image_GM = exp(mean(log(max(atom_probability, 1e-300))))
batch_AM = 100 * mean(image_AM)
batch_GM = 100 * mean(image_GM)
```

AM is the atom-level continuous score; GM is the prompt-level score and the primary Flow-DPPO reporting metric. Both differ from thresholded atom pass rate. Gen-Retry currently selects best by passed-atom count and keeps the earlier attempt on a tie; it does not rank attempts by Soft-TIFA GM. Consequently, submitted score can be lower than the highest GM observed in the same trajectory.

The Planner did not see confidence values, AM, or GM during these rollouts; it saw normalized atom statuses and observed answers. AM and GM below are post-hoc environment metrics computed from persisted probabilities.

These are actual Soft-TIFA AM/GM scores recomputed from the persisted local Qwen3-VL correct-answer probabilities. They are not official leaderboard scores: this batch uses Flow-DPPO training prompts, Qwen-Image-Edit at 1024 x 1024, and one trajectory-selected image per prompt rather than the official 800-prompt benchmark generation protocol.

## Difficulty Policy

The tiers are a deterministic local sampling policy over committed Flow-DPPO training metadata, not official Geneval2 difficulty labels and not post-hoc image outcomes:

- **Hard:** `atom_count >= 9`, actual `len(vqa_list) >= 10`, and at least one relation/action phrase.
- **Medium:** `atom_count` 7-8, actual VQA count 8-10, and at least one relation/action phrase.
- **Easy:** `atom_count <= 5`, actual VQA count <= 7, and at least one relation/action phrase.
- Mix: 12 hard, 5 medium, 3 easy.

Within each tier, ranking rewards more metadata atoms, actual VQAs, distinct skill types, verb/position atoms, high-count atoms, new relation types, and new entities; repeated entity families are penalized. The actual VQA count is used because 6,007/20,000 source rows have `atom_count != len(vqa_list)`.

## Episode Results

| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `phase3_ep_001` | hard | 5 | 8/11 | 72.38 | 5.28 | 8/11 (`a_000`) | 72.38 | 5.28 | 8.16 (`a_001`) | +0 |
| `phase3_ep_002` | hard | 5 | 9/11 | 81.34 | 4.81 | 9/11 (`a_000`) | 81.34 | 4.81 | 19.37 (`a_003`) | +0 |
| `phase3_ep_003` | hard | 5 | 6/11 | 53.71 | 0.34 | 9/11 (`a_004`) | 81.57 | 14.27 | 14.27 (`a_004`) | +3 |
| `phase3_ep_004` | hard | 5 | 10/12 | 83.48 | 43.56 | 10/12 (`a_000`) | 83.48 | 43.56 | 62.46 (`a_001`) | +0 |
| `phase3_ep_005` | hard | 5 | 7/11 | 63.96 | 6.36 | 9/11 (`a_004`) | 85.73 | 75.39 | 75.39 (`a_004`) | +2 |
| `phase3_ep_006` | hard | 5 | 8/12 | 68.24 | 9.98 | 11/12 (`a_004`) | 90.99 | 62.75 | 62.75 (`a_004`) | +3 |
| `phase3_ep_007` | hard | 5 | 9/11 | 80.75 | 13.90 | 10/11 (`a_002`) | 86.46 | 57.58 | 74.25 (`a_003`) | +1 |
| `phase3_ep_008` | hard | 5 | 9/11 | 81.23 | 8.08 | 9/11 (`a_000`) | 81.23 | 8.08 | 25.70 (`a_002`) | +0 |
| `phase3_ep_009` | hard | 5 | 4/10 | 40.44 | 0.02 | 8/10 (`a_001`) | 79.73 | 34.01 | 34.01 (`a_001`) | +4 |
| `phase3_ep_010` | hard | 5 | 7/11 | 65.31 | 1.80 | 8/11 (`a_001`) | 69.55 | 3.34 | 3.34 (`a_001`) | +1 |
| `phase3_ep_011` | hard | 3 | 10/11 | 91.92 | 83.44 | 11/11 (`a_002`) | 95.26 | 94.64 | 94.64 (`a_002`) | +1 |
| `phase3_ep_012` | hard | 5 | 5/11 | 45.66 | 0.76 | 9/11 (`a_002`) | 79.77 | 10.70 | 21.05 (`a_003`) | +4 |
| `phase3_ep_013` | medium | 5 | 4/9 | 48.28 | 8.44 | 8/9 (`a_002`) | 77.22 | 56.17 | 56.17 (`a_002`) | +4 |
| `phase3_ep_014` | medium | 5 | 7/9 | 77.77 | 5.29 | 9/9 (`a_004`) | 93.42 | 92.06 | 92.06 (`a_004`) | +2 |
| `phase3_ep_015` | medium | 5 | 8/10 | 84.52 | 55.90 | 8/10 (`a_000`) | 84.52 | 55.90 | 55.90 (`a_000`) | +0 |
| `phase3_ep_016` | medium | 5 | 5/10 | 50.00 | 0.01 | 8/10 (`a_001`) | 78.52 | 15.76 | 15.76 (`a_001`) | +3 |
| `phase3_ep_017` | medium | 5 | 7/10 | 69.91 | 0.14 | 9/10 (`a_002`) | 89.93 | 42.44 | 71.83 (`a_003`) | +2 |
| `phase3_ep_018` | easy | 3 | 3/7 | 43.19 | 0.58 | 7/7 (`a_002`) | 97.39 | 97.16 | 97.16 (`a_002`) | +4 |
| `phase3_ep_019` | easy | 1 | 6/6 | 100.00 | 100.00 | 6/6 (`a_000`) | 100.00 | 100.00 | 100.00 (`a_000`) | +0 |
| `phase3_ep_020` | easy | 5 | 5/6 | 85.49 | 71.11 | 5/6 (`a_000`) | 85.49 | 71.11 | 82.43 (`a_004`) | +0 |

## Strategy Evidence From Real Trajectories

The canonical action has no `decision_summary`, so the statements below show observable input state, selected action, and outcome rather than claiming an unrecorded hidden rationale.

### Abandon Repeated Ineffective Edits: `phase3_ep_003`

- Fresh `a_000`: 6/11, GM 0.34.
- Two consecutive edits (`a_001`, `a_002`) fixed no atoms; the latest remained 6/11.
- The next action was source-free `generate_image`, producing `a_003`: 8/11, GM 4.11.
- A focused edit of improved latest `a_003` produced `a_004`: 9/11, GM 14.27.
- Before regeneration, the Planner saw two no-fix outcomes at 6/11; post-hoc `a_002` GM was 0.78.

### Branch From Historical Best After No Gain: `phase3_ep_011`

- `a_000` was best at 10/11, GM 83.44; only `c_008` failed.
- Editing it produced latest `a_001` with no fixed atom: 10/11, GM 78.05.
- The next PlannerContext showed latest `a_001`, best `a_000`, and persistent `c_008`.
- The Agent selected `edit_image.source_attempt_id = a_000`, not latest `a_001`.
- Result `a_002` fixed `c_008`, preserved ten atoms, and reached 11/11, GM 94.64.

### Continue Editing, Then Submit Historical Best: `phase3_ep_007`

- `a_002` became reducer best at 10/11, GM 57.58.
- Continuing from `a_002` produced `a_003`, still 10/11 but GM 74.25.
- Because best ordering uses pass count and keeps the earlier tie, reducer best remained `a_002` despite `a_003` having higher GM.
- A later branch from `a_002` produced latest `a_004`, regressed one atom, and fell to 9/11, GM 57.92.
- Submission correctly protected pass-count best `a_002`, while the score report exposes that peak-GM `a_003` was not selected.

### Regenerate Broad Failure, Then Local Edit: `phase3_ep_018`

- First Agent attempt `a_000`: 3/7, GM 0.58.
- Source-free regeneration produced `a_001`: 6/7, GM 60.42; only the chasing verb remained failed.
- Editing latest `a_001` for that remaining verb produced `a_002`: 7/7, GM 97.16.

### Stop Immediately On Complete Success: `phase3_ep_019`

- First Agent attempt `a_000` passed 6/6 with GM 100.00.
- The next action was `submit_attempt(a_000, all_constraints_passed)`; no retry budget was wasted.

## Invariants

Every row passed schema validation, manifest hash closure, fresh-start generation, local Qwen-Image-Edit 1024x1024/40-step metadata checks, complete Geneval2 atom coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time PlannerContext latest/best/budget checks, best-attempt submission, and sanitized GPT-5.5 output checks.
