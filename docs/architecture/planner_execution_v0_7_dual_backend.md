# Planner Execution v0.7 Candidate: Qwen Dual-Backend Profile

Status: accepted and implemented by ADR-0006. Live diagnostics are recorded in
`docs/status.md`; this document preserves the original design rationale.

## Version boundary

The Action protocol remains v0.5. New rollouts now use PlannerContext v0.7;
v0.6 and earlier PlannerContext versions remain immutable replay/resume modes.

This v0.7 proposal is deliberately limited to image-action execution semantics.
It does not depend on a v0.6 schema and does not add fields to the canonical
Planner Action. The implementation uses independent version axes:

```text
action_protocol_version: "0.5"
planner_context_version: "0.5"
execution_profile_id: "qwen_dual_backend"
execution_profile_version: "1"
```

The example above records the proposal's original version tuple. Current
episodes persist their actual PlannerContext version and the same independent
execution-profile ID/version; no backend field is added to the Action.

## Human workflow being modeled

Gen-Retry models the operations a person would use to complete one image task:

```text
generate a fresh image
-> inspect verifier feedback
-> edit a useful existing image, regenerate from scratch, or submit
-> optionally roll back to a historical best image before editing
```

The Planner chooses the logical operation. The environment owns backend
selection, model loading, image artifacts, evaluation, scores, lineage, and
budget accounting.

## Frozen logical action space

The action space remains:

```text
query_skill
generate_image
edit_image
submit_attempt
```

No `refine_prompt`, `regenerate_image`, `mode`, or model-selection action is
added.

### `generate_image`

- Has no `source_attempt_id`.
- May be used for the first image or for a later source-free restart.
- Executes through local `Qwen-Image-2512`.
- Creates a new root Attempt with no image parent.

### `edit_image`

- Requires a valid historical `source_attempt_id`.
- May use latest or any historical best Attempt as its source.
- Executes through local `Qwen-Image-Edit-2511`.
- Creates a child Attempt whose parent is the declared source.

### `submit_attempt`

- May submit latest or a historical best Attempt.
- Does not invoke either image backend.

## Why backend choice is not an action field

The Planner already expresses the meaningful decision through
`generate_image` versus `edit_image`. Adding `backend`, `model_id`, or `mode`
would duplicate that decision and create unnecessary SFT targets.

The deterministic environment routing is:

```text
generate_image -> qwen_image_2512
edit_image     -> qwen_image_edit_2511
```

Backend and model provenance must be persisted in environment-owned execution
events and artifact metadata.

## Prompt semantics

The shared canonical field remains `arguments.instruction`, but its executable
meaning differs by action:

- A generation instruction must be self-contained and describe the complete
  desired image. It cannot refer to preserving pixels or objects from an
  unavailable source image.
- An edit instruction must identify the intended local changes and explicitly
  preserve already-correct visible content from the declared source image.

During the first diagnostic comparison, new action-specific instruction checks
are warning-only. Existing v0.5 schema and reference validation remain the only
protocol-validity rules. A future deterministic hard rule would require a
separate Action Protocol change and tests.

## Compatibility

- Existing v0.5 actions remain structurally valid.
- Existing trajectories retain their recorded legacy backend provenance and
  are never rewritten.
- New dual-backend trajectories must record an execution-profile version so
  legacy edit-only and dual-backend results cannot be silently mixed.
- PlannerContext, reducer selection, Geneval2, image-attempt budget, Skill
  content, and SFT masking remain unchanged unless separately approved.

## Required execution provenance

Every image execution must persist environment-owned provenance equivalent to:

```json
{
  "execution_profile_id": "qwen_dual_backend",
  "execution_profile_version": "1",
  "logical_action": "generate_image",
  "backend_id": "qwen_image",
  "model_id": "Qwen-Image-2512",
  "model_revision_or_fingerprint": "...",
  "pipeline_id": "QwenImagePipeline",
  "adapter_version": "1",
  "sampling": {
    "seed": 0,
    "num_inference_steps": 50,
    "true_cfg_scale": 4.0,
    "guidance_scale": null,
    "width": 1024,
    "height": 1024
  },
  "source_attempt_id": null,
  "source_artifact_digest": null,
  "result_attempt_id": "a_000",
  "output_artifact_digest": "..."
}
```

The edit form records `backend_id=qwen_image_edit`,
`pipeline_id=QwenImageEditPlusPipeline`, a real source Attempt and source
artifact digest, and its edit sampling parameters.

Required invariants:

1. One episode is locked to one execution profile from preparation through
   submission and resume.
2. `generate_image` routes only to Qwen-Image, has no source, and creates a root
   Attempt.
3. `edit_image` routes only to Qwen-Image-Edit, has a valid source artifact,
   and creates a child Attempt.
4. The Teacher system prompt describes this capability mapping, but backend
   provenance never enters the assistant target.
5. SFT export filters or groups records by execution profile.
6. Legacy edit-only generation instructions and dual-backend generation
   instructions are never silently mixed as one homogeneous training source.

## Local model evidence

- Text-to-image model:
  `/root/private_data/agentic_image/models/Qwen-Image-2512`
- Editing model:
  `/root/private_data/agentic_image/models/Qwen-Image-Edit-2511`
- The Qwen-Image-2512 model card identifies `QwenImagePipeline`, uses
  source-free text-to-image generation, and recommends 50 inference steps with
  `true_cfg_scale=4.0`.
- Existing Qwen-Image-Edit quality evidence uses 40 inference steps,
  `true_cfg_scale=4.0`, `guidance_scale=1.0`, and a source image.

## Initial comparison scope

The first comparison is diagnostic, not a benchmark claim. It reuses five
frozen, previously difficult Flow-DPPO prompts and compares:

1. legacy edit-only execution;
2. v0.7 dual-backend execution.

Each prompt runs once under each profile, producing ten complete adaptive
trajectories. Both arms use the same prompt set, image-attempt cap, Teacher
policy, Skills, Geneval2 evaluator, submission policy, and reporting. Report
initial and submitted GM/AM, per-attempt action/backend routing, atom
transitions, image calls, GPU-seconds, and any failure or resume events.

Because the initial images differ by backend, the adaptive comparison estimates
the whole execution-profile effect. Renderer attribution is restricted to a
separate paired first-generation test:

1. Freeze the original canonical first `generate_image.instruction` and seed
   for each of the five prompts.
2. Send the identical instruction and seed to white-canvas
   Qwen-Image-Edit-2511 and source-free Qwen-Image-2512.
3. Evaluate both outputs with the same Geneval2 configuration.
4. Attribute only these paired first-generation differences to the
   source-free renderer configuration.

At least one fixed source image, edit instruction, and seed must also be routed
through both profiles to verify that `edit_image` resolves to the same
Qwen-Image-Edit configuration.

## Non-goals

- No live trajectory in the design step.
- No claim that v0.7 improves Geneval2 before matched evidence exists.
- No change to the official Geneval2 held-out split.
- No replacement of Qwen-Image-Edit for source-conditioned edits.
- No conversion of old trajectories to new backend provenance.
