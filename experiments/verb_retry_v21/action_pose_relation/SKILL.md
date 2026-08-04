# Skill: action_pose_relation

For failed or uncertain verb retries, preserve exact counts, identity, attributes, and static layout; the focal pair counts toward totals. Chasing uses one lateral pursuer/target pair. Playing uses reciprocal cross-role interaction. Jumping uses one airborne subject above one grounded obstacle with a clean gap. One scene; each required instance appears once; no panels.

## Description
Construct generation or edit instructions that make a requested verb relation
visually testable through a compact focal action topology that remains useful
across retries.

## Instructions

### Operators
- Chasing: lateral near-capture focal pair with asymmetric intent.
- Playing with: cross-role pair uses reciprocal gaze, reach, and contact.
- Jumping over: airborne subject crosses one grounded obstacle.
- Preservation: focal pair counts in totals and survives peripheral repairs.
- Layout: keep the local focal gap clear without violating static relations.

### Applicable when
- A verb atom failed or is uncertain and the next instruction needs a
  different composition rather than another synonymous motion-cue rewrite.
- A historical source already passes the verb and a local non-verb repair must
  preserve its action evidence.

### Do not use when
- The task has no verb relation.
- The relation is only static left/right/front/behind/under/on-top.
- The failure is only count, attribute, or object identity and the selected
  source has no verb evidence at risk.
- To choose generate versus edit, select a source attempt, override the
  reducer, or decide whether to submit.

### Shared focal topology
- Build one decisive cross-role focal pair. The focal instances are included
  in the requested totals; never add an extra demonstration pair.
- Give the pair a locally clear action corridor: a small non-contact gap for
  chasing, a clean vertical non-contact gap for jumping, or gentle cross-role
  contact for playing. Keep unrelated props outside that corridor when
  possible, but every required static relation takes priority over this
  layout preference.
- Continue remaining instances as separated, countable supporting
  participants. Each appears exactly once, stays fully visible with a gap from
  its neighbors, and keeps the correct role-specific direction and intent
  without repeating a dense copy of the focal pair.
- Use one continuous scene. Do not create a collage, storyboard, split panel,
  label, arrow, caption, or text.

### Chasing operator
- State the asymmetric roles once: `<subject>` are the pursuers and `<object>`
  are the fleeing targets; never reverse or intermix the roles.
- Use a lateral or three-quarter lateral action lane. Put one lead pursuer a
  small non-contact gap trailing one lead target along the direction of
  travel, not behind it in camera depth.
- Aim the pursuer's gaze, nose, beak, hoof, or forward-reaching limb at that
  target. Make the target move away and look back in alarm.
- Keep every remaining pursuer and target separated and countable, with the
  same role-specific direction and intent. Do not force them into dense rows.
- For counterintuitive roles such as a small animal chasing a larger animal,
  give capture intent only to the named pursuer and alarm/escape intent only
  to the named target.
- Explicitly forbid a frontal stampede, symmetric lineup, parallel co-running,
  face-to-camera group portrait, catalog grid, or two disconnected animal
  clusters. Generic dust or blur alone is not chase evidence.
- Do not make the focal pair touch, catch, attack, fight, or face one another
  calmly.

### Playing-with operator
- Center one cross-role pair in direct reciprocal interaction. Use reciprocal
  gaze plus an unmistakable gentle reach or playful contact between one
  `<subject>` and one `<object>`.
- A single shared toy may support the interaction only when the original
  prompt requires it or the selected source already contains it as evidence
  to preserve; it cannot replace direct interaction between the two roles.
- Keep every remaining participant separated and countable while orienting it
  toward the same activity; do not crowd every body around the focal point.
- Use reciprocal gaze and relaxed, interactive poses. Avoid parallel posing,
  unrelated activity, or fighting.

### Jumping-over operator
- Freeze one focal `<subject>` at the decisive airborne crossing directly
  above one grounded `<object>`.
- Leave a clean vertical air gap between the jumper's feet/body and the
  obstacle. Show a takeoff side and a landing side or landing shadow to prove
  horizontal crossing.
- Keep the obstacle grounded and fully visible. Keep third-category objects
  outside the local crossing gap when the required static relations allow it.
- Show every required subject exactly once. Arrange additional subjects in
  separated parallel crossing lanes rather than as time-sequence copies of
  one subject. Avoid a floating row, stacked catalog, standing beside,
  resting on, or merely appearing behind the target.

### Verb-pass preservation
- When the selected source already passes the verb, treat its focal pair,
  action corridor, role order, shared contact, or airborne gap as a
  preservation lock.
- Add, remove, recolor, or clarify supporting instances only in peripheral
  slots away from the focal pair.
- Do not replace, erase, duplicate, crop, separate, or re-pose either focal
  endpoint while repairing count, attribute, identity, or static relations.
- Include the passed verb constraint among `preserve_constraint_ids` whenever
  an edit targets only non-verb atoms.

### Minimal instruction patterns
Generation: "In one continuous scene, expand the selected typed operator into explicit pose, orientation, contact, and gap evidence for one focal <subject>/<object> pair. Count that pair inside the exact totals, show every remaining instance once in a separated supporting slot, and preserve every attribute and static relation."

Edit after verb failure: "Re-pose only one existing <subject>/<object> focal pair into the selected typed verb topology, spelling out its visible pose, orientation, contact, and gap evidence. Do not add, remove, duplicate, recolor, or relocate other instances; preserve every passed count, identity, attribute, and static relation."

Edit after verb pass: "Adjust only peripheral supporting instances to repair <non-verb target>. Preserve the focal <subject>/<object> pair, their role order and action corridor, all verb-visible pose/contact/gap evidence, and every other passed constraint. Do not redraw or duplicate either focal endpoint."
