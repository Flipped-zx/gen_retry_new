# Skill: object_identity_presence

## Description
Construct generation or edit instructions that make required object categories recognizable, present, fully visible, and distinct from related substitutions.

## Instructions

### Applicable when
- An `object` atom failed or is uncertain.
- A required object is missing, substituted by a related category, or too malformed or occluded to identify.

### Do not use when
- The category is already clear and only count, color, material, position, or action relation is wrong.
- To decide generate versus edit, choose a source attempt, or stop.

### Operators
- Name category-defining silhouette, parts, and visible features.
- Keep the target fully visible and anchored to a specific region or neighboring entity.
- Replace or clarify only the wrong or missing target.
- Exclude similar-category substitutions.
- Avoid distracting copies that could break count atoms.

### Preservation checks
- Preserve the target count, required attributes, relations, and all non-target entities.
- Do not add props that resemble the required category.

### Minimal instruction pattern
Generation: "Show a clearly recognizable <object> with <defining parts/silhouette>, fully visible; do not substitute a related category or add distracting copies."

Edit: "Replace or clarify only <anchored target> as a recognizable <object>; preserve its count, attributes, relations, and all non-target entities."
