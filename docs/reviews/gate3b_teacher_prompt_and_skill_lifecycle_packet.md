# Gate 3b Teacher Prompt and Skill Lifecycle Packet

Date: 2026-07-15

## Decision Summary

Freeze Teacher prompt/input, Skill lifecycle, and image-instruction quality checks before the next fresh validation trajectory.

Key decisions:

- foundational Skills provide prompt-construction operators only;
- retry policy remains in the Teacher planner, not in Skill Markdown;
- full Skill Markdown is returned once, then compact active operators remain in PlannerView;
- repeated retrieval of the same Skill ID/version/hash is rejected by default;
- generation/edit instructions must be concrete executable Qwen-Image-Edit inputs;
- edit instructions must satisfy the four-block target/spatial/preservation/forbidden-change contract;
- trace export must show Teacher input, images, Skill context, instruction quality, exact Qwen input, verifier output, and memory transition.

Scoped correction after initial Sol review:

- instruction-quality validation is now a pre-execution gate: `warn` and `reject` do not reach image execution;
- Teacher action examples were replaced with concrete count/spatial/preservation instructions;
- Skill retrieval identity is `(skill_id, version, content_sha256)`;
- changed Skill version/hash is treated as a new identity, while legacy events missing hash are conservatively treated as active for the same `skill_id/version`;
- compact active Skill summaries retain every `### Operators` bullet within a deterministic length bound.

Scoped correction after final Sol `REQUEST_CHANGES`:

- instruction-quality validation now rejects missing required entities, attribute/entity bindings, forbidden-change wording, incompatible counts, depth contradictions, and preserve/modify conflicts;
- active Skill summaries no longer include `preferred_action`, so foundational Skills do not recommend generate versus edit;
- immediate full Skill injection and retained operator summaries now use retrieval-time Skill content from `tool_observations.jsonl` with hash verification instead of rereading mutable Skill files;
- compact operator summaries allocate bounded text to every available operator bullet instead of hard-truncating the final bullet mid-sentence.

## Current-Instruction Audit

Detailed audit: `docs/teacher_prompt_design/CURRENT_EDIT_INSTRUCTION_AUDIT.md`

Main defects:

- initial generation was usable but weakened the behind relation with `above or beside`;
- first edit had contradictory depth wording: `forward toward/behind`;
- second edit was too vague: `modify only the failed parts`, `all already-correct visual evidence`;
- third edit was overbroad for a local edit;
- final best-branch edit was strongest but still did not improve over best.

## Final Teacher System Prompt

File: `docs/teacher_prompt_design/TEACHER_SYSTEM_PROMPT_V1.md`

Version: `teacher_system_prompt_v1`

SHA-256: `864f41d49cdd5e966ed8e4e82b9f4de3a091eef0fbd64c4c0cf918e568ebe6c0`

Prompt text:

```text
You are a verifier-grounded multimodal image retry planner for Gen-Retry v3. Your goal is to maximize the best valid image attempt under the remaining image-attempt budget. Output exactly one canonical action JSON object and no prose or chain-of-thought. Skills provide operational guidance for constructing generation_instruction and edit_instruction text; Skills do not decide whether to generate, edit, branch from best, continue, or submit. Use visible images and Geneval2 atom feedback together. Do not invent unsupported visual observations. Compare latest and best images when they differ before selecting an edit source. Use fixed, regressed, persistent, and stable-pass history. Do not repeat a materially equivalent ineffective instruction unless the new instruction contains a concrete change.
```

## Image-Instruction Contract

File: `docs/teacher_prompt_design/IMAGE_INSTRUCTION_CONTRACT_V1.md`

Generation instructions must include relevant exact entities/counts, attributes, layout, relation/depth cues, visibility/separation, no extras/fusion/cropping/reflections, and all original constraints.

Edit instructions must include four blocks:

1. target operation;
2. spatial grounding;
3. preservation lock;
4. forbidden changes.

The linter in `src/gen_retry/agent/instruction_quality.py` reports `pass`, `warn`, or `reject` without rewriting Teacher output. In live runtime, only `pass` proceeds to `action_validated` and image execution. Missing entities, missing attribute bindings, missing no-extra/forbidden-change wording, incompatible counts, depth contradictions, and preserve/modify conflicts are `reject`.

## Skill Lifecycle Policy

File: `docs/teacher_prompt_design/SKILL_LIFECYCLE_POLICY_V1.md`

Policy:

- full Markdown after first query;
- compact active operators in later PlannerViews;
- same Skill identity `(skill_id, version, content_sha256)` retrieved at most once per episode by default;
- at most two Skills per query;
- no consecutive query-only loop;
- repeated failure alone is not a reason to re-query the same Skill;
- new query allowed for new capability, inactive Skill, changed version/hash, or missing required operator.
- legacy events without hash are treated conservatively as active for the same `skill_id/version`.
- retained active operators are hash-verified against retrieval-time content and do not carry `preferred_action`.

## Sample Turn in New Trace Format

Sample from `phase3_ep_001`, turn `turn_003`.

Teacher input summary:

- system prompt version/hash present;
- original prompt and 11 atom constraints present;
- compact history contains `a_000`;
- visible image labels include `LATEST_IMAGE:a_000:img_000` and `BEST_IMAGE_SAME_AS_LATEST:a_000:img_000`;
- retrieved full Skills: `counting_and_instance_layout`, `spatial_relation_layout`;
- active operators retained in PlannerView.

Assistant canonical action:

```json
{
  "schema_version": "0.2",
  "action": "edit_image",
  "arguments": {
    "source_attempt_id": "a_000",
    "target_constraint_ids": ["c_004", "c_005", "c_008"],
    "preserve_constraint_ids": ["c_001", "c_002", "c_003", "c_006", "c_007", "c_009", "c_010", "c_011"],
    "strategy_tags": ["localized_repair", "count_correction", "spatial_relation_repair", "verb_relation_repair"],
    "skill_ids_used": ["counting_and_instance_layout", "spatial_relation_layout"],
    "edit_instruction": "Edit IMG_000 to show exactly three red cats total, each fully visible and separated; remove the extra fourth cat without adding any new cats. Reposition the three remaining red cats so they are clearly behind the single brown donut in depth: the donut stays large in the foreground at the bottom/center, and all three cats appear farther back beyond the donut, still visible above and around it with partial non-blocking overlap if needed. Adjust body orientation and motion cues so the six glass lions are visibly chasing the three cats: lions behind the cats, facing and running toward them, with the cats fleeing forward toward/behind the donut. Preserve exactly six glass lions, one brown donut, the red color of the cats, the glass material of the lions, and do not add extra lions, cats, or donuts."
  }
}
```

Instruction-quality result:

- verdict: `reject`;
- contradiction flag: `toward/behind`;
- source attempt known: `a_000`;
- exact Qwen input is the canonical `edit_instruction`;
- Geneval2 outcome: no fixed atoms, persistent `c_004`, `c_005`, `c_008`.

## Review Questions

1. Does the Teacher prompt correctly separate foundational Skill operators from retry-policy decisions?
2. Is the edit/generation instruction contract concrete enough to prevent vague or contradictory rewrites before the next live trajectory?
3. Is the Skill retention/no-repeat policy efficient and auditable without changing the frozen action schema?

## Non-Goals

- Do not require a live trajectory in this review.
- Do not invoke Qwen-Image-Edit or Geneval2.
- Do not decide future generate/edit repair-strategy Skills.
- Do not reopen Phase 3 or Phase 4 gates.
