# 10102 Versus RL Environment Comparison

## 1. Scope And Evidence Rules

This report compares the no-GPU `model_deploy_10102` environment with the RL
host handoff initially published at `01e2a62` and incrementally updated with
the RL disposition at `e5f3a299f94ddccc9c91633b83d20164de35cf1b`.
The Phase 8 scaffold baseline is
`95c1441cf269fa9e037cc44dc27491b3e80a08d0`.

Evidence labels:

- `REAL_HCU_PASS`: persisted execution on an allocated RL HCU.
- `CPU_OR_STATIC_PASS`: metadata, source, schema, fixture, unit, or safe-import
  evidence that does not establish accelerator execution.
- `NOT_RUN`: deliberately not executed.
- `BLOCKED`: the checked interface cannot yet be claimed usable.

The 10102 checkout remained on `research/hpsv3-quality-guard` at
`9533ba04e63badf8d3b3a5c2d162d02ac15dbd62`. It was not switched, reset, or
cleaned because it contains unrelated user work. Local `main` was `95c1441`,
while `origin/main` became `e5f3a29` after the requested fetch. The untracked
local copy of `docs/operations/RL_TO_10102_ENV_HANDOFF.md` still matches the
initial file at `01e2a62`; the latest handoff was read directly with
`git show e5f3a29:docs/operations/RL_TO_10102_ENV_HANDOFF.md` and was not copied
over unrelated local work.

Role decision: 10102 is currently an environment and protocol validation host,
not a proven new Qwen-Image service deployment. It has no GPU/HCU available and
no model, image, or readiness smoke was run here. Promoting it to a service host
requires device allocation, model artifacts, network policy, and separate
generate/edit model evidence.

## 2. Layered Comparison

| Layer/item | RL baseline | 10102 measurement | Difference and impact | Recommendation |
| --- | --- | --- | --- | --- |
| Reproduction ref | latest handoff `main@e5f3a29`; Phase 8 at `95c1441` | dirty inspection checkout `9533ba0` | Code state is not identical | Use `git show e5f3a29:...` for the latest handoff; do not reset the dirty checkout |
| Python | 3.11.9 | 3.10.12 | Different ABI | Keep separate wheel inventories; do not compare CPython tags as if identical |
| Torch | `2.9.0+das.opt1.dtk2604`; HIP 6.3.26093; `REAL_HCU_PASS` | distribution `2.9.0+das.opt1.dtk2604.2605281139.gd0fc8c`; runtime `torch.__version__=2.9.0`; HIP `6.3.26113`; git `d0fc8cbcdbd76e69f3e44152ff7a22a54bb6bb9e`; wheel `cp310-cp310-manylinux_2_28_x86_64`; root import passed | Same Torch major/minor and DTK family, different vendor build and HIP patch identity; no 10102 device ABI proof | Preserve vendor Torch; require a real HCU probe before runtime equivalence |
| Accelerator | historical one RL HCU pass | no GPU/HCU | Runtime equivalence cannot be established | `NOT_RUN`; do not initialize engines on 10102 |
| Policy engine | vLLM `0.11.0+...torch290`, real multimodal HCU pass | system vLLM `0.15.1+...torch290`, metadata conflicts; not imported in this audit | Different engine generation and dependency closure | Do not use 10102 vLLM metadata as evidence for the intended SGLang path |
| SGLang | not installed | pip reports `0.5.12+das.opt1.dtk2604`; METADATA internally reports `0.5.12+das.opt.dtk2604`; wheel `cp310-cp310-linux_x86_64`; root import passed | 10102 has the requested Torch-2.9 vendor package, but its filename and METADATA version disagree | Retain package; ask vendor to clarify build provenance; require HCU engine smoke |
| SGLang kernel | not installed | `sglang-kernel 0.4.2.post2`, `cp39-abi3-linux_x86_64`; shared `sgl_kernel` namespace import reports 0.4.2.post2 | SGLang explicitly requires this exact distribution; no device execution | Preserve files; require vendor/HCU confirmation |
| Additional `sgl-kernel` metadata | not installed | `sgl-kernel 0.3.21`, `cp39-abi3-linux_x86_64`; not independently import-verified | Its RECORD overlaps 57 paths with 0.4.2.post2 and disagrees with 15 current file hashes | Treat duplicate ownership as an environment-pollution `BLOCKED`; do not uninstall by trial |
| verl | 0.6.1, interface/DataProto HCU evidence | 0.6.1, `py3-none-any`; root safe import passed | Version aligned; deep rollout imports are slow and were not completed | Static registry passes; real rollout remains `NOT_RUN` |
| rLLM | not installed | 0.2.1, `py3-none-any`; root safe import passed | 10102 uniquely has the Gen-Searcher-derived rLLM runtime | Keep isolated; its Gen-Retry adapter semantics still need implementation/review |
| rLLM/verl source | adapter plan only | non-editable wheels built from Gen-Searcher commit `e5078d31859bafee6b6b610f0cd40095cc72e2a4` | Installability is proven, live rollout is not | No production import to the external repository; preserve wheel/source evidence |
| transformers | 4.57.6, HCU reference scorer pass | 5.6.0, safe import passed | Major version difference; 10102 vLLM metadata requires 5.2.0 | Freeze the selected rollout stack before HCU validation; do not downgrade for `pip check` alone |
| Ray | 2.48.0, real task pass | 2.55.1, safe import passed | Version difference | CPU import is sufficient only for interface inventory |
| xgrammar | 0.1.25 metadata | 0.1.32, `cp310` wheel; import passed | SGLang declares 0.2.0 and vLLM declares 0.1.29 | This is a real metadata conflict; resolve only against a vendor-tested SGLang HCU matrix |
| tvm-ffi | not installed | `apache-tvm-ffi 0.1.0`, `cp310` wheel; import waits on stale-looking `/root/.cache/torch_extensions/py310_cpu/c_dlpack/lock` | SGLang declares 0.1.9; tilelang/quack also require newer 0.1.x | `BLOCKED`; retain the lock for forensic/vendor review and do not replace packages |
| SGLang feature deps | none | missing `easydict`, `kernels`, `sgl-deep-gemm`, `tokenspeed-mla`, `torch-memory-saver`, `torchao`, `torchcodec` | Some are feature-specific, but SGLang's declared closure is incomplete | Do not call all missing entries fatal; map imports during a declared engine/config smoke |
| Repository CPU checks | 82 contract and 219 unit tests in RL handoff | 24 schemas, 108 fixture records, 82 contract tests, 52 focused RL tests, and 2 old-contract fake remote-adapter tests passed | Relevant static contracts agree | Preserve as `CPU_OR_STATIC_PASS`, not runtime evidence |

## 3. SGLang And Kernel Provenance

The installed SGLang wheel filename is
`sglang-0.5.12+das.opt1.dtk2604-cp310-cp310-linux_x86_64.whl` (the local
direct-url record percent-encodes `+`). Its archived wheel SHA-256 is
`17b2904aca18d027e2ab889759718ea9389494cacbb9a308fe1ef35075fe7fbb`.
The installed dist-info directory says `das.opt1`, while METADATA says
`Version: 0.5.12+das.opt.dtk2604`. This is recorded as a provenance
inconsistency, not interpreted as ABI evidence.

| Distribution/file | SHA-256 |
| --- | --- |
| SGLang WHEEL | `388d76b66a8c35e057a4642d5edc3a4d4a10cf925c89c193093ed3c2092e34d0` |
| SGLang METADATA | `fc8e715f2b6764969e8c459fa5ba5a4595e9f287decee23a1ff7dfc9321918c4` |
| SGLang RECORD | `cdb92c16dd6525a17505eba9ee48a46ab19190c27b5329aa723943cd2b0a1424` |
| `sglang-kernel 0.4.2.post2` WHEEL | `03fa2b59c3231c3020988d060e8585309599cf39987748b6e0f26ded462734d3` |
| `sglang-kernel 0.4.2.post2` METADATA | `d815e895a9d3584368e36ee89914d1a289017cab86566f484436ce7e13d9ffcd` |
| `sglang-kernel 0.4.2.post2` RECORD | `bb20feddb0543b72ec40cfcdffd1658750e91983c711df07610f596b6119b987` |
| `sgl-kernel 0.3.21` WHEEL | `c770da72f3e0ffbdf721744d331433274ec1228fa833f99942b8f35a813fabce` |
| `sgl-kernel 0.3.21` METADATA | `d8a469290e14ef5f939b5fb50f8d87fca5f8ee67aef35b54e111b9e587226d53` |
| `sgl-kernel 0.3.21` RECORD | `20a698c11c718689d5129b0b8c866c15cc434ebb3c80d4339b622df233cbbb64` |

SGLang METADATA declares these relevant exact requirements:

```text
sglang-kernel==0.4.2.post2
torch==2.9.0
apache-tvm-ffi==0.1.9
xgrammar==0.2.0
cuda-python>=13.0
nvidia-cutlass-dsl==4.5.0
sgl-deep-gemm==0.1.0
tokenspeed_mla==0.1.1
torch_memory_saver>=0.0.9.post1
torchao==0.17.0
torchcodec==0.11.1 (platform-qualified)
kernels
```

`importlib.util.find_spec("sgl_kernel").origin` resolves to
`/usr/local/lib/python3.10/dist-packages/sgl_kernel/__init__.py`. Both kernel
RECORD files claim 57 shared paths, including `__init__.py`, `version.py`, and
`common_ops.cpython-310-x86_64-linux-gnu.so`. Among the hashed overlaps, all 29
current files match `sglang-kernel 0.4.2.post2`; 15 disagree with the hashes
declared by `sgl-kernel 0.3.21` and 14 happen to match both. The loaded
`version.py` reports 0.4.2.post2. This identifies the currently resolved file
content, but it does not make the duplicate 0.3.21 ownership safe. No files or
metadata were changed.

The kernel archive evidence is:

```text
sglang_kernel-0.4.2.post2-cp39-abi3-linux_x86_64.whl
sha256 3f7475f440095dfb0a97879a5b2809dc5400c750f99b85909bed533edf661699

sgl_kernel-0.3.21-cp39-abi3-linux_x86_64.whl
sha256 027d6d4b701dbbb12846714daebf0447cf2e04958d6f0bc5e495191f70cf2a5a
```

## 4. Environment Mutation During This Audit

Before the RL handoff's later instruction to perform no more installs arrived,
two pure-Python packages were added serially with `--no-deps`:

```text
pyvers 0.1.0
omegaconf 2.3.0
```

They unblocked `tensordict` and then the verl root import. No Torch, SGLang,
kernel, transformers, Ray, xgrammar, tvm-ffi, CUDA/DTK, or other native package
was installed or replaced. No further package operation was performed after
the instruction arrived. `pyvers 0.1.0` declares `packaging<26`, while this
environment has `packaging 26.2`; that new metadata warning is retained below.

## 5. Complete 10102 `pip check`

Command:

```bash
runs/rl_envs/rllm_verl_py310/bin/python -m pip check
```

Result: exit 1. This is metadata evidence, not a runtime verdict.

```text
wandb 0.28.1 requires platformdirs, which is not installed.
tensorboard 2.21.0 requires absl-py, which is not installed.
tensorboard 2.21.0 requires markdown, which is not installed.
tensorboard 2.21.0 requires tensorboard-data-server, which is not installed.
polars 1.43.2 requires polars-runtime-32, which is not installed.
oss2 2.19.1 requires aliyun-python-sdk-core, which is not installed.
oss2 2.19.1 requires aliyun-python-sdk-kms, which is not installed.
oss2 2.19.1 requires crcmod, which is not installed.
oss2 2.19.1 requires pycryptodome, which is not installed.
eval-protocol 0.3.32 requires backoff, which is not installed.
eval-protocol 0.3.32 requires dataclasses-json, which is not installed.
eval-protocol 0.3.32 requires deepdiff, which is not installed.
eval-protocol 0.3.32 requires fireworks-ai, which is not installed.
eval-protocol 0.3.32 requires litellm, which is not installed.
eval-protocol 0.3.32 requires peewee, which is not installed.
eval-protocol 0.3.32 requires questionary, which is not installed.
eval-protocol 0.3.32 requires toml, which is not installed.
eval-protocol 0.3.32 requires zstandard, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires easydict, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires kernels, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires sgl-deep-gemm, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires tokenspeed-mla, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires torch-memory-saver, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires torchao, which is not installed.
sglang 0.5.12+das.opt1.dtk2604 requires torchcodec, which is not installed.
pygobject 3.42.1 requires pycairo, which is not installed.
pyvers 0.1.0 has requirement packaging<26.0,>=25.0, but you have packaging 26.2.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement flash_mla==1.0.0, but you have flash-mla 1.2.0+das.opt1.dtk2604.torch290.2605281449.ge3aed6.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement llguidance<1.4.0,>=1.3.0; platform_machine == "x86_64" or platform_machine == "arm64" or platform_machine == "aarch64" or platform_machine == "s390x" or platform_machine == "ppc64le", but you have llguidance 0.7.30.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement opencv-python-headless>=4.13.0, but you have opencv-python-headless 4.10.0.84.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement outlines_core==0.2.11, but you have outlines-core 0.1.26.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement runai-model-streamer[gcs,s3]==0.15.3, but you have runai-model-streamer 0.16.0.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement setuptools<80.0.0,>=77.0.3, but you have setuptools 81.0.0.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement timm>=1.0.17, but you have timm 1.0.16.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement transformers==5.2.0, but you have transformers 5.6.0.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement triton==3.3.1, but you have triton 3.5.1+das.opt1.dtk2604.torch290.2605281608.g799061.
vllm 0.15.1+das.opt1.alpha.dtk2604.torch290.2605261031.gdb9e4b has requirement xgrammar==0.1.29; platform_machine == "x86_64" or platform_machine == "aarch64" or platform_machine == "arm64" or platform_machine == "s390x" or platform_machine == "ppc64le", but you have xgrammar 0.1.32.
tilelang 0.1.9+das.opt1.dtk2604.torch290.2605291651.gb066c6 has requirement apache-tvm-ffi>=0.1.2,~=0.1.0, but you have apache-tvm-ffi 0.1.0.
sglang 0.5.12+das.opt1.dtk2604 has requirement apache-tvm-ffi==0.1.9, but you have apache-tvm-ffi 0.1.0.
sglang 0.5.12+das.opt1.dtk2604 has requirement cuda-python>=13.0, but you have cuda-python 12.9.0.
sglang 0.5.12+das.opt1.dtk2604 has requirement nvidia-cutlass-dsl==4.5.0, but you have nvidia-cutlass-dsl 4.5.2.
sglang 0.5.12+das.opt1.dtk2604 has requirement xgrammar==0.2.0, but you have xgrammar 0.1.32.
quack-kernels 0.5.0 has requirement apache-tvm-ffi<0.2,>=0.1.6, but you have apache-tvm-ffi 0.1.0.
```

The missing rLLM application dependencies can generally be installed as
ordinary Python packages, but doing so is a separate environment-build step.
It must use a locked resolution and verify that no vendor native package is
replaced. The SGLang/tvm/xgrammar/native conflicts cannot be safely solved by
blindly installing the PyPI-declared versions because the current image is a
vendor DTK build.

## 6. Safe Import Results

Every probe ran in its own subprocess with CUDA/HIP/ROCR/Ascend visibility set
to the empty string. No engine, model, CUDA/HIP API, or device enumeration was
requested.

| Module/path | Result | Interpretation |
| --- | --- | --- |
| `torch` | PASS, root import; module reports 2.9.0 | `CPU_OR_STATIC_PASS`; not an ABI/device smoke |
| `sglang` | PASS, root import; module `__version__` is `0.0.0.dev0` | Conflicts with distribution metadata and needs vendor clarification |
| `sgl_kernel` | PASS, shared namespace reports 0.4.2.post2 | Validates `sglang-kernel`; does not independently validate the co-installed `sgl-kernel 0.3.21`; no kernel launch |
| `transformers` | PASS, 5.6.0 | Safe import took tens of seconds |
| `ray` | PASS, 2.55.1 | Ray cluster/task not started |
| `rllm` | PASS, root package | Installability proven; no workflow/rollout execution |
| `verl` | PASS after the two pure-Python additions | Printed missing `libhydmi.so` warning, then completed |
| `xgrammar` | PASS | Package has no `__version__`; distribution metadata is 0.1.32 |
| `tvm_ffi` | BLOCKED at 30/75 seconds | `tvm_ffi/_optional_torch_c_dlpack.py:610` calls `load_inline("c_dlpack")`; stack stops at `torch/utils/file_baton.py:50` via `cpp_extension.py:2210` |
| `rllm.engine.rollout.verl_engine.VerlEngine` | 30/75-second timeout | Stack was at Transformers `import_utils.py:2605/2821/2985`, reached through `rllm/agents/utils.py:1`; class exists statically |
| verl vLLM/SGLang async class lookup | 30/75-second timeout | Both stacks were at Transformers `import_utils.py:2718-2719/2985`, reached through `verl/utils/torch_functional.py:29`, before backend resolution |

The timeouts are not reported as import exceptions or runtime passes. They are
`BLOCKED` for dynamic verification and `CPU_OR_STATIC_PASS` only for source
resolution.

The tvm-ffi baton path is
`/root/.cache/torch_extensions/py310_cpu/c_dlpack/lock`. It is an empty file
created at 2026-08-11 05:10:16 UTC alongside `main.cpp`; `build.ninja` appeared
one second later. At the 05:22 UTC inspection, neither `lsof` nor `fuser`
reported an owner and no live compiler process existed. Only orphaned zombie
`ninja`/`cc1plus` processes with PPID 1 remained from 05:10. Torch `FileBaton`
waits solely while the path exists and removes it only during normal release.
The evidence therefore strongly indicates an interrupted-JIT stale lock, but
the lock was not deleted and the import was not retried.

## 7. verl And rLLM Routing

Static AST/source inspection, without importing a backend, resolves:

```text
('vllm', 'sync')   -> verl.workers.rollout.vllm_rollout.vLLMRollout
('vllm', 'async')  -> verl.workers.rollout.vllm_rollout.vLLMAsyncRollout
('sglang', 'sync') -> verl.workers.rollout.sglang_rollout.sglang_rollout.SGLangRollout
('sglang', 'async')-> verl.workers.rollout.sglang_rollout.sglang_rollout.ServerAdapter
```

The SGLang target classes are present. The installed verl source explicitly
deprecates sync/SPMD for SGLang >=0.5.5 and directs 0.5.12 users to async native
server mode. rLLM's `VerlEngine` accepts either `vllm` or `sglang`, then calls
verl's `AgentLoopManager`/`AsyncLLMServerManager`; rLLM does not directly choose
or initialize SGLang. Its workflow trainer also requires `hybrid_engine=True`
and `rollout.mode=async`.

Therefore rLLM + verl + SGLang is structurally represented in this environment,
but it has not passed dynamic class import, Ray worker creation, server launch,
model load, generation, log-prob alignment, or HCU execution. The formal
Gen-Retry config still naming `rllm_verl_adapter + sglang` is not satisfied by
root imports alone.

RL disposition at `e5f3a29`: the intended amendment is
`gen_retry_vllm_verl_adapter + vllm`. The historical
`rllm_verl_adapter + sglang` binding remains accepted until the required ADR,
config, schema, hash, and tests change together; it must not be silently
renamed. The 10102 SGLang+rLLM stack remains compatibility evidence only.

## 8. Remote Qwen-Image Contract Gap

The accepted target from the RL handoff is `/v1/images/generations` and
`/v1/images/edits`, configured only by
`GEN_RETRY_IMAGE_SERVICE_BASE_URL` and `GEN_RETRY_IMAGE_SERVICE_TOKEN`.

An untracked local draft exists at
`src/gen_retry/tools/remote_qwen_image_adapter.py`. It is not part of current
HEAD or `e5f3a29` and implements the older `model_deploy_10099_v1` contract.
An untracked fake-server test appeared during the audit and passed 2 tests, but
it tests only that older contract. Neither file is part of this comparison
commit. The draft must not be described as the accepted remote API
implementation.

| Requirement | Local draft status | Impact |
| --- | --- | --- |
| Preserve seed | Implemented in request, response-parameter validation, and metadata | Useful, but only under old contract |
| Preserve source digest | Implemented for edit request and response validation | Source `attempt_id` is not sent to the service |
| Preserve resolved model revision | Expected model-index fingerprint is validated and persisted | Contract is tied to a preconfigured fingerprint, not capabilities negotiation |
| Explicit idempotency key/header | Not implemented | Fake test proves same-process local artifact-cache reuse, not service idempotency |
| Required request/profile headers | Bearer auth only; no `Idempotency-Key`, `X-Request-ID`, or `X-Execution-Profile` | Not protocol-compatible |
| Accepted routes | Uses `/v1/generate`, `/v1/edit`, `/v1/jobs/{request_id}` | Not protocol-compatible |
| Inline verified PNG result | Fetches a service-relative `result_url`, then validates digest/length/dimensions and atomically saves | Validation is good, transport differs from accepted default |
| `/healthz` | No client or server implementation found | Not implemented |
| `/readyz` | No client or server implementation found | Not implemented |
| authenticated `/v1/capabilities` | No implementation found | Route/model/limit negotiation absent |
| idempotency conflict 409 | No explicit handling beyond generic structured error | Not implemented as a verified behavior |
| retryable status mapping and `Retry-After` | Trusts server `retryable`; no bounded retry loop/status allowlist | Incomplete |
| structured errors | Parses `code/message/retryable`; fake test covers one 503 edit-capability error | Does not validate full required shape or protect all status semantics |

A loopback fake endpoint was executed by
`tests/unit/test_remote_qwen_image_adapter.py`: 2 tests passed for Bearer auth,
generate polling, seed/model/digest validation, atomic PNG/cache reuse, and one
edit-model-unavailable error. No live or private endpoint was called. The
accepted canonical protocol remains `BLOCKED` because the fake implements the
old routes and omits accepted idempotency, provenance, health, readiness, and
capabilities behavior.

## 9. Reproducible Commands

```bash
git fetch origin main
git rev-parse origin/main
git show e5f3a29:docs/operations/RL_TO_10102_ENV_HANDOFF.md

runs/rl_envs/rllm_verl_py310/bin/python -m pip list --format=freeze
runs/rl_envs/rllm_verl_py310/bin/python -m pip check

env CUDA_VISIBLE_DEVICES='' HIP_VISIBLE_DEVICES='' \
  ROCR_VISIBLE_DEVICES='' ASCEND_RT_VISIBLE_DEVICES='' \
  runs/rl_envs/rllm_verl_py310/bin/python -c \
  "import verl; print(verl.__file__, flush=True)"

PYTHONPATH=src python -m gen_retry.cli.validate_schemas
PYTHONPATH=src python -m gen_retry.cli.validate_fixtures
PYTHONPATH=src pytest tests/contract -q
PYTHONPATH=src pytest \
  tests/unit/test_rl_config_tracking_preflight.py \
  tests/unit/test_rl_credit.py tests/unit/test_rl_data.py \
  tests/unit/test_rl_objective.py tests/unit/test_rl_runtime_gate.py \
  tests/unit/test_rl_training.py tests/unit/test_rl_verl_adapter.py -q
PYTHONPATH=src pytest tests/unit/test_remote_qwen_image_adapter.py -q
```

Commands intentionally not run on 10102:

```text
torch.cuda / HIP device enumeration
SGLang or vLLM engine initialization
Ray rollout worker creation
Qwen3-VL or Qwen-Image model loading
generate/edit image execution
Geneval2 scoring
optimizer backward/update
live/private remote service HTTP calls
```

## 10. Remaining Coordinated Work

1. Implement the RL-owned `gen_retry_vllm_verl_adapter + vllm` amendment with
   its ADR, config, schema, hash, tests, and accepted review. Until then the
   current YAML and runtime evidence remain intentionally different.
2. On a restored HCU allocation, provide an isolated SGLang 0.5.12 async smoke
   matrix for the exact vendor Torch build, both kernel distributions,
   xgrammar, and tvm-ffi. 10102 cannot supply this evidence.
3. Obtain the intended vendor package manifest for SGLang: its dist-info
   directory says `das.opt1`, while its METADATA `Version` says `das.opt`.
4. Resolve the duplicate kernel ownership through a vendor-provided image or
   locked rebuild, not by uninstall trial. Current critical files match
   `sglang-kernel 0.4.2.post2`, which SGLang requires, but the 0.3.21 RECORD
   still claims them.
5. Supersede/migrate the old `model_deploy_10099_v1` draft. If retained, it is
   only an OpenAI-compatible generate facade; the canonical generate/edit,
   idempotency, provenance, health, and capabilities contract belongs in a new
   adapter/gateway.
6. Implement the currently missing fake/non-inference API schemas and fixtures
   so 10102
   can execute route isolation, auth, digest, 409 replay conflict, retry, and
   error-shape tests without a GPU or private endpoint.
7. Once the RL host has HCU access again, rerun only the missing formal gates:
   real multi-turn on-policy collection, live image+Geneval2, optimizer update,
   and interruption/resume. Do not reinterpret the prior synthetic reward
   bridge as those passes.

## 11. Final Status

The Torch 2.9 versus old Torch-2.5.1 SGLang-kernel incompatibility has been
addressed at the package-selection level on 10102: the installed SGLang package
declares Torch 2.9 and its root package plus the resolved 0.4.2 kernel namespace
do not abort. The co-installed `sgl-kernel 0.3.21` was not independently import
verified. The problem is not fully solved at runtime because the declared SGLang
dependency closure conflicts, tvm-ffi import is blocked on a JIT baton, and no
HCU async-engine smoke can run here.

rLLM and verl are installed and their root packages import. Their actual async
rollout route is statically present but not dynamically or on-device validated.
Accordingly, the environment is suitable for continued CPU protocol work and
vendor-matrix preparation, not yet for claiming SGLang RL rollout readiness.
