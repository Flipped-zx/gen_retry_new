# Flow-DPPO 1000 v9 Final Trajectory Analysis

## Decision

The 1000 completed trajectories are accepted as a valid canonical trajectory
pool. They are not yet a frozen positive SFT dataset.

GPT-5.6 Sol verdict: `PASS_WITH_BLOCKED_SFT_EXPORT`. The block applies to
post-hoc action labeling and Gate-3 export, not to the trajectory artifacts.

This report describes a synthetic Flow-DPPO train-prompt batch. Its Geneval2
scores are valid for this batch but are not an official held-out Geneval2
leaderboard result.

## Integrity

| Check | Result |
| --- | ---: |
| Frozen prompts | 1000 |
| Valid submissions | 1000 |
| Incomplete or failed episodes | 0 |
| Image Attempts | 3443 |
| Start / completion / image / Geneval2 records | 3443 each |
| Resume scheduler exit | 0 |
| Active rollout workers | 0 |
| Orphan images or half-written Attempts | 0 |
| Manifest closure | 1000/1000 |
| Credential-like audited output | 0 files |

The Teacher billing interruption affected 83 requests. Each resumed once from
persisted state. Existing Attempts and the 917 already submitted trajectories
were reused rather than regenerated.

All 1000 trajectories use the same provenance:

- Action Protocol `0.5`;
- PlannerContext `0.7`;
- Teacher `gpt-5.5`;
- system policy `teacher_system_prompt_v9_meaningful_retry_verb_retention`;
- execution profile `qwen_dual_backend@1`;
- score policy `geneval2_pass_count_then_gm@1`;
- 1024 x 1024 local Qwen generation/editing.

## Aggregate Quality

| Metric | First image | Submitted | Change |
| --- | ---: | ---: | ---: |
| Passed atoms | 5540/6937 | 6302/6937 | +762 |
| Atom pass rate | 79.86% | 90.85% | +10.98 pp |
| Soft-TIFA AM | 80.60 | 90.25 | +9.65 |
| Soft-TIFA GM | 40.32 | 71.14 | +30.82 |
| All-pass episodes | 260/1000 | 552/1000 | +292 |

The post-hoc per-trajectory GM peak is `72.30`. It is an oracle diagnostic,
not the Agent submission score. The submitted-to-peak gap is `1.16` points.

- GM improved over the first image in 674 episodes, tied in 307, and decreased
  in 19.
- Seventy-two submitted Attempts are not the highest-GM Attempt because they
  pass more atoms. This is the intended pass-count-first, GM-tie-break policy.
- All 19 first-to-submitted GM decreases gain one passed atom. The policy is
  behaving as designed, but this trade-off must remain visible when GM is the
  reported metric.

## Difficulty

| Tier | N | Avg attempts | Atom pass | GM | All-pass | Submit-peak GM gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Easy | 375 | 2.58 | 84.22% -> 94.00% | 57.58 -> 83.29 | 286/375 | 0.45 |
| Medium | 375 | 3.63 | 80.41% -> 91.57% | 35.50 -> 70.36 | 199/375 | 0.91 |
| Hard | 250 | 4.46 | 76.11% -> 87.77% | 21.68 -> 54.08 | 67/250 | 2.60 |

The difficulty tiers are behaviorally meaningful: hard prompts use almost the
full budget on average and have both the lowest final GM and the largest
selection gap.

## Constraint Types

| Type | Slots | First pass | Submitted pass | Net passed atoms |
| --- | ---: | ---: | ---: | ---: |
| Object | 2224 | 98.70% | 99.37% | +15 |
| Count | 2224 | 62.95% | 83.41% | +455 |
| Attribute | 1518 | 79.18% | 93.54% | +218 |
| Position | 863 | 83.66% | 89.57% | +51 |
| Verb | 108 | 19.44% | 40.74% | +23 |

Count supplies most of the absolute gain. Verb has a substantial relative
gain but remains the weakest type. Chasing accounts for 61 verb atoms and
improves only from `8/61` to `19/61`; it is the clearest residual capability
gap.

## Budget And Actions

| Attempts used | Episodes | All-pass | Mean submitted GM |
| ---: | ---: | ---: | ---: |
| 1 | 260 | 260 | 98.64 |
| 2 | 108 | 108 | 97.21 |
| 3 | 67 | 67 | 97.61 |
| 4 | 59 | 59 | 96.97 |
| 5 | 506 | 58 | 44.93 |

Every episode ending before five Attempts is all-pass. Of the 506 episodes
that use the full budget, 448 remain non-all-pass. There is no premature
submission pattern.

The canonical pool contains 1174 `generate_image`, 2269 `edit_image`, 1051
`query_skill`, and 1000 `submit_attempt` Actions. The 1174 generations contain
1000 first images and 174 source-free regenerations.

| Post-initial action | N | Became best | Fixed atom | Regression | Strict ineffective |
| --- | ---: | ---: | ---: | ---: | ---: |
| Regenerate | 174 | 64.37% | 63.22% | 26.44% | 16.09% |
| Edit | 2269 | 52.05% | 37.15% | 30.98% | 22.87% |
| All retries | 2443 | 52.93% | 39.01% | 30.66% | 22.39% |

Regeneration is selected rarely but is useful when the current visual route is
globally unsuitable. Its higher observed success rate is descriptive, not a
causal action comparison, because the Planner chooses actions on different
states. Editing supplies most repairs by volume and also most regressions.

## Recovery And Memory

- 560 episodes encounter at least one regression or strict no-progress result.
- Of 950 such outcomes with another image step available, a later Attempt
  becomes reducer-best in 552 cases (58.11%).
- These difficult episodes still end with positive atom gain in 358/560 cases
  and all-pass in 125/560.
- 2168/2269 edits use the reducer-best source. Another 70 use latest-but-not-
  best, and 31 use a different non-best historical source.
- 657 edits branch from an Attempt other than latest.
- 316 episodes submit historical best instead of latest. All 1000 submissions
  select reducer-best.

These results validate the separation between latest image state, historical
Round memory, and best Attempt. Without that separation, 316 episodes would
have submitted a later inferior image.

## Meaningful Retry

Using the old route signature `(action, source, targets)`, 612/2443 retries
reuse the preceding route. After regression or strict no progress, route reuse
is 588/950. None repeats the exact instruction text; median text similarity is
0.277.

Route reuse is therefore not equivalent to blind retry. It includes both:

- useful persistence, such as `phase3_ep_001`, where a stronger material
  conversion on the same source and target finally fixes the atom;
- repeated failure, such as `phase3_ep_012`, where four different flower-count
  edits still cannot preserve the flower attribute.

Only 197/588 same-route retries after a bad outcome are productive or fix an
atom without regression; 391/588 regress again or remain strictly ineffective.
The v9 decision to permit route reuse is correct, but positive SFT eligibility
must also verify a concrete intervention change and a qualifying outcome.

## Skill Behavior

- 947/1000 episodes query at least one Skill.
- 910 query before the first image; 90 generate directly.
- 139 query after image feedback, usually for a newly isolated failure.
- Skill references: counting/layout 915, attribute binding 722, object
  identity 644, spatial layout 477, action/pose 92, local preservation 71.

This is a real `query_skill -> tool_response -> later image Action` protocol.
However, `query_skill` and its tool response remain context-only until Skill
timing and utility are separately accepted for positive supervision.

## Linter

Episodes 001-020 predate the advisory metadata and contain all 13 historical
`instruction_quality_rejected` repair turns. Episodes 021-1000 create zero such
turns. Canonical image Actions with advisory metadata have 2998 `pass`, 91
`warn`, and 290 `reject` verdicts.

At least 169 `reject`-verdict canonical Actions are a first generation or a
clean new-best outcome. Conversely, 121 are regression/no-progress outcomes.
The linter has diagnostic value but cannot safely act as an execution gate or
an SFT label.

## Representative Trajectories

| Episode | Pattern | Main observation |
| --- | --- | --- |
| `phase3_ep_038` | Direct success | Skill-conditioned first generation reaches 9/9. |
| `phase3_ep_001` | Productive edit | Returns from worse latest to best source and fixes material. |
| `phase3_ep_007` | Regenerate then edit | Rebuilds global layout, then repairs surface patterns to 10/10. |
| `phase3_ep_098` | Verb recovery | Failed chase edits lead to regeneration, then count repair to 5/5. |
| `phase3_ep_003` | Historical submit | Equal atom counts use GM to retain `a_001` over later Attempts. |
| `phase3_ep_012` | Ineffective persistence | Different count edits repeatedly regress flower attributes. |
| `phase3_ep_088` | Hard residual failure | Count, chasing, and spatial binding cannot be solved together. |
| `phase3_ep_004` | Linter false positive | Four rejected raw turns consume no image budget; canonical history remains valid. |

## What Caused The Gain

1. Strong initial prompt rewriting directly solves 260 episodes.
2. Count and attribute interventions account for 673 of the 762 net atom gain.
3. Editing repairs local failures; regeneration abandons globally unsuitable
   layouts.
4. PlannerContext exposes evaluated history, allowing the Planner to change
   route or intervention after failure.
5. Reducer-best source selection and historical-best submission contain
   destructive retries.

## What Limits The Gain

1. Verb/action relations, especially chasing, remain difficult for generation,
   editing, and VQA verification.
2. Exact-count repair often breaks attributes, object identity, or relations.
3. Hard multi-entity prompts combine several coupled failure modes; 198/250
   hard episodes exhaust all five Attempts.
4. More than half of post-initial retries either expose regression or strict
   no progress, so unfiltered imitation would teach harmful behavior.
5. The pass-count-first comparator creates a small but real GM trade-off.

## SFT Boundary

The immutable trajectories should be retained in full. Before positive export:

1. reconstruct each point-in-time PlannerContext with no future information;
2. run outcome-blind v9 semantic compatibility review;
3. label the result against `best_before`;
4. include only compatible first generations, qualifying atom/strong-GM
   retries, and correct reducer-best submissions;
5. keep harmful, ineffective, marginal, raw, tool, evaluator, linter, image,
   and unapproved query-Skill records at loss zero;
6. finish the paired-policy requirement and Gate-3 freeze.

The final Sol review is recorded in
`docs/reviews/flow_dppo1000_v9_ckpt_1000_sol_review.md`.
