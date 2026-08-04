# Verb Failed-12 Multi-Round A/B

Date: 2026-07-31

Post-study adoption note (2026-08-01): the typed Skill, delayed retrieval, and
verb-pass retention behavior are retained in
`teacher_system_prompt_v9_meaningful_retry_verb_retention`. V9 removes the
unrelated coarse action/source/target tuple rejection and uses PlannerContext
v0.7. The A/B tables below remain the immutable v8 versus v8.1 experiment and
must not be relabeled as v9 evidence.

## Outcome

The retry-integrated candidate passed the predeclared promotion rule on the
ten episodes not used in the earlier two-episode pilot:

| Primary cohort | Atoms | Verb passes | All-pass | Images | Mean GM |
| --- | ---: | ---: | ---: | ---: | ---: |
| Production A | 54/71 | 0/10 | 0/10 | 50 | 0.2770 |
| Candidate B | **56/71** | **3/10** | 0/10 | 50 | **0.3197** |
| Delta | **+2** | **+3** | 0 | 0 | **+0.0427** |

The frozen rule required at least two new primary-cohort verb passes, no loss
of total atoms, and no loss of all-pass episodes. Candidate B satisfies all
three conditions.

Across all twelve official-current verb-nonpass episodes, including the two
earlier development cases:

| Full failed cohort | Atoms | Verb passes | All-pass | Images | Mean GM |
| --- | ---: | ---: | ---: | ---: | ---: |
| Official current | 64/84 | 0/12 | 0/12 | 60 | 0.3106 |
| Production A | 66/84 | 1/12 | 1/12 | 59 | 0.3465 |
| Candidate B | **67/84** | **4/12** | **1/12** | 60 | **0.3751** |

This answers the earlier question directly: the multi-round candidate did not
only add one verb pass. Relative to the production A control it added three;
relative to the official current submissions it added four on this frozen
failure cohort.

## Intervention

Candidate B is a retry-system strategy, not a forced verb score override:

1. `action_pose_relation@2.1.0` has typed operators:
   - chasing: one lateral near-capture pair, asymmetric role intent, no role
     reversal, frontal stampede, co-running, catalog grid, or split clusters;
   - playing with: reciprocal cross-role gaze plus gentle reach/contact,
     without crowding all counted participants;
   - jumping over: one decisive airborne subject over one grounded obstacle,
     a clean vertical gap, and no time-sequence duplication.
2. Retrieval is delayed until an evaluated image reports a failed or uncertain
   verb. Production A queried the action Skill before the first image in
   12/12 episodes; Candidate B queried it after the first image in 12/12.
   This makes the full Skill content available at the first actual verb retry
   instead of leaving only a compact summary.
3. `teacher_system_prompt_v8_1_verb_evidence_retention` preserves a historical
   verb-pass branch when it matches reducer-best on passed-atom count and only
   non-verb failures remain. The environment still owns reducer-best, scores,
   transitions, budgets, and submission facts.

No action schema, reducer ordering, score policy, memory ownership, or SFT
masking changed.

## Per-episode submitted result

| Episode | Verb | Production A | Candidate B | Atom delta |
| --- | --- | --- | --- | ---: |
| `ep014` | chasing | 7/8 fail | 6/8 fail | -1 |
| `ep032` | jumping over | 8/10 fail | **8/10 pass, 0.9769** | 0 |
| `ep042` | chasing | 4/5 fail | 4/5 fail | 0 |
| `ep051` | chasing | 4/5 fail | 4/5 fail | 0 |
| `ep098` | chasing | 5/5 pass | **5/5 pass, 0.8533** | 0 |
| `ep107` | chasing | 2/5 fail | 3/5 fail | +1 |
| `ep116` | chasing | 7/8 fail | **7/8 pass, 0.8807** | 0 |
| `ep135` | playing with | 7/10 fail | **8/10 pass, 0.7761** | +1 |
| `ep154` | chasing | 4/5 fail | 4/5 fail | 0 |
| `ep163` | chasing | 3/5 fail | 4/5 fail | +1 |
| `ep181` | chasing | 7/8 fail | 7/8 fail | 0 |
| `ep200` | chasing | 8/10 fail | 7/10 fail | -1 |

The negative cases remain material. Candidate B regressed `ep014` by one atom
and `ep200` by one atom relative to A; it did not solve seven submitted
chasing verbs. The promotion decision rests on the frozen primary aggregate,
not on claiming universal verb resolution.

## Multi-round mechanism evidence

### `ep032`: generate, acquire typed evidence, then preserve it

- `a_000`: 8/10, jumping-over fail, confidence 0.000045.
- After the verifier result, the Teacher queried `action_pose_relation@2.1.0`.
- `a_002`: 8/10, jumping-over pass, confidence 0.994735.
- `a_003`: a peripheral edit preserved jumping-over at 0.981990.
- `a_004`: submitted 8/10 with jumping-over pass at 0.976900.

The atom count tied Production A, while the verb changed from fail to pass.

### `ep135`: recover a historical verb-pass branch

- `a_001`: 8/10, playing-with pass at 0.880226; only two non-verb counts failed.
- `a_002`: also 8/10 with higher GM, so the environment made it reducer-best,
  but playing-with regressed to fail.
- The new Teacher policy selected historical `a_001`, not reducer-best
  `a_002`, as the next edit source and placed the verb in
  `preserve_constraint_ids`.
- `a_003`: 8/10, playing-with pass at 0.776092; its GM exceeded the regressive
  branch, so reducer-best returned to verb-pass evidence.

This is the requested history-aware retry behavior: the improvement survives
multiple image attempts and changes an executable `source_attempt_id`, rather
than being a single-generation prompt comparison.

## Relation to the 200-episode result

The actual final 200 submissions remain 1301/1419 atoms, 10/22 verb passes,
and 111/200 all-pass episodes until those 200 episodes are rerun.

Two counterfactual views are useful and must not be conflated:

- Replacing only the twelve frozen failures with Candidate B produces
  1304/1419 atoms, 14/22 verb passes, 112/200 all-pass, and mean GM 73.89.
- Applying the frozen pass-count-then-GM historical comparator to official
  current plus Candidate B produces 1306/1419 atoms, 12/22 verb passes,
  112/200 all-pass, and mean GM 74.62. It retains only two of the four new
  verb passes because the score policy does not special-case verb atoms.

The first estimates the submitted output of targeted reruns. The second is a
conservative observed-candidate compatibility calculation. Neither is a fresh
200-episode rollout.

## Reproducibility

- Teacher: GPT-5.5
- A prompt: `teacher_system_prompt_v8_retry_closure_policy`
- B prompt: `teacher_system_prompt_v8_1_verb_evidence_retention`
- B prompt SHA-256:
  `291bdf812ec84f6cafbf6708333b114d45b95af54677f843b038bf6d1423eaf0`
- Skill: `action_pose_relation@2.1.0`
- Skill SHA-256:
  `4b1d64ee0d951efbaea1bb9923261ae72a652e1217b27c65523c8c8f06ba499a`
- Image execution: `qwen_dual_backend@1`
- Qwen-Image-2512 generation: 50 steps, 1024 x 1024
- Qwen-Image-Edit-2511 edit: 40 steps, 1024 x 1024
- Five image attempts per episode
- Two physical HCUs; one sequential episode per HCU
- Local Geneval2 after every image attempt

Artifacts:

- `artifacts/verb_multiround_failed12_v21_live/comparison.json`
- `artifacts/verb_multiround_failed12_v21_live/rollout_audit.json`
- `artifacts/verb_multiround_failed12_v2_expansion10/rollout_audit.json`
- `runs/verb_multiround_failed12_v21_live/`
- `runs/verb_multiround_failed12_v2_expansion10/`

Validation at report time:

- Production A rollout audit: PASS, 10 episodes, 50 attempts.
- Candidate B rollout audit: PASS, 12 episodes, 60 attempts.
- Production A trajectory analysis: 10 episodes, 73 labeled actions, 0 invalid.
- Candidate B trajectory analysis: 12 episodes, 102 labeled actions, 0 invalid.
- `pytest tests/contract -q`: 79 passed.
- `pytest tests/unit -q`: 145 passed.
- Schema validation: 12 schemas passed.
- Fixture validation: 104 records passed.
- Standard episode replay: PASS.
