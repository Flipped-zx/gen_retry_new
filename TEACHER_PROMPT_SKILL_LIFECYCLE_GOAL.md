# TEACHER PROMPT + SKILL LIFECYCLE + EDIT INSTRUCTION CONTRACT GOAL
## Stop before live execution and ask for user confirmation

Repository:

`/root/private_data/agentic_image/gen_retry_new`

Legacy repository:

`/root/private_data/agentic_image/gen-retry`

External repositories are strictly read-only.

---

# 0. Current state

The project already has:

- approved canonical protocol and deterministic replay;
- completed Phase 3 trajectories;
- a working `query_skill -> SKILL.md -> tool observation -> next PlannerView` chain;
- foundational Skill v1 trace/I/O approval;
- one validation trajectory showing repeated Skill queries and uneven edit-instruction quality.

This file replaces all earlier unexecuted Skill/Teacher prompt goals.

Do not rerun any live trajectory in this task.

Do not modify completed trajectory artifacts.

Do not activate a new Skill catalog yet.

Do not change the frozen action schema unless a concrete correctness defect is demonstrated.

---

# 1. Objective

Freeze three things before running the next fresh validation trajectory:

1. Teacher system prompt and multimodal input contract.
2. Skill lifecycle and no-repeat retrieval policy.
3. Edit/generation instruction construction contract.

The core design boundary is:

- Skills teach how to operationalize count, spatial, attribute, and preservation constraints.
- The retry policy decides whether to generate, edit, branch, continue, or submit.
- Every generate/edit action must contain the exact instruction sent to Qwen-Image-Edit.
- The Teacher must see the relevant current image, best image when different, Geneval2 feedback, compact history, and active Skill operators.

---

# 2. Role split

## GPT-5.5 High/XHigh

Use for:

- repository inspection;
- source-grounded evidence extraction;
- Teacher prompt drafting;
- edit-instruction contract design;
- Skill lifecycle design;
- trace-export redesign;
- tests and mock validation;
- preparing the review packet.

## Source researcher: GPT-5.5 High, read-only

Inspect only the minimum relevant sources:

- current Teacher prompt and message builder;
- PlannerView builder;
- Skill store and Skill tool observations;
- current trajectory trace and behavior analysis;
- completed Phase 3 action/outcome evidence;
- GEMS Skill-loading conventions already recorded in the Source Ledger;
- GenEvolve trajectory/program conventions already recorded in the Source Ledger;
- Gen-Searcher heavy-model service organization already recorded in the Source Ledger;
- official Qwen-Image-Edit instruction/prompt guidance already available locally or in the Source Ledger.

Do not repeat broad searches.

## GPT-5.6 Sol XHigh, read-only

Review exactly:

1. Does the Teacher prompt correctly separate foundational Skills from retry-policy decisions?
2. Is the edit/generation instruction contract concrete enough to prevent vague or contradictory rewrites?
3. Is the Skill retention policy efficient and auditable?

Return exactly:

- `APPROVE`
- `REQUEST_CHANGES`
- `BLOCKED`

Allow one scoped correction cycle.

---

# 3. Part A — Audit the current trajectory prompts

Use the completed trajectory containing:

`phase3_ep_001`

Audit every image-execution instruction:

- initial generation instruction;
- first edit instruction;
- second edit instruction;
- third edit instruction;
- best-so-far branch edit instruction.

For each instruction, record:

- target atoms;
- preservation atoms;
- source attempt;
- concrete object operations;
- spatial anchors;
- count constraints;
- ambiguous phrases;
- contradictions;
- missing preservation details;
- unsupported new content;
- whether the instruction is too global for a local edit;
- actual outcome;
- fixed/regressed/persistent result.

Classify each instruction:

- `strong`
- `usable_but_risky`
- `too_vague`
- `contradictory`
- `overbroad`
- `unsupported`

Required output:

`docs/teacher_prompt_design/CURRENT_EDIT_INSTRUCTION_AUDIT.md`

---

# 4. Part B — Freeze the Teacher input contract

Every Teacher decision must receive:

1. System policy version/hash.
2. Original Prompt.
3. Atomic constraints with IDs.
4. Latest Geneval2 atom results.
5. Latest attempt summary.
6. Best attempt summary.
7. Compact attempt history.
8. Fixed / regressed / persistent / stable-pass state.
9. Remaining budget.
10. Active Skill operators.
11. Tool capabilities.
12. Latest image as an actual multimodal image input.
13. Best image as an actual multimodal image input when best differs from latest and is decision-relevant.

The Teacher request must clearly label:

- `LATEST_IMAGE`
- `BEST_IMAGE`
- source attempt IDs
- whether latest equals best

The Teacher must never receive only a path string when an image is required for decision-making.

Required output:

`docs/teacher_prompt_design/TEACHER_MULTIMODAL_INPUT_CONTRACT.md`

Add tests proving:

- latest image enters the actual API request;
- best image enters when required;
- image order and labels are unambiguous;
- compact history and active Skills are present;
- secrets are redacted.

---

# 5. Part C — Freeze the Teacher system prompt

The Teacher system prompt must enforce:

## Role

You are a verifier-grounded multimodal image retry planner.

## Goal

Maximize the best valid attempt under the remaining image-attempt budget.

## Skill semantics

- Skills provide operational guidance for constructing generation/edit instructions.
- Skills do not decide edit versus regenerate, branch versus latest, or continue versus submit.
- Query only a Skill version that is not already active or when a genuinely new capability is needed.
- Apply retrieved operators in the next image action.

## Image grounding

- Use the visible images and Geneval2 feedback together.
- Do not invent unsupported visual observations.
- Compare latest and best images when they differ before selecting a source.

## History

- Use fixed, regressed, persistent, and repeated-strategy history.
- Do not blindly continue from the latest attempt.
- Do not repeat a materially equivalent ineffective instruction without a concrete change.

## Output

Output exactly one canonical action JSON.
No prose.
No chain-of-thought.

Required output:

`docs/teacher_prompt_design/TEACHER_SYSTEM_PROMPT_V1.md`

---

# 6. Part D — Freeze Skill lifecycle

Implement or specify:

1. Full Skill Markdown is returned after the first successful query.
2. A compact deterministic operator summary remains active for later turns.
3. The same Skill ID/version/hash may be retrieved at most once per episode by default.
4. At most two Skills per query.
5. Consecutive query-only actions are forbidden.
6. A repeated failure of the same capability is not sufficient reason to retrieve the same Skill again.
7. A new query is allowed only for:
   - a new capability;
   - a Skill not already active;
   - a changed Skill version/hash;
   - demonstrated absence of a required operator.
8. Log:
   - Skill ID;
   - version;
   - content hash;
   - retrieval turn;
   - active operators;
   - downstream action ID.

Do not encode edit/regenerate strategy into foundational Skills.

Required output:

`docs/teacher_prompt_design/SKILL_LIFECYCLE_POLICY_V1.md`

Add unit tests for:

- duplicate Skill retrieval rejection;
- two-Skill maximum;
- no consecutive query loop;
- active operator retention;
- version/hash behavior.

---

# 7. Part E — Freeze the image-instruction construction contract

Do not add a separate `refine_prompt` action.

The image instruction is part of the canonical `generate_image` or `edit_image` action.

## 7.1 Generation instruction contract

A `generation_instruction` must include, when relevant:

1. exact requested entities and counts;
2. entity-specific attributes;
3. explicit spatial layout;
4. relation/orientation/depth cues;
5. visibility and separation requirements;
6. prohibition of extras, duplicates, fusion, reflection artifacts, and cropped instances;
7. all original constraints that must be satisfied.

## 7.2 Edit instruction contract

An `edit_instruction` must contain four semantic blocks:

### A. Target operation

- exact object(s) or region(s) to modify;
- exact add/remove/reposition/attribute operation;
- exact final state.

### B. Spatial grounding

- bounded region or relative position;
- subject/object orientation;
- depth or occlusion requirements when relevant.

### C. Preservation lock

- explicit stable passed constraints that must remain unchanged;
- preserved entities, counts, materials, colors, relations, background, composition;
- source attempt identity.

### D. Forbidden changes

- no extra instances;
- no unrelated object changes;
- no background redraw unless required;
- no broad scene reconstruction under a local edit action.

The instruction must not rely only on vague phrases such as:

- “fix the failed parts”
- “preserve all correct evidence”
- “make the image satisfy the constraints”
- “adjust as needed”

These phrases may appear only after concrete targets and preservation locks are stated.

## 7.3 Contradiction checks

Reject or repair instructions that:

- conflict with the original Prompt;
- contain ambiguous direction such as “forward toward/behind” without a clear frame/depth interpretation;
- request incompatible counts;
- preserve and modify the same property without clarification;
- introduce unsupported entities or attributes;
- use a local edit action for an instruction that effectively reconstructs the whole scene.

Required output:

`docs/teacher_prompt_design/IMAGE_INSTRUCTION_CONTRACT_V1.md`

---

# 8. Part F — Add instruction-quality validation

Implement a deterministic validator or linter outside the canonical action schema.

For every generate/edit action, report:

- target constraints referenced;
- preservation constraints referenced;
- exact count coverage;
- spatial grounding coverage;
- vague-language flags;
- contradiction flags;
- overbroad-edit flag;
- unsupported-content flag;
- source-attempt consistency;
- final verdict:
  - `pass`
  - `warn`
  - `reject`

The linter must not silently rewrite the Teacher output.

If a canonical action is rejected, return a structured validation observation so the Teacher can produce a corrected action.

Required outputs:

- `src/gen_retry/agent/instruction_quality.py`
- `docs/teacher_prompt_design/INSTRUCTION_QUALITY_VALIDATION.md`
- focused unit tests

---

# 9. Part G — Upgrade the human-readable trajectory trace

Keep immutable audit events unchanged.

Produce a human-readable turn trace showing:

1. System prompt version/hash.
2. Exact sanitized Teacher text input.
3. Atomic constraints.
4. Compact history table.
5. Latest/best state.
6. Visible image references and labels.
7. Retrieved full Skill or active compact operators.
8. Raw redacted Teacher output.
9. Canonical action.
10. Instruction-quality result.
11. Exact Qwen-Image-Edit input.
12. Output image.
13. Geneval2 atom table.
14. Fixed/regressed/persistent transition.
15. Latest/best/budget update.
16. Supervision assessment.

Required output:

`docs/teacher_prompt_design/HUMAN_READABLE_TRACE_FORMAT.md`

Update the trace exporter and add mock tests only.

Do not run a live trajectory in this task.

---

# 10. Part H — Sol review

Prepare:

`docs/reviews/gate3b_teacher_prompt_and_skill_lifecycle_packet.md`

Include only:

- one-page decision summary;
- current-instruction audit;
- final Teacher system prompt;
- image-instruction contract;
- Skill lifecycle policy;
- one sample turn rendered in the new trace format;
- no more than three review questions.

Invoke Sol.

If `REQUEST_CHANGES`, allow one scoped correction cycle.

---

# 11. Part I — User confirmation packet

After the final Sol verdict, create:

`docs/teacher_prompt_design/USER_CONFIRMATION_PACKET.md`

It must contain:

1. the main defects found in the existing trajectory prompts;
2. the final Teacher system-prompt rules;
3. the final edit-instruction four-block contract;
4. Skill no-repeat/retention policy;
5. exact files changed;
6. tests run;
7. Sol verdict;
8. selected fresh validation task;
9. exact live calls that will occur after approval;
10. maximum image attempts;
11. unresolved risks;
12. a clear yes/no confirmation request.

STOP after this packet.

Do not:

- run GPT-5.5 live rollout calls;
- run Qwen-Image-Edit;
- run Geneval2;
- execute a fresh trajectory;
- modify completed trajectory artifacts.

Return to the user for confirmation.
