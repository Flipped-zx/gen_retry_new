# Phase 8 Geneval2 RL SOL Review

- Date: 2026-08-07
- Gate: Phase 8 Geneval2 atomic branch credit RL design
- Verdict: `PASS_WITH_REQUIRED_CHANGES`
- Scope: offline scaffold and bounded pilot design only; no live rollout or
  optimizer launch is approved by this verdict

## 1. Naive GRPO Baseline

Yes, terminal-only GRPO with four complete on-policy rollouts per exact prompt
is a clean first optimizer baseline. `pass_count + 0.25 * GM` preserves the
accepted pass-count-first order when every group contains one exact prompt and
therefore one fixed atom set. The naive config correctly disables process
credit, call cost, all-pass bonus, submission regret, Skill credit, and pivot
groups. An active reference-policy KL and assistant-action-only mask are
appropriate; the reference objective implements both rather than relying on an
inert launcher flag.

Four candidates are sufficient for a smoke/mechanism baseline, not a promise
of adequate reward variance. Report zero-variance-group rate and effective
candidate count. A later increase to six or eight candidates is permissible
only through a predeclared variance admission rule and must be reflected in
equal-call comparisons.

Before a live naive pilot, add an immutable rollout-sample contract that binds
each candidate and advantage to all of the following rather than accepting an
unverifiable `on_policy: true` assertion:

- exact prompt/group and atom-set digest;
- canonical initial-state digest;
- policy checkpoint/revision digest and complete sampling configuration;
- sampled token IDs, assistant-action mask, and aligned old/reference
  log-probability artifact digests;
- rollout/reward artifact digests and infrastructure-retry disposition.

The trainer adapter must validate these bindings, candidate uniqueness, group
size, and policy freshness before optimizer admission. The current candidate
and advantage Schemas are valid offline return/advantage fixtures, but are not
yet sufficient live-training provenance.

## 2. Atomic Branch Credit

The source-relative intervention credit and best-before-relative retained
progress are identifiable from canonical Geneval2 transitions. Exact-state,
same-policy sibling normalization is also identifiable as relative sampled
action-outcome credit. It must not be described as the intrinsic causal effect
of an action because Qwen image execution is stochastic and four siblings do
not separately identify policy choice from renderer noise.

The following are required before an ABC live arm, but do not block the naive
pilot:

- Persist the reward-component provenance used to derive every `local_return`
  and `episode_return`; accepting only final scalar fields is not an auditable
  verifier-grounded credit path.
- Define local return for every legal sibling action, especially one-step
  `query_skill` and `submit_attempt`. A one-step Skill sibling cannot receive
  delayed benefit from an unexecuted image action.
- Charge image-call cost once in the optimized return, or explicitly justify
  and ablate the current edge cost plus terminal cumulative cost. As written,
  a full episode can count the same image calls in both process and terminal
  components.
- Define the action-probability margin used for pivot selection over structured
  autoregressive actions and persist its calculation. Otherwise keep that
  trigger disabled and use only environment-owned pivot signals.
- Predeclare coefficient scale audits and compare outcome-only, atomic without
  pivots, and full ABC. In particular, separate initial-generation absolute
  quality from terminal quality so repeated outcome credit is measurable.

Forced action-balanced probes remain diagnostic only. Pivot siblings without
equal-budget continuations must retain local-only advantage and zero terminal
weight, as proposed.

## 3. Data Boundary And Evidence Ladder

The fresh family-disjoint Flow-DPPO synthetic-train boundary is correct. The
existing 1,000 Teacher episodes are valid for offline calibration and replay,
but not GRPO updates. The official Geneval2 800 must remain untouched until the
one-time external evaluation.

The 32/128/500/conditional-1,000 ladder is sufficient for runtime admission and
an exploratory efficacy result if counts mean prompt groups with four complete
rollouts. It is not, by itself, sufficient for a promotion claim. Before live
collection, freeze and hash the train, development-validation, and confirmation
manifests; the semantic-family algorithm and exclusions; optimizer/sampling
seeds; stopping rules; and primary paired metrics. Report paired confidence
intervals, reward variance, valid/zero-variance group rates, and image calls.

Equal-call frozen-SFT, naive-GRPO, Best-of-K/independent-regeneration, and ABC
ablations are the right controls. A branch claim requires equal total image
calls, not merely equal prompt counts. A single 500-group training seed should
be labeled a pilot; promotion-quality evidence needs replicated optimizer seeds
or a predeclared replication run after the first seed, plus the untouched
paired confirmation cohort.

## Blockers Before Live Naive Pilot

1. Add and validate the immutable rollout/token/log-probability provenance
   contract described in Question 1.
2. Freeze hash-bound family-disjoint train/validation/confirmation manifests
   and the evaluation/stopping/seed declaration described in Question 3.
3. Demonstrate end-to-end resume/replay on the 32-group smoke path, including
   infrastructure retry exclusion, active KL metrics, mask alignment, and
   zero-variance masking, before the 128-group optimizer pilot.

## Optional Later ABC Work

The Question 2 changes are mandatory for a live ABC comparison but do not block
the terminal-only naive implementation. Descendant backup, learned process
reward, HPSv3, larger branch trees, and forced action-type training remain
deferred.

## Validation Reviewed

```text
pytest tests/unit/test_rl_credit.py tests/unit/test_rl_objective.py \
       tests/unit/test_rl_training.py tests/contract/test_schema_validation.py -q
26 passed
```

## Post-Review Implementation Status

The verdict remains `PASS_WITH_REQUIRED_CHANGES`. After this review, the
rollout contract was extended with a hash-bound raw sampled response and an
explicit state ID. Trainer-side offline admission now verifies real artifact
hashes, token/mask/log-prob alignment, trainable-token counts, policy freshness,
candidate uniqueness/cardinality, and rollout-to-return group/candidate
digests. Focused tests cover successful admission, artifact tampering, and a
stale policy revision. Frozen prompt manifests and the 32-group end-to-end
resume/replay smoke remain blockers to live rollout or optimization.

## Follow-up Review - 2026-08-08

- Gate: Phase 8 naive Geneval2 GRPO data/admission/runtime follow-up
- Verdict: `PASS_WITH_REQUIRED_CHANGES`
- Scope: the offline data and optimizer bridge are accepted as useful
  foundations; this verdict does not approve a live 32-group rollout or any
  optimizer update

### 1. Data Boundary

Yes. The exact source-row and normalized-prompt exclusions close the known
SFT/RL overlap, the conservative official-family exclusion keeps the official
Geneval2 800 out, and the entity/relation/ordered-skill/VQA-count family key is
a reasonable conservative boundary among RL splits. Direct inspection of the
frozen artifacts found 1,000/200/500 unique rows, prompts, and RL families and
zero pairwise overlap on all three keys. Every manifest and the config match
the SHA values in the experiment declaration.

The hard skew is honestly disclosed, but it limits the estimand. Development
and confirmation contain only 2 and 5 easy prompts, respectively, so aggregate
results support the hard-skewed retry pool, not broad easy-case retention or
the official distribution. Before a 500-group efficacy or promotion claim,
either add a separately frozen, family-disjoint easy-stratum regression canary
from non-official unused rows, or explicitly scope the claim to the hard-skewed
pool. The official 800 must remain untouched in either case.

### 2. Rollout And Optimizer Admission

The implementation materially closes the prior offline provenance gap. It
re-hashes linked artifacts, checks candidate/group uniqueness and cardinality,
policy/checkpoint/sampling declarations, token-vector shape and finiteness,
trainable mask counts, terminal-only reward arithmetic, and policy-invalid
rate. `prepare_optimizer_batch` then regenerates candidate returns and
advantages and requires canonical equality before loading only non-zero-
variance groups. Tampered advantage or linked artifact content therefore
cannot silently enter this reference bridge.

This is not yet a complete semantic on-policy proof. The following claims are
not supported by the current Schema/admission implementation and must be
closed by the custom workflow and smoke replay:

- `prompt_sha256`, `atom_set_sha256`, and `canonical_state_sha256` are asserted
  fields. Admission does not recompute them from the frozen manifest and
  canonical initial event prefix.
- `rollout_events` is content-hashed but not parsed/replayed. The submitted
  Geneval2 score in the reward artifact is checked for arithmetic consistency,
  but is not cross-bound to evaluator/reducer events. A self-consistent invented
  score would pass the current offline gate.
- Token IDs are not re-tokenized/decoded against `sampled_response`, and the
  assistant-action mask is checked as a binary vector rather than derived from
  canonical assistant/tool roles. Old/reference log-probs are finite and
  aligned, but their model/token provenance still depends on the missing tensor
  adapter.
- `minimum_valid_group_fraction` and
  `maximum_zero_variance_group_fraction` are not enforced by admission. Zero-
  variance groups are correctly masked and reported, but the declared
  four-to-six rollout escalation is currently a runbook rule, not a stage gate.

There is also a concrete live-contract mismatch: rollout admission expects
`sampling_config.max_response_tokens == max_action_tokens` (1,400), while the
verl plan sets full multi-turn `data.max_response_length` to
`max_total_assistant_tokens` (16,000). The rollout contract must represent and
validate both the per-action and cumulative limits before the 32-group smoke.

### 3. Runtime, Tracking, And Topology

The proposed numerical parameters are conservative for a first naive GRPO
pilot, active actor KL is explicitly mapped, W&B defaults are safe, and the
two-stage eight-device topology avoids claiming simultaneous rollout services
and FSDP-8. These remain a parameter map and scheduling plan until tested
against the exact vendor rLLM/verl/SGLang versions.

The documented stock-runtime blockers are correct, but they are not yet
machine-enforced. `run_rl_preflight` can return `READY` and
`ready_for_live_training=true` once packages, paths, hashes, and eight devices
pass; it does not check that the custom Gen-Retry workflow and tensor adapter
exist or that a 32-group smoke artifact passed. The focused test currently
codifies that premature `READY` state. Split the gate into at least
`READY_FOR_SMOKE` and `READY_FOR_OPTIMIZATION`, and require a hash-bound smoke
report for the latter. Until then, neither the adapter-plan JSON nor preflight
`READY` is live-training approval.

### Blockers Before The 32-Group Smoke

1. Install and pin a vendor-compatible rLLM/verl/SGLang/W&B environment and
   expose the required eight HCUs; the current preflight correctly reports
   five environmental blockers.
2. Implement the strict-JSON, multimodal, multi-turn Gen-Retry collector and
   define the per-action 1,400 versus cumulative 16,000 token contract.
3. Implement semantic admission replay: bind prompt/atom/state to the frozen
   manifest and event prefix, bind terminal reward to canonical Geneval2/
   reducer events, and verify tokenizer-derived masks and old/reference
   log-probs from the declared models.
4. Implement the staged service-release/tensor handoff and make preflight emit
   `READY_FOR_SMOKE`, not `ready_for_live_training`.

### Blockers Before 128/500 Optimization

1. Complete the 32-group artifact-backed interruption/resume/replay smoke and
   freeze its hash-bound report. Require that report in an
   `READY_FOR_OPTIMIZATION` gate.
2. Enforce the declared valid-group, policy-invalid, and zero-variance stage
   thresholds. If zero variance exceeds 0.35, freeze a six-rollout amendment
   and restore equal-call comparisons before optimization.
3. Measure backend timing and memory on the smoke before approving the staged
   128/500 topology. Before a 500-group efficacy claim, add the easy-case
   guardrail or restrict the stated estimand as described in Question 1.

### Validation Performed

```text
pytest tests/unit/test_rl_credit.py tests/unit/test_rl_objective.py \
       tests/unit/test_rl_training.py \
       tests/unit/test_rl_config_tracking_preflight.py \
       tests/unit/test_rl_data.py tests/unit/test_rl_verl_adapter.py \
       tests/contract/test_schema_validation.py -q
51 passed

python -m gen_retry.cli.validate_schemas
validated 21 schemas

python -m gen_retry.cli.validate_fixtures
validated 108 fixture records
```

## Post-Follow-Up Implementation Status - 2026-08-08

The verdict remains `PASS_WITH_REQUIRED_CHANGES` because no live custom
collector/tensor adapter or 32-group smoke exists yet. The concrete offline
contract findings from the follow-up are now addressed:

- rollout artifacts distinguish and enforce 1,400 tokens per assistant Action
  from 16,000 cumulative assistant-action tokens per episode;
- planned, valid, and infrastructure-excluded groups are explicit, with a
  minimum 0.95 valid-group gate and maximum 0.05 policy-invalid gate;
- optimizer admission rejects a zero-variance fraction above 0.35 and points
  to the frozen six-rollout amendment path;
- preflight now emits control-plane, `READY_FOR_SMOKE`, or
  `READY_FOR_OPTIMIZATION` readiness and cannot authorize optimization without
  hash-bound adapter evidence plus a passing 32-group smoke report;
- the hard-skew estimand and the 2/5 easy-prompt development/confirmation
  limitation are explicit in the runbook and status.

Semantic manifest/state/event replay and tokenizer/model provenance are still
live-adapter work. They are represented as mandatory evidence checks and keep
preflight from reaching `READY_FOR_SMOKE`; the current implementation does not
claim that assertions alone prove them.

## Final Delta Review - 2026-08-08

- Gate: Phase 8 naive Geneval2 GRPO final offline admission follow-up
- Verdict: `PASS_WITH_REQUIRED_CHANGES`
- Scope: only the token-limit, stage-threshold, and runtime-readiness deltas
  requested by the updated review

### 1. Token And Group Contract

Yes for the offline contract. Sampling now carries distinct
`max_action_tokens` and `max_episode_assistant_tokens` fields, bound to 1,400
and 16,000 by config and admission. Each candidate records per-Action token
counts; admission requires their sum to equal the action-token mask count,
rejects any Action above 1,400, and rejects cumulative assistant-action tokens
above 16,000. This closes the prior single-field ambiguity. The live adapter
must still derive the per-Action boundaries rather than merely assert them,
which is correctly left behind the adapter-evidence gate.

Planned/admitted/excluded accounting is also internally closed. The rollout
Schema represents infrastructure-excluded groups separately, admission
requires `planned == admitted + excluded`, rejects duplicate group/prompt IDs
across both sets, and verifies each exclusion artifact. This supports the
stated accounting claim.

### 2. Stage Gates

Yes. The thresholds are enforced at the right boundaries and with the intended
inclusive semantics:

- rollout admission rejects valid-group fraction below 0.95;
- rollout admission rejects policy-invalid candidate fraction above 0.05;
- optimizer admission regenerates exact advantages, masks zero-variance
  groups, and rejects their admitted-group fraction above 0.35 before returning
  tensor samples.

The 0.35 failure points to the frozen six-rollout amendment rather than
silently optimizing a low-signal batch. Smoke-report admission applies the same
three limits. No unsupported threshold claim remains in the reviewed
admission/optimizer path.

### 3. Runtime Readiness

The three readiness labels now have the correct control flow. Missing packages
or frozen-data failures block the control plane; accelerator and adapter
evidence gate `READY_FOR_SMOKE`; and a smoke report gates
`READY_FOR_OPTIMIZATION`. A missing smoke report is pending rather than an
optimization approval, so the prior unconditional `ready_for_live_training`
failure is removed.

However, preflight can still overstate readiness because the attached evidence
is hash-bound but not substantively derived. The focused passing fixture uses
`{}` as both rollout and advantage artifacts, a comment-only implementation
file, and an arbitrary `passed` text artifact. `probe_smoke_report` verifies
their hashes but does not parse the rollout/advantage batches or recompute the
reported planned, valid, excluded, candidate, invalid, and zero-variance
counts. The six adapter checks are self-declared booleans, not typed test
results. Consequently a self-consistent fabricated report can currently reach
`READY_FOR_OPTIMIZATION`.

Evidence refs are described as repository-relative, but `_validate_ref` only
rejects absolute paths. A `../` traversal to an external readable file is
accepted if its hash matches. This weakens both the repository boundary and the
meaning of the evidence bundle.

Therefore the offline admission foundation passes, but live readiness does
not. Hash binding proves immutability of referenced bytes; it does not prove
that those bytes contain a valid adapter or a completed smoke.

### Blockers Before The 32-Group Smoke

1. Materialize the vendor-compatible runtime, eight visible HCUs, and custom
   adapter; the current preflight artifact remains correctly below
   `READY_FOR_SMOKE` because those live facts are absent.
2. Replace self-declared adapter booleans with typed, machine-validated test
   reports for the six required checks, bound to the implementation/config/
   checkpoint and exact installed runtime versions.
3. Resolve every evidence ref against an explicit repository/artifact root and
   reject path traversal as well as absolute paths.

### Blockers Before 128/500 Optimization

1. Run the real 32-group interruption/resume/replay smoke; no such artifact is
   currently present.
2. Build the smoke report from admitted rollout data rather than hand-entered
   counters. The optimization gate must validate the rollout and advantage
   Schemas, rerun rollout admission and exact advantage/optimizer joining, and
   compare all report counts to the recomputed result. A hash-bound optimizer-
   admission report is an acceptable equivalent if its builder is tested and
   fail-closed.
3. Keep `READY_FOR_OPTIMIZATION` impossible until the recomputed smoke result,
   adapter evidence, config, checkpoint, and runtime versions all form one
   closed hash chain.

### Validation Performed

```text
pytest tests/unit/test_rl_training.py tests/unit/test_rl_runtime_gate.py \
       tests/unit/test_rl_config_tracking_preflight.py \
       tests/contract/test_schema_validation.py -q
34 passed

python -m gen_retry.cli.validate_schemas
validated 23 schemas

python -m gen_retry.cli.validate_fixtures
validated 108 fixture records
```

## Post-Final-Delta Hardening - 2026-08-08

The final review's runtime-evidence findings were addressed without changing
its `PASS_WITH_REQUIRED_CHANGES` verdict or claiming live readiness:

- evidence refs now resolve against an explicit repository root and reject
  absolute paths and `../` traversal;
- adapter and smoke checks now reference typed runtime-check reports bound to
  config, implementation, checkpoint, exact runtime versions, and, for smoke,
  adapter/rollout/advantage hashes;
- smoke admission reloads and validates the referenced rollout and advantage,
  reruns `prepare_optimizer_batch`, and requires all six reported counts to
  equal recomputed values;
- tests cover typed adapter admission, rejection of empty `{}` smoke batches,
  repository escape rejection, and a complete positive rollout-to-optimizer
  evidence chain.

The remaining blockers are external/live facts: the actual vendor runtime,
custom collector/tensor adapter, eight visible HCUs, and real 32-group smoke do
not yet exist in this container.

Final repository validation after this hardening: 82 contract tests, 251 unit
tests, 24 Schemas, 108 fixture records, canonical replay, compileall, and
`git diff --check` all passed.
