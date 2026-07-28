# Skill: counting_and_instance_layout

## Description
Construct generation or local edit instructions for exact counts by diagnosing and repairing missing, extra, fused, hidden, cropped, or ambiguous instances.

## Instructions

### Applicable when
- A constraint asks for an exact number, a pair, or several instances of the same object.
- An edit must add, remove, separate, or clarify instances after `edit_image` is already selected.

### Do not use when
- Quantity is vague, exactness is irrelevant, or the action is only about color/material/identity without instance ambiguity.
- To decide whether to edit, regenerate, branch, continue, or submit.

### Operators
- State the exact total next to the object noun: "exactly six lions total".
- Classify the observed count failure as missing, extra, fused, hidden, cropped, or ambiguous before writing the operation.
- Use a bounded formation: row, arc, triangle, grid, or two rows of three.
- Require full visibility and gaps; avoid piles, cropped bodies, merged bodies, and countable reflections.
- For edits, anchor the group to a region and name the smallest operation: add, remove, separate, uncrop, or clarify.
- Add only the missing number or remove only the excess instances.

### Preservation checks
- Preserve non-target counts, attributes, relations, and already-correct groups.
- Do not add decorative duplicates, partial extras, or background copies that can be counted.

### Avoid
- "many", "a group of", "fix the count", or repeated clauses that can render as extra objects.

### Minimal instruction pattern
Generation: "Show exactly <N> <object> total in <formation/region>, each fully visible and separated. Do not include extra, cropped, fused, reflected, or background <object>."

Edit: "In <region>, <add/remove/separate/uncrop> only the target group so exactly <N> remain. Preserve correct instances and <non-target constraints>."
