# User Confirmation Packet: Skill Catalog v1 Foundational Capabilities

Date: 2026-07-15

Status: Skill-v1 activated for validation; one fresh validation trajectory completed.

## Final Sol Verdict

`REQUEST_CHANGES`

Sol approved the four-Skill catalog direction and the corrected Skill drafts, then identified one remaining runtime-design issue: the persistent-worker design must not allow a Qwen unload/reload fallback while also claiming a load-once worker invariant. This packet was updated to resolve that issue by requiring separate hardware/service, verified offload that keeps Qwen loaded, or one scheduler-owned shared-GPU lock across Qwen and Geneval2 queues. The user then approved activating the Skill-v1 catalog for a limited validation run.

## 1. Final Proposed Skill IDs

1. `counting_and_instance_layout`
2. `spatial_relation_layout`
3. `attribute_entity_binding`
4. `local_edit_preservation`

## 2. One-Line Purpose

| Skill ID | Purpose |
| --- | --- |
| `counting_and_instance_layout` | Express exact cardinality with visible, separated, bounded, non-duplicated instances. |
| `spatial_relation_layout` | Express position and verb relations with frame, depth, orientation, contact, and visibility cues. |
| `attribute_entity_binding` | Bind color, material, texture, and identity attributes to the correct entity without leakage. |
| `local_edit_preservation` | Write narrow edit instructions that repair target evidence while preserving already-correct visual facts. |

## 3. Exact Markdown Template

```markdown
# Skill: <Name>

## Description
<one concise paragraph>

## Instructions

### Applicable when
...

### Do not use when
...

### Operators
...

### Preservation checks
...

### Avoid
...

### Minimal instruction pattern
...
```

Draft files:

- `docs/skills/design_review/drafts/counting_and_instance_layout/SKILL.md`
- `docs/skills/design_review/drafts/spatial_relation_layout/SKILL.md`
- `docs/skills/design_review/drafts/attribute_entity_binding/SKILL.md`
- `docs/skills/design_review/drafts/local_edit_preservation/SKILL.md`

## 4. Skill Token Lengths

Measured with the local `Qwen3-VL-8B-Instruct` tokenizer, `add_special_tokens=False`.

| Skill ID | Tokens | SHA-256 |
| --- | ---: | --- |
| `counting_and_instance_layout` | 327 | `4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685e02` |
| `spatial_relation_layout` | 348 | `154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019` |
| `attribute_entity_binding` | 339 | `15b693e5fd14a05fdc9c0f6ee23224e7f97c657e8386bfbc65d1b9f62f840b01` |
| `local_edit_preservation` | 347 | `559b9af9b3e40446a11a9fe15d2a9b1d8f84a7a0eb2196306320431045346335` |

Reference note: comparable GenEvolve Skills are longer, about 570-739 local Qwen tokens. Skill v1 keeps the same operator style but compresses it for v3's per-turn context budget.

## 5. Retrieval Limits

- One `query_skill` may request at most two Skills.
- A single query cannot request the same Skill twice.
- Re-querying the same Skill version later in the episode is allowed only after new image/evaluator observation makes the capability relevant again.
- Consecutive `query_skill`-only loops are forbidden.
- Full Markdown content is returned only after `query_skill`.
- Version and content hash must be logged.
- Skill text is a tool observation and receives no SFT loss.
- `query_skill` remains context-only until fresh action-outcome evidence shows retrieval was relevant, used, and materially helpful.

## 6. Provenance Summary

- Current v3 proves the Markdown retrieval mechanism exists, but active Skill files are placeholders.
- Ten fresh Phase 3 trajectories show both productive fixes and frequent regressions.
- High-quality supplemental trajectories show count and relation atoms remain hard even with 40-step, 1024-class rendering.
- Legacy Gen-Retry records support count, attribute, position, and verb as frequent unresolved signatures, but remain counterfactual only.
- GenEvolve provides useful Markdown Skill operator patterns for counting, spatial layout, and attribute binding.
- Gen-Searcher, GenEvolve, the local Qwen README, and the v3 rendering baseline support persistent Qwen loading and 40-step quality defaults.

## 7. Retry Policy Boundary

High-level retry policy is not encoded in Skills.

Skills may describe how to phrase exact counts, relations, attributes, and local edit preservation after an action mode is selected. Skills may not decide whether to edit, regenerate, branch from best-so-far, continue, or submit.

## 8. Persistent-Worker Recommendation

Recommended:

- immediate validation: one in-process persistent Qwen-Image-Edit worker;
- later scale: local persistent service worker with one loaded model per GPU/endpoint.

Required runtime invariants:

- no Qwen unload/reload fallback inside the load-once worker design;
- separate hardware/service or verified offload must keep the Qwen pipeline loaded;
- one in-flight Qwen invocation per loaded pipeline.

## 9. Geneval2/Qwen Concurrency Policy

- if Qwen and Geneval2 share a GPU, use one scheduler-owned lock spanning both Qwen and Geneval2 queues;
- do not rely only on a Qwen-local lock;
- allow concurrency only on separate hardware/services or after profiling proves no harmful contention;
- recognize image cache/manifest completion only after atomic artifact publication and hash agreement.

## 10. Selected First Validation Trajectory

Use the `phase3_ep_001` task spec as a fresh Skill-v1 validation episode:

```text
six glass lions chasing three red cats behind a brown donut
```

The validation must start from empty history, reuse no old images or attempt states, use the accepted Skill Catalog v1, and preserve full traceability.

## 11. Activated Files

The Skill-v1 files were installed to:

- `skills/counting_and_instance_layout/SKILL.md`
- `skills/spatial_relation_layout/SKILL.md`
- `skills/attribute_entity_binding/SKILL.md`
- `skills/local_edit_preservation/SKILL.md`

Runtime activation also updated:

- the default Skill manifest to expose the four v1 IDs;
- retrieval-policy validation for max-two retrieval, no duplicate Skill in one query, re-query only after a new image/evaluator observation, and no query-only loop;
- keeping `query_skill` context-only until validation evidence supports targetability.

## 12. Validation Run

One fresh Skill-v1 validation trajectory was completed:

- run root: `runs/skill_v1_validation_policyfix`;
- episode: `phase3_ep_001`;
- prompt: `six glass lions chasing three red cats behind a brown donut`;
- result: 5 attempts, 5 Geneval2 evaluations, submitted `a_000` as best available under budget;
- trace: `docs/skills/validation/trajectory_trace_skill_v1_policyfix_ep_001.md`;
- analysis: `docs/skills/validation/SKILL_V1_VALIDATION_ANALYSIS.md`.

No standalone image smoke was run.

## 13. Expected Maximum Image Attempts

First validation trajectory: at most `5` image attempts.

## 14. Unresolved Risks

- The most recent pre-validation Sol verdict was `REQUEST_CHANGES`; a follow-up Sol review is required on the completed validation evidence.
- Persistent-worker runtime is documented but not yet implemented as a load-once worker; the validation runner still uses the current local adapter.
- Skill utility is structurally demonstrated but not outcome-proven: the completed validation trajectory preserves traceability and Skill-conditioned instructions, but the hard count/spatial relation atoms remain failed.
- `query_skill` remains context-only in SFT policy until accepted non-placeholder Skills produce useful action-outcome evidence.
- Count and relation failures may remain hard even with better Skill content.

## 15. Confirmation State

The user has authorized resolving the scoped runtime-design issue and proceeding to one to three Skill-v1 validation trajectories. Any live execution must still avoid standalone image smoke by default, reuse no old images, and preserve full traceability.
