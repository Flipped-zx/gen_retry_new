# Related-Work Evidence Map For Gen-Retry

## Purpose

This is the consolidated map between external agentic-generation work and the
current Gen-Retry system. It distinguishes three questions that were
previously scattered across source, prompt, Skill, and operations documents:

1. What has already been adapted into Gen-Retry?
2. What is intentionally not reused because it changes the research problem?
3. What new evidence should change experiments, without silently changing the
   frozen protocol?

External papers and repositories are evidence. Versioned schemas and accepted
ADRs remain the protocol source of truth.

## Current Coverage

| Source | Grounded use already present | Explicit boundary |
| --- | --- | --- |
| Gen-Searcher | Assistant actions versus tool observations; observation masking; artifact paths instead of persisted base64; cache/provenance patterns; heavy image execution after agent rollout | Web/image search and OOD grounding are outside the current retry problem; rollout retry creates a new application rather than canonical resume, and saved results lack v3 content-addressed replay provenance |
| GenEvolve | Real `query_skill -> tool response`; one-action-per-turn formatting; stable image IDs; assistant-only SFT masking; 40-step, 1024-class Qwen rendering evidence | Its final output is a prompt-reference program followed by one render, not edit/regenerate retry with verifier feedback and rollback; only evaluation has true skip-completed resume |
| Geneval2 | Atom-level immutable constraints, per-atom observations, Soft-TIFA scoring, held-out benchmark discipline | The evaluator does not choose planner actions or write memory |
| GEMS | Atomic binary criteria and verifier vectors; historical-best selection; image/feedback/experience memory; always-visible Skill manifests with detailed instructions loaded on demand | Its memory can contain raw reasoning and uses an LLM compressor; it has no v3 event replay, edit lineage, environment-fact ownership, or action-only recovery export contract |
| Generation Navigator | Direct same-problem evidence for state-conditioned generate/edit/stop decisions, historical-best delivery, regression-aware trajectory objectives, and turn efficiency | Its scalar reviewer, current-image-only refinement, monotonic SFT filtering, and PRE-GRPO reward are not adopted as Gen-Retry protocol facts |

The practical conclusion is that Gen-Searcher and GenEvolve have been used
substantially, but their influence is mostly infrastructural. Generation
Navigator is the first local paper in this corpus that closely matches the
central sequential decision question.

This also narrows defensible novelty wording. Gen-Retry should not claim to be
the first state-aware image agent, the first learned edit-versus-regenerate
router, the first system to retain a trajectory peak, or the first to penalize
regressive/inefficient image trajectories. GEMS also prevents treating
verifier vectors, historical best, compressed experience, or on-demand Skills
alone as new. Gen-Retry's stronger contribution
candidates are verifier-atomic state, immutable canonical history, arbitrary
historical-source recovery, strict action/environment ownership, real Skill
tool interactions, and harmful-history/recovery supervision.

## Generation Navigator: Exact Comparison

Paper evidence is from arXiv `2605.17969v1`.

| Dimension | Generation Navigator | Current Gen-Retry | Interpretation |
| --- | --- | --- | --- |
| Planner action | `STOP`, `REFINE`, `REGENERATE` plus revised prompt | `query_skill`, `generate_image`, `edit_image`, `submit_attempt` plus executable instruction | The three execution/termination choices are nearly isomorphic; Gen-Retry additionally models real Skill retrieval |
| State | Original prompt plus accumulated selected-path actions, images, and scalar/text reviewer feedback | Task constraints, visible images, atom feedback, canonical round memory, best/latest/historical evidence, lineage, and budget | Strong support for state-conditioned action making; Gen-Retry makes ownership and replay more explicit |
| Edit source | Current image | Any valid historical `source_attempt_id` | Historical branching and rollback are a substantive Gen-Retry distinction |
| Final output | Automatically return the reviewer-score maximum over the trajectory | Planner explicitly submits any historical Attempt; reducer exposes environment-owned best-so-far | Both preserve earlier peaks, but Gen-Retry makes selection an auditable action |
| Evaluator | External reviewer with scalar score `0.3 visual + 0.7 instruction` and diagnosis | Geneval2 atom observations plus prompt-level GM | Gen-Retry has more localized repair evidence; neither evaluator is a substitute for human calibration |
| SFT data | Branch-and-select exploration; keep only score-above-threshold, strictly monotonic trajectories | Preserve harmful/regressive actions in history, mask them as positive targets by default, and supervise productive recovery | The paper does not prove learning recovery from non-monotonic histories; this remains a Gen-Retry contribution candidate |
| Optimization | SFT followed by PRE-GRPO using Peak, terminal Retention, turn Efficiency, and format reward | Current work freezes action-only SFT and deterministic best/history semantics; no PRE-GRPO protocol adoption | PRE-GRPO is a future objective/ablation reference, not authority to modify current score or supervision semantics |
| Execution | One generator supports T2I and I2I; three-turn default | Environment-owned dual Qwen execution profile with explicit source provenance and configurable budget | Same logical action distinction, different backend/provenance contract |
| Persistence | Paper describes full trajectories but not immutable event replay | Immutable events plus deterministic reducers | Event-sourced reproducibility remains a local architectural contribution |

### What The Paper Grounds

- Section 3.1 directly supports treating image generation as a
  state-conditioned action problem rather than fixed prompt rewriting.
- Sections 3.1 and Appendix G support retaining and returning the best
  historical image instead of assuming the latest is best.
- Section 3.2.3 and Appendix E support measuring peak discovery, post-peak
  regression, and turn efficiency separately.
- Appendix B shows neither edit-only nor regenerate-only dominates and uses a
  per-turn two-branch preference reference.
- Appendix F includes Best-of-3 and prompt-enhanced Best-of-3 controls, which
  strengthens the requirement for equal-image-call comparisons.
- Appendix L reports only about 70.3% reviewer/human agreement on decisive
  comparisons, reinforcing the need to calibrate verifier-derived claims.

### What The Paper Does Not Ground

- It does not establish that raw full chat history is a safe persistent-memory
  format.
- It does not test editing an arbitrary earlier branch after a later
  regression; `REFINE` operates on the current image.
- Its 103K SFT set discards plateauing and regressive branches, so it does not
  establish recovery supervision from harmful history.
- It does not justify replacing atom-first best selection with its scalar
  reviewer or changing Gen-Retry's accepted execution profile.
- The v1 preprint exposes no public code repository in the supplied PDF;
  implementation claims are paper-grounded, not independently reproduced.

## Concrete Experiment Implications

The paper changes the priority of experiments, not the current protocol:

1. Complete a provenance-matched, equal-image-call comparison among one-shot,
   independent Best-of-K, fixed edit/regenerate routing, and the adaptive
   planner. Report image calls and total compute separately.
2. Add trajectory metrics for peak discovery, submitted-to-peak retention,
   post-peak regressions, no-progress turns, and attempts-to-peak. Existing
   canonical events can derive these without a schema change.
3. Report the value of historical-source branching separately from merely
   selecting the historical best at the end.
4. Calibrate Geneval2/verifier pairwise preferences against a bounded blind
   human sample before making quality claims beyond benchmark atom fidelity.
5. Consider a PRE-style RL objective only after the v9 SFT supervision freeze,
   under a separate design/ADR and reviewer gate. Do not reuse the paper's
   scalar reward unchanged.

## Reference Placement Policy

- Keep source PDFs and web snapshots under `references/`; keep extracted
  conclusions under `docs/research/`; keep exact evidence in
  `docs/SOURCE_LEDGER.md`.
- Keep parent source repositories and the shared parent paper corpus read-only.
  Do not move or edit sibling Gen-Retry versions.
- Reserve `paper/` for the Gen-Retry manuscript and its owned assets. External
  papers always stay under `references/`.
