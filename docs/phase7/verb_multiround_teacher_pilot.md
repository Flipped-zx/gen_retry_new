# Verb Multi-Round Teacher Pilot

Date: 2026-07-31

## Outcome

`action_pose_relation@2.0.0` produced a real multi-round improvement on one of
two preselected `chasing` failures and tied the other on passed atoms and verb
status:

| Episode | Current submitted | New multi-round submitted | Outcome |
| --- | ---: | ---: | --- |
| `phase3_ep_014` | 7/8, verb fail | 7/8, verb fail | Tie on atoms and verb; lower GM |
| `phase3_ep_098` | 4/5, verb fail | **5/5, verb pass** | Improved |
| Combined | 11/13, 0/2 verbs | **12/13, 1/2 verbs** | +1 atom, +1 verb |

The new runs used nine image attempts versus ten in the historical runs.
When old and new attempts are combined under the frozen comparator, the old
`ep_014` submission is retained and the new `ep_098` submission is selected.
Therefore the history-aware result is also 12/13 atoms, 1/2 verbs, and 1/2
all-pass episodes, with no accepted regression.

This is the requested multi-round system validation. It is not the earlier
single-generation counterfactual.

## Why these two episodes

The episodes were selected before the new live runs:

- `phase3_ep_098`, `a dog chasing four kangaroos`, represented preservation
  conflict. The historical system generated a verb-pass image but lost the
  kangaroo count, then lost the verb while repairing count, and submitted
  4/5.
- `phase3_ep_014`, `four suitcases in front of five giraffes chasing seven
  monkeys`, represented a high-cardinality composite scene. Its historical
  submission was already 7/8 and failed only the verb.

Together they test both a recoverable action/count conflict and a hard
verb-only tail under heavy count and depth constraints.

## Setup

- Fresh empty episode state; no historical image or Attempt imported
- GPT-5.5 Teacher API
- `teacher_system_prompt_v8_retry_closure_policy`
- `action_pose_relation@2.0.0`
- Action Protocol 0.5 and PlannerContext 0.6
- `qwen_dual_backend@1`
- Qwen-Image-2512 generation: 50 steps, 1024 x 1024
- Qwen-Image-Edit-2511 edit: 40 steps, 1024 x 1024
- Local Geneval2 after every image Attempt
- Five-image maximum per episode
- One sequential episode per physical HCU, with the two episodes running in
  parallel on HCU 0 and HCU 1

Both episodes independently chose `query_skill` and retrieved
`action_pose_relation@2.0.0`; the focal-action operator then appeared in the
Teacher's executable image instructions. No external instruction required a
pass or supplied an evaluator answer.

## Successful trajectory: `phase3_ep_098`

| Attempt | Action | Atoms | Verb | Verb confidence | GM |
| --- | --- | ---: | --- | ---: | ---: |
| `a_000` | generate | 3/5 | fail | 0.017747 | 0.047128 |
| `a_001` | edit best | 3/5 | fail | 0.163062 | 0.282380 |
| `a_002` | edit best | 3/5 | uncertain | 0.410476 | 0.433876 |
| `a_003` | edit best | **5/5** | **pass** | **0.999018** | **0.999621** |

This trajectory verifies the multi-round mechanism:

1. the first generation used the retrieved focal-action composition;
2. edits stayed attached to reducer-best history;
3. verb evidence progressed from fail to uncertain to pass;
4. the final edit simultaneously closed the missing count and verb atoms;
5. the Teacher submitted immediately with `all_constraints_passed`.

The final image is
`runs/verb_multiround_teacher_v2/phase3_ep_098/images/img_003.png`.

## Hard negative: `phase3_ep_014`

The new trajectory improved from 5/8 to 7/8 but still failed chasing:

| Attempt | Action | Atoms | Failed atoms |
| --- | --- | ---: | --- |
| `a_000` | generate | 5/8 | giraffe count, chasing, monkey count |
| `a_001` | edit | 6/8 | chasing, monkey count |
| `a_002` | edit | 6/8 | chasing, monkey count |
| `a_003` | edit | **7/8** | chasing |
| `a_004` | verb-only edit | 6/8 | chasing, monkey count |

The reducer correctly submitted `a_003`. Visual inspection shows why the
verb remains hard: the image contains the required high counts and foreground
suitcases, but the five giraffes are mostly front-facing while the monkeys
occupy a separate side cluster. The composition reads as two groups in one
scene rather than a pursuit chain.

This result suggests a generator/layout capacity bottleneck, not merely
missing chase vocabulary.

## Rejected route-closure variant

An experiment-only Teacher variant added a semantic closure rule: after two
verb-targeted edits with no fixed or new-uncertain atom, switch to a complete
source-free regeneration. It was run fresh on the same two episodes.

| Episode | Variant submitted | Comparison |
| --- | ---: | --- |
| `phase3_ep_014` | 5/8, verb fail | Regressed from current 7/8 |
| `phase3_ep_098` | 5/5, verb pass in three images | Successful and faster |
| Combined | 10/13, 1/2 verbs | Worse atom total than current and Skill v2 pilot |

The rule successfully changed the action route, but the regenerated
high-cardinality image failed the same giraffe-count, monkey-count, and verb
atoms. Because final quality regressed on `ep_014`, the variant was rejected
and removed from production code. The production Teacher remains v8.

Artifact-backed traces remain under
`runs/verb_multiround_teacher_v3_route_closure` for negative evidence.

## Decision

Keep:

- `action_pose_relation@2.0.0`;
- conditional retrieval for failed or uncertain verbs;
- focal pursuit pair plus asymmetric pursuer/target roles;
- canonical history and reducer-best protection.

Do not promote:

- unconditional verb prefixes;
- the experiment-only forced route-closure rule;
- a claim that both representative failures were solved.

The next credible performance estimate requires a prospective multi-round
run over the remaining current `chasing` failures, with a frozen cohort and
the same five-attempt budget. The two-episode result demonstrates mechanism
and a positive signal, not a reliable population effect.

## Validation

- Deterministic rollout audit, Skill v2: PASS, 2 episodes, 9 attempts
- Deterministic rollout audit, rejected variant: PASS, 2 episodes, 8 attempts
- Trajectory analysis, Skill v2: 2 valid submitted episodes, 13 labeled
  actions
- Trajectory analysis, rejected variant: 2 valid submitted episodes, 13
  labeled actions

