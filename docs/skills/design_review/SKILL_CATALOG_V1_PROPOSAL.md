# Skill Catalog v1 Proposal

Date: 2026-07-15

Status: design proposal only. These Skills are not activated in `skills/`.

## Boundary

Skill v1 answers: how to operationalize a visual constraint in a generation or edit instruction.

Skill v1 does not answer: whether to edit, regenerate, branch from best-so-far, continue, or submit. Those remain retry-policy decisions grounded in current image evidence, Geneval2 atom feedback, canonical attempt history, transition state, best-so-far, strategy history, and remaining budget.

## Proposed Catalog

Token counts are measured with the local `Qwen3-VL-8B-Instruct` tokenizer using `add_special_tokens=False`.

| Skill ID | Manifest summary | Constraint types covered | Modes | Draft token count | Draft hash |
| --- | --- | --- | --- | ---: | --- |
| `counting_and_instance_layout` | Exact cardinality, instance separation, full visibility, no extras or fused objects. | `count`; object-presence failures only when entangled with instance count/visibility | `generate_image`, `edit_image` | 327 | `4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685e02` |
| `spatial_relation_layout` | Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations. | `position`, `verb` | `generate_image`, `edit_image` | 348 | `154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019` |
| `attribute_entity_binding` | Bind color, material, texture, and identity attributes to the correct entity. | `attribute`; identity/material aspects of `object` when tied to recognizability | `generate_image`, `edit_image` | 339 | `15b693e5fd14a05fdc9c0f6ee23224e7f97c657e8386bfbc65d1b9f62f840b01` |
| `local_edit_preservation` | Narrow edit scope and preserve already-correct visual evidence. | Cross-cutting for all constraint types after `edit_image` is selected | `edit_image` | 347 | `559b9af9b3e40446a11a9fe15d2a9b1d8f84a7a0eb2196306320431045346335` |

GenEvolve's comparable Markdown Skills are longer reference documents: `quantity_counting.md` is 613 local Qwen tokens, `spatial_layout.md` is 739, and `attribute_binding.md` is 570. Skill v1 reuses their operator ideas but compresses them for v3's per-turn `query_skill` context budget and max-two retrieval rule.

## Skill Details

### `counting_and_instance_layout`

- One-sentence purpose: express exact cardinality by making every instance countable, separated, visible, and bounded.
- Actual constraint types covered: `count`; sometimes `object` when the object is absent because counted instances are fused, cropped, or unrecognizable.
- Supported action modes: `generate_image`, `edit_image`.
- Applicable failure signatures:
  - wrong count observed, such as four/five when six are required;
  - extra or missing instances;
  - merged, cropped, reflected, or background duplicates that confuse counting;
  - count edits that add one object but create extra ambiguous objects.
- Non-applicable conditions:
  - vague quantity with no exact cardinality;
  - single-object existence without count ambiguity;
  - choosing edit versus generation.
- Overlap analysis:
  - Pair with `spatial_relation_layout` when a counted group participates in a relation.
  - Pair with `attribute_entity_binding` when a counted group has material/color constraints.
  - Pair with `local_edit_preservation` only for edits.
- Evidence references:
  - `docs/skills/design_review/FOUNDATIONAL_CAPABILITY_EVIDENCE.md`
  - `docs/phase3/legacy_failure_signature_summary.md`
  - `docs/phase3/hq5_completed_trajectory_behavior_analysis.md`
  - GenEvolve `genevolve/knowledge/skills/quantity_counting.md`
- Useful retrieval pairings:
  - `counting_and_instance_layout` + `spatial_relation_layout`
  - `counting_and_instance_layout` + `attribute_entity_binding`
  - `counting_and_instance_layout` + `local_edit_preservation`

### `spatial_relation_layout`

- One-sentence purpose: express relations with subject/object anchors, frame regions, depth, orientation, and visible relation cues.
- Actual constraint types covered: `position`, `verb`.
- Supported action modes: `generate_image`, `edit_image`.
- Applicable failure signatures:
  - behind/front/right-of relation is side-by-side, occluded, or ambiguous;
  - verbs such as chasing, facing, following, playing with, or jumping over are rendered as static co-presence;
  - relation fixes regress because count or attribute cues were changed without relation preservation.
- Non-applicable conditions:
  - pure attribute or count issue without relation ambiguity;
  - choosing source attempt, action type, or stop/continue behavior.
- Overlap analysis:
  - Does not own exact cardinality or attribute binding.
  - Provides relation cues that can be combined with count/attribute wording.
- Evidence references:
  - `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md`
  - `docs/skills/design_review/FOUNDATIONAL_CAPABILITY_EVIDENCE.md`
  - GenEvolve `genevolve/knowledge/skills/spatial_layout.md`
- Useful retrieval pairings:
  - `spatial_relation_layout` + `counting_and_instance_layout`
  - `spatial_relation_layout` + `attribute_entity_binding`
  - `spatial_relation_layout` + `local_edit_preservation`

### `attribute_entity_binding`

- One-sentence purpose: attach attributes to the right object by using self-contained entity clauses, spatial anchors, and visual material evidence.
- Actual constraint types covered: `attribute`; limited `object` support when recognizability depends on material/identity cues.
- Supported action modes: `generate_image`, `edit_image`.
- Applicable failure signatures:
  - target entity lacks required color or material;
  - material/color leaks to the wrong object;
  - global adjective lists make the binding ambiguous;
  - material is named but not visibly evidenced.
- Non-applicable conditions:
  - pure count/position failure with all attributes passing;
  - attributes not present in the task or observation;
  - deciding how severe an attribute failure is.
- Overlap analysis:
  - Complements counting when a counted group is attributed.
  - Complements spatial relation when anchors distinguish entities.
  - Does not own preservation mechanics beyond attribute stability.
- Evidence references:
  - `docs/phase3/legacy_failure_signature_summary.md`
  - `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md`
  - GenEvolve `genevolve/knowledge/skills/attribute_binding.md`
- Useful retrieval pairings:
  - `attribute_entity_binding` + `counting_and_instance_layout`
  - `attribute_entity_binding` + `spatial_relation_layout`
  - `attribute_entity_binding` + `local_edit_preservation`

### `local_edit_preservation`

- One-sentence purpose: write minimal edit instructions that repair named failed evidence while preserving already-correct content.
- Actual constraint types covered: cross-cutting for `count`, `attribute`, `object`, `position`, and `verb` after `edit_image` is already selected.
- Supported action modes: `edit_image`.
- Applicable failure signatures:
  - previous edit fixed a target but regressed a stable atom;
  - broad edit changed unrelated objects or counts;
  - target repair should affect one object/region while preserving the rest of the scene.
- Non-applicable conditions:
  - fresh `generate_image`;
  - no source attempt exists;
  - deciding whether edit is the right action.
- Overlap analysis:
  - Does not define count, attribute, or relation operators.
  - Wraps those operators in narrow edit scope and preservation clauses when editing.
- Evidence references:
  - `docs/phase3/behavior_coverage_report.md`
  - `docs/phase4/sft_supervision_freeze.md`
  - `artifacts/phase3/action_supervision_labels.jsonl`
- Useful retrieval pairings:
  - `local_edit_preservation` + one of the three visual capability Skills;
  - at most one additional visual Skill if target atoms span two capability types.

## Catalog Minimality Decision

Keep exactly four Skills for v1.

- Splitting counting from spatial relation is justified because count failures and relation failures have different operators and failure signatures.
- Splitting attribute binding is justified by frequent legacy `attribute` failures and material/color leakage risk.
- Keeping local edit preservation separate is justified by pervasive regression evidence and by the need to express edit scope after the retry policy has already selected `edit_image`.
- A standalone `object_presence` Skill is not justified yet. Object failures in the evidence are mostly coupled to count, attribute binding, image quality, or broad edit regression.
- A `retry_action_selection` Skill is explicitly rejected because it would encode policy decisions into static Markdown.

## Activation Gap After Approval

The active runtime currently exposes older IDs in `DEFAULT_SKILL_MANIFEST` and reads `skills/<skill_id>/SKILL.md`. After user approval, activation will require:

- adding the four approved `skills/<skill_id>/SKILL.md` files;
- replacing or versioning the current placeholder active Skills;
- updating `DEFAULT_SKILL_MANIFEST` to expose the four v1 IDs and summaries;
- adding retrieval-policy validation tests for max-two retrieval, no duplicate version by default, and no consecutive query-only loop.
