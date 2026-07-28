# Image Instruction Contract v1

Date: 2026-07-15

## Principle

Do not add a separate `refine_prompt` action. The image instruction is part of the canonical `generate_image` or `edit_image` action and must be the exact text sent to Qwen-Image-Edit.

## Generation Instruction Contract

A `generation_instruction` must include, when relevant:

1. exact requested entities and counts;
2. entity-specific attributes;
3. explicit spatial layout;
4. relation, orientation, and depth cues;
5. visibility and separation requirements;
6. prohibition of extras, duplicates, fusion, reflection artifacts, and cropped instances;
7. all original constraints that must be satisfied.

## Edit Instruction Contract

An `edit_instruction` must contain four semantic blocks.

### A. Target Operation

- exact object or region to modify;
- exact add/remove/reposition/attribute operation;
- exact final state.

### B. Spatial Grounding

- bounded region or relative position;
- subject/object orientation;
- depth or occlusion requirements when relevant.

### C. Preservation Lock

- source attempt identity;
- stable passed constraints that must remain unchanged;
- preserved entities, counts, materials, colors, relations, background, and composition.

### D. Forbidden Changes

- no extra instances;
- no unrelated object changes;
- no background redraw unless required;
- no broad scene reconstruction under a local edit action.

## Vague Phrase Policy

The following phrases are insufficient alone:

- `fix the failed parts`;
- `preserve all correct evidence`;
- `make the image satisfy the constraints`;
- `adjust as needed`;
- `modify only the failed parts`;
- `all already-correct visual evidence`.

They may appear only after concrete target operations, spatial grounding, preservation locks, and forbidden changes are stated.

## Contradiction Checks

Reject or repair instructions that:

- conflict with the original prompt;
- contain ambiguous direction such as `forward toward/behind` without a clear frame/depth interpretation;
- request incompatible counts;
- preserve and modify the same property without clarification;
- introduce unsupported entities or attributes;
- use a local edit action for broad scene reconstruction.
