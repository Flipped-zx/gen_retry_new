# Foundational Capability Evidence

Date: 2026-07-15

Scope: Skill Catalog v1 design evidence. No live teacher, Qwen-Image-Edit, Geneval2, or trajectory execution was run for this review.

## Evidence Sources

- Current placeholder skills: `skills/*/SKILL.md`
- Skill runtime: `src/gen_retry/tools/skill_store.py`, `src/gen_retry/agent/teacher_client.py`, `src/gen_retry/phase3/live_runner.py`
- Ten completed fresh trajectories: `runs/phase3/phase3_ep_001` through `runs/phase3/phase3_ep_010`
- Supplemental high-quality trajectories: `runs/phase3_hq5/phase3_ep_001` through `runs/phase3_hq5/phase3_ep_003`
- Phase 3 reports: `docs/phase3/ten_trajectory_comparison.md`, `docs/phase3/behavior_coverage_report.md`, `docs/phase3/hq5_completed_trajectory_behavior_analysis.md`
- SFT label evidence: `artifacts/phase3/action_supervision_labels.jsonl`, `docs/phase4/sft_supervision_freeze.md`
- Legacy counterfactual evidence: `docs/phase3/legacy_failure_signature_summary.md`, `docs/phase3/legacy_edit_plausibility_analysis.md`
- External evidence ledger: `docs/SOURCE_LEDGER.md`

## Current Skill Mechanism

The retrieval mechanism is already present. `query_skill` calls `LocalSkillStore`, reads `skills/<skill_id>/SKILL.md`, records version/hash metadata in the event stream, and returns full content in `tool_observations.jsonl`. The teacher client then includes retrieved skill content under `Retrieved skills:` in the next request. The current limitation is content quality: all active skill files contain placeholder `TODO` sections.

## Evaluator-Grounded Frequency Table

The table below counts existing normalized Geneval2 atom results. Frequencies are atom-attempt observations, not unique prompts. Constraint types are the actual Geneval2 types present in the v3 task specs: `attribute`, `count`, `object`, `position`, and `verb`.

| Constraint type | Ten fresh non-pass frequency | HQ supplemental non-pass frequency | Representative failure signature | Representative episodes / attempts |
| --- | ---: | ---: | --- | --- |
| `count` | 110 / 147 | 12 / 36 | Wrong number, merged instances, extra instances, or countable target absent | `phase3_ep_001:a_000` lion count observed `0` vs `six`; `phase3_hq5_ep_001:a_001` lion count observed `5` vs `six`; `phase3_hq5_ep_002:a_000` croissant count observed `4` vs `five` |
| `verb` | 42 / 49 | 10 / 12 | Static co-presence does not satisfy chasing/playing/facing/following relation | `phase3_ep_001:a_000` lions not chasing cats; `phase3_hq5_ep_001:a_002` chasing still failed; `phase3_hq5_ep_002:a_004` flamingos still not playing with sheep |
| `position` | 37 / 49 | 1 / 12 | Behind/front/right-of relation unclear, occluded, or composed side-by-side | `phase3_ep_001:a_000` cats behind donut uncertain; `phase3_hq5_ep_001:a_000` cats behind donut failed, then fixed in `a_001` |
| `attribute` | 46 / 118 | 2 / 36 | Material or color not bound to the intended entity | `phase3_ep_001:a_000` lions not glass; `phase3_ep_001:a_000` cats not red; `phase3_hq5_ep_001:a_002` glass material fixed |
| `object` | 66 / 147 | 0 / 36 | Object not recognized after generation/edit, often entangled with count or identity failures | `phase3_ep_001:a_000` no recognizable lions/cats; low-quality ten-run evidence only, not persistent in HQ supplement |

## Trajectory-Derived Transition Table

The counts below compare each non-initial image action to its source attempt when available, otherwise to the previous attempt. `Repeated ineffective` is counted when a targeted atom was non-pass before the action and remained non-pass after the action. This is transition evidence, not a rule for choosing actions.

| Constraint type | Target fixed count | Regression count | Repeated ineffective count | Common instruction defect | Capability knowledge that could address it |
| --- | ---: | ---: | ---: | --- | --- |
| `count` | 17 | 23 | 64 | Mentions exact number but does not force separation, full visibility, bounded region, or no extras | Instance layout operators: bounded group, visible gaps, full bodies, enumerate target group, forbid duplicate/cropped/fused instances |
| `verb` | 3 | 5 | 29 | Names the verb but lacks subject orientation, motion direction, contact/interaction cue, or before/after depth relation | Relation operators: subject/object anchors, facing direction, motion vectors, chase/follow spacing, interaction contact cues |
| `position` | 4 | 11 | 20 | Uses relation word without frame regions, depth cue, occlusion control, or both entities visible | Spatial layout operators: foreground/background, left/right frame halves, overlap rules, visible separation, relative anchor phrase |
| `attribute` | 12 | 25 | 14 | Attribute phrase can leak across nearby objects or is too global | Entity binding operators: describe each entity in a separate clause, repeat bound attribute next to noun, use spatial anchor to disambiguate |
| `object` | 19 | 29 | 24 | Broad edits transform or erase already-correct objects | Preservation operators: name exact object/region to edit, list stable entities unchanged, preserve counts/materials/relations outside target |

## Legacy Counterfactual Evidence

Legacy diagnostic/action records are not current-protocol positive supervision and did not provide new parents or images. They support difficulty and capability-priority estimates only.

- Top unresolved signatures include `count:1` with 163 records, `attribute:1,count:1` with 97 records, `count:2` with 80 records, `attribute:1` with 78 records, `count:1,verb:1` with 65 records, `position:1` with 49 records, and `verb:1` with 29 records.
- Historical action decisions in the legacy analysis were all `regenerate`; this cannot justify a v3 Skill that chooses edit vs regenerate.
- Counterfactual edit plausibility was high for 698 / 1276 legacy records and medium for 428 / 1276, supporting the need for better local edit instruction construction after the retry policy has already selected `edit_image`.

## Productive Versus Harmful Evidence

The ten fresh trajectories contain both useful and harmful actions:

- `local_edit_used`: 10 / 10 episodes
- `target_constraint_fixed`: 10 / 10 episodes
- `constraint_regression`: 10 / 10 episodes
- `repeated_ineffective_strategy`: 10 / 10 episodes
- `historical_best_submission`: 9 / 10 episodes
- SFT labels: 29 `trainable_positive`, 9 `recovery_positive`, 28 `history_only_harmful`, and 3 `history_only_ineffective`

Interpretation: Skill v1 should improve instruction construction, but it must not encode high-level retry policy. Regression and historical-best recovery remain policy/runtime responsibilities.

## Counterfactual Skill Hypotheses To Validate

These hypotheses are plausible but not proven until a fresh Skill-v1 trajectory is run:

1. Count failures may drop when instructions explicitly require separated, fully visible, non-overlapping instances in a bounded region.
2. Verb and position failures may drop when instructions specify frame anchors, depth cues, orientation, and relation-specific visual evidence.
3. Attribute failures may drop when each entity is described in its own clause with bound color/material adjacent to the noun.
4. Edit regressions may drop when edit instructions name the exact region/object to change and explicitly preserve stable counts, attributes, relations, and background.

## Skill Catalog Implication

The evidence supports four foundational capabilities:

- `counting_and_instance_layout` for `count` and instance separability.
- `spatial_relation_layout` for `position` and `verb`.
- `attribute_entity_binding` for `attribute` and identity/material/color binding.
- `local_edit_preservation` for edit-only non-target preservation and regression control.

No fifth Skill is justified at this stage. `object` failures appear important in the low-quality ten-run evidence but are mostly entangled with count, identity, and preservation failures, and disappear in the high-quality supplemental runs. A standalone object-presence Skill should wait for fresh high-quality evidence showing frequent non-overlapping object failures.
