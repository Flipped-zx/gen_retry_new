# Gate 3a Skill-v1 Validation Sol Review

Date: 2026-07-15

Verdict: `REQUEST_CHANGES`

## 1. Interaction Standard

Sol accepts the interaction mechanics.

The completed trajectory shows explicit `query_skill`, a tool observation containing complete `SKILL.md` content with version/hash, and an immediately following action that cites and applies concrete Skill operators. The readable trace is sufficiently clear and grounded:

- `docs/skills/validation/trajectory_trace_skill_v1_policyfix_ep_001.md`
- `runs/skill_v1_validation_policyfix/phase3_ep_001/tool_observations.jsonl`

Repeated re-querying was repetitive but protocol-legal because each query followed a new evaluator observation.

## 2. Acceptance Decision

Sol does not accept Skill-v1 utility yet.

Reasons:

- every Skill-conditioned edit produced zero fixed constraints;
- one edit regressed `c_002`;
- the original failures `c_004`, `c_005`, and `c_008` persisted through budget exhaustion;
- only `counting_and_instance_layout` and `spatial_relation_layout` were retrieved;
- `attribute_entity_binding` and `local_edit_preservation` remain unvalidated.

The retrieval plumbing and trace format are accepted, but Skill-v1 should not yet be treated as an accepted utility design.

## 3. SFT Decision

`query_skill` must remain context-only.

None of the four `query_skill` actions from this validation qualifies as a positive SFT target. The generic Phase 3 analyzer labels query actions positive when a `skill_returned` event exists, but that is not enough for Skill-v1: relevance, actual use, and material help must all be demonstrated before targeting retrieval behavior.

## 4. Minimal Follow-Up Experiment

Run one fresh, capability-isolated episode with at most three attempts, targeting an attribute/local-preservation failure.

Acceptance criteria:

- `query_skill(attribute_entity_binding, local_edit_preservation)` followed by an immediate edit;
- the edit instruction concretely uses both Skills;
- at least one targeted `fail` or `uncertain` atom becomes `pass`;
- no preserved atom regresses.

One such diagnostic trajectory is sufficient. A run without an applicable failure or helpful transition does not satisfy acceptance.
