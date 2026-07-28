# Skill: spatial_relation_layout

## Description
Construct generation or edit instructions for static spatial relations using frame anchors, depth, support, containment, occlusion, and visibility cues.

## Instructions

### Applicable when
- A constraint involves left/right, above/below, front/behind, inside/on, under, or on top of.
- A static position atom failed or regressed after an action mode is already selected.

### Do not use when
- The prompt only asks for attributes, style, or exact count without a static spatial relation.
- The failed atom is a verb such as chasing, playing with, or jumping over; use `action_pose_relation`.
- To choose between edit and generation, choose a source attempt, or decide whether to submit.

### Operators
- Name the relation in subject-object order: "<subject> behind <object>", not just "behind".
- Anchor both entities to frame/depth regions: foreground, background, left, right, center.
- For behind/in front, state depth and non-blocking occlusion.
- For left/right, use viewer-frame wording.
- For above/below, state vertical separation and contact/gap.
- For inside/on, state containment or support contact.

### Preservation checks
- Keep both entities visible.
- Preserve correct counts and attributes.

### Avoid
- Ambiguous words like "near", "around", "with", or "interacting" without concrete visual evidence.
- Contradictory relations or hiding either endpoint.

### Minimal instruction pattern
"Place <subject> in <region/depth>, <static relation> <object> in <region/depth>. Keep both visible and show the relation with separation, support, containment, or occlusion cues. Preserve <non-target constraints>."
