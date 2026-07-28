# Skill: action_pose_relation

## Description
Construct generation or edit instructions that make verb relations visually testable through pose, orientation, contact, spacing, and motion evidence.

## Instructions

### Applicable when
- A `verb` atom such as chasing, playing with, or jumping over failed or is uncertain.
- The image contains the required entities but does not visibly prove their action relation.

### Do not use when
- The relation is only static left/right/front/behind/under/on-top.
- The failure is only count, attribute, or object identity.
- To choose generate versus edit, select a source attempt, or decide whether to submit.

### Operators
- Chasing: place the chaser behind and facing the target, align motion direction, put the target ahead or escaping, and leave visible pursuit spacing.
- Playing with: face or converge the subjects around a shared toy, contact point, or focal point with an interactive posture.
- Jumping over: show the subject airborne with a clear vertical gap, the object underneath as an obstacle, and a takeoff or landing cue.
- Keep both action endpoints fully visible and recognizable.
- Describe verifier-visible evidence instead of merely repeating the verb.

### Preservation checks
- Preserve required counts, identities, attributes, and static relations.
- Avoid pose changes that hide, fuse, crop, or duplicate either endpoint.

### Minimal instruction pattern
Generation: "Show <subject> <verb> <object> through <pose/orientation/contact/motion cues>; keep both identities and full bodies visible."

Edit: "Adjust only <subject/object pose or placement> to make <verb> explicit through <cues>; preserve counts, identities, attributes, and required static relations."
