# Current Image-Instruction Audit

Date: 2026-07-15

Run audited: `runs/skill_v1_validation_policyfix/phase3_ep_001`

Prompt: `six glass lions chasing three red cats behind a brown donut`

## Summary

The initial generation instruction is a reasonable prompt rewrite from the original prompt into a count-aware, spatially grounded generation prompt. The edit instructions are less consistent: one is concrete but contains ambiguous depth wording, one is too vague, one is overbroad for a local edit, and the final best-so-far branch is the strongest edit but still does not improve the evaluator result.

The main defect is not that foundational Skills failed structurally. The defect is that edit-instruction construction does not yet enforce four concrete blocks: target operation, spatial grounding, preservation lock, and forbidden changes.

## Instruction Audit

| Turn | Action | Source | Target atoms | Preserve atoms | Classification | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `turn_001` | `generate_image` | fresh | `c_001`-`c_011` | none | `usable_but_risky` | `a_000`, 8/11 pass; persistent failures `c_004`, `c_005`, `c_008` |
| `turn_003` | `edit_image` | `a_000` | `c_004`, `c_005`, `c_008` | `c_001`, `c_002`, `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011` | `contradictory` | `a_001`, 8/11 pass; no fixed atoms; `c_005` becomes uncertain |
| `turn_005` | `edit_image` | `a_001` | `c_004`, `c_005`, `c_008` | `c_001`, `c_002`, `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011` | `too_vague` | `a_002`, 7/11 pass; regressed `c_002` |
| `turn_007` | `edit_image` | `a_002` | `c_002`, `c_004`, `c_005`, `c_008` | `c_001`, `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011` | `overbroad` | `a_003`, 7/11 pass; no fixed atoms |
| `turn_008` | `edit_image` | `a_000` | `c_004`, `c_005`, `c_008` | `c_001`, `c_002`, `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011` | `usable_but_risky` | `a_004`, 8/11 pass; no improvement over best |

## Per-Instruction Findings

### turn_001: initial generation

Instruction quality: `usable_but_risky`

Strengths:

- uses exact counts: six lions, three cats, one donut;
- binds lion material and cat/donut colors;
- uses bounded layout and visibility/separation constraints;
- prohibits extras, cropping, fusion, reflections, and background duplicates;
- includes relation and motion cues.

Risk:

- the phrase `visible above or beside the donut` weakens the `cats behind donut` relation because "beside" can satisfy visibility while undermining depth.

Outcome:

- pass: `c_001`, `c_002`, `c_003`, `c_006`, `c_007`, `c_009`, `c_010`, `c_011`;
- persistent failed: `c_004`, `c_005`, `c_008`.

### turn_003: first edit

Instruction quality: `contradictory`

Strengths:

- exact source attempt: `a_000` / `IMG_000`;
- concrete target operations: remove extra fourth cat, reposition cats, adjust orientation and motion;
- preservation lock names lions, donut, cat color, lion material, and no extra objects.

Defect:

- `cats fleeing forward toward/behind the donut` is ambiguous and directionally contradictory. "Toward" and "behind" need a frame/depth interpretation.

Outcome:

- no fixed atoms;
- no regressed pass atoms;
- `c_005` remains non-pass as `uncertain`;
- `c_004` and `c_008` remain failed.

### turn_005: second edit

Instruction quality: `too_vague`

Defects:

- relies on vague phrases: `modify only the failed parts`, `all already-correct visual evidence`;
- does not specify exact add/remove/reposition operations;
- does not restate stable passed constraints as explicit preservation locks;
- too little spatial grounding for a relation repair.

Outcome:

- regressed `c_002` glass lions;
- `c_004`, `c_005`, and `c_008` remain failed.

### turn_007: third edit

Instruction quality: `overbroad`

Defects:

- targets lion material/count, cat count, cat position, and chasing in one local edit;
- says `latest image` rather than clearly naming the source attempt in the instruction body;
- does not say which instances to add/remove/reposition;
- preservation lock is generic.

Outcome:

- no fixed atoms;
- no recovery of `c_002`;
- persistent failures remain.

### turn_008: best-so-far branch edit

Instruction quality: `usable_but_risky`

Strengths:

- correctly branches from historical best `a_000`;
- explicitly preserves six glass lions, one brown donut, and red cat appearance;
- states remove exactly one cat;
- uses foreground/background depth and partial occlusion.

Risks:

- starts with vague `satisfy the failed constraints`;
- assumes the visual problem is exactly one removable fourth cat;
- chasing evidence remains weaker than count/depth evidence.

Outcome:

- returns to best-equivalent 8/11;
- no improvement over `a_000`;
- final submission correctly selects `a_000`.
