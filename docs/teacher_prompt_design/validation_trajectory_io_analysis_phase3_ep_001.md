# Validation Trajectory I/O Analysis: `phase3_ep_001`

Date: 2026-07-15

Run directory: `runs/teacher_prompt_v1_validation/phase3_ep_001`

Readable trace: `docs/teacher_prompt_design/validation_trace_phase3_ep_001.md`

## Verdict

This trajectory is fit for the structure we want: it shows a clear `query_skill -> generate/edit attempts -> verifier feedback -> history-aware branch -> submit best` loop.

The Teacher did internalize the planning policy into prompt/instruction construction:

- generation prompts became exact-count, layout-aware, no-extra/no-fusion/no-reflection instructions;
- edit prompts used target operation, spatial grounding, preservation lock, and forbidden-change blocks;
- later edits targeted only persistent failed atoms instead of rewriting the full prompt;
- after `a_003` regressed the glass atom, the Teacher branched from best `a_002` rather than blindly continuing from latest;
- at budget zero, the Teacher submitted `a_002`, the historical best.

Important caveat: this is a strong canonical trajectory, not a clean raw Teacher transcript. There were 12 Teacher requests, 7 canonical accepted actions, and 5 rejected raw outputs.

## Budget Semantics

`max_image_attempts=5` means five image executions, not five Teacher turns.

Image attempts:

| Attempt | Action | Source | Passed | Failed |
| --- | --- | --- | ---: | --- |
| `a_000` | `generate_image` | none | 6/11 | `c_001`, `c_002`, `c_004`, `c_005`, `c_008` |
| `a_001` | `generate_image` | none | 8/11 | `c_001`, `c_004`, `c_008` |
| `a_002` | `edit_image` | `a_001` | 9/11 | `c_004`, `c_008` |
| `a_003` | `edit_image` | `a_002` | 8/11 | `c_002`, `c_004`, `c_008` |
| `a_004` | `edit_image` | `a_002` | 9/11 | `c_004`, `c_008` |

Submitted attempt: `a_002`

Submit reason: `best_available_under_budget`

## What the Teacher Receives

Every Teacher request persists a sanitized record in `planner_requests.jsonl`. The main fields are:

- `request_id`;
- `teacher_model_id`;
- `system_prompt_version`;
- `system_prompt_sha256`;
- `planner_view_ref`;
- `planner_view_sha256`;
- `teacher_text_input`;
- `visible_images`;
- `retrieved_skill_ids`;
- `extra_observations`.

The full `teacher_text_input` contains:

- original prompt;
- atomic constraints with IDs;
- current PlannerView canonical JSON;
- remaining image budget;
- compact attempt history;
- latest attempt summary;
- best attempt summary;
- latest transition;
- per-constraint state;
- active Skill operator summaries;
- retrieved full Skill Markdown immediately after `query_skill`;
- allowed canonical action schema instructions;
- generation/edit instruction contracts;
- image labels such as `LATEST_IMAGE` and `BEST_IMAGE`.

Persisted requests do not store raw image bytes or file paths. They store sanitized `visible_images` with role, attempt ID, artifact ID, and path hash. The actual Teacher API request includes multimodal image inputs; the persisted version redacts the image payload.

## Raw Versus Canonical Action

The intended contract is not "free raw text first, then convert it into the action we wanted."

The Teacher is required to output the canonical action JSON directly. The runtime then performs parse, schema validation, reference validation, runtime validation, and instruction-quality validation. If any required field is missing or invalid, the action is rejected and no image/tool execution happens.

The accepted canonical action is the parsed and validated JSON object from the Teacher. The runtime must not fill missing fields, rename fields, change the selected action, repair invalid IDs, or rewrite the instruction to make it executable.

`raw_teacher_outputs` is kept for audit, debugging, and SFT masking. It is not persistent memory and is not a positive assistant target.

## Per-Turn Teacher I/O Matrix

Every row below contains the shared base input fields listed above. The table only calls out the fields that changed or mattered for that turn.

| Teacher turn | Planner input state | Visible image fields | Extra observation / feedback field | Raw Teacher output | Canonical result |
| --- | --- | --- | --- | --- | --- |
| `turn_000` | `planner_view_000`: original prompt, 11 atoms, budget `5`, empty `compact_history`, no active Skills | none | no image exists yet | `query_skill` for counting and spatial Skills | accepted, Skill Markdown returned |
| `turn_001` | `planner_view_001`: same prompt/atoms/budget, active retrieved Skills present | none | no image exists yet | `generate_image` with useful prompt rewrite but missing required `mode` | schema rejected, no image attempt |
| `turn_002` | `planner_view_002`: no attempts yet, active Skills present, budget still `5` | none | no image exists yet | `generate_image`, `mode: initial`, all atoms targeted | accepted, produced `a_000` |
| `turn_003` | `planner_view_003`: latest/best `a_000`, history length `1`, failed atoms `c_001,c_002,c_004,c_005,c_008`, budget `4` | `LATEST_IMAGE` / `BEST_IMAGE` = `img_000` | latest transition from `a_000` evaluation | `generate_image`, cleaner exact-count regeneration | accepted, produced `a_001` |
| `turn_004` | `planner_view_004`: latest/best `a_001`, history length `2`, failed atoms `c_001,c_004,c_008`, budget `3` | `LATEST_IMAGE` / `BEST_IMAGE` = `img_001` | latest transition from `a_001` evaluation | `edit_image` from `a_001`, add lions and repair relations | linter rejected, no image attempt |
| `turn_005` | `planner_view_005`: same canonical state as `turn_004` | `img_001` | validation rejection not injected strongly enough | `edit_image` from `a_001`, revised wording | linter rejected, no image attempt |
| `turn_006` | `planner_view_006`: same canonical state as `turn_004` | `img_001` | validation rejection not injected strongly enough | `edit_image` from `a_001`, revised wording | linter rejected, no image attempt |
| `turn_007` | `planner_view_007`: same canonical state as `turn_004` | `img_001` | validation rejection not injected strongly enough | `edit_image` from `a_001`, revised wording | linter rejected, no image attempt |
| `turn_008` | `planner_view_008`: same canonical state as `turn_004`, budget still `3` | `img_001` | latest stable passes and persistent failures visible | `edit_image` from `a_001`, targets `c_001,c_004,c_008` | accepted, produced `a_002` |
| `turn_009` | `planner_view_009`: latest/best `a_002`, history length `3`, failed atoms `c_004,c_008`, budget `2` | `LATEST_IMAGE` / `BEST_IMAGE` = `img_002` | latest transition from `a_002` evaluation | `edit_image` from `a_002`, relation-focused repair | accepted, produced `a_003` |
| `turn_010` | `planner_view_010`: latest `a_003`, best `a_002`, history length `4`, budget `1`, regression `c_002` visible | `LATEST_IMAGE` = `img_003`, `BEST_IMAGE` = `img_002` | latest transition marks `a_003` worse than best | `edit_image` from `a_002`, not latest `a_003` | accepted, produced `a_004` |
| `turn_011` | `planner_view_011`: latest `a_004`, best `a_002`, budget `0`, full five-attempt history | `LATEST_IMAGE` = `img_004`, `BEST_IMAGE` = `img_002` | budget exhausted, submit best available | `submit_attempt` selecting `a_002` | accepted, final submission |

This is the clearest way to read the trajectory:

1. `PlannerView` is the structured agent state given to the Teacher.
2. `visible_images` is the image evidence available to the Teacher.
3. `raw Teacher output` is the model's proposed action text.
4. `canonical result` is what the runtime accepted after schema/reference/runtime/instruction validation.

## Raw `stop` Fields

The repeated `finish_reason: "stop"` entries in `raw_teacher_outputs*.jsonl` are normal model-provider metadata.

`stop` means the model finished generation normally. It does not mean:

- the action is valid;
- the trajectory stopped;
- the Teacher chose `submit_attempt`;
- the output passed our schema or instruction-quality gate.

For example, the invalid turn missing `mode` also has `finish_reason: "stop"` because the model completed its text response normally, but our action parser rejected it afterward.

## Round-by-Round I/O

### Turn 000: Skill Query

Input state:

- no image attempts;
- remaining budget `5`;
- no visible images;
- skill manifest available;
- extra observation says no image exists yet.

Teacher output:

```json
{"action":"query_skill","skill_ids":["counting_and_instance_layout","spatial_relation_layout"]}
```

Runtime result:

- accepted;
- returned full Skill Markdown for counting and spatial layout;
- compact active operator summaries remain in later PlannerViews.

Why this is good:

- it uses foundational Skills before constructing image instructions;
- it does not query edit-strategy Skills or encode retry policy into Skills.

### Turn 001: First Generate Attempt, Rejected

Input state:

- no image attempts;
- remaining budget `5`;
- full retrieved Skill Markdown in context;
- active Skill operators available.

Raw Teacher output:

- `generate_image`;
- good concrete `generation_instruction`;
- missing required `mode`.

Runtime result:

- rejected by action schema;
- no image attempt consumed.

Interpretation:

- the prompt rewrite content was already useful;
- the output format constraint was not strong enough to prevent a missing required field.

### Turn 002: First Accepted Generation, `a_000`

Input state:

- no image attempts;
- remaining budget `5`;
- active counting/spatial operators;
- no visible images.

Teacher output:

- `generate_image`;
- `mode: initial`;
- targets all constraints;
- instruction specifies exactly one donut, three red cats behind donut, six glass lions chasing cats, no extra/cropped/fused/reflected duplicates.

Image/evaluator result:

- produced `a_000`;
- passed 6/11;
- failed lion count, glass uncertainty, chasing, cat count, cats behind donut.

Transition:

- best becomes `a_000`;
- remaining budget `4`.

### Turn 003: Second Generation, `a_001`

Input state:

- latest/best `a_000`;
- visible image: `LATEST_IMAGE/BEST_IMAGE` for `a_000`;
- compact history contains `a_000`;
- per-atom failures identify count, material uncertainty, chasing, cat count, behind relation.

Teacher output:

- `generate_image`;
- creates a cleaner white studio layout;
- exact foreground/midground/background structure;
- exact counts and no extra objects.

Image/evaluator result:

- produced `a_001`;
- passed 8/11;
- fixed glass and cat count;
- persistent failures: lion count, chasing, cats behind donut.

Transition:

- best becomes `a_001`;
- remaining budget `3`.

Why this is good:

- the Teacher used attempt history to switch from the previous weaker layout to a cleaner regeneration;
- it preserved the prompt rewrite style from Skills.

### Turns 004-007: Raw Edit Attempts Rejected

Input state:

- latest/best `a_001`;
- visible image: `a_001`;
- compact history contains `a_000`, `a_001`;
- persistent failures: `c_001`, `c_004`, `c_008`;
- stable passes include glass, cat count, red cats, donut count/color/object.

Raw Teacher intent:

- edit `a_001`;
- add missing lions to reach six;
- repair chasing and cats-behind-donut relation;
- preserve stable passes.

Runtime result:

- rejected by instruction-quality gate.

Important diagnosis:

- these were mostly false positives from the linter, not obviously bad Teacher plans;
- the old linter misread operation counts like "add exactly two additional lions so there are exactly six" as incompatible final count claims;
- it also treated reciprocal depth wording like "cats behind donut; donut in front of cats" as contradiction.

Correction applied during the run:

- linter now distinguishes operation count from final count;
- reciprocal depth statements are no longer treated as contradictions by default;
- the run resumed from the same episode without reusing or rerunning completed valid image attempts.

Current limitation:

- validation rejections are recorded in the event log, but the specific rejection payload was not consistently injected into the next Teacher text input. This weakens self-repair and should be tightened before larger batches.

### Turn 008: Accepted Edit, `a_002`

Input state:

- latest/best `a_001`;
- compact history includes `a_000`, `a_001`;
- visible image `a_001`;
- remaining budget `3`;
- active counting/spatial operators.

Teacher output:

- `edit_image`;
- source `a_001`;
- targets `c_001`, `c_004`, `c_008`;
- preserves glass, lion object, cat count, red cats, cat object, donut count/color/object;
- instruction adds exactly two transparent glass lions so final lion count is six;
- also tries to repair chasing and behind relation.

Image/evaluator result:

- produced `a_002`;
- passed 9/11;
- fixed lion count;
- persistent failures: chasing and cats behind donut.

Transition:

- best becomes `a_002`;
- remaining budget `2`.

Why this is good:

- edit targets only failed atoms and locks stable atoms;
- it demonstrates the desired "local repair from improved attempt" behavior.

### Turn 009: Relation-Focused Edit, `a_003`

Input state:

- latest/best `a_002`;
- compact history includes three attempts;
- failures only `c_004`, `c_008`;
- remaining budget `2`.

Teacher output:

- `edit_image`;
- source `a_002`;
- targets only chasing and cats-behind-donut relation;
- preserves all nine passing constraints.

Image/evaluator result:

- produced `a_003`;
- still failed chasing and behind relation;
- regressed glass material `c_002`;
- passed 8/11.

Transition:

- best remains `a_002`;
- latest becomes `a_003`;
- remaining budget `1`.

Why this matters:

- this creates the key history-aware test: latest is worse than best.

### Turn 010: Branch From Best, `a_004`

Input state:

- latest `a_003`;
- best `a_002`;
- visible images include both latest and best;
- compact history includes `a_003` regression;
- latest transition records `c_002` regressed;
- remaining budget `1`.

Teacher output:

- `edit_image`;
- source `a_002`, not latest `a_003`;
- targets only `c_004`, `c_008`;
- preserves the nine passing atoms from best.

Image/evaluator result:

- produced `a_004`;
- passed 9/11;
- still failed chasing and cats behind donut;
- did not beat `a_002`.

Transition:

- best remains `a_002`;
- latest becomes `a_004`;
- remaining budget `0`.

Why this is good:

- this is the strongest evidence that the Teacher used attempt history and best-so-far state;
- it avoided continuing from a regressed latest image.

### Turn 011: Submit Best

Input state:

- budget exhausted;
- latest `a_004`;
- best `a_002`;
- visible images include both latest and best;
- extra observation explicitly instructs `best_available_under_budget`.

Teacher output:

```json
{"action":"submit_attempt","selected_attempt_id":"a_002","reason_code":"best_available_under_budget"}
```

Runtime result:

- accepted;
- submitted `a_002`.

Why this is good:

- submits historical best instead of latest;
- respects budget semantics;
- uses the canonical reason code.

## Comparison With Gen-Searcher / GenEvolve-Style Format Discipline

Current Gen-Retry v3 has several strong constraints:

- strict canonical action schema;
- exactly one executable action per accepted turn;
- no separate `refine_prompt` action;
- schema validation;
- runtime validation;
- instruction-quality validation;
- canonical event history;
- deterministic reducer-owned best/latest/budget state;
- trace exporter showing Teacher input, raw output, canonical action, Qwen input, evaluator output, transition, and submission.

But the constraints are still weaker than a hard tool/function/program interface in two ways:

1. The Teacher is still producing raw JSON text through an OpenAI-compatible chat API. Invalid JSON-shaped actions can finish with `finish_reason: "stop"` and only fail after our parser/linter runs.
2. Repair feedback is not yet strong enough. The runtime records validation errors, but the next Teacher request should include the exact structured rejection observation more directly and consistently.

What to strengthen next:

- use provider-level structured output or tool/function calling if the GPT-5.5 endpoint supports it;
- add action-specific mini templates immediately before each decision, especially for `generate_image` requiring `mode`;
- inject the previous validation rejection payload into the next Teacher input, not just the event log;
- keep the instruction-quality linter, but avoid overfitting lexical patterns that reject semantically valid instructions;
- expose rejected raw turns in a separate "raw repair appendix" so canonical traces remain clean while debugging remains transparent.

## Bottom Line

For training/demo structure, this is the kind of trajectory we want.

It demonstrates:

- skill-conditioned prompt construction;
- image-aware and verifier-grounded retry;
- atom-targeted edits;
- preservation locks;
- best-so-far branching;
- budget-aware submission.

It does not yet prove:

- the Teacher will rarely make raw format mistakes;
- the linter is fully calibrated;
- the model can solve the hardest visual relations reliably.

The highest-priority engineering improvement is to make validation-error feedback explicit in the next Teacher input and, if available, move from raw JSON text generation to provider-enforced structured output.
