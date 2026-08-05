# HPSv3 Teacher Decision Probe

## Purpose

This is a six-trajectory counterfactual probe for the frozen mini-pilot in
`artifacts/phase7/hpsv3_mini_pilot_manifest_v1.json`. It tests whether an
environment-owned HPSv3 same-prompt quality signal is visible to the Teacher
and can change the next Planner Action while Geneval2 remains the primary
objective. No image action was executed and no canonical trajectory was
modified.

## Setup

- `G`: GPT-5.5 Teacher v9 with PlannerContext v0.7.
- `G+H`: the same Teacher with PlannerContext v0.8 and the
  `planner_context_only_hpsv3_advisory_v1` policy.
- HPSv3 checkpoint and preprocessing are exactly those recorded in
  `artifacts/phase7/hpsv3_mini_pilot_v1.json`.
- Exploratory thresholds only: `watch_below=-0.5`, `high_below=-1.0`.
  They are not calibrated admission thresholds.
- Both arms saw the same historical prefix and visible images for each pair.

The HPS diagnostic reported a lower child-minus-parent `mu` for all six edit
pairs. This is an uncalibrated model-score change, not a human-validated claim
that perceptual quality dropped:

| Episode | Stratum | HPS delta | Risk | Geneval2 context |
| --- | --- | ---: | --- | --- |
| `phase3_ep_926` | U | -0.898564 | watch | semantic gain / GM drop |
| `phase3_ep_461` | U | -1.455826 | high | semantic gain / GM drop |
| `phase3_ep_855` | D | -1.560818 | high | semantic regression / GM rise |
| `phase3_ep_063` | D | -0.053028 | low | semantic regression / GM rise |
| `phase3_ep_283` | N | -0.117944 | low | positive control |
| `phase3_ep_648` | N | -0.028915 | low | positive control |

## Decision result

All 12 Teacher calls returned parseable canonical actions. Three pairs differed
under strict JSON action comparison. Only one changed action type; two retained
`edit_image` but changed the executable wording/details:

| Episode | Risk | G | G+H | Changed? |
| --- | --- | --- | --- | --- |
| `phase3_ep_926` | watch | `edit_image` | `edit_image` | Yes, wording made local preservation more explicit |
| `phase3_ep_461` | high | `edit_image` | `query_skill(local_edit_preservation)` | Yes |
| `phase3_ep_855` | high | `submit_attempt` | `submit_attempt` | No |
| `phase3_ep_063` | low | `submit_attempt` | `submit_attempt` | No |
| `phase3_ep_283` | low | `edit_image` | `edit_image` | Yes under exact JSON; same semantic repair with more preservation detail |
| `phase3_ep_648` | low | `submit_attempt` | `submit_attempt` | No |

The high-risk D pair did not continue because its image budget was already
exhausted. This is consistent with the policy boundary: HPS is advisory and
cannot override the primary Geneval2/budget semantics. The high-risk U pair is
the cleanest mechanism signal because HPS changed the next action to a real
preservation-skill query before another edit.

## Interpretation

The probe supports two narrow feasibility observations:

1. HPSv3 reports a lower same-prompt score after edit in this selected set.
2. The v0.8 field design is sufficient for the Teacher to propose a different
   retry behavior without changing reducer best selection or the canonical
   Action protocol.

It does **not** establish mitigation. The probe neither generated a new image
nor measured a post-intervention Geneval2/HPS result. In addition, the Teacher
API calls were separate requests without a fixed sampling seed and were always
issued in `G` then `G+H` order; action differences therefore combine context
effect with ordinary Teacher sampling/provider and time-order variation. The
reported `query_skill` is only a proposed Action: this probe did not execute
the query, emit its Skill response, or request the following Action. The
offline context also includes synthetic `missing` HPS records for historical
attempts outside each selected parent/child pair. Finally, one G+H instruction
contained an action-quality typo (it said four cows although the TaskSpec
requires seven). The result is a qualitative feasibility probe, not a causal
estimate.

## Next experiment

Run the pre-registered paired intervention in
`docs/phase7/hpsv3_edit_stress_pilot.md` on the disjoint 60-episode cohort:

- freeze prompt, TaskSpec, Teacher version/sampling, Qwen seed, image budget,
  and execution profile;
- run fresh `G` and `G+H` episodes with HPS evaluated before every v0.8
  planning call;
- keep Geneval2 as the primary non-inferiority guard;
- require successful HPS coverage, improved submitted HPS, lower high-risk edit
  rate, and blind human preference as a conjunctive quality gate;
- report episode-cluster bootstrap intervals and keep unknown HPS results
  conservative rather than imputing low risk.

Until that paired rerun is complete, the defensible conclusion is: **HPSv3 is
a plausible auxiliary decision signal and the field integration is
implementable; it has not yet been shown to preserve image quality while
retaining Geneval2 gains.**
