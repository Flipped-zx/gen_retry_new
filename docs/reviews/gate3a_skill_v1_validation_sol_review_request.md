# SOL_REVIEW_REQUEST

## Gate

`Skill-v1 Validation`

## Decision to review

Decide whether the completed Skill-v1 validation trajectory meets the intended GenSearcher/GenEvolve-like standard for a clear, tool-grounded, Skill-conditioned retry trajectory, and whether it is enough to proceed with Skill-v1 as an accepted interaction design.

## Current evidence

- Relevant design:
  - `docs/skills/design_review/USER_CONFIRMATION_PACKET.md`
  - `docs/skills/design_review/SKILL_FORMAT_AND_RETRIEVAL_POLICY.md`
  - `docs/skills/validation/SKILL_V1_VALIDATION_ANALYSIS.md`
- Completed trajectory:
  - `runs/skill_v1_validation_policyfix/phase3_ep_001`
  - trace: `docs/skills/validation/trajectory_trace_skill_v1_policyfix_ep_001.md`
  - behavior reports: `docs/skills/validation/behavior_coverage_report.md`, `docs/skills/validation/sft_candidate_action_report.md`
- Minimal test/live summary:
  - `pytest tests/unit/test_skill_v1_runtime_policy.py tests/contract/test_action_protocol.py tests/contract/test_event_schema.py -q` passed, 42 tests
  - one live GPT-5.5 + local Qwen-Image-Edit + Geneval2 trajectory completed with 5 attempts and 5 evaluator reports
  - final submission selected historical best `a_000` under budget exhaustion
- Conflicting evidence:
  - The Skill interaction is real and the generated instructions use Skill operators, but no edit fixed the persistent count/spatial relation failures.
  - The teacher repeatedly re-queried the same two Skills after new evaluator observations; this is allowed by the revised policy but may be too repetitive.
  - Generic Phase 3 analyzer labels `query_skill` as trainable-positive, but current SFT policy keeps `query_skill` context-only until Skill-v1 utility is accepted.

## Questions

1. Does this completed trajectory satisfy the required interaction standard: explicit `query_skill -> SKILL.md tool response -> next action uses Skill content`, with a clear GenSearcher/GenEvolve-style readable trace?
2. Is one trajectory with structurally correct but outcome-ineffective Skill-conditioned edits enough to accept the Skill-v1 interaction design, or should validation require 1-2 more trajectories with at least one materially helpful Skill-conditioned transition?
3. Should `query_skill` remain context-only for SFT after this evidence, or can any `query_skill` actions from this validation be considered positive targets?

## Explicit non-goals

- Do not review image aesthetic quality except where it affects evaluator-grounded behavior.
- Do not propose code implementation changes beyond blocking design/runtime issues.
- Do not revisit the full Phase 3 or Phase 4 gates.
- Do not require a persistent Qwen worker implementation for this review; this validation used the current local adapter.

## Expected response

- blocking issues only;
- recommended decision;
- risks and one minimal validation experiment;
- no code implementation.
