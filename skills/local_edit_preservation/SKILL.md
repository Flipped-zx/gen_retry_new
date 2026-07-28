# Skill: local_edit_preservation

## Description
Construct narrow edit instructions with explicit target operation, spatial anchor, preservation lock, and forbidden changes.

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
- Anchor the operation to a visible region or entity.
- Translate preserve constraint IDs into visible counts, colors/materials, identities, layout, and relation cues.
- End with forbidden changes, including full-scene redraw, unrelated style changes, or new copies.

### Preservation checks
- Non-target objects remain the same type and count.
- Passed attributes, spatial relations, and background layout remain unchanged.
- Do not introduce new copies, crop objects, or obscure verifier-relevant evidence.

### Avoid
- "Fix the image", "improve the scene", or broad restyling.
- Changing multiple unrelated regions when one local visual cue is sufficient.

### Minimal instruction pattern
"Target operation: <smallest change>. Spatial anchor: <object/region>. Preservation lock: keep <stable objects/counts/attributes/relations/layout> unchanged. Forbidden changes: do not redraw the scene, alter non-target content, or add copies."
