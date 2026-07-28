# First Skill-v1 Trajectory Plan

Date: 2026-07-15

Status: plan only. No validation trajectory was executed.

## Selected Task

Use `phase3_ep_001` as the first fresh Skill-v1 validation task.

Original prompt:

```text
six glass lions chasing three red cats behind a brown donut
```

Rationale:

- It tests exact counts: six lions, three cats, one donut.
- It tests attribute binding: glass lions, red cats, brown donut.
- It tests a verb relation: lions chasing cats.
- It tests a spatial relation: cats behind donut.
- Existing HQ evidence shows multi-step improvement, regression, best-so-far tracking, and historical-best submission.
- The trace is already readable in `docs/phase3/trajectory_trace_phase3_hq5_ep_001.md`, which makes fresh comparison possible without reusing old images.

## Fresh-Start Requirements

The validation trajectory must:

- start from empty attempt history;
- use a fresh initial generation;
- reuse no old images;
- reuse no old attempt states;
- reuse only the same original prompt and atomic constraints;
- use the accepted Skill Catalog v1;
- use the same teacher, Qwen-Image-Edit, and Geneval2 versions/configs unless explicitly changed before execution;
- use at most five image attempts unless explicitly approved otherwise;
- preserve full PlannerView, raw-but-redacted teacher output, canonical action, instruction, image, Geneval2 atom result, transition, best-so-far, and submission records.

## Expected Skill Coverage

Likely relevant Skills:

- `counting_and_instance_layout`
- `spatial_relation_layout`
- `attribute_entity_binding`
- `local_edit_preservation` for edit turns only

Because one `query_skill` may request at most two Skills, expected first retrieval should prioritize:

- `counting_and_instance_layout`
- `spatial_relation_layout`

If a later edit targets material/attribute or preservation risk, the policy may retrieve:

- `attribute_entity_binding`
- `local_edit_preservation`

No query-only loop should occur.

## Falsifiable Success Criteria

1. The Agent queries a relevant Skill or correctly decides no Skill is needed.
2. The next generation/edit instruction visibly uses concrete operators from the retrieved Skill.
3. The query does not create a redundant query-only loop.
4. Skill use does not worsen action selection or context cost without benefit.
5. The resulting trajectory is sufficiently traceable to judge whether Skill retrieval helped, was ignored, or was harmful.

## Skill Failure Criteria

Skill use should be classified as failed if any of the following occur:

- retrieved Skill is not applicable to the target constraints;
- downstream action lists `skill_ids_used` but the instruction does not use Skill operators;
- Skill wording causes broad edits that regress stable atoms;
- Skill retrieval causes repeated query-only turns;
- Skill content pushes policy-like decisions such as edit vs regenerate or submit timing;
- context cost increases without visible operator use or traceability benefit.

## Criteria For Running Two Additional Fresh Trajectories

Run two more fresh Skill-v1 trajectories only if the first validation trajectory shows:

- valid retrieval behavior with no query-only loop;
- at least one downstream instruction materially uses retrieved Skill operators;
- no obvious schema or runtime mismatch from the new Skill IDs/manifest;
- traceability is sufficient to classify Skill use as helpful, ignored, or harmful;
- no severe regression clearly attributable to Skill wording.

## Criteria For Revising Skill Content Before Further Runs

Revise Skill content before additional trajectories if:

- teacher repeatedly retrieves irrelevant Skills;
- instructions become too long or mix conflicting operators;
- local edits become broader and regress more stable constraints;
- relation/count/attribute operators are ignored by teacher despite retrieval;
- a Skill includes policy guidance that affects action selection rather than instruction construction;
- manifest summaries are misleading or cause poor retrieval.

## Expected Post-Run Analysis

After the approved validation trajectory, produce:

```text
docs/skills/validation/<episode_id>_skill_utilization_analysis.md
```

This should classify retrieved Skill use as `used_materially`, `retrieved_but_ignored`, `misapplied`, or `harmful_or_regressive`, using canonical actions, instruction text, `skill_ids_used`, and Geneval2 transitions.
