# RL To model_deploy_10102 Environment Handoff

## 1. Scope And Reproduction Ref

This handoff records the RL-side baseline for comparison on
`model_deploy_10102`. It does not authorize package installation, Torch
replacement, live image calls, or an optimizer update.

- Reproduction branch: `main`; it was at
  `e29c63a19b448b2171a90a0a777eedf47b95b6e0` immediately before this handoff.
- Phase 8 RL scaffold baseline:
  `95c1441cf269fa9e037cc44dc27491b3e80a08d0` (`Add Phase 8 naive GRPO scaffold`).
- Inspection checkout on the RL host: `research/hpsv3-quality-guard`, commit
  `9533ba04e63badf8d3b3a5c2d162d02ac15dbd62`, with unrelated dirty/untracked
  work. Do not use this checkout as the reproduction ref.
- Fixed execution profile: `qwen_dual_backend@1`.
- Policy checkpoint: `runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42`.
- Policy model: Qwen3-VL-8B; `generate_image` routes to Qwen-Image-2512 and
  `edit_image` routes to Qwen-Image-Edit-2511.

Evidence labels used below:

- `REAL_HCU_PASS`: executed successfully on an allocated HCU and persisted.
- `CPU_OR_STATIC_PASS`: metadata, schema, unit, or CPU-side interface evidence.
- `NOT_RUN`: not executed and must not be inferred from a nearby check.
- `BLOCKED`: an accepted formal gate is not satisfied.

## 2. RL Host Environment

The environment used for the 2026-08-10 HCU evidence was activated as:

```bash
source /opt/dtk-26.04/env.sh
source /opt/hyhal/env.sh
source runs/rl_envs/torch290_py311/bin/activate
export PYTHONPATH=src
```

On 2026-08-11 `/opt/hyhal/env.sh` is no longer present and no HCU is currently
available. Therefore the historical HCU artifacts remain authoritative; a
same-day rerun is not claimed. `hipcc --version` currently reports DCC
`25.10.0-0`, clang 17, from `/opt/dtk-26.04`.

| Component | RL environment | Evidence/interpretation |
| --- | --- | --- |
| Python | `3.11.9` | metadata probe, executable `runs/rl_envs/torch290_py311/bin/python` |
| Torch | `2.9.0+das.opt1.dtk2604` | `REAL_HCU_PASS`; runtime reports HIP `6.3.26093` |
| HCU | 1 x `BW`, 68,702,699,520 bytes | `REAL_HCU_PASS` on 2026-08-10; unavailable on 2026-08-11 |
| vLLM | `0.11.0+das.opt1.dtk2604.torch290` | `REAL_HCU_PASS` model load and multimodal sampling |
| SGLang | not installed | not required by the diagnostic vLLM path; still named by the unamended formal YAML |
| sgl_kernel | not installed | no RL-host pass exists |
| verl | `0.6.1` | `REAL_HCU_PASS` interface resolution and `DataProto` tensorization |
| rLLM | not installed | no RL-host pass exists; current repository has an adapter plan, not an installed runtime |
| transformers | `4.57.6` | `REAL_HCU_PASS` independent multimodal reference scoring |
| Ray | `2.48.0` | `REAL_HCU_PASS` local start, remote task, and shutdown |
| xgrammar | `0.1.25` | distribution metadata present; no independent HCU claim |
| tvm-ffi | not installed | no RL-host pass exists |
| W&B | `0.28.1` | offline sanitized smoke passed |
| CuPy | `12.3.0` | real device arithmetic passed on 2026-08-10 |
| flash-attn | `2.8.3+das.opt1.dtk2604.torch290` | import/runtime passed; metadata differs from vLLM's declared `2.6.1` |
| flash-mla | not installed | no CPython 3.11 Torch-2.9 vendor wheel was found |
| lmslim | `0.4.0+das.opt1.dtk2604.torch290` | import passed; metadata differs from vLLM's declared `0.3.1` |

`pip check` currently reports exactly these packaging issues:

```text
vllm requires flash-mla, which is not installed
vllm requires flash_attn==2.6.1, installed metadata is 2.8.3+vendor build
vllm requires lmslim==0.3.1, installed metadata is 0.4.0+vendor build
```

These are packaging-closure failures, not evidence that the persisted vLLM HCU
smokes failed. Conversely, a clean `pip check` on 10102 is not evidence of an
HCU pass. Keep metadata and execution conclusions separate.

An earlier isolated probe of SourceFind SGLang packages found only Torch-2.5.1
builds. Pip tag compatibility was not the blocker, but importing the retained
Torch-2.5.1 `sgl_kernel` against Torch 2.9 aborted with
`std::length_error: vector::reserve`. Those packages were not installed into
the RL environment. 10102's claimed Torch-2.9 SGLang/sgl_kernel build must be
reported by its own exact wheel/version and safe-import evidence.

Do not run one aggregate import of Torch, vLLM, FlashAttention, SGLang, and
sgl_kernel on a node without its device/runtime libraries. On the RL node in
the current no-HCU state, that pattern aborted during compiled-extension
initialization with `hipErrorNoDevice`; it does not revise the earlier HCU pass.

## 3. What Has And Has Not Run

### `REAL_HCU_PASS`

- Frozen Qwen3-VL checkpoint loaded through vendor vLLM and returned `OK`.
- One real image-aware PlannerContext was rendered identically by Transformers
  and vLLM: 2,313 prompt token IDs and `image_grid_thw=[[1,64,64]]`.
- vLLM sampled a 345-token strict `edit_image` Action and persisted one finite
  old log-probability per sampled token.
- The Action passed JSON Schema, constraint-reference, source-Attempt, and
  runtime-legality validation.
- A separate Transformers scorer produced aligned reference log-probabilities.
- Two independent vLLM processes reproduced prompt IDs, sampled IDs, raw Action
  hash, and old log-probabilities exactly with seed 42.
- Ray, W&B offline redaction, device release, rollout admission, GRPO advantage
  joining, optimizer-batch preparation, and verl `DataProto` tensorization
  passed.

Primary evidence:

- `artifacts/rl/torch290_env_validation.json`
- `artifacts/rl/torch290_vllm_hcu_smoke.json`
- `runs/rl_runtime_probe_v0_1/vllm_model_smoke.json`
- `runs/rl_single_hcu_validation_v0_1/single_hcu_validation.json`
- `runs/rl_single_hcu_validation_v0_1/environment.json`
- `runs/rl_single_hcu_validation_v0_1/generation_first.json`
- `runs/rl_single_hcu_validation_v0_1/generation_replay.json`
- `runs/rl_single_hcu_validation_v0_1/reference_score.json`
- `runs/rl_single_hcu_validation_v0_1/optimizer_bridge_report.json`

### `CPU_OR_STATIC_PASS`

- Naive GRPO config and frozen 1,000/200/500 prompt manifests exist.
- Rollout/return/reward/advantage/runtime evidence Schemas validate.
- Terminal-only reward arithmetic, same-state GRPO advantages, stage admission,
  action-token mask/objective, persisted old/reference-logprob joins, W&B
  redaction, preflight, and runtime-gate unit tests pass.
- On the isolated `main + RL` tree: contract `82 passed`; unit `219 passed,
  11 skipped`; 22 schemas and 107 fixtures validated; canonical episode replay
  passed.

### `NOT_RUN` / `BLOCKED`

- No real multi-turn on-policy candidate episode has been collected.
- Qwen-Image-2512, Qwen-Image-Edit-2511, and Geneval2 were not executed by the
  single-HCU RL validation.
- The diagnostic four-candidate group duplicated one real Action and used
  synthetic rewards; it is join evidence, not learning evidence.
- No optimizer backward/update or RL checkpoint save has run.
- No live remote Qwen image adapter exists in the repository.
- No formal 32-group interruption/resume/replay smoke has run.
- Only one HCU was visible during the pass; the accepted formal topology names
  eight HCUs.
- `configs/rl/naive_geneval2_grpo_v0_1.yaml` still binds
  `rllm_verl_adapter + sglang`. Direct vLLM is technically validated below the
  live-adapter boundary, but the required ADR/config/schema/hash amendment has
  not been implemented or accepted as the formal runtime.

## 4. RL Rollout Boundary

The remote image service is an environment-owned image executor. It is not the
policy rollout engine, rLLM workflow manager, verl optimizer, Geneval2 scorer,
or canonical event store.

The intended division is:

```text
RL host: vLLM policy sampling + strict Action validation
  -> remote image service: generate/edit only
  -> RL host or separately declared evaluator: Geneval2
  -> RL host: immutable events + reducer + submitted terminal reward
  -> release rollout processes
  -> RL host: verl optimizer
```

For every policy decision the future collector must persist exact prompt/image
inputs, sampled token IDs, old/reference log-probabilities, tokenizer-derived
Action mask, canonical Action or typed policy-invalid result, state/policy/
sampling hashes, semantic request ID, and infrastructure retry records.

Policy-invalid output is a model outcome and receives the frozen negative
reward. Transport, image backend, or Geneval2 infrastructure failure retries
the same semantic request and, after exhaustion, excludes the entire prompt
group. Infrastructure failure must never become a legal zero reward.

## 5. Remote Qwen-Image Contract

The detailed design source on the RL inspection checkout is
`REMOTE_IMAGE_SERVICE_REQUIREMENTS.md`. It is a requirements draft, not an
implemented endpoint. The future client should read only these environment
variables; values must not enter YAML, events, artifacts, prompts, or logs:

```text
GEN_RETRY_IMAGE_SERVICE_BASE_URL
GEN_RETRY_IMAGE_SERVICE_TOKEN
```

### Common request contract

- TLS endpoint; `Authorization: Bearer $GEN_RETRY_IMAGE_SERVICE_TOKEN`.
- `Content-Type` and `Accept`: `application/json`.
- `Idempotency-Key`: canonical request digest.
- `X-Request-ID`: stable semantic request ID.
- `X-Execution-Profile: qwen_dual_backend@1`.
- UTF-8 strict JSON, `schema_version="1.0"`, unknown fields rejected, finite
  numbers only.

### Generate

`POST /v1/images/generations` with:

```json
{
  "schema_version": "1.0",
  "request_id": "<semantic request id>",
  "execution_profile": {"id": "qwen_dual_backend", "version": "1"},
  "instruction": "<non-empty executable instruction>",
  "sampling": {
    "seed": 0,
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "true_cfg_scale": 4.0,
    "negative_prompt": "<configured generation negative prompt>"
  },
  "output": {"count": 1, "format": "png", "transport": "inline_base64"},
  "wait": {"mode": "sync", "timeout_ms": 180000}
}
```

Generate must reject source, reference, and mask fields. It resolves only to
Qwen-Image-2512 / backend `qwen_image` / `QwenImagePipeline` and creates a root
Attempt.

### Edit

`POST /v1/images/edits` with the common fields plus:

```json
{
  "source": {
    "attempt_id": "a_000",
    "media_type": "image/png",
    "sha256": "<64 lowercase hex>",
    "b64_json": "<base64 without data-URI prefix>"
  },
  "references": [],
  "sampling": {
    "seed": 1,
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 40,
    "true_cfg_scale": 4.0,
    "guidance_scale": 1.0,
    "negative_prompt": " "
  }
}
```

Edit requires exactly one lineage source, currently no references or mask, and
resolves only to Qwen-Image-Edit-2511 / backend `qianwen_image_edit` /
`QwenImageEditPlusPipeline`. The response must echo the source attempt/digest
so the RL host can create the correct child Attempt.

### Success result

Success must return request/job/status/operation, idempotency replay status,
resolved model ID and revision/fingerprint, pipeline/adapter version, resolved
sampling, timing, and exactly one PNG output containing media type, dimensions,
byte length, SHA-256, and base64 bytes (or a separately allowlisted signed
artifact URI). The client must decode and verify PNG, dimensions, byte length,
and digest before atomic local commit. It must not accept arbitrary image URLs,
redirects, local paths, or unverified bytes.

### Health and capabilities

- `GET /healthz`: process liveness only; must not load a model.
- `GET /readyz`: dependencies, artifact store/queue, and declared model
  readiness; return 503 when not ready.
- `GET /v1/capabilities`: authenticated structured report containing API and
  service versions, exact model revisions, execution routes, transports,
  formats, dimension/pixel limits, output count, edit reference/mask support,
  seed determinism scope, timeouts, queue depth, and concurrency limits.

10102 can validate schemas, route isolation, and health/capability response
shape without a GPU. It cannot assert model readiness or output determinism.

### Idempotency and resume

- Same key + same canonical body returns the original job/result and
  `replayed=true`; it must not execute or charge twice.
- Same key + different body returns `409 idempotency_conflict`.
- Persist key/body-digest/job mapping before inference starts.
- Timeout or connection loss is an unknown execution state: query/retry with
  the same key, never create a new semantic request.
- Sync timeout may return `202` with job/status URL; polling uses
  `GET /v1/image-jobs/{job_id}`.

### Error semantics

All errors are structured JSON with `code`, safe `message`, `retryable`,
`request_id`, optional `job_id`, and bounded field details. Stable codes must
cover invalid request/image/digest/dimensions, unsupported operation/feature/
profile, authentication/permission, payload too large, idempotency conflict,
rate limit, queue full, deadline exceeded, inference failure, expired result,
and internal error.

Only transport errors and HTTP 408/425/429/500/502/503/504 are retryable,
always under the same idempotency key. HTTP 401/403/404/409/413/422 are not.
Honor `Retry-After`; otherwise use bounded full-jitter exponential backoff.
Never expose credentials, internal paths, base64 payloads, signed URIs, or
tracebacks in errors or logs.

## 6. Minimal 10102 Validation Order

Run in order and stop at the first unexplained mismatch.

1. **Read-only Git check, no GPU**

   ```bash
   git fetch origin main
   git rev-parse origin/main
   git show --stat --oneline 95c1441
   ```

2. **Metadata-only inventory, no imports/GPU**

   Use `importlib.metadata.version()` or `pip list` for Python, Torch, SGLang,
   sgl_kernel, verl, rLLM, transformers, Ray, xgrammar, tvm-ffi and vendor
   extensions. Record exact distribution versions and wheel tags.

3. **Dependency metadata check, no GPU**

   Run `python -m pip check`. Report every line separately. Do not install or
   downgrade anything to make it green during comparison.

4. **Repository static/CPU checks, no GPU**

   ```bash
   PYTHONPATH=src python -m gen_retry.cli.validate_schemas
   PYTHONPATH=src python -m gen_retry.cli.validate_fixtures
   PYTHONPATH=src pytest tests/contract -q
   PYTHONPATH=src pytest tests/unit/test_rl_config_tracking_preflight.py \
     tests/unit/test_rl_credit.py tests/unit/test_rl_data.py \
     tests/unit/test_rl_objective.py tests/unit/test_rl_runtime_gate.py \
     tests/unit/test_rl_training.py tests/unit/test_rl_verl_adapter.py -q
   ```

5. **Isolated safe imports, no GPU claim**

   Import one module per subprocess. Begin with `transformers`, `ray`,
   `xgrammar`, `tvm_ffi`, and `verl`. Treat `torch`, `sglang`, `sgl_kernel`,
   FlashAttention and vLLM compiled imports as vendor-runtime-sensitive. If a
   package initializes a device or aborts, record it and stop; do not retry by
   swapping Torch or shared libraries.

6. **Remote service static contract, no GPU**

   Validate `/healthz` shape, authentication behavior, request/response/error
   Schemas, generate/edit route isolation, idempotency conflict behavior, size
   limits, and `/v1/capabilities` structure using a fake or non-inference mode.

7. **HCU runtime smoke, GPU required and not executable on current 10102**

   Only on a correctly allocated HCU node, load vendor environment scripts,
   verify one visible device and BF16, then import Torch and each compiled
   extension separately. Do not describe this as passed from static imports.

8. **Model smoke, GPU required and expensive**

   Load the frozen Qwen3-VL checkpoint through the declared rollout engine,
   sample one bounded multimodal Action, and persist prompt tokens, image grid,
   sampled tokens and old log-probs. This may allocate about 17 GiB for weights
   plus KV/runtime memory.

9. **Image service smoke, GPU/remote execution and artifact mutation**

   Execute one generate and one source-conditioned edit using unique semantic
   request IDs, then replay both with the same idempotency keys. Verify model
   routes, PNG/digests, source echo, provenance, and no duplicate inference.

10. **Live RL and optimizer gates, not authorized by this handoff**

    Do not claim a real rollout or optimizer pass until canonical multi-turn
    events, Geneval2 terminal reward, resume evidence, current-logprob scoring,
    and the formal gates exist.

## 7. Environment-Preservation Rules

- Do not run generic `pip install torch`, `pip install -U`, or an upstream
  SGLang install script in a vendor environment.
- Do not install the RL host's Torch-2.5.1 SGLang probe wheels.
- Do not use CPython 3.10/3.12 binary wheels in Python 3.11.
- Do not import all compiled extensions in one process before checking device
  allocation and vendor runtime paths.
- Do not add editable installs or runtime imports from Gen-Searcher, GenEvolve,
  legacy Gen-Retry, or other external evidence roots.
- Do not persist tokens, private URLs, credentials, or full signed artifact
  URLs in reports.

## 8. Questions For 10102

10102 should return the following without credentials or private URLs:

1. Exact Python version/executable and Torch distribution/version/HIP metadata.
2. Exact SGLang and sgl_kernel distributions, wheel tags, build suffixes, and
   whether each imports in an isolated subprocess without device initialization.
3. Exact verl, rLLM, transformers, Ray, xgrammar, and tvm-ffi versions; identify
   which are absent rather than treating them as failures.
4. Full `pip check` output, separated from safe-import results.
5. Whether `verl.workers.rollout.base.get_rollout_class("vllm", "async")` and
   any SGLang rollout-class lookup resolve without starting a model.
6. Whether the proposed generate/edit request and response fields can be
   represented by the available service implementation without silently
   dropping seed, source digest, model revision, or idempotency semantics.
7. Which health/readiness/capabilities and structured error behaviors are
   implemented now versus requiring an adapter or gateway.
8. Confirmation that no HCU/model/image smoke was claimed on the GPU-less
   10102 host.

## 9. 10102 Static Comparison Return

On 2026-08-11, 10102 reported the following from a GPU-less inspection
checkout. Its detailed report is currently uncommitted at
`docs/operations/ENV_10102_VS_RL_COMPARISON.md`; these results are therefore
informational until that report and its command outputs are versioned.

| Component/check | 10102 report | Status boundary |
| --- | --- | --- |
| Python | `3.10.12` | `CPU_OR_STATIC_PASS` |
| Torch | vendor 2.9, exact suffix/HIP pending | metadata only |
| SGLang | `0.5.12` vendor CPython 3.10; root import passes | `CPU_OR_STATIC_PASS`, no HCU/model claim |
| sglang-kernel | `0.4.2.post2`; root import passes | ownership/ABI unresolved |
| sgl-kernel | `0.3.21`; root import passes | ownership/ABI unresolved |
| verl | `0.6.1`; root import passes after a missing-`libhydmi.so` probe warning | `CPU_OR_STATIC_PASS` |
| rLLM | `0.2.1`; root import passes | `CPU_OR_STATIC_PASS`, workflow not run |
| transformers | `5.6.0`; import passes | differs materially from RL `4.57.6` |
| Ray | `2.55.1`; import passes | differs from RL `2.48.0` |
| xgrammar | `0.1.32`; import passes | differs from RL `0.1.25` |
| tvm-ffi | `0.1.0`; waits in Torch cpp-extension `file_baton` during optional C-DLPack JIT | `BLOCKED`, not proven ABI failure |
| rollout targets | vLLM/SGLang async targets discoverable statically | dynamic deep imports timed out in Transformers scanning |

Before the no-install instruction arrived, 10102 added only the pure-Python
packages `pyvers==0.1.0` and `omegaconf==2.3.0`; it reported no Torch, SGLang,
or native-package replacement. This timing must remain in its environment
provenance.

RL-side disposition:

1. Proceed toward the reviewed `gen_retry_vllm_verl_adapter + vllm` amendment.
   Keep the existing SGLang/rLLM YAML as the historical accepted binding until
   the required ADR, config, Schema, hash, fixture, test, and runbook changes
   are implemented. A GPU-less SGLang root import is not enough to change the
   runtime decision.
2. Treat the SGLang/kernel/xgrammar/tvm-ffi set as a static compatibility
   candidate. Vendor support remains unproven until exact wheel tags,
   `WHEEL`/`METADATA`/`RECORD`, loaded module/native-library ownership, and an
   HCU smoke are available.
3. Record the reported SGLang dist-info `das.opt1` versus METADATA `das.opt`
   spelling as packaging provenance inconsistency. Do not edit metadata or
   infer ABI compatibility from either string.
4. Do not guess which of `sglang-kernel` and `sgl-kernel` is authoritative.
   Determine it from SGLang `Requires-Dist`, both RECORD files,
   `importlib.util.find_spec("sgl_kernel").origin`, and the owner of the loaded
   native extension. Overlapping file ownership is a blocker, not a reason to
   uninstall one package experimentally.
5. Supersede/migrate the untracked `model_deploy_10099_v1` remote draft. It may
   remain only as an optional legacy generate facade; it does not satisfy the
   accepted dual-route, provenance, idempotency, health, capabilities, or
   structured-error contract.
6. Add repository-owned fake non-inference API Schemas, fixtures, and contract
   tests before connecting a real service. They do not exist yet.
7. When HCU access returns, rerun compiled imports individually, a bounded
   engine/model smoke, one generate/edit idempotency smoke, one real development
   rollout, and eventually the formal 32-group gate.

Still requested from 10102: exact Torch vendor suffix/HIP metadata, SGLang
wheel filename/tag, both kernel RECORD/module ownership reports, complete
`pip check`, the read-only `tvm-ffi` file-baton/cache location, dynamic-import
timeout stacks, and a committed comparison artifact. No cache lock should be
deleted merely to make the probe pass.

## 10. Remaining RL-Side Work

This handoff does not close the direct-vLLM runtime amendment. RL still needs a
versioned remote image client/config, fake-service contract tests, the real
multi-turn collector, event-derived reward replay, crash-safe semantic resume,
actual multimodal current-logprob scoring, one real development episode, the
32-group formal smoke, and an optimizer update/checkpoint. Those changes must
update the accepted ADR/config/schema/hash/test set before formal training.
