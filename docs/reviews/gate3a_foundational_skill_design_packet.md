# Gate 3A Foundational Skill Design Packet

Date: 2026-07-15

Reviewer scope: read-only high-level review. Do not reopen the canonical event protocol, completed Phase 3 trajectories, Gate 2, Gate 3, the Phase 4 SFT schema, or unrelated runtime modules.

## Decision Brief

Gen-Retry v3 already has a working `query_skill -> LocalSkillStore -> SKILL.md -> tool observation -> later teacher context` mechanism, but active skill content is placeholder. Skill Catalog v1 should replace placeholder content with four concise foundational capabilities that teach how to express visual constraints in generation/edit instructions. The Skills must not choose high-level retry actions.

The evidence supports exactly four Skills: counting/instance layout, spatial/verb relation layout, attribute/entity binding, and local edit preservation. These map to actual Geneval2 constraint types and observed failure signatures from completed trajectories and legacy counterfactual records. A fifth Skill is not justified yet.

## Proposed Four-Skill Catalog

| Skill ID | Purpose | Constraint types | Modes |
| --- | --- | --- | --- |
| `counting_and_instance_layout` | Exact cardinality, visible separated instances, no extras/fusion/cropping. | `count`, limited `object` | `generate_image`, `edit_image` |
| `spatial_relation_layout` | Frame/depth/orientation/occlusion/motion cues for spatial and verb relations. | `position`, `verb` | `generate_image`, `edit_image` |
| `attribute_entity_binding` | Bind color/material/texture/identity attributes to the correct entity. | `attribute`, limited `object` | `generate_image`, `edit_image` |
| `local_edit_preservation` | Narrow edit scope and preserve stable visual evidence. | cross-cutting after `edit_image` | `edit_image` |

## Representative Drafted Skill

```markdown
# Skill: local_edit_preservation

## Description
Construct narrow edit instructions that change only failed visual evidence while preserving already-correct counts, attributes, relations, objects, and composition.

## Instructions

### Applicable when
- The retry policy has already selected `edit_image`.
- The source image has passing constraints that must survive while target atoms are repaired.
- Broad edits risk regressing stable atoms.

### Do not use when
- The action is `generate_image`.
- No source attempt exists.
- To decide whether editing is preferable to regeneration, which source attempt to use, or whether to stop.

### Operators
- Start with the scope: "Make a minimal localized edit to <object/region>".
- Name the target object, group, attribute, or relation.
- State the smallest operation: add/remove one instance, separate merged instances, recolor one entity, adjust pose/orientation, or move one object.
- Preserve stable content in visual terms: counts, colors/materials, identities, layout, and relation cues.
- For high-risk edits, explicitly say "do not redraw the whole scene".

### Preservation checks
- Non-target objects remain the same type and count.
- Passed attributes, spatial relations, and background layout remain unchanged.
- Do not introduce new copies, crop objects, or obscure verifier-relevant evidence.

### Avoid
- "Fix the image", "improve the scene", or broad restyling.
- Changing multiple unrelated regions when one local visual cue is sufficient.

### Minimal instruction pattern
"Make a minimal localized edit to <target>: <specific change>. Preserve <stable objects/counts/attributes/relations/layout>. Do not redraw the whole scene or alter non-target content."
```

## Provenance Summary

- Current v3 repository proves the retrieval mechanism exists but active Markdown content is placeholder.
- Ten completed fresh trajectories show `local_edit_used` and `target_constraint_fixed` in all ten, but also `constraint_regression` and `repeated_ineffective_strategy` in all ten.
- Type-level evidence shows count, verb, position, attribute, and entangled object failures; count and relation are especially persistent.
- Legacy diagnostic records support count, attribute, position, and verb as frequent unresolved signatures, but remain counterfactual only.
- GenEvolve provides grounded Markdown skill examples for count, spatial layout, and attribute binding.
- Gen-Searcher, GenEvolve, local Qwen README, and `docs/operations/qwen_rendering_quality_baseline.md` support 40-step, 1024-class Qwen rendering and persistent loading/service patterns.

## Retrieval Policy

- One `query_skill` may request at most two Skills.
- A single query cannot request the same Skill twice.
- Re-querying the same Skill version later in the episode is allowed only after new image/evaluator observation makes the capability relevant again.
- Consecutive `query_skill`-only loops are forbidden.
- Full Markdown content is returned only after `query_skill`.
- Version and content hash must be logged.
- Skill text is a tool observation and receives no SFT loss.
- `query_skill` remains context-only until fresh evidence shows retrieval was relevant, used, and materially helpful.
- Skill utilization should initially be audited post hoc from `skill_ids_used`, retrieved hashes, instruction text, and Geneval2 transitions; no canonical action schema change is proposed.

## Persistent Worker Recommendation

Immediate recommendation after user approval: implement an in-process long-lived Qwen-Image-Edit worker for the first Skill-v1 validation trajectory. It loads the pipeline once, preserves existing deterministic artifact/cache semantics, and handles both `generate_image` and `edit_image`.

Later-scale recommendation: implement a local persistent service worker for multi-episode batches, one loaded model per GPU/endpoint, with health checks and queueing.

Concurrency policy: enforce one in-flight Qwen invocation per loaded pipeline through a single-consumer queue or lock. Before first validation, check whether persistent Qwen and Geneval2 can co-reside in GPU memory. If co-residency fails, use a separate service/GPU or a verified offload path that keeps Qwen loaded. If they share a GPU and co-residency is viable, use one scheduler-owned GPU lock spanning both Qwen and Geneval2 queues. Cache/manifest completion is recognized only after atomic artifact publication and hash agreement.

## First Validation Trajectory Plan

Use `phase3_ep_001` task spec as a fresh Skill-v1 validation episode:

```text
six glass lions chasing three red cats behind a brown donut
```

It tests counting, attribute binding, spatial/verb relation, local edit preservation, repeated editing, regression, and best-so-far submission. The validation must start from empty history, reuse no old images/states, use accepted Skill v1, use at most five image attempts, and preserve full traceability.

## Corrections After First Sol Review

- Attribute applicability now covers single-entity visible material/texture realization and has separate generation/edit instruction patterns.
- Spatial operators now explicitly include vertical separation, containment, and support contact.
- Draft lengths are measured with the local `Qwen3-VL-8B-Instruct` tokenizer: `327`, `348`, `339`, and `347` tokens.
- Persistent worker design now requires single-flight Qwen invocation, GPU model-residency checks for Qwen/Geneval2 co-use, and atomic artifact publication before cache/manifest completion.
- Final runtime correction removes the Qwen unload/reload fallback and requires either separate hardware/service, verified offload that keeps Qwen loaded, or one scheduler-owned shared-GPU lock across Qwen and Geneval2 queues.

## Questions For Sol

1. Is the Skill Catalog minimal, non-overlapping, and aligned with the actual Geneval2 failure evidence?
2. Is each Skill operational, concise, grounded, and clearly separated from retry-policy decisions?
3. Is the proposed persistent Qwen-Image-Edit worker and concurrency design technically appropriate?

## Expected Verdict Format

Return exactly one verdict: `APPROVE`, `REQUEST_CHANGES`, or `BLOCKED`, followed by concise rationale. If requesting changes, restrict them to the three questions above.
