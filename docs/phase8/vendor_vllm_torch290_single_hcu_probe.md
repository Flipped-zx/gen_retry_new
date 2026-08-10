# Vendor vLLM Torch 2.9 Single-HCU Probe

- Date: 2026-08-10
- Scope: current Torch 2.9 + vendor vLLM environment validation on one visible HCU
- Result: runtime PASS, packaging closure still incomplete

## Environment

Loaded both vendor environment scripts:

```bash
source /opt/dtk-26.04/env.sh
source /opt/hyhal/env.sh
```

Then used `runs/rl_envs/torch290_py311/bin/python`.

Observed runtime versions:

| Component | Version |
| --- | --- |
| Torch | `2.9.0+das.opt1.dtk2604` |
| HIP | `6.3.26093` |
| vLLM | `0.11.0+das.opt1.dtk2604.torch290` |
| verl | `0.6.1` |
| Ray | `2.48.0` |
| W&B | `0.28.1` |
| NumPy | `1.25.0` |
| CuPy | `12.3.0` |
| amdsmi | `24.5.3+02cbffb.dirty` |
| flash-attn dist | `2.8.3+das.opt1.dtk2604.torch290` |
| lmslim dist | `0.4.0+das.opt1.dtk2604.torch290` |

One BW device was visible:

- device count: `1`
- device name: `BW`
- memory: `68702699520` bytes

## Runtime Validation

- `probe_rl_vllm_runtime.py` loaded the frozen
  `runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42` checkpoint.
- Model architecture resolved to `Qwen3VLForConditionalGeneration`.
- Engine startup completed on vLLM 0.11.0 with Flash Attention backend.
- The smoke returned exactly `OK`.
- Result artifact: `artifacts/rl/torch290_vllm_hcu_smoke.json`.

Additional checks passed:

- Torch import and HCU visibility
- CuPy real-device arithmetic: `sum(arange(8)^2) == 140.0`
- Ray local task smoke
- W&B offline run smoke
- `amdsmi.amdsmi_init()`
- `flash_attn`, `lmslim`, and `numa` imports

## Remaining Packaging Gaps

`pip check` still reports:

- missing `flash-mla`
- `flash_attn==2.6.1` expected, installed distribution metadata is `2.8.3+...`
- `lmslim==0.3.1` expected, installed distribution metadata is `0.4.0+...`

An attempted source install from the SourceFind/OpenDAS `flashmla` repository
at commit `fd3420872d8b4c8b5406e32d29a91d91e78483e3` reached wheel
compilation only after setting `FLASH_MLA_OPT=1`, but failed under DTK 26.04.
The compile errors included unsupported `hipcc/clang` `-mllvm` arguments and a
missing `cuda/std/utility` header. The package was not installed.

The SourceFind download API exposes `flash_mla/DAS1.8` wheels for
`dtk2604.torch290`, but only for `cp310` and `cp312`. The inferred
`cp311` URL returns a JSON `no such file or directory` error, so there is no
directly installable wheel for the current Python 3.11 environment.

So the runtime is usable, but the environment is not yet a formally clean dependency closure.

## Gate Impact

This unblocks further RL environment work on the current single visible HCU, but not the full eight-HCU rollout or the 32-group resume/replay smoke.
