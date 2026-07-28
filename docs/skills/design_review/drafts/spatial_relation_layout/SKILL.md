# Skill: spatial_relation_layout

## Description
Construct generation or edit instructions for spatial or directional relations using anchors, depth, orientation, and visibility cues.

## Instructions

### Applicable when
- A constraint involves left/right, above/below, front/behind, inside/on, facing, chasing, following, or playing with.
- A relation atom failed or regressed after an action mode is already selected.

### Do not use when
- The prompt only asks for attributes, style, or exact count without a spatial or verb relation.
- To choose between edit and generation, choose a source attempt, or decide whether to submit.

### Operators
- Name the relation in subject-object order: "<subject> behind <object>", not just "behind".
- Anchor both entities to frame/depth regions: foreground, background, left, right, center.
- For behind/in front, state depth and non-blocking occlusion.
- For left/right, use viewer-frame wording.
- For above/below, state vertical separation and contact/gap.
- For inside/on, state containment or support contact.
- For chasing/following/facing, state orientation, motion, spacing, and evidence.

### Preservation checks
- Keep both entities visible.
- Preserve correct counts and attributes.

### Avoid
- Ambiguous words like "near", "around", "with", or "interacting" without concrete visual evidence.
- Contradictory relations or hiding either endpoint.

### Minimal instruction pattern
"Place <subject> in <region/depth>, <relation> <object> in <region/depth>. Keep both visible; show the relation with <orientation/motion/occlusion cues>. Preserve <non-target constraints>."
