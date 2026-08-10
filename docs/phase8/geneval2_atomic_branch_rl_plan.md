# Phase 8 Geneval2 Atomic Branch RL Plan

## Decision Summary

The first RL experiment should stay narrow: optimize the Qwen3-VL retry
planner against Geneval2 while keeping both Qwen image backends and Geneval2
frozen. HPSv3 is deferred. Run terminal-only **naive GRPO first**. The
provisional follow-up method is **Atomic Branch Credit GRPO (ABC-GRPO)**.

The naive baseline uses four complete on-policy rollouts per exact prompt and
group-normalizes only the submitted terminal utility. It has no process
reward, call cost, all-pass bonus, submission-regret shaping, Skill credit, or
pivot group. This makes the first result directly interpretable before testing
the proposed credit mechanism.

The contribution being tested is not generic GRPO. It is whether three facts
already owned by the Gen-Retry environment improve policy learning:

1. source-relative target fixes and preserve regressions;
2. progress relative to the reducer best that existed before the action;
3. same-state relative action outcomes under a bounded retry budget.

## Evidence From The Completed 1k

| Item | Count |
| --- | ---: |
| Episodes | 1,000 |
| Image Attempts | 3,443 |
| Canonical actions | 5,494 |
| Post-initial image retries | 2,443 |
| Retry actions that became reducer-best | 1,293 |
| Retry actions with regression | 749 |
| Strictly ineffective retry actions | 547 |
| Episodes containing regression or ineffectiveness | 560 |
| Still-budgeted bad outcomes later reaching a new best | 552 / 950 |
| Historical-best submissions | 316 |

Atom attribution is unusually clean: 1,126/1,127 fixed atoms were explicit
action targets, while all 857 edit-regressed atoms were in the action's
preserve set. This supports source-relative local credit instead of a learned
process reward model.

The existing pool does not contain bad submit decisions: all 1,000 Teacher
episodes submitted reducer-best. Fresh Student rollouts are required to train
stopping and submission error recovery.

## Data Boundary

Use the existing 1k only for reward coefficient and variance audits,
deterministic replay, pivot prevalence, and regression fixtures. Any optional
offline value or advantage-weighted behavior-cloning warm-start must use only
the frozen 800-prompt SFT-train split; the 100 validation and 100 test prompts
stay out. Do not use any of the 1k for policy-gradient updates: it is Teacher
behavior with one action per state and no behavior propensity.

Select fresh RL prompts from unused Flow-DPPO synthetic-train rows. Exclude all
prior 1,220 selected train prompts, official Geneval2 prompts, and exact or
conservative semantic-family overlap with validation and confirmation sets.
The frozen source has 20,000 rows and SHA256
`1822f92dbf848f66d0dbe6b1f9d10114496b104d12b5c32b48e01a83e66b4fe7`.
After official conservative-family exclusion and the 1,220 prior source rows,
9,130 rows remain. SFT/RL are source-row disjoint. RL train/development/
confirmation are additionally disjoint under an entity-aware family hash:
sorted evaluator-derived entities, sorted relation phrases, ordered skills,
and actual VQA count.

The frozen manifests contain 1,000 train, 200 development, and 500
confirmation prompts. Because prior selection and official-family exclusion
consume nearly all easy families, the fresh pool is intentionally hard-skewed:
the train manifest has 10 easy, 542 medium, and 448 hard prompts. This is a
retry-RL training/confirmation pool, not a substitute for the untouched
official 800 distribution.

## How Much RL Data

Count **prompt groups**, not isolated trajectories. GRPO needs multiple
on-policy candidates for the same prompt/state.

| Stage | Fresh prompt groups | Candidate budget | Purpose |
| --- | ---: | ---: | --- |
| Runtime smoke | 32 | 4 full rollouts; bounded pivot probe | parser, masks, reward, resume |
| Mechanism pilot | 128 | 4 full rollouts; one 4-way pivot group | detect reward collapse and branch signal |
| Minimum trainable batch | 250 | same | first learning curve, not promotion evidence |
| Recommended efficacy run | 500 | same | main first-stage result |
| Conditional expansion | 1,000 | same | only if curve rises or 500-group CI is unstable |

Using the historical mean of 3.443 image calls, four full trajectories per
500 prompts would cost about 6,886 image executions before pivot probes. The
branch arm must cap and report extra calls separately. If the budget is
expressed as only 500 or 1,000 total
trajectories, choose 1,000 and call it a pilot; it is not enough for the full
branch-aware experiment.

Five hundred paired confirmation prompts can reliably detect only a moderate
GM shift under the historical variance proxy. A target near three GM points
may require about 1,000 confirmation prompts. Training scale and evaluation
scale must not be conflated.

## Rollout Structure

Start four independent on-policy rollouts per prompt from the frozen SFT
checkpoint. Each has at most five image Attempts and preserves the existing
one-action protocol. For the branch arm, select at most one deterministic
pivot state per prompt, snapshot the exact canonical event prefix, and sample
four one-step sibling actions from the same policy and decoding configuration.
The pivot group uses immediate verified credit only in v0.1; it does not use a
max/top-k descendant backup. This avoids crediting a regressive child for a
later recovery that actually branched from a different historical Attempt.

Pivot reasons in v0.1 are regression, latest/best divergence, two consecutive
strict no-progress actions, or one or two remaining image calls. The structured
action-probability margin trigger is disabled until its autoregressive
calculation and provenance contract are specified.

Do not require one candidate of each action type in a training group. Forced
balanced action groups are useful diagnostics but are not on-policy GRPO data.
Duplicate sampled actions remain valid because their image outcomes expose
generator variance; infrastructure failures are retried with the same semantic
request and never converted to a legitimate zero reward.

## Reward And Credit

For one prompt with fixed atom count:

```text
U(I) = passed_atoms(I) + 0.25 * Geneval2_GM(I)

R_submit = U(submitted)
           - lambda_regret * (U(environment_best) - U(submitted))
           - lambda_call * image_calls
```

This scalar preserves the accepted lexicographic order. `environment_best`
comes from the reducer; reward code cannot invent or replace it.

For declared edit source `p`, pre-action reducer best `b`, and image result
`c`:

```text
r_intervention = fixed_weight * |fixed(p,c)| / max(1, failed(p))
         - regression_weight * |regressed| / max(1, passed(p))
         + gm_weight * (GM(c) - GM(p))  # only when pass count ties

r_progress = (U(c) - U(b)) / atom_count

r_edge = r_intervention
         + best_progress_weight * r_progress
         - no_progress_penalty
         - image_call_cost
```

The `image_call_cost` term above applies to a one-step pivot return. In a full
episode group, edge rewards set `charge_image_cost=false` and the cumulative
cost appears once in `R_submit`; it is not present in both normalized
components.

For source-free regeneration, `b` is also the atom-transition comparison.
Initial generation has no invented `fixed` atoms and receives only normalized
initial utility. This dual comparison is required by the 1k audit: late edits
can improve a weak historical source while still remaining below the current
best. The initial regression/fixed/best-progress weights are 1.25/1.0/0.5.
They are experiment hypotheses requiring scale audits and ablations, not
Geneval2 protocol facts.

`query_skill` receives no reward for the call itself. If a hash-verified Skill
observation is consumed by the next image action, 20% of downstream edge credit
moves to the query and 80% remains on the image action. Moving rather than
copying prevents longer query chains from manufacturing reward.

In a one-step pivot group, `query_skill` has no executed downstream image and
therefore receives only its query/repetition cost. A `submit_attempt` sibling
is immediately executable and receives terminal utility/regret normalized by
atom count so its local scale is comparable with image-edge credit. No sibling
gets credit for an observation or continuation that was not executed.

For candidates from exact state `s`:

```text
A_local(i) = zscore(r_local(i), candidates from s)
A_episode(i) = zscore(R_episode(i), same prompt group)
A_episode_group(i) = 0.65 * A_process(i) + 0.35 * A_terminal(i)
A_pivot_group(i) = A_local(i)
```

Full episode groups use summed verified process return plus submitted terminal
return. Pivot groups use only the same-state one-step relative signal; v0.1
does not pretend an uncontinued sibling has a terminal return. Zero-variance
groups are loss-masked. On-policy parser/reference failures receive an explicit
negative policy reward, while backend/evaluator/transport failures are tracked
and retried outside the advantage batch.

Only assistant action tokens receive policy loss. Tool responses, images,
Geneval2 observations, paths, and reducer facts remain loss-zero context. The
reference-policy KL is explicit and active; old-policy and reference
log-probabilities must be persisted for the exact sampled tokens. This avoids
the inert-KL configuration found in the inspected Gen-Searcher launch path.

## Baselines And Ablations

Run with equal prompt/image-call accounting:

1. Frozen SFT policy, no RL.
2. Naive outcome-only GRPO using submitted Geneval2 utility; this is the first
   optimizer experiment and contains no process shaping.
3. PRE-style peak/retention/efficiency trajectory reward.
4. Outcome plus atomic transition credit, without pivot groups.
5. ABC-GRPO with same-state pivot groups.
6. Remove regression penalty.
7. Remove branch-local advantage while keeping total compute.
8. Forced balanced branch probe, evaluation only.

Add Best-of-K and independent-regeneration controls. Do not claim the branch
method wins if it only receives more image calls.

## Evaluation And Promotion

Primary metrics are submitted atoms/all-pass/GM, reducer-best and submission
regret, regression and no-progress rates, target fixes and preserve regressions,
historical-source recovery, image calls, attempts-to-best, HCU time, action
validity, KL, entropy, and action distribution.

Use a fresh family-disjoint validation cohort during development and a separate
confirmation cohort only after method/coefficients freeze. The official
Geneval2 800 remains a one-time external test, never reward-tuning or early-stop
data.

Promotion requires paired equal-budget improvement over SFT, no material
regression/compute blow-up, stable optimization metrics, and an ablation that
separates local branch credit from additional sampling.

## Implementation State

Implemented: versioned rollout-provenance, reward, and optimizer configs;
pass-count-preserving
utility, all-pass bonus, and submit regret; source-relative intervention plus
best-relative retained progress; source-free generation handling;
credit-conserving Skill delay; policy-invalid versus infrastructure-failure
separation; deterministic pivot detection; same-state/same-policy/on-policy
validation; group-kind-specific advantages and zero-variance masking; an
action-token-only clipped GRPO/reference-KL objective; Schemas, fixture, CLI,
and tests. The rollout provenance contract binds prompt/atom/state/policy/
sampling digests and sampled-token/mask/old-reference-log-prob/event/reward
artifacts; candidate and advantage batches retain source digests.
Trainer-side admission now re-hashes the raw sampled response and every linked
artifact, validates token/mask/log-prob alignment and trainable-token counts,
checks policy/checkpoint/sampling freshness and candidate cardinality, and
cross-binds rollout group/candidate digests to the scalar-return batch.

Also implemented: strict experiment config loading; result-blind 1,000/200/500
prompt selection; prompt-manifest and experiment-declaration Schemas; SHA-bound
data validation; W&B offline/online/disabled runtime with secret redaction;
runtime preflight; an optimizer bridge that re-joins admitted rollout tokens,
masks, persisted old/reference log-probs, and exact advantages; and an audited
rLLM/verl Hydra mapping with active KL.

Not yet approved: materialized live Student rollout artifacts, the custom
rLLM workflow and verl tensor adapter, optimizer/resume execution, or a live
image pilot. The adapter plan deliberately records these stock-runtime
blockers rather than claiming the Gen-Searcher workflow is directly reusable.

The mandatory Phase 8 review returned `PASS_WITH_REQUIRED_CHANGES`. The
immutable provenance bindings, offline trainer admission checks, frozen
family-disjoint manifests, seeds, metrics, and stopping rules requested by
that review are implemented. Before a live naive run, install and validate a
vendor-compatible rLLM/verl/SGLang environment, wire the custom Gen-Retry
workflow to the optimizer bridge, and pass a 32-group end-to-end resume/replay
smoke. Four candidates are
the initial setting; expansion to six or eight is allowed only under a
predeclared zero-variance admission rule. See
`docs/reviews/geneval2_rl_sol_review.md`.
