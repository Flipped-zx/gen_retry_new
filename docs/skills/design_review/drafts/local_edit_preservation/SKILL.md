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
