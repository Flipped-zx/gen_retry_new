# SOL_REVIEW_REQUEST

## Gate

`SFT Supervision Freeze`

## Decision to review

Whether to implement Planner I/O v0.5 as the next SFT-facing protocol by renaming state/history fields, simplifying generate/edit action arguments, and materializing missing foundational Skill markdown files.

## Current evidence

- Relevant schema/ADR:
  - `schemas/action_protocol_v0_4.schema.json`
  - `schemas/planner_context_v0_4.schema.json`
  - `docs/decisions/ADR-0005-sft-supervision-freeze.md`
  - `docs/phase3/planner_io_v05_field_design_packet.md`
  - `docs/phase3/planner_io_v05_round_memory_walkthrough_phase3_ep001.md`
  - `docs/reviews/planner_io_v05_field_sft_review.md`
  - `docs/skills/geneval2_skill_coverage_review.md`
  - `docs/skills/geneval2_missing_skill_content_proposal_sol.md`
- Minimal test/pilot summary:
  - v0.4 contract/unit/schema/fixture/replay validation previously passed.
  - v0.5 is currently design-only; no v0.5 schemas/runtime/SFT renderer exist yet.
  - Several `skills/*/SKILL.md` files are still TODO placeholders; missing capability content exists only as a proposal document.
- Conflicting evidence, if any:
  - Prior Sol suggested deleting or zero-loss masking `decision_summary` because it may be free-text SFT noise.
  - Main-thread design preference is to keep a short bounded `decision_summary` for generate/edit because Gen-Retry trains planner decisions, not only Qwen instructions.

## Questions

1. Should v0.5 keep bounded `decision_summary` as a trainable generate/edit action field, or remove/mask it to reduce SFT noise?
2. Is the proposed v0.5 PlannerContext naming (`latest_attempt`, `last_completed_image_round`, `prior_image_rounds`, `best_attempt`) sufficiently clear and non-duplicative for SFT?
3. For v0.5, should missing Skills be materialized as upgraded existing SKILL.md files plus two new Skill IDs, while `query_skill` remains loss 0 until utility validation passes?

## Explicit Non-Goals

- Do not review live Qwen rendering quality.
- Do not require new live rollouts.
- Do not add new planner actions beyond `query_skill`, `generate_image`, `edit_image`, `submit_attempt`.
- Do not implement code.

## Expected Response

- PASS/FAIL;
- blocking issues only;
- recommended decision on `decision_summary`;
- minimal validation required before using v0.5 for new rollout/SFT data.
