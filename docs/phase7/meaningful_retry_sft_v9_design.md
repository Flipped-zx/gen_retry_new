# Meaningful-Retry SFT v9 Candidate Design

## Status

Sol design review: `PASS`. The rollout-side v9 Teacher policy and
PlannerContext v0.7 memory are implemented. This does not freeze Gate 3.

The design does not modify Action Protocol v0.5,
completed trajectories, image backends, Geneval2, or the reducer comparator.
It includes one narrow PlannerContext v0.7 memory change because v0.6 does not
show the Planner enough information to detect an older repeated intervention.
The schema and live policy are now implemented; Gate 3 remains open until the
compatibility audit, supervision rules, and paired pilot below are implemented
and reviewed.

The target behavior is:

> Do not perform a blind retry. Reusing the same action, source Attempt, target
> constraints, or even the same high-level operation is allowed when it is a
> defensible attempt to repair a persistent failure. What must be avoided is an
> action with no new intervention, no deliberate resampling basis, and no
> plausible path to improving the current best.

## 1. Why v8 Is Too Coarse

v8 treats this tuple as the retry strategy:

```text
(action, source_attempt_id, target_constraint_ids)
```

That tuple identifies a retry route, not the concrete visual intervention.
The same source and targets may legitimately require several attempts with
different placement, separation, pose, identity, or preservation instructions.

Across the 162 v7-only trajectories:

- 148 decisions followed a regression or strict no-progress result.
- 65 next actions reused the same tuple.
- all 65 changed the image instruction text;
- 25 became `recovery_positive` SFT targets;
- 16 were ineffective;
- 24 were harmful.

The hard tuple rule therefore blocks both blind retries and useful persistent
repairs. The report must call these `same-route retries`, not equivalent
strategies, until semantic intervention equivalence has been audited.

## 2. Evidence From The 200 Trajectories

### 2.1 Outcome and supervision inventory

- 200 episodes, 684 image Attempts.
- 200 initial generations and 484 post-initial retries.
- 263 post-initial image actions are current SFT targets.
- 221 post-initial image actions are not positive targets:
  - 106 harmful;
  - 115 ineffective.
- 99 episodes consumed all five image Attempts.
- At Attempt index four, 41/99 actions became positive targets and 58/99 were
  harmful or ineffective.
- 60 episodes correctly submitted a historical best rather than latest.

### 2.2 Current positive-label weaknesses

Of the 263 post-initial positive image targets:

- 259 became a new reducer-best;
- four only improved a non-best source and remained below global best;
- 129 improved best atom pass-count;
- 130 tied best pass-count and became best only through higher GM.

Among the 130 GM-only new best actions:

- 20 improved GM by at most 0.01;
- 29 improved GM by at most 0.02;
- 55 improved GM by at most 0.05.
- 23 changed which atom IDs passed despite tying total pass-count;
- three did not improve any declared target atom confidence;
- 17 changed a declared preserve atom from pass to non-pass;
- 69 reduced the preserve set's aggregate correct-answer log-probability.

Any positive supervision policy must distinguish metric-relevant soft progress
from negligible score movement. The reducer may retain its exact comparator;
SFT eligibility is a separate decision.

Applying the candidate outcome rules in Section 4 before semantic-policy
review retains 124/129 atom-gain retries and 73/130 GM-only retries. Of the 25
productive same-route retries, 20 pass these outcome rules before the separate
ex-ante semantic audit.

### 2.3 Coverage weaknesses

- Retry positives are 234 edits versus only 29 post-history regenerations.
  Initial generations do not teach when to abandon an edit route.
- All 193 `query_skill` actions are loss-zero. The current SFT export therefore
  cannot teach the policy to query a Skill.
- There are zero `no_productive_action_remaining` submissions.
- There were 82 rejected raw Teacher turns in 42 episodes. All were
  instruction-quality failures; corrected canonical actions remain usable.
- Verb atoms end at 10/22 pass, with `chasing` at 2/12.
- The batch does not isolate adaptive retry value from equal-compute Best-of-K
  or stochastic rejection sampling.

### 2.4 Policy-provenance mismatch

The pool contains 162 v7-only episodes, 37 v8-only episodes, and one mixed
resume episode. Rendering every target with one training system prompt removes
literal prompt variation but does not prove behavioral compatibility.

There are 21 total edits from a non-best source: ten are current positive
targets and eleven are context-only. Nine lack the v8 atom-status advantage;
five of those nine are positive targets. All 21 sources were the visible
latest image at decision time; none selected an image hidden from the Planner.

This supports keeping reducer-best as a strong default while allowing the
visible latest image when its pixels support the choice. A hidden historical
source may be selected only from recorded atom evidence unless the
visible-image protocol is separately expanded.

### 2.5 PlannerContext v0.6 cannot support episode-wide semantic closure

`episode_memory.last_completed_image_round` retains the complete most recent
image instruction. `prior_image_rounds` retains action, source, target,
preserve, and outcome summaries but omits the earlier instructions.

The Planner can therefore compare its next plan with only the immediately
preceding instruction. It cannot know whether a proposed intervention already
failed two or three rounds earlier. A system rule against episode-wide
equivalent retry would be unlearnable from this input.

With at most five image Attempts, retaining earlier execution instructions
adds at most four bounded instructions. This is preferable to an LLM summary
or strategy ontology and is deterministically reconstructable from immutable
action events.

Across all 1,159 persisted PlannerContext snapshots, a deterministic dry
calculation gives:

- current context JSON: 5,557 mean characters, 11,468 maximum;
- restored prior instructions: 1,152 mean added characters, 6,425 maximum;
- augmented context: 6,709 mean characters, 15,760 maximum, roughly 3,940
  tokens at the existing character-based estimator.

This is well below the frozen 24,000-token SFT context budget.

## 3. Three Separate Decision Layers

### 3.1 Runtime validity

Runtime validation must enforce only facts that are deterministic from the
current event prefix:

- schema-valid single action;
- legal and existing source Attempt;
- budget and submit eligibility;
- target/preserve references;
- executable instruction quality;
- no future references or environment-owned output fields.

Runtime must not reject an action solely because action/source/targets match a
prior action. It also must not claim that atom statuses fully determine visual
editability. Strategy quality is a policy and supervision question, not an
environment fact.

### 3.2 PlannerContext v0.7 memory

Introduce one narrow versioned context change:

- keep the complete `last_completed_image_round`;
- add `instruction` to every `prior_image_rounds` record;
- preserve existing source, target, preserve, and outcome fields;
- include only instructions produced before the current action;
- keep the five-Attempt budget unchanged.

Do not generate memory summaries with an LLM. Completed v0.6 trajectories can
be rebuilt as v0.7 training inputs from immutable canonical action events. The
original v0.6 snapshots and hashes remain rollout provenance.

This is past-only context augmentation, not future leakage. Because the old
Teacher did not see these additional earlier instructions, every reused target
still requires v9 compatibility review. A target that becomes contradictory
when its prior failed instruction is visible must be masked.

### 3.3 Planner policy

The frozen v9 system should instruct the Planner:

1. Prefer the reducer-best source for editing.
2. A non-best source is allowed when it is the visible latest image and its
   visible composition provides a concrete advantage, or when recorded atom
   evidence establishes an advantage for the target/preserve set.
3. Do not justify a hidden historical source using unseen visual composition.
4. After regression or no progress, compare the candidate plan with all
   relevant failed instructions visible in episode memory, not only the
   immediately preceding plan.
5. Reusing the same action/source/targets is allowed when the instruction
   changes a concrete visual intervention.
6. A concrete intervention change includes changed instance operation,
   spatial anchor, separation/layout, pose/contact/motion evidence, identity
   disambiguation, or preservation response to a regression.
7. Source-free regeneration is appropriate when the visual route is globally
   unsuitable; it is not required merely to make a tuple different.
8. Runtime may execute a semantic resample, but without an explicit rationale
   signal an equivalent retry is not eligible as a positive SFT target.

No `decision_summary`, strategy ID, backend, score prediction, or additional
assistant field is added.

### 3.4 Offline supervision eligibility

Every candidate target receives environment-owned annotations that are not
part of the assistant target:

```json
{
  "target_policy_version": "meaningful_retry_v9",
  "policy_compatibility": "compatible | incompatible | review",
  "retry_relation": "not_applicable | material_change | deliberate_resample | equivalent | uncertain",
  "outcome_tier": "initial | atom_best_gain | strong_gm_best_gain | marginal_gm_gain | local_only | harmful | ineffective | submit_best",
  "include_as_sft_target": true,
  "review_provenance": "deterministic | bounded_semantic_review"
}
```

Compatibility and outcome must be computed in two isolated passes:

1. `policy_compatibility` and `retry_relation` receive only the reconstructed
   point-in-time v0.7 context, its visible images, and the candidate action.
   They must not receive the candidate result image, Geneval2 result,
   transition, later rounds, final best, or submission.
2. `outcome_tier` then compares the persisted result with `best_before`.

The joined annotations are derived from immutable events, but none may be
shown as prior information in the PlannerContext used to train the annotated
action.

## 4. SFT Inclusion Policy

### 4.1 Full-weight include

- schema-valid first generation with complete executable instruction;
- compatible atom-gain retry satisfying Section 4.3;
- compatible strong GM-only retry satisfying Section 4.4;
- correct submission of reducer-best;
- later, only separately validated `query_skill` actions.

### 4.2 Context-only

- harmful or ineffective actions;
- the four actions that improve only a non-best source but not global best;
- policy-incompatible source choices;
- equivalent, semantic-resample, or uncertain retry relations;
- marginal or structurally unsafe GM-only gains;
- equal-pass atom swaps;
- raw rejected Teacher output;
- `query_skill` until utility and timing are accepted.

Harmful and ineffective actions remain visible in canonical history so later
targets can learn recovery. They do not receive assistant loss.

### 4.3 Atom-gain rule

Compare the result with `best_before`, never with edit source or previous
latest. A retry is `atom_best_gain` only when:

1. result pass-count is greater than `best_before` pass-count;
2. at least one declared target changes from non-pass to pass;
3. no declared preserve constraint changes from pass to non-pass.

Otherwise the action remains context-only for v9 SFT even if the reducer
selects it under the broader environment objective.

### 4.4 Strong GM-only rule

Compare the result with `best_before`. A retry is `strong_gm_best_gain` only
when all conditions hold:

1. the complete passed-constraint ID set is unchanged;
2. GM delta is at least `0.02` on the `[0, 1]` scale;
3. mean target-set correct-answer log-probability delta is greater than `0`;
4. mean preserve-set correct-answer log-probability delta is at least `-0.02`;
5. the action passed the independent ex-ante compatibility audit.

An empty preserve set has preserve delta `0`. Probabilities are floored with
the same numerical floor used by the frozen Geneval2 GM calculation.

The `0.02` margins mean at least two displayed GM points globally and no more
than about two percent average geometric degradation across declared preserve
atoms. Sensitivity at `0.01`, `0.02`, and `0.05` must remain in the audit
report; changing the frozen threshold creates a new supervision-policy
version.

The reducer continues to use every positive GM tie-break. These stricter
conditions control only which decisions are strong enough to imitate.

## 5. Semantic Retry Audit

The current 65 same-route retries require a bounded one-time audit.

The compatibility audit compares the candidate with every relevant historical
failed instruction in its v0.7 context, including non-adjacent routes such as
`A -> B -> A`. It compares each instruction by semantic block:

- target operation;
- spatial grounding;
- preservation lock;
- forbidden changes.

`material_change` requires a concrete executable difference, not synonyms or
additional verbosity. This audit must run before and without access to the
candidate result or outcome. Outcome success cannot be used to decide whether
the action was a meaningful ex-ante plan.

Deterministic checks can identify exact duplicates and changed entities,
counts, relations, and spatial anchors. Borderline cases receive bounded
semantic review. Because Action Protocol v0.5 has no resampling rationale,
semantic-equivalent retries are context-only even when their sampled result
later improved. The resulting annotation is supervision metadata only.

## 6. Reusing The Existing 200 Trajectories

The 200 trajectories remain the immutable evidence pool. Do not rewrite or
rerun them.

Re-export procedure:

1. Freeze one v9 training system prompt.
2. Rebuild each sample as PlannerContext v0.7 from its exact temporal event
   prefix, while preserving the original v0.6 context as provenance.
3. Run the outcome-blind v9 compatibility annotation.
4. Independently compute outcome tiers against `best_before`.
5. Mask incompatible, local-only, marginal, equivalent-resample, and uncertain
   actions.
6. Preserve original v7/v8 prompt provenance plus original v0.6 and rebuilt
   v0.7 context hashes in metadata.
7. Export to a new versioned output directory; do not overwrite the checkpoint
   200 dry run.
8. Balance evaluation reports by decision stage:
   initial generate, query, retry edit, retry regenerate, and submit.

Most existing data is reusable because Action Protocol, backends, evaluator,
and event ownership did not change. PlannerContext v0.7 only restores past
instructions already present in the event log. Loss eligibility still
requires review because the original Teacher saw v0.6.

## 7. Missing Data To Add

Do not collect another broad 200-row batch before closing these gaps.

1. A small v9 pilot containing persistent failures where repeated repair of
   the same target is appropriate.
2. More post-history regeneration positives so the model learns edit-versus-
   restart decisions rather than only source-free initial generation.
3. A capability-isolated Skill study before promoting `query_skill`.
4. Verb-heavy trajectories, especially chasing, after the action-pose Skill
   and generator instruction policy are frozen.
5. If early stopping is desired, explicit cost-aware examples and an objective
   that prices image calls. With zero image-call penalty, exhausting the budget
   can be rational and must not be labeled meaningless merely because the
   realized image failed.

## 8. Validation

### Static

- every SFT target is compatible with the single v9 system;
- no future outcome is present in its input;
- compatibility annotations contain no candidate outcome fields or refs;
- outcome tiers compare result against `best_before`;
- no local-only positive remains;
- no equal-pass atom swap remains positive;
- no semantic-equivalent resample remains positive;
- every masked failure remains available as history;
- v7/v8 origin alone never decides eligibility;
- no Action schema migration is introduced;
- PlannerContext v0.7 contains only past information and reproduces every
  prior instruction from canonical action events.

### Small live pilot

Use ten fixed prompts and equal image budgets to compare v8-hard and
v9-semantic, producing 20 paired trajectories:

- four persistent targets where the same route should remain legal after a
  material intervention change;
- three semantic-equivalence traps;
- two edit-to-regenerate cases;
- one visible non-best branch case.

Report:

- final atom pass, AM, and GM;
- productive same-route repairs;
- semantically equivalent blind retries;
- regressions and non-best branches;
- retry edit versus regenerate choices;
- submitted best and image-call count.

This pilot validates policy behavior. It does not establish model-level
superiority.

## 9. Recommended Decision

Adopt v9 as a forward training-policy candidate:

- remove the tuple-equality hard rejection;
- keep Action Protocol v0.5 unchanged;
- version PlannerContext as v0.7 with prior execution instructions retained;
- express meaningful retry in the system policy;
- enforce target-policy compatibility during SFT export;
- use global-best and target-relevant outcome tiers for positive labels;
- preserve all 200 trajectories as an off-policy evidence pool;
- run a small v9 pilot before Gate 3 supervision freeze.
