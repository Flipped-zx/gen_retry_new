# Geneval2 Missing Skill Content Proposal

Reviewer: GPT-5.6 Sol

Date: 2026-07-26

Scope: accepted content basis. The v0.5 implementation materializes this
proposal under `skills/*/SKILL.md`; utility validation remains separate.

## Verdict

`IMPLEMENTED` for content coverage; `REQUEST_CHANGES` remains for Skill utility
and `query_skill` SFT targetability.

The current skill system is structurally clear, but hard Geneval2 retry still lacks capability coverage for action relations, count editing, preservation, and object identity.

## Priority

1. P0: upgrade `counting_and_instance_layout` to v2 and absorb `counting_edit`.
2. P0: upgrade `local_edit_preservation` to v2 and absorb `constraint_preservation`.
3. P0: add `action_pose_relation` and remove verb handling from `spatial_relation_layout`.
4. P1: add `object_identity_presence`.
5. Keep `attribute_entity_binding`; validate it instead of adding an overlapping attribute skill.

## 1. `counting_and_instance_layout` v2

Purpose: cover both fresh count layout and local count repair.

Trigger when:

- exact count is failed or uncertain;
- an edit action has already been selected and must add, remove, separate, uncrop, or clarify instances.

Do not trigger when:

- deciding whether to edit or regenerate;
- the issue is pure object identity replacement;
- there is no exact quantity requirement.

Operators:

- First classify the count problem: missing, extra, fused, hidden, cropped, or ambiguous.
- Anchor the target group in a bounded region.
- Add only the missing number or remove only the extra instances.
- Preserve already-correct instances and non-target facts.
- Forbid reflected, background, cropped, fused, or decorative copies.

Generation pattern:

```text
Show exactly <N> <object> total in <bounded formation>, fully visible with gaps; no extra, fused, cropped, reflected, or background copies.
```

Edit pattern:

```text
In <region>, <add/remove/separate/uncrop> only the target group so exactly <N> remain; keep correct instances and <preserved facts> unchanged.
```

## 2. `local_edit_preservation` v2

Purpose: make every edit instruction use a stable four-part structure:

```text
target operation
spatial anchor
preservation lock
forbidden changes
```

Trigger when:

- `edit_image` has already been selected;
- a source attempt exists;
- passed atoms must be preserved while repairing target atoms.

Do not trigger when:

- generating from scratch;
- no source attempt exists;
- deciding source, branch, stop, or submit;
- the whole scene is too broken for local edit.

Operators:

- Check target and preserve sets do not conflict.
- Translate constraint IDs into visible facts.
- Preserve non-target category, count, attribute, relation, and layout.
- Forbid full-scene redraws, unrelated style changes, and new copies.

Edit pattern:

```text
Make one localized edit in <region>: <operation>. Keep <stable entities/counts/attributes/relations/layout> unchanged. Do not redraw the scene, alter non-target content, or add copies.
```

## 3. `action_pose_relation` v1

Purpose: make verb atoms visually testable. This should cover `chasing`, `playing with`, and `jumping over`, instead of treating them as generic spatial layout.

Trigger when:

- a verb atom failed or is uncertain;
- the prompt requires a visible action relation.

Do not trigger when:

- the relation is only static left/right/front/behind/under/on-top;
- entities only need to co-exist.

Operators:

- For `chasing`: same motion direction, chaser behind and facing target, target ahead/escaping, visible pursuit spacing.
- For `playing with`: facing or converging subjects, shared toy/contact/focal point, relaxed interactive posture.
- For `jumping over`: subject airborne, clear vertical gap, object underneath as obstacle, landing/motion cue.
- Always keep both subject and object visible and identifiable.
- Do not merely say the verb; describe the visual evidence that makes the VQA answer yes.

Generation pattern:

```text
Show <subject> <verb> <object>: <relation-specific pose/orientation/contact cues>; keep both identities and full bodies visible, not merely adjacent.
```

Edit pattern:

```text
Adjust only <subject/object pose or placement> to make <verb> explicit through <cues>; preserve counts, identities, attributes, and required static relations.
```

Design note:

Remove verb-trigger responsibility from `spatial_relation_layout`. That skill should handle static spatial relations only.

## 4. `object_identity_presence` v1

Purpose: repair missing objects, wrong object categories, category substitutions, and unrecognizable silhouettes.

Trigger when:

- an object atom is not pass;
- the problem is not simply count, attribute, or relation.

Do not trigger when:

- the object category is clear but count, color, material, or relation is wrong.

Operators:

- Name category-defining silhouette and parts.
- Keep the target fully visible.
- Replace or clarify only the wrong/missing anchored target.
- Exclude similar-category substitutions.
- Avoid adding distracting copies that would break count atoms.

Generation pattern:

```text
Show a clearly recognizable <object> with <defining parts/silhouette>, fully visible; do not substitute a related category or add distracting copies.
```

Edit pattern:

```text
Replace or clarify only <anchored target> as a recognizable <object>; preserve its count/attribute/relation and all non-target entities.
```

## Foundational vs Experience

Foundational capability skills:

- `counting_and_instance_layout` v2
- `local_edit_preservation` v2
- `action_pose_relation` v1
- `object_identity_presence` v1
- existing `attribute_entity_binding`
- existing static `spatial_relation_layout`

Future experience skills should wait for multi-episode transition evidence:

- high-count formation success rates;
- specific confusing object pairs;
- relation-specific Qwen success/failure rates;
- Qwen-Image-Edit failure signatures;
- when to regenerate vs edit;
- when to branch from latest vs best;
- when to stop and submit.

## `query_skill` SFT Target Condition

Keep `query_skill` loss 0 for now.

A `query_skill` action can become a positive SFT target only if all conditions hold:

1. the queried skill matches current failed or uncertain atoms;
2. it is not a duplicate query of already-active guidance;
3. returned content has version/hash provenance;
4. the immediately following generate/edit action visibly uses at least one unique operator from that skill;
5. at least one corresponding target atom changes from fail/uncertain to pass;
6. preserve atoms do not regress;
7. no future outcome leaks into the query action target.

Each new skill family needs at least one capability-isolated successful trajectory before retrieval is supervised as positive behavior.

## Placeholder Handling

Recommended deletion or consolidation:

| Placeholder | Recommendation |
|---|---|
| `attribute_binding` | delete; replaced by `attribute_entity_binding` |
| `counting_layout` | delete; replaced by `counting_and_instance_layout` |
| `spatial_relation` | delete; replaced by `spatial_relation_layout` |
| `counting_edit` | merge into `counting_and_instance_layout` v2 |
| `constraint_preservation` | merge into `local_edit_preservation` v2 |

Do not rename existing valid skill IDs unless there is a migration plan, because historical events store skill IDs, versions, and hashes.
