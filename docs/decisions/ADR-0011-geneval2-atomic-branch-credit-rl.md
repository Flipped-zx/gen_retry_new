# ADR-0011: Geneval2-Centered Atomic Branch Credit RL

- Status: Accepted for offline scaffold; live RL remains gated
- Date: 2026-08-08
- Owners: Gen-Retry v3

## Context

The completed v9 pool contains 1,000 Teacher trajectories, 3,443 image
Attempts, and a formal action-only SFT checkpoint. Those trajectories expose
source-relative `fixed`, `regressed`, stable, and persistent atom states plus
arbitrary historical-source lineage. They do not contain current-policy
sampling log-probabilities or multiple actions sampled from the same state.

The first RL phase must optimize the retry policy, not Qwen-Image or
Geneval2. HPSv3 is explicitly outside this version. The accepted reducer
ordering remains:

```text
higher passed-atom count -> higher Geneval2 Soft-TIFA GM -> earlier Attempt
```

## Decision

Adopt `geneval2_terminal_outcome@0.1` as the first optimizer baseline, followed
by `geneval2_atomic_branch_credit@0.1` as the research reward and credit policy.
The naive baseline group-normalizes only submitted terminal utility and has no
process shaping or pivot groups.

1. Start from the frozen v9 SFT checkpoint.
2. Collect fresh on-policy rollouts on unused Flow-DPPO synthetic-train
   prompts. Do not use official Geneval2 test prompts for RL.
3. Use the completed 1k Teacher pool only for reward-scale audits, pivot
   prevalence, offline value warm-starts, and regression fixtures.
4. Preserve the canonical pass-count-first comparator in the terminal scalar:

   ```text
   U(attempt) = pass_count + 0.25 * Soft-TIFA_GM
   ```

   Because GM is in `[0, 1]` and the coefficient is below one, no GM change
   can compensate for one fewer passed atom.
5. Give image-producing actions two distinct verified credits: intervention
   effect relative to the declared edit source (or reducer best for source-free
   regeneration), and retained progress relative to the pre-action reducer
   best. Include same-pass GM movement, strict no-progress, and image-call cost.
6. Give `submit_attempt` direct credit for the selected historical Attempt,
   lexicographic submission regret, and image-call cost.
7. Give `query_skill` no intrinsic success bonus. Split a bounded fraction of
   the next attributable image-action credit onto the query, then charge query
   and repeated-query cost. The split must conserve credit rather than copy it.
8. Permit at most one local branch group per episode in v0.1, triggered by
   deterministic regression/latest-best/no-progress/budget signals or a small
   policy action margin.
9. Compute local group-relative advantage only among candidates sampled from
   the exact same canonical state and sampling policy. Off-policy Teacher
   actions and forced action-type probes are rejected as policy-gradient data.
10. Use process/terminal blending for full episode groups and local-only credit
    for one-step pivot groups. Do not fabricate a terminal return for an
    uncontinued sibling. Keep every component in the audit artifact.
11. Give on-policy parser/reference failures an explicit negative reward.
    Retry and exclude infrastructure failures; never silently map them to zero.
12. Require active reference-policy KL and exact old/reference log-probability
    provenance for assistant action tokens. Mask zero-variance groups.
13. Charge image calls once: full episode process edges defer cost to the
    cumulative terminal return; one-step pivot edges charge their own call
    because they have no terminal continuation in v0.1.
14. Reject an optimizer batch unless trainer-side admission re-hashes every
    sampled-response/token/mask/log-prob/event/reward artifact, verifies token
    alignment and policy freshness, and cross-binds each return candidate to
    its immutable rollout group and candidate digest.
15. Distinguish the 1,400-token limit for each strict assistant Action from the
    16,000-token cumulative assistant-action budget for a complete multi-turn
    episode. Persist per-Action token counts and enforce both limits.
16. Admit a rollout stage only when valid groups are at least 95% and
    policy-invalid candidates are at most 5%. Reject optimizer admission when
    zero-variance groups exceed 35%; a six-rollout amendment must be frozen
    before retrying optimization.
17. Separate runtime readiness into `READY_FOR_SMOKE` and
    `READY_FOR_OPTIMIZATION`. The former requires hash-bound custom workflow/
    tensor-adapter evidence; the latter additionally requires a passing,
    hash-bound 32-group interruption/resume/replay report.
18. Evidence hashes are necessary but not sufficient. Every required runtime
    check must use a typed report bound to the config, adapter implementation,
    checkpoint, and exact runtime versions. Evidence refs cannot escape the
    repository root. Smoke readiness must re-run rollout admission, exact
    advantage construction, and optimizer joining from referenced artifacts,
    then compare report counters to recomputed values.

The Action protocol, PlannerContext v0.7, environment-owned facts, reducer
best ordering, execution profile, and Geneval2 adapter do not change.

The first data freeze uses exactly unused source rows, not Teacher episodes.
It reserves 1,000 train, 200 development, and 500 confirmation prompts. The
three RL splits are disjoint under an entity-aware RL family hash; official
Geneval2 exclusion continues to use the earlier broader conservative family.
This distinction preserves strict official holdout protection without putting
hundreds of unrelated object prompts into one RL split family.

## Why Not Terminal-Only GRPO

Terminal-only reward broadcasts the same outcome over productive repairs,
regressive edits, recovery actions, and wasted calls. In the existing 1k,
749 retries regress at least one atom and 547 are strictly ineffective, while
552 of the still-budgeted bad outcomes later reach a new reducer-best. A
single terminal label cannot distinguish those edges.

## Why Not Train Directly On The Existing 1k

The 1k trajectories were sampled by GPT-5.5 Teacher. Each logged state has one
chosen action, no behavior propensity, and no same-state counterfactual group.
Using them as GRPO samples would be off-policy and would confound the Teacher
with the SFT Student. At most the frozen 800-prompt train split may support an
offline value/weighted-BC warm-start; its 100/100 validation/test groups remain
isolated.

## Consequences

- Live RL requires new image execution and Geneval2 calls.
- Fresh prompt selection must exclude the prior 1,220 selected train prompts,
  official Geneval2 prompts, and predeclared semantic-family overlaps.
- The v0.1 reward coefficients are hypotheses and require scale/admission
  audits. They are not benchmark semantics.
- Branch candidates cost extra image calls. Forced balanced action candidates
  may be used for diagnosis, but not for the policy-gradient loss.
- Descendant max/top-k backup is deferred: a later successful recovery from an
  old best is not causal evidence that the regressive child deserved credit.
- A distributed trainer adapter is not approved until the reward/credit batch
  replay and the review gate pass.

## Alternatives Rejected

- **GM-only reward**: conflicts with the canonical pass-count-first policy and
  the 72 existing submissions that correctly prefer more atoms over peak GM.
- **Geneval2 plus HPSv3 linear reward**: out of scope for v0.1 and changes the
  estimand before the semantic RL mechanism is established.
- **One reward copied onto every turn**: does not solve action credit.
- **Full exponential attempt trees**: too expensive and introduces pruning
  bias before the one-pivot method is validated.
- **Forced edit/generate/submit groups for training**: useful as a controlled
  diagnostic, but not an on-policy GRPO group without proposal correction.

## Review Gate

Live image rollout and optimizer launch require a high-level review of:

1. comparator preservation and reward-hacking surface;
2. local/episode credit identifiability;
3. prompt split, sample-size ladder, and equal-compute ablations.

## Review Result

GPT-5.6 Sol returned `PASS_WITH_REQUIRED_CHANGES` for the initial offline
scaffold. The immutable rollout/token/log-prob contract, trainer-side offline
admission validation, hash-bound train/dev/confirmation manifests, and frozen
experiment declaration are now implemented and tested. The rLLM/verl mapping
is recorded as a non-executable adapter plan because stock rLLM recomputes
log-probs and does not implement the Gen-Retry dual-backend state machine.
Before a live naive pilot, the custom workflow/optimizer bridge must be wired
on a compatible vendor runtime and produce the required adapter evidence.
Before any optimizer update, the 32-group smoke must pass end-to-end resume/
replay and stage-admission thresholds. ABC has additional
reward-component, scale-audit, one-step Skill/submit, and equal-call blockers.
The full verdict is `docs/reviews/geneval2_rl_sol_review.md`.
