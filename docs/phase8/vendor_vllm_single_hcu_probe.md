# Vendor vLLM Single-HCU RL Validation

- Date: 2026-08-10
- Scope: all RL-path diagnostics feasible on one allocated HCU
- Result: `PASS`
- Not authorized by this probe: live RL collection, optimizer updates, or
  replacement of the frozen SGLang adapter plan

## Environment

The probe used one visible 64 GiB HCU after loading `/opt/dtk-26.04/env.sh` and
`/opt/hyhal/env.sh`. A repository-local probe venv overlaid only Python
dependencies while retaining the system vendor builds:

| Component | Version |
| --- | --- |
| Torch | `2.7.1+das.opt1.dtk2604` metadata / HIP `6.3.26093` |
| vLLM | `0.11.0+das.opt1.dtk2604.torch271` |
| verl | `0.6.1` |
| NumPy overlay | `1.25.0` |
| W&B overlay | `0.28.1` |

`verl.workers.rollout.base.get_rollout_class("vllm", "async")` resolved to
`vLLMAsyncRollout`. Torch and vLLM continued to load from the vendor system
site; pip did not replace either distribution.

Ray 2.48.0 started a local instance, executed one remote task, and shut down
cleanly. W&B 0.28.1 created and finished an offline run without an API key; a
credential-shaped test config field was persisted only as `REDACTED`.

## Model Smoke

The probe loaded the frozen
`runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42` checkpoint as
`Qwen3VLForConditionalGeneration` with BF16, tensor parallel size 1, eager
execution, a 4,096-token model limit, and 0.75 device-memory utilization.

- Weight load: 4/4 safetensors shards, 16.7803 GiB, 56.36 seconds.
- Complete engine startup plus generation: 127.99 seconds.
- Available KV-cache memory: 24.65 GiB.
- Generated output for `Reply with exactly OK.`: `OK`.
- Machine-readable result:
  `runs/rl_runtime_probe_v0_1/vllm_model_smoke.json`.
- Full runtime log:
  `runs/rl_runtime_probe_v0_1/vllm_model_smoke.log`.

The first attempt launched the probe from standard input and failed because
the vendor vLLM runtime requires multiprocessing `spawn`. The checked-in probe
script uses a real module path and a guarded `main`, which resolved that
launcher error.

## Multimodal Action And Token Validation

`scripts/validate_single_hcu_rl.py` then exercised PlannerContext 002 from
`runs/phase7_sft_frozen_test20_v2/phase3_ep_028` with the real
`img_000.png` artifact. This is a canonical image-aware edit state, not a
synthetic text prompt.

- The image processor produced `image_grid_thw = [[1, 64, 64]]`.
- The frozen Transformers renderer and vendor vLLM produced exactly the same
  2,313 prompt token IDs.
- Sampling used the frozen naive-GRPO settings `temperature=0.7`, `top_p=0.95`,
  `top_k=-1`, and seed 42, with a diagnostic 512-token cap below the formal
  1,400-token Action limit.
- The model emitted one 345-token `edit_image` JSON Action targeting `c_001`
  and `c_004`, preserving `c_002/c_003/c_005/c_006`, and sourcing `a_000`.
- Strict JSON parsing, Action Schema v0.5, runtime action availability, known
  constraint IDs, and the source Attempt reference all passed.
- vLLM persisted one finite old log-probability per sampled token.

A separate Transformers process re-rendered the same image-aware prompt and
re-scored the exact sampled token IDs from the frozen checkpoint. The decoded
tokens exactly reproduced the persisted raw Action. The tokenizer-derived
single-assistant-Action mask, sampled tokens, old log-probabilities, and
reference log-probabilities all have length 345 and contain finite values. The
maximum absolute old/reference difference was 0.192901; equality is not
required because the old values come from the sampled vLLM path while the
reference values come from the independent BF16 Transformers scorer.

## Restart, Release, And Optimizer Bridge

The validation launched vLLM in two separate processes. After a full engine
exit and restart, the prompt IDs, sampled IDs, raw Action hash, and every old
log-probability reproduced exactly with seed 42. Fresh memory probes before
and after both vLLM processes and the Transformers scorer each reported zero
process allocation/reservation and 68,365,058,048 free bytes.

The real sampled Action/token/mask/log-probability artifacts were then copied
into a four-candidate diagnostic group. Synthetic terminal rewards with
explicit provenance supplied variance solely for join validation. The
following path passed:

```text
rollout Schema + artifact SHA admission
-> terminal-only candidate returns
-> same-state GRPO advantages
-> prepare_optimizer_batch
-> verl DataProto tensorization
```

Admission accepted 1/1 planned group and 4/4 candidates with zero policy-
invalid and zero zero-variance groups. The resulting tensors had shape
`[4, 345]` for tokens, mask, old log-probabilities, and reference log-
probabilities, and contained 1,380 trainable Action tokens in total. No image
backend, Geneval2 execution, optimizer step, or efficacy claim is attached to
the synthetic reward fixture.

Machine-readable summary:
`runs/rl_single_hcu_validation_v0_1/single_hcu_validation.json` with SHA256
`f949a0126dfef8c068c2ac10d3c7502943a12ab7d04eec53f95f7caf006bdc81`.
The complete run took 388.057 seconds.

A fresh accepted-config preflight is stored at
`runs/rl_single_hcu_validation_v0_1/formal_preflight_current.json`. It passes
the dual-backend/model/Geneval2/checkpoint, frozen 1,000/200/500 manifest,
Torch/Transformers/Ray/W&B/verl, and one-device availability checks. It remains
`BLOCKED` on exactly four items: missing SGLang, missing rLLM, one visible HCU
versus the required eight, and missing formal live-adapter evidence. The smoke
report is consequently `PENDING`.

## Remaining Limits

- Only one HCU was visible; the frozen topology and 32-group smoke require
  eight.
- This venv deliberately inherits vendor system packages and therefore is not
  the final isolated runtime. `pip check` also sees unrelated system
  `anndata`/`zarr` requirements that conflict with the vLLM-required NumPy
  overlay.
- vLLM's internal tokenizer construction still emits the Mistral-regex warning
  even though the caller-side processor enables `fix_mistral_regex`; the custom
  adapter must prove token identity rather than suppress the warning.
- The runtime warns that its process group is not explicitly destroyed at
  shutdown. The service lifecycle must close it before staged device release.
- rLLM and SGLang remain uninstalled. The accepted custom Gen-Retry workflow,
  semantic event replay, and staged service-to-FSDP adapter do not yet exist.
- One-request engine restart/replay passed, but this is not the formal
  interruption/resume of a 32-group artifact-backed multi-turn rollout.
- The offline optimizer bridge passed, but no optimizer update was executed.
- The accepted adapter plan still names SGLang. A vLLM runtime amendment must
  update config, experiment hashes, preflight, evidence Schemas, tests, and
  review status before live collection.

## Review Gate

No new review gate was triggered. This is stronger single-HCU runtime evidence
for deciding a future adapter amendment, not approval of that amendment or of
live optimization.
