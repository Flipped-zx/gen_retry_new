# Qwen Rendering Quality Baseline

## Rule

Do not use smoke-test rendering parameters for trajectories that will be analyzed, reviewed, or used as SFT evidence.

Future live rollouts should match the reference-rendering quality class used by Gen-Searcher and GenEvolve:

- `num_inference_steps`: 40
- `true_cfg_scale`: 4.0
- `guidance_scale`: 1.0
- `negative_prompt`: `" "`
- target resolution: long side around 1024, or 1024 x 1024 for square fresh-start canvases
- dtype: bfloat16 when using the local diffusers runtime

The prior ten Phase 3 trajectories were run at `512 x 512` and `4` steps for infrastructure throughput. Treat their image quality as low-quality pilot evidence, not as a measure of Qwen-Image-Edit capability.

## No Standalone Image Smoke By Default

Standalone image smoke tests spend real rendering opportunities and should not be part of the default live workflow.

Default preflight should verify only:

- teacher env visibility as SET/MISSING;
- teacher model ID and minimal sanitized teacher API call;
- local Qwen model path exists;
- adapter is `provider=local` and does not require an HTTP endpoint;
- Geneval2 path/config is visible.

If an image call is necessary, run it with explicit operator intent and production-like rendering parameters, or make the first real episode the validation point.

## New High-Quality Trajectory Runs

When making a new batch of trajectories, use this policy:

- create fresh run directories for the selected prompts;
- skip standalone image smoke by default;
- run a sanitized config preflight only;
- execute the first real episode as a counted trajectory;
- use `40` steps and `1024 x 1024` unless a reviewed source-backed reason changes the parameters;
- preserve all canonical action, PlannerView, raw redacted teacher output, image artifact, Geneval2 atom result, transition, best-so-far, and submission records.

Within a single trajectory, turns remain sequential because each planner action depends on canonical history. Across different episodes, run in parallel whenever resources allow.

Recommended parallelization:

- episode-level parallelism is the default target;
- assign at most one local Qwen renderer process per GPU unless a service wrapper proves higher safe concurrency;
- if using service endpoints, run one worker per endpoint and dispatch episodes round-robin;
- teacher calls may run concurrently subject to rate limits;
- Geneval2 evaluation may run concurrently only when evaluator GPU/model memory permits;
- if resource pressure appears, reduce worker count rather than lowering image quality.

Do not rerun a valid trajectory just to obtain preferred behavior. If higher-quality evidence is needed, create a new fresh trajectory batch and mark the old low-quality pilot as historical evidence.

## External Evidence

Use `docs/SOURCE_LEDGER.md` section `Qwen-Image-Edit Configuration Evidence` when uncertain.

Recorded reference points:

- Gen-Searcher Qwen service: `Qwen/Qwen-Image-Edit-2509`, FastAPI, `num_inference_steps=40`, `true_cfg_scale=4.0`, `guidance_scale=1.0`.
- GenEvolve Qwen renderer: `Qwen/Qwen-Image-Edit-2511`, service/local debug, `num_inference_steps=40`, `true_cfg_scale=4.0`, `guidance_scale=1.0`, `long_side=1024`.

## Implementation Defaults

The v3 local adapter and rollout CLI should default to:

- `image_steps=40`
- `image_height=1024`
- `image_width=1024`

Lower values are allowed only when explicitly named as non-trajectory infrastructure checks and must not be used to judge model quality.
