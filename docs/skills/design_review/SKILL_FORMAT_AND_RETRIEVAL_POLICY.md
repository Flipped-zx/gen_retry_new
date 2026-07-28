# Skill Format And Retrieval Policy

Date: 2026-07-15

Status: proposed. Not activated.

## Markdown Format

Skill Markdown remains compatible with the current `LocalSkillStore` path convention:

```text
skills/<skill_id>/SKILL.md
```

Draft Skill files are currently staged only under:

```text
docs/skills/design_review/drafts/<skill_id>/SKILL.md
```

Required outer format:

```markdown
# Skill: <Name>

## Description
<one concise paragraph>

## Instructions

### Applicable when
...

### Do not use when
...

### Operators
...

### Preservation checks
...

### Avoid
...

### Minimal instruction pattern
...
```

`### Preservation checks` may be omitted only when genuinely irrelevant. Skill v1 keeps it for all four Skills.

## Proposed Manifest

The planner should see only summaries before retrieval. Full Markdown is returned only after `query_skill`.

| skill_id | version | summary | constraint_types | supported_action_modes | content_hash |
| --- | --- | --- | --- | --- | --- |
| `counting_and_instance_layout` | `1.0.0` | Exact cardinality, instance separation, full visibility, no extras or fused objects. | `count`, limited `object` | `generate_image`, `edit_image` | `4e7077c8653684b9338326928ae11b5927ff8bc08197f16adfa18679ba685e02` |
| `spatial_relation_layout` | `1.0.0` | Frame, depth, orientation, occlusion, and motion cues for spatial/verb relations. | `position`, `verb` | `generate_image`, `edit_image` | `154561266eb98fd63676e7f68d15732df1e9fbaf49d5872f49f8cb9b65d2c019` |
| `attribute_entity_binding` | `1.0.0` | Bind color, material, texture, and identity attributes to the correct entity. | `attribute`, limited `object` | `generate_image`, `edit_image` | `15b693e5fd14a05fdc9c0f6ee23224e7f97c657e8386bfbc65d1b9f62f840b01` |
| `local_edit_preservation` | `1.0.0` | Narrow edit scope and preserve already-correct visual evidence. | `count`, `attribute`, `object`, `position`, `verb` | `edit_image` | `559b9af9b3e40446a11a9fe15d2a9b1d8f84a7a0eb2196306320431045346335` |

Draft token counts, measured with the local `Qwen3-VL-8B-Instruct` tokenizer and `add_special_tokens=False`, are 327, 348, 339, and 347 respectively.

## Retrieval Rules

1. One `query_skill` action may request at most two Skills.
2. A single query cannot request the same Skill twice.
3. Re-querying the same Skill version later in the episode is allowed only after new image/evaluator observation makes the capability relevant again.
4. Consecutive `query_skill`-only loops are forbidden.
5. After a successful Skill query, the next canonical action should normally be `generate_image`, `edit_image`, or `submit_attempt`.
6. Retrieved Skill content enters the next teacher context exactly once under current reducer policy unless a future accepted policy explicitly retains it.
7. Repeated retrieval of an unchanged Skill version is cache-backed semantically: it returns the same version/hash/content and creates a fresh tool observation for traceability.
8. Skill version and content hash must be logged in the event stream and tool observation.
9. Skill text is a tool observation and receives no SFT loss.
10. `query_skill` remains context-only until fresh action-outcome evidence shows that retrieval was relevant, used, and materially helpful.

## Retrieval Pairing Policy

Use at most two Skills per query:

- Counted relation: `counting_and_instance_layout` + `spatial_relation_layout`
- Counted attributed entity: `counting_and_instance_layout` + `attribute_entity_binding`
- Attribute relation: `attribute_entity_binding` + `spatial_relation_layout`
- Count edit: `counting_and_instance_layout` + `local_edit_preservation`
- Relation edit: `spatial_relation_layout` + `local_edit_preservation`
- Attribute edit: `attribute_entity_binding` + `local_edit_preservation`

If more than two capabilities are relevant, the teacher should prefer the two most directly tied to the current target constraints. It must not start a query-only loop to fetch the remaining Skills.

## Skill Utilization Auditing

Initial utilization should be inferred from existing fields and post-hoc analysis, not by changing the canonical action schema.

Use:

- `canonical_action.arguments.skill_ids_used`
- retrieved Skill IDs and content hashes in `tool_observations.jsonl`
- downstream generation/edit instruction text
- target/preserve constraint IDs
- Geneval2 transition outcomes

For the first validation trajectory, write a separate post-hoc analysis artifact after execution, for example:

```text
docs/skills/validation/<episode_id>_skill_utilization_analysis.md
```

That artifact can classify each retrieved Skill as:

- `used_materially`: instruction contains concrete operators from the Skill and targets matching constraints;
- `retrieved_but_ignored`: Skill was retrieved but downstream instruction lacks its operators;
- `misapplied`: Skill operators are used for non-applicable constraints;
- `harmful_or_regressive`: Skill-guided action plausibly contributed to regression.

No action-schema change is justified for v1 because traceability is already available through retrieved Skill IDs, hashes, `skill_ids_used`, instruction text, and atom transitions.

## Activation Requirements After Approval

Activation requires code and fixture updates after user confirmation:

- add active files under `skills/<skill_id>/SKILL.md`;
- update the default manifest from old placeholder IDs to the four v1 IDs;
- ensure `validate_action_references` accepts these IDs through the manifest path;
- enforce or validate max-two Skill retrieval and no duplicate same-version retrieval by default;
- add tests that `query_skill -> tool observation -> next teacher context` includes v1 content and hashes.
