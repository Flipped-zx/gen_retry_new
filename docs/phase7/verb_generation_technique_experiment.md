# Verb Generation Technique Experiment

Date: 2026-07-31

## Decision

Adopt `focal_action_anchor` as a targeted `action_pose_relation` Skill
operator for a failed or uncertain verb atom. Do not prepend it to every
initial generation.

For `chasing`, the operator makes the asymmetric action legible through one
decisive pursuit pair:

1. keep the pursuer and target roles explicit and never reverse them;
2. place one lead pursuer directly behind one lead fleeing target;
3. show gaze, reaching, escape, and look-back intent across a short
   capture-imminent gap;
4. continue remaining instances in separate, countable role trails;
5. keep supporting objects outside the focal gap and use one continuous
   scene.

This is a prompt-composition technique, not a verifier override. It contains
no score, threshold, expected answer, or submit rule. The Planner still emits
one canonical action, Geneval2 remains environment-owned, and the reducer
still protects the best historical attempt.

## Why this scope

The completed 200-trajectory Flow-DPPO result had:

- all verbs: 10/22 submitted passes (45.45%);
- `playing with`: 5/6;
- `jumping over`: 3/4;
- `chasing`: 2/12, from an initial 0/12.

Therefore the experiment used the complete 12-prompt `chasing` subtype,
rather than mixing the relatively stronger verb forms into the result.

## Controlled setup

- Baseline root: `runs/phase7_flow_dppo200_fresh8_v1`
- Prompt source: the exact `a_000` generation instruction from each episode
- Candidate change: one deterministic verb-composition operator added to the
  existing instruction
- Generator: Qwen-Image-2512 through the accepted `qwen_dual_backend@1`
  generation path
- Sampling: seed 0, 50 steps, 1024 x 1024, true CFG 4.0
- Evaluation: the original task atoms through local Geneval2
- Execution: two physical HCU lanes (`ROCR_VISIBLE_DEVICES=0` and `1`)
- Persistence: every input, image, Geneval2 report, manifest, per-episode
  comparison, and summary is artifact-backed under `runs/verb_strategy_*`

The baseline `a_000` images used the same generator and sampling settings.
Candidate comparison is paired at the episode and seed level.

## Iterations

Six formulations were tried in alternating two-card lanes. The first pilot
used seven prompts; the next blind slice used the five prompts not in that
pilot. The viable formulations were then completed over all 12 prompts.

| Technique | Cohort | Chasing pass | Non-verb atoms passed | Decision |
| --- | ---: | ---: | ---: | --- |
| `lateral_kinematic_chain` | 7 | 2/7 | 30/34 initial | Useful diagnostic, not selected |
| `graphic_action_strip` | 5 blind | 0/5 | 21/26 initial | Reject |
| `compact_capture_gap` | 12 | 1/12 | 49/60 initial | Reject |
| `compact_intent_asymmetry` | 12 | 2/12 | 54/60 initial | Ties submitted verb result; reject |
| `imminent_capture_frontload` | 12 | 3/12 | 49/60 initial | Verb gain, excessive preservation loss |
| `focal_action_anchor` | 12 | **3/12** | **55/60 initial** | Select as targeted retry operator |

On the same 12 episodes, the original first images passed 0/12 chasing atoms
and 60 non-verb atoms. The existing multi-attempt submitted results passed
2/12 chasing atoms and 64 non-verb atoms. Thus the selected technique beats
the current chasing count as a one-image candidate, but its standalone total
does not beat the current submissions. This is why the technique is
conditional and history-aware rather than a global prompt prefix.

## Direct paired improvement

`phase3_ep_098` is the cleanest controlled result:

| Measure | Existing `a_000` and submitted | Focal candidate |
| --- | ---: | ---: |
| Passed atoms | 4/5 | **5/5** |
| Chasing status | fail | **pass** |
| Chasing confidence | 0.002505 | **0.996891** |
| Soft-TIFA GM | 0.301479 | **0.999290** |
| Previously passed atoms regressed | — | **0** |

This candidate changed only the prompt composition and used the same seed and
generation settings. It is an observed evaluated image, not a projected
model result.

## History-aware comparison with the current result

To estimate the effect of adding this operator as one extra retry, the
observed focal candidates were replayed through the frozen comparator:

`higher atom pass count -> higher GM -> earlier attempt`

The comparator would retain the focal result for `phase3_ep_042` (+1
non-verb atom), `phase3_ep_098` (+1 verb atom and a new all-pass trajectory),
and `phase3_ep_200` (equal atom count, slightly higher GM). It would reject
all regressive focal candidates.

| Metric | Current submitted 200 | With observed focal retry + reducer | Change |
| --- | ---: | ---: | ---: |
| Passed atoms | 1301/1419 | **1303/1419** | +2 |
| Atom pass rate | 91.68% | **91.83%** | +0.14 points |
| All verbs | 10/22 | **11/22** | +1 |
| `chasing` | 2/12 | **3/12** | +1 |
| All-pass trajectories | 111/200 | **112/200** | +1 |

This table is a historical-best-compatible counterfactual over newly
generated and evaluated candidates. It is not a fresh 200-episode policy
rollout and does not claim an equal-compute causal improvement over the
original up-to-five-attempt policy.

## Integration

`action_pose_relation@2.0.0` now carries the selected operator. Its usage
contract is:

- query it after a verb atom failed or is uncertain;
- switch from generic dust, blur, or synonymous action wording to the focal
  action topology;
- preserve counts, identities, attributes, and static relations;
- keep a regressive candidate in canonical history, but continue from or
  submit the reducer-best attempt.

No Action schema, message schema, event ownership, memory reducer, score
policy, or SFT masking rule changed.

## Limitations and next evidence

- The measured gain is for `chasing`; the generalized `playing with` and
  `jumping over` formulations have unit coverage but no new image benchmark
  in this experiment.
- Geneval2 sensitivity and generator capability remain entangled.
- The 12 prompts are the full existing subtype cohort, not a new held-out
  prompt set.
- A two-episode prospective multi-round Teacher pilot is now complete. It
  improved one selected failure to all-pass and tied the other on atoms and
  verb status. See `docs/phase7/verb_multiround_teacher_pilot.md`. This small
  pilot demonstrates mechanism and a positive signal, not a population
  estimate.
