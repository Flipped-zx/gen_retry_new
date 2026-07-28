# Skill: attribute_entity_binding

## Description
Construct generation or edit instructions that bind color, material, texture, and identity attributes to the correct entity without leakage.

## Instructions

### Applicable when
- A constraint asks whether a specific object is red, green, glass, metal, shiny, sparkling, or otherwise attribute-bound.
- Multiple entities have different attributes, or one entity needs a visibly realized material/texture.

### Do not use when
- The action only concerns count or spatial relation with no attribute ambiguity.
- To decide whether an attribute failure should be repaired by edit or generation.

### Operators
- Describe each entity in a separate self-contained clause: "<attribute> <object> in <anchor>".
- Put the attribute next to the noun; avoid floating adjective lists.
- Add spatial anchors when multiple objects are present.
- For materials, include visible evidence: glass highlights, metal reflections, sparkling glints, matte fur.
- For edits, change only the target entity and preserve other entities' colors/materials.

### Preservation checks
- Preserve identity, count, position, and relation while changing only the target attribute.
- Do not spread the attribute to non-target objects or background props.

### Avoid
- "Make everything more red/metal/glass" when only one entity needs the attribute.
- Combined phrases like "red and green cats and sheep".

### Minimal instruction pattern
Generation: "Show <entity> as <attribute> with <visible evidence>; describe other entities separately."

Edit: "Change only the <target object> to <attribute> with <visible evidence>; preserve <other objects> and do not apply <attribute> to non-target objects."
