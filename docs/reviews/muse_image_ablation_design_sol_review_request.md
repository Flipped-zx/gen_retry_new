# SOL Review Request — Muse Image-Informed Ablation Design

## Gate

`Pre-experiment claim-sufficiency review; no protocol gate`

## Decision to review

Whether the staged plan in
`docs/research/muse_image_selective_lessons_and_ablation_plan.md` is the
minimum credible experiment program for isolating the contribution of a
verifier-grounded, image-aware, history-aware retry policy without conflating
adaptive planning with extra image sampling, verifier-based selection, or
student training.

## Current evidence

- Current live evidence: 20 design-exposed native v0.5 trajectories, 92
  Qwen-Image-Edit attempts, first-to-submitted atom pass
  `137/200 -> 171/200`, Soft-TIFA GM `20.99 -> 47.25`, AM
  `69.38 -> 84.70`, and 4/20 all-pass.
- Current Planner is GPT-5.5 Teacher, not a trained Qwen3-VL student.
- Reducer best uses thresholded pass count with earlier-attempt tie breaking;
  submitted GM is 47.25 while post-hoc peak GM is 53.33.
- Meta Muse Image supplies closed-blog precedent for edit/regenerate/tool
  routing and deliberate-compute versus Best-of-N, not a reproducible baseline.
- Google RichHF + Muse supplies a verifier/selection/inpainting precedent, but
  no sequential action planner or canonical attempt history.
- Proposed order:
  1. zero-image-call analysis of the existing 20 trajectories;
  2. planner-only `V x I x H` screen plus atom-level versus aggregate-only
     feedback;
  3. matched one-step mechanism tests;
  4. shared-initial-image four-arm live pilot: single-shot,
     equal-budget Best-of-K, fixed verifier heuristic, and full planner;
  5. promote live `-V/-I/-H` only if earlier evidence justifies the cost;
  6. separate Skill and base-versus-SFT-student studies.
- No schema, reducer, runtime, or supervision policy is changed by the plan.

## Questions

1. Does this ordering and the four-arm live pilot isolate adaptive retry value
   strongly enough, or is a missing baseline/control still blocking the main
   contribution claim?
2. Is the nested `atom-level vs aggregate-only vs no verifier` comparison a
   necessary part of the verifier-grounding claim, and can the planner-only
   screen legitimately decide whether it deserves live evaluation?
3. Before confirmatory execution, which selector/primary-metric decision is
   blocking: GM-only, pass-count/GM lexicographic, or separate named
   best-by-pass and best-by-GM views?

## Explicit non-goals

- No schema, reducer, PlannerContext, action, or SFT implementation.
- No new Teacher, Qwen-Image-Edit, Geneval2, or human-evaluation calls.
- No power/sample-size claim without paired live ablation variance.
- No claim of parity or numerical comparison with Muse Image.

## Expected response

- verdict: `PASS`, `PASS_WITH_REQUIRED_CHANGES`, or `FAIL`;
- only claim-blocking issues and minimum required corrections;
- separate must-run experiments from optional enrichments;
- flag any evaluator circularity, leakage, or statistical-unit error.
