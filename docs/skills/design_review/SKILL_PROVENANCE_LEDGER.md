# Skill Provenance Ledger

Date: 2026-07-15

This ledger explains how Skill Catalog v1 was authored from evidence. It records provenance for substantive Skill instructions and separates validated evidence from hypotheses. No live rollout, Qwen-Image-Edit call, Geneval2 call, or teacher rollout call was run for this design review.

## Provenance Categories

- `repository_grounded`: grounded in current v3 repository behavior, legacy read-only records, or grounded local external repositories.
- `paper_grounded`: grounded in prior paper notes already recorded in `docs/SOURCE_LEDGER.md`.
- `trajectory_grounded`: grounded in current completed v3 trajectories and action/outcome labels.
- `backend_documentation_grounded`: grounded in Qwen-Image-Edit usage evidence and local model README.
- `our_hypothesis`: proposed instruction operator not yet validated in a fresh Skill-v1 trajectory.

## Shared System Provenance

| Design item | Provenance | Evidence |
| --- | --- | --- |
| Markdown skill content loaded on demand | `repository_grounded` | `src/gen_retry/tools/skill_store.py`; current `tool_observations.jsonl` records full skill content |
| Skill content enters later teacher context | `repository_grounded` | `src/gen_retry/agent/teacher_client.py` includes `Retrieved skills:` in requests |
| Skill should not choose retry action | `repository_grounded` | `DEVELOPMENT_BLUEPRINT.md`, `docs/architecture/MODULE_CONTRACTS.md`, `docs/phase4/sft_supervision_freeze.md` |
| Skill content is context-only, not SFT target | `repository_grounded` | `docs/phase4/sft_supervision_freeze.md` keeps `query_skill` context-only until accepted non-placeholder content |
| Compact skills rather than raw long reasoning | `paper_grounded` | `docs/SOURCE_LEDGER.md` prior GEMS note: skill/memory engineering and compressed memory as background |
| Compress GenEvolve-style Markdown for v3 context limits | `repository_grounded` | GenEvolve references are 570-739 local Qwen tokens; v3 drafts are 327-348 local Qwen tokens and one query retrieves at most two Skills |

## `counting_and_instance_layout`

| Substantive instruction | Provenance | Evidence | Validation plan if hypothesis |
| --- | --- | --- | --- |
| State exact total next to object noun | `trajectory_grounded` | Count is the highest non-pass type in `FOUNDATIONAL_CAPABILITY_EVIDENCE.md`; HQ `phase3_ep_001` lion count remained difficult | Check whether first Skill-v1 validation instruction includes exact total adjacent to noun |
| Use bounded formation/region such as row, grid, arc, two rows | `repository_grounded` | GenEvolve `quantity_counting.md` recommends rows/grids/semicircles and unique positions | N/A |
| Require full visibility and visible gaps | `repository_grounded` + `trajectory_grounded` | GenEvolve counting guidance; v3 failures include merged/cropped/ambiguous count signatures | N/A |
| For 5+ objects, use formation rather than enumerating all objects | `repository_grounded` | GenEvolve `quantity_counting.md` recommends grouping for 6+ objects | N/A |
| For local count edits, name operation: add/remove/separate/clarify | `trajectory_grounded` | Edits often fixed one atom but caused regressions; target count remained non-pass 64 times in ten-run transitions | N/A |
| Avoid reflections/background copies being countable | `our_hypothesis` | Motivated by count ambiguity, not directly isolated in current reports | Inspect validation trajectory images and Geneval2 observations for extra countable artifacts; revise if this wording adds clutter |

## `spatial_relation_layout`

| Substantive instruction | Provenance | Evidence | Validation plan if hypothesis |
| --- | --- | --- | --- |
| Name relation in subject-object order | `trajectory_grounded` | Verb/position failures were common; relation words alone often did not make chasing/behind verifiable | Check instruction trace for explicit subject-object relation clause |
| Anchor both entities to frame/depth regions | `repository_grounded` | GenEvolve `spatial_layout.md` recommends frame coordinates, foreground/midground/background, and relative placement | N/A |
| For behind/in front, state depth and non-blocking occlusion | `repository_grounded` + `trajectory_grounded` | GenEvolve spatial guidance; `phase3_hq5_ep_001:a_001` fixed cats behind donut after stronger foreground wording | N/A |
| For left/right, use viewer-frame wording | `repository_grounded` | GenEvolve spatial guidance emphasizes absolute frame-relative terms | N/A |
| For chasing/following/facing, specify pose, orientation, motion direction, and target | `trajectory_grounded` | HQ `phase3_ep_001` fixed chasing at `a_003`; relation later regressed after a count-only edit | N/A |
| Use motion cues such as motion lines only when natural for the scene | `our_hypothesis` | Present in teacher edits but not isolated as causal | If validation uses motion cues, inspect whether they help Geneval2 verb atom without harming style/count |

## `attribute_entity_binding`

| Substantive instruction | Provenance | Evidence | Validation plan if hypothesis |
| --- | --- | --- | --- |
| Use self-contained entity clauses | `repository_grounded` | GenEvolve `attribute_binding.md` recommends complete subject clauses | N/A |
| Put attribute adjacent to the noun | `repository_grounded` | GenEvolve warns against floating adjective lists | N/A |
| Add spatial anchor for each attributed entity | `repository_grounded` | GenEvolve recommends spatial separation to reduce leakage | N/A |
| Include visible material evidence such as transparent/refractive glass or reflective metal | `trajectory_grounded` + `backend_documentation_grounded` | HQ `phase3_ep_001:a_002` fixed glass material; Qwen README examples emphasize prompt-driven edit semantics | N/A |
| For edits, target only incorrectly attributed entity and preserve other attributes | `trajectory_grounded` | Attribute regressions occurred in ten fresh trajectories; SFT freeze treats harmful edits as context-only | N/A |
| Use negative leakage controls such as "do not apply glass to cats" | `our_hypothesis` | Supported by attribute leakage logic but not isolated in v3 outcomes | Track whether negative clauses reduce leakage or increase prompt complexity in first validation |

## `local_edit_preservation`

| Substantive instruction | Provenance | Evidence | Validation plan if hypothesis |
| --- | --- | --- | --- |
| Start edit with minimal localized scope | `trajectory_grounded` | Constraint regression occurred in all ten fresh trajectories; harmful edits are context-only | N/A |
| Name exact target object/region and smallest operation | `trajectory_grounded` | HQ `phase3_ep_002` repeated broad edits from best did not beat initial image; ten-run labels show many harmful edits | N/A |
| Preserve stable content in visual terms, not just constraint IDs | `repository_grounded` + `trajectory_grounded` | Planner action already carries IDs, but Qwen instruction needs visual text; current traces list preserve IDs and natural-language preservation clauses | N/A |
| Say "do not redraw the whole scene" for high-risk edits | `our_hypothesis` | Motivated by edit regressions; not yet isolated as a causal fix | Compare validation edit outputs for composition drift; remove if it harms edit effectiveness |
| Do not add/remove/recolor/move non-target entities | `trajectory_grounded` | Regressions include count, object, attribute, position, and verb atoms after edits | N/A |

## Backend And Runtime Provenance

| Design item | Provenance | Evidence |
| --- | --- | --- |
| Qwen local pipeline can stay loaded and serve repeated inference | `backend_documentation_grounded` | Local Qwen README loads `QwenImageEditPlusPipeline` once then calls the pipeline |
| Quality defaults should use 40 steps, CFG 4.0, guidance 1.0 | `backend_documentation_grounded` + `repository_grounded` | Local Qwen README, Gen-Searcher service defaults, GenEvolve renderer defaults, `docs/operations/qwen_rendering_quality_baseline.md` |
| Current v3 adapter reloads per image action | `repository_grounded` | `src/gen_retry/tools/qianwen_image_edit_adapter.py` calls `_load_pipeline()` inside `_run()` and deletes the pipeline afterward |
| Persistent worker should preserve existing artifact-cache/idempotency behavior | `repository_grounded` | Current adapter returns cache hits when deterministic output path exists |
| First validation should prioritize correctness with one worker | `our_hypothesis` | Conservative design based on current single-GPU evidence and user preference to avoid wasted calls | Validate by running one approved fresh Skill-v1 trajectory only after user confirmation |

## Unsupported Or Deferred Claims

- No claim is made that Skill v1 improves outcomes before a fresh Skill-v1 validation trajectory is run.
- Legacy trajectories remain counterfactual evidence and are not positive SFT targets.
- Object-presence is not separated into a fifth Skill because current evidence does not show a high-quality, non-overlapping object capability gap.
- Persistent service implementation is deferred; this design review does not implement or activate a worker.
