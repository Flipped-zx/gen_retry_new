# Edit-Stress Confirmation Cohort v1

This report defines a deterministic confirmation cohort that is disjoint from
the 18-episode calibration cohort in
`docs/phase7/edit_stress_cohort_report.md`. It does not read HPS results,
quality sidecars, or a new image re-evaluation. The machine-readable source of
truth is `artifacts/phase7/edit_stress_confirmation_cohort_v1.json`.

## Freeze

- Selection ID: `flow_dppo1000_v9_edit_stress_confirmation_v1`
- Episodes: 60, all distinct and all disjoint from the 18 calibration episode
  IDs.
- Selection hash: `cd2adfecd7a49ae712734cb4bb7db59b633d856ad8285433711e2ae3f58c046e`
- Manifest SHA-256: `4be6405795b2d135d389ac0b482ba6e0ddaf5a27d1d8d5d7ae020ef7df45f8af`
- Source run: `runs/phase7_flow_dppo1000_v9_fresh8_v1`
- Candidate predicate: `edit_count >= 2` and `max_depth >= 2`.

An episode is the statistical unit. A parent/child Attempt pair is a paired
within-episode observation, never an independent sample.

## Stratification

`D2` means maximum lineage depth exactly 2; `D3+` means at least 3. `U` means
an existing Geneval2 semantic gain with GM decrease, `D` means an existing
semantic regression with GM increase, and `N` has neither conflict. Episodes
with both U and D are assigned once, to the larger absolute GM conflict; ties
resolve U then child Attempt ID.

The initial quota was three episodes in each of 18 cells. After excluding the
calibration cohort, the U cells at D2 cannot meet that quota: easy has 0
available (shortfall 3), medium has 2 (shortfall 1), and hard has 1 (shortfall
2). Those six unfillable baseline seats plus the six seats needed to reach the
60-episode target are preallocated to D3+ conflict cells. The exact quotas,
available counts, and selected counts are in `stratum_summary`; no cell is
silently relaxed.

The resulting confirmation mix is 3 D2 easy D, 3 D2 easy N, 2 D2 medium U,
3 D2 medium D, 3 D2 medium N, 1 D2 hard U, 3 D2 hard D, 3 D2 hard N, 5 D3+
easy U, 4 D3+ easy D, 3 D3+ easy N, 5 D3+ medium U, 5 D3+ medium D, 3 D3+
medium N, 5 D3+ hard U, 6 D3+ hard D, and 3 D3+ hard N.

## Predeclared Endpoints

The manifest provides one direct `primary_hps_rescore_pair` for every selected
episode, including parent/child Attempt IDs, image and Geneval2 paths, and the
already-persisted `delta_pass`/`delta_GM`. This defines 60 primary paired
endpoints and 120 unique primary images. It also lists all 297 canonical
Attempt IDs and every episode image directory, allowing an explicitly
secondary all-Attempt analysis without changing the primary endpoint.

Offline diagnostic endpoint: report the persisted per-pair Geneval2 vector
`(delta_pass, delta_GM)` and its U/D/N stratum. This is descriptive and must
reproduce from the current canonical artifacts.

Offline HPS annotation: score the same predeclared parent and child images with one
fixed HPS version and compute
`(delta_pass, delta_GM, delta_HPS)`. The primary joint contrasts are
`delta_pass > 0 AND delta_HPS < 0` for U and
`delta_pass < 0 AND delta_HPS > 0` for D. N is a paired control; it must not
be relabelled using HPS after scoring.

These two offline views are not `G` versus `G+H` policy arms and cannot show
mitigation. The intervention test must rerun every prompt from a clean directory
under the two GPT-5.5 Teacher arms defined in `hpsv3_edit_stress_pilot.md`; the
frozen SFT planner remains v0.7-only. It first applies the `-0.02` Geneval2
passed-atom non-inferiority guard, then requires successful submitted HPS
coverage, positive submitted-`mu` lower bound, reduced high-risk edit rate,
and a blind human preference lower bound above 0.5. Root
`delta_from_anchor=null` is kept null and is not imputed as zero.

Use a stratified cluster bootstrap that resamples `episode_id` within the
frozen stratum. The primary analysis has one pair per sampled episode. A
secondary analysis may use all edit pairs, but must retain episode clusters;
it must not resample Attempts independently.

## Validation

Validate before HPS execution:

```bash
jq '.selected_episode_count, (.episodes | length), ([.episodes[].episode_id] | unique | length)' \
  artifacts/phase7/edit_stress_confirmation_cohort_v1.json
jq '[.episodes[].episode_id] as $confirmation | .calibration_exclusion_episode_ids as $calibration | [$confirmation[] | select(. as $id | $calibration | index($id))] | length' \
  artifacts/phase7/edit_stress_confirmation_cohort_v1.json
sha256sum artifacts/phase7/edit_stress_confirmation_cohort_v1.json
```

Expected values are `60`, `60`, `60`; overlap is `0`; and the manifest hash is
the frozen value above. For each primary pair, verify both image paths and
both Geneval2 paths exist before scoring. No protocol/reviewer gate is
triggered by this analysis-only cohort manifest.
