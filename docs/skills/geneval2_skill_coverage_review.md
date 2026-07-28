# Geneval2 Skill Coverage Review

Date: 2026-07-26

Scope: read-only review of whether the current Gen-Retry skills can cover Geneval2/Geneval tasks from easy to hard.

## Verdict

`PARTIAL: CONTENT COVERAGE LANDED, UTILITY NOT YET ACCEPTED`

The v0.5 catalog now covers the six foundational capability families, but
capability-isolated utility evidence is still insufficient to make
`query_skill` a positive SFT target.

## Geneval2 Evidence

Source: `/root/private_data/agentic_image/GenEval2/geneval2_data.jsonl`

Dataset statistics:

| Item | Value |
|---|---:|
| prompts | 800 |
| `atom_count` bins | 3 to 10, exactly 100 prompts each |
| actual VQA atoms | 6012 |

Skill atom distribution:

| Geneval2 skill | Atom count | Prompt coverage |
|---|---:|---:|
| `count` | 2025 | 800 / 800 |
| `object` | 2025 | 800 / 800 |
| `attribute` | 1214 | 721 / 800 |
| `position` | 662 | 519 / 800 |
| `verb` | 86 | 82 / 800 |

Position relations:

| Relation | Count |
|---|---:|
| `to the left of` | 119 |
| `in front of` | 112 |
| `behind` | 111 |
| `under` | 108 |
| `to the right of` | 108 |
| `on top of` | 104 |

Verb relations:

| Verb relation | Count |
|---|---:|
| `playing with` | 30 |
| `chasing` | 28 |
| `jumping over` | 28 |

Important interpretation:

- `atom_count` is compositionality, not the exact number of VQA checks.
- Geneval2 still evaluates object existence and one-object count questions even when they are not counted as prompt atomicity.
- Therefore coverage should be judged from `vqa_list` and `skills`, not only from `atom_count`.

## Current Skill Catalog

Default exposed skills:

| Skill | Status | Covers |
|---|---|---|
| `counting_and_instance_layout` | real v2 | count layout plus local count repair |
| `attribute_entity_binding` | real | color/material/texture binding to correct entity |
| `spatial_relation_layout` | real v2 | static position relations only |
| `local_edit_preservation` | real v2 | four-part narrow edit and regression avoidance |
| `action_pose_relation` | real v1 | visible evidence for verb/action relations |
| `object_identity_presence` | real v1 | object category, presence, and recognizability |

Deprecated compatibility IDs on disk:

| Skill | Status |
|---|---|
| `attribute_binding` | deprecated; use `attribute_entity_binding` |
| `constraint_preservation` | deprecated; use `local_edit_preservation` |
| `counting_edit` | deprecated; merged into `counting_and_instance_layout` |
| `counting_layout` | deprecated; use `counting_and_instance_layout` |
| `spatial_relation` | deprecated; split into static/action relation Skills |

Only the six manifest-exposed real Skills count as current capability guidance.

## Coverage Judgment

| Geneval2 atom family | Current coverage | Risk |
|---|---|---|
| `count` | content-complete, utility pending | v2 covers fresh layout and local count repair. |
| `object` | content-complete, utility pending | Explicit identity/presence/no-substitution guidance is now exposed. |
| `attribute` | medium | Good design direction, but utility validation is incomplete. |
| `position` | medium | Covers left/right/front/behind/under/on-top, but hard layouts need stronger examples. |
| `verb` | content-complete, utility pending | Dedicated action-pose guidance covers chasing, playing with, and jumping over. |
| preservation | content-complete, utility pending | v2 provides the four-part local-edit structure; prior utility validation still failed. |

## Remaining Utility Gaps

1. Capability-isolated validation

   The newly materialized count-edit, action-pose, object-identity, and
   preservation operators need isolated executed evidence before retrieval is
   supervised.

2. Attribute/local-preservation validation

   `attribute_entity_binding` and `local_edit_preservation` are plausible, but prior Sol review did not accept utility because the Skill-conditioned edits failed to repair target atoms.

## SFT Implication

Do not make `query_skill` a positive SFT target yet.

Current retrieval mechanics are clear, but utility is not accepted. A `query_skill` action should become trainable only when:

```text
queried skill is relevant
-> returned content is actually used in the next action
-> the following image action materially improves at least one target atom
-> preserved atoms do not regress
```

Until then:

- keep `query_skill` in trajectory history;
- include skill responses as context with loss 0;
- train only selected generate/edit/submit actions that pass supervision filters.

## Minimum Skill Work Before Treating Retrieval As Trainable

Recommended before query-skill SFT:

1. Run one capability-isolated successful trajectory for each new or upgraded
   Skill family used as retrieval supervision.
2. Run one isolated attribute/local-preservation validation episode that fixes
   at least one target atom without regression.

Experience skills can wait:

- object-pair quirks;
- high-count layouts such as 5, 6, and 7;
- relation-specific success rates;
- Qwen-Image-Edit failure signatures;
- when to regenerate, rollback, or submit.

## Recommended Decision

For v0.5 field design, the current skills are enough to test the interaction format.

For SFT, content coverage alone is not enough to supervise retrieval behavior.
Keep `query_skill` context-only until the required capability-isolated utility
validations succeed.
