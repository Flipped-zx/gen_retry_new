# Persistent Worker And Concurrency Design

Date: 2026-07-15

Status: design only. No worker implementation, Qwen-Image-Edit call, Geneval2 call, teacher rollout call, or trajectory execution was run for this review.

## Current Runtime Issue

`src/gen_retry/tools/qianwen_image_edit_adapter.py` currently calls `_load_pipeline()` inside each uncached image `_run()` and deletes the pipeline in `finally`. That is correct for a simple smoke/pilot adapter, but it wastes time for multi-attempt trajectories.

Current strengths to preserve:

- deterministic artifact destination: `images/<image_artifact_id>.png`;
- cache hit behavior when output already exists;
- one adapter supports both logical `generate_image` and `edit_image`;
- metadata records provider, runtime, size, steps, CFG, guidance, and seed.

## Required Architecture

```text
Episode scheduler
  -> teacher API request queue
  -> persistent Qwen-Image-Edit worker
  -> Geneval2 evaluation queue
  -> reducer
  -> next PlannerView
```

Within one episode, dependent rounds stay sequential:

```text
teacher action -> image job -> Geneval2 job -> reducer -> next PlannerView
```

Across episodes, independent teacher work, image work, and evaluation may be pipelined if resources allow.

## Image Job Contract

Every image job should include:

- `job_id`
- `episode_id`
- `action_event_id`
- `request_id`
- `attempt_id`
- `operation`: `generate` or `edit`
- `idempotency_key`
- deterministic output path
- source image path for edits
- instruction text
- render parameters
- expected artifact manifest entry
- cache/resume status

The idempotency key should be derived from:

- episode ID;
- action event ID;
- operation;
- attempt ID;
- source attempt/image hash for edits;
- instruction hash;
- model path/version;
- render parameters;
- seed;
- output path.

If the deterministic output exists and the manifest/hash match, the job returns `cache_hit=True` and does not rerun Qwen.

## Option A: In-Process Long-Lived Worker

Design:

- Create a `PersistentQwenImageEditWorker` owned by the rollout process.
- Load `QwenImageEditPlusPipeline` once during worker startup.
- Submit `ImageJob` objects through a single-consumer in-process queue or a worker-owned lock.
- Use one worker per configured GPU or GPU group.
- Guarantee one in-flight Qwen invocation per loaded pipeline.
- Reuse the same loaded pipeline for both `generate_image` and `edit_image`.
- Keep existing artifact/cache semantics.

Assessment:

| Dimension | Assessment |
| --- | --- |
| Implementation effort | Moderate; smallest change from current adapter |
| Model-load lifetime | Loaded once per worker process |
| Failure isolation | Lower; a fatal pipeline/GPU error can affect the rollout process |
| Resume behavior | Good if artifact cache and manifest checks remain authoritative |
| Suitability for one fresh validation trajectory | Best immediate choice |

Recommendation for first Skill-v1 validation trajectory: use Option A after approval. It minimizes moving parts and prioritizes correctness over throughput.

## Option B: Local Persistent Service Worker

Design:

- Run Qwen-Image-Edit as a local service, similar to Gen-Searcher/GenEvolve evidence.
- Keep one loaded model per GPU or endpoint.
- The rollout scheduler sends image jobs over HTTP or IPC.
- Service owns queueing, per-GPU locks, single-flight pipeline invocation, health checks, reload, and timeout handling.

Assessment:

| Dimension | Assessment |
| --- | --- |
| Implementation effort | Higher; requires service lifecycle, request schema, auth/local access policy, logs, and health checks |
| Process isolation | Better; model crashes do not necessarily kill the scheduler |
| Queueing | Better for multi-episode batches and multi-GPU scheduling |
| Multi-episode throughput | Better once stable |
| Suitability for later batch construction | Best later-scale choice |

Recommendation for later scale: implement Option B after the first Skill-v1 validation trajectory proves the Skill design is useful.

## Concurrency Policy

Default GPU policy:

- one Qwen worker per configured GPU or GPU group;
- one in-flight Qwen invocation per loaded pipeline, enforced by a single-consumer queue or lock;
- do not run multiple local Qwen workers on the same GPU by default;
- do not lower image quality to increase throughput;
- preserve `40` steps, `1024 x 1024`, `true_cfg_scale=4.0`, `guidance_scale=1.0` unless an approved evidence-backed change is made.

Teacher API:

- teacher calls can be queued and pipelined across episodes subject to API/rate limits;
- teacher calls must not continue beyond prepared episodes or user-approved validation scope.

Geneval2:

- before first validation, check whether persistent Qwen and Geneval2 can co-reside in GPU memory under the chosen model/offload settings;
- if co-residency fails, use a separate GPU/service for Geneval2 or a verified offload path that keeps the Qwen pipeline loaded and preserves the load-once worker invariant;
- if Geneval2 and Qwen share a GPU and co-residency is viable, enforce serialization with one scheduler-owned GPU lock spanning both Qwen and Geneval2 queues;
- allow concurrent Qwen and Geneval2 only when they use separate hardware/services or profiling proves no harmful contention;
- preserve evaluator idempotency through report path and report hash.

First validation trajectory:

- run one fresh episode only;
- one persistent in-process Qwen worker;
- serialize Qwen and Geneval2 if they share the GPU;
- keep episode turns sequential;
- do not run a batch until the user reviews the validation evidence.

## Resume Behavior

On resume:

- scan events and manifest before queueing jobs;
- if `image_execution_completed` exists and image artifact hash matches, skip image job;
- if image exists but completion event is missing, require a repair/reconciliation path before treating it as complete;
- if `image_execution_started` exists without completion, requeue only after checking deterministic output/cache state;
- publish image artifacts atomically: write to a temporary path, fsync/close, rename into the deterministic destination, then compute hash and append manifest/completion events;
- recognize cache or manifest completion only after the final artifact path and recorded hash agree;
- never repeat completed expensive jobs merely to obtain preferred behavior.

## Recommendation

Immediate implementation after approval: Option A, in-process persistent worker.

Later implementation: Option B, local persistent service worker for multi-episode throughput and better process isolation.
