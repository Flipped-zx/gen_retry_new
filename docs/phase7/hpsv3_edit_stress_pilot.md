# HPSv3 Edit-Stress Pilot

This is a prospective evaluation plan for the auxiliary quality branch. It is
not a leaderboard claim and it does not alter the frozen 1k trajectory pool.

## Stage 0: Calibration and Feasibility

Use only the frozen 18-episode D2/D3+ x difficulty x U/D/N set in
`edit_stress_cohort_report.md`. Score all 90 existing images with one HPSv3
checkpoint and preprocessing profile. Blind reviewers label pairwise visible
degradation without seeing HPS or Geneval2. Choose `watch_below` and
`high_below` from HPS source deltas against those labels, write one canonical
risk-policy artifact, and freeze its SHA-256. This set cannot admit a policy.

Use three independent raters per parent/child pair. Show the two images in a
left/right order generated from a recorded randomization seed; hide arm names,
HPS, and Geneval2. Each rater assigns `child better=1`, `tie=0.5`, or
`parent better=0` for visible fidelity, non-target preservation, and artifacts.
The calibration label is the mean of the three ratings, and report Fleiss'
kappa (or Krippendorff's alpha) as an inter-rater diagnostic; do not relabel
the pair after seeing HPS.

## Stage 1: Held-Out Offline Check

Use the disjoint 60-episode manifest in
`artifacts/phase7/edit_stress_confirmation_cohort_v1.json`. Score its 120
predeclared parent/child images without retuning. This estimates whether the
calibrated signal transfers to held-out edit-stress pairs. It still cannot show
that HPS-aware planning mitigates quality loss.

## Stage 2: Paired Intervention

Rerun the same 60 prompt groups from clean run directories under both arms.
This admission pilot uses the GPT-5.5 `teacher_system_prompt_v9` planner for
both arms so the only planner-input change is the recorded v0.8 advisory. The
frozen SFT service remains v0.7-only and is not silently treated as a v0.8
planner; an HPS-aware SFT rollout would require a separate training/version
change. Freeze prompt, TaskSpec, planner model and sampling, execution profile,
Qwen seed and rendering settings, maximum image attempts, and image-call
budget. Pair results by episode and seed. HPS calls do not consume image-call
budget. Attempts within an episode are repeated observations, not independent
samples.

## Arms

- `G`: GPT-5.5 Teacher v9, PlannerContext v0.7, Skill store, Geneval2, and
  `qwen_dual_backend@1`.
- `G+H`: PlannerContext v0.8, the same system and budgets, visible HPSv3
  observations, and `planner_context_only_hpsv3_advisory_v1`.

There is no hidden middleware or source filter. The Planner may explicitly
query `local_edit_preservation`, choose a historical source, or regenerate;
those decisions remain canonical Actions. HPSv3 never changes reducer ordering
or filters a Geneval2 result.

The environment emits one explicit HPS result per evaluated Attempt before the
next v0.8 PlannerContext: `success` carries the score, while `failed` or
`missing` carries only `unknown` quality. This makes an absent score observable
without turning HPS into a blocking evaluator.

## Endpoints

Use this frozen, conjunctive admission rule:

1. Primary semantic guard: paired mean submitted Geneval2 passed-atom fraction
   for `G+H - G`; the episode-cluster bootstrap 95% lower bound must exceed the
   pre-registered `-0.02` non-inferiority margin. Also report all-pass rate and
   GM without substituting either for the primary guard.
2. HPS coverage guard: all submitted Attempts in both arms must have successful
   HPS scores, and at least 95% of non-root edit Attempts visible to `G+H` must
   have successful scores. Any failed/missing event is reported as unknown;
   it is never imputed as low risk. If coverage fails, the result is
   `inconclusive`, not admitted.
3. Quality guard: among the complete submitted pairs, the episode-cluster
   bootstrap 95% lower bound for `mu(G+H) - mu(G)` must be strictly above `0`;
   the upper bound for the paired high-risk edit-rate difference must be below
   `0`; and the blind human score (`G+H win=1`, tie=`0.5`, `G win=0`) must have
   a 95% lower bound above `0.5`. All three are required. A favorable HPS shift
   without the semantic guard or without the human guard does not admit the
   policy.
4. Mechanism audit: `local_edit_preservation` queries, edit-chain depth,
   lineage-root rebranches, regenerations, semantic-gain/HPS-drop conflicts,
   missing HPS events, and image-call counts.

For each arm and episode, define high-risk edit rate as
`(high + unknown edit observations) / all edit Attempts`; an episode with no
edit Attempt has rate `0`. Counting unknown as high is the conservative
admission analysis; also report observed-only rates separately.

For a submitted root Attempt, the primary quality endpoint uses its successful
absolute `mu`; `delta_from_anchor=null` is retained and excluded from the
lineage-delta mechanism analysis, never replaced by a fabricated zero. A
failed/missing submitted score fails the coverage guard. The 95% intervals are
cluster bootstrap intervals over episode IDs, with thresholds frozen before
opening confirmation results.

For Stage 2, use the same three-rater protocol on the submitted `G`/`G+H`
pair, randomizing left/right independently with a recorded seed. The human
score for each episode is `G+H win=1`, tie=`0.5`, `G win=0`; report the
three-rater mean and inter-rater agreement before applying the lower-bound
gate.

The 60 prompts are an enriched edit-stress cohort, not a representative 1k
estimate. A positive result supports only the tested quality-aware advisory;
it cannot claim that edit is intrinsically lossy, that HPSv3 guarantees
perceptual preservation, or that the effect generalizes to all prompts.
