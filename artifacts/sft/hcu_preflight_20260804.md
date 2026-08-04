# HCU SFT Preflight (2026-08-04)

## Scope

Read-only device and runtime checks for the allocated eight-card HCU host. No
formal SFT training was started and no source or credential files were changed.

## Hardware

The DTK environment is required before importing the vendor Torch build:

```bash
source /opt/dtk-26.04/env.sh
```

`/opt/hyhal/bin/hy-smi --showid --showproductname --showmeminfo all` reports:

- 8 devices, `HCU[0]` through `HCU[7]`.
- Device ID `0x6320`, product `BW`, vendor `C-3000 IC Design Co., Ltd.`.
- Per card: 65,520 MiB VRAM total, 65,453 MiB available at probe time,
  approximately 64 GiB. GTT total is 257,631 MiB.
- Driver `6.3.31-V1.5.0a`, 80 CUs per card, 1,500 MHz sclk in the probe.
- `/dev/kfd` and eight `/dev/dri/card*` devices are visible.

## Isolated SFT Runtime

From `runs/sft_runtime_v2/venv/bin/python`:

```text
torch 2.7.1+das.opt1.dtk2604 (HIP 6.3.26093)
torchvision 0.22.0+das.opt1.dtk2604.torch271
deepspeed 0.18.2+das.opt1.dtk2604.torch271
flash-attn 2.6.1+das.opt1.dtk2604.torch271
llamafactory 0.9.5
wandb 0.28.1
pip check: No broken requirements found
```

The clean venv currently omits the vendor `triton` distribution. Importing
`flash_attn` in that venv fails with `ModuleNotFoundError: No module named
'triton'`. The host DTK installation contains
`triton 3.1.0+das.opt1.dtk2604.torch271`; exposing that host site-packages
directory only for the smoke command makes FA2 import successfully. The formal
runtime should snapshot/install this exact vendor Triton package instead of
using an unrelated upstream wheel.

## Device Tests

With DTK env sourced, all eight devices are visible to Torch:

```text
torch.cuda.is_available() = True
torch.cuda.device_count() = 8
device 0..7: name BW, total_memory 65,520 MiB, capability 9.3
```

A BF16 matmul forward/backward probe passed independently on all eight cards;
the tiny probe used about 64 MiB peak allocation per card.

FA2 BF16 forward/backward passed with the exact host Triton package exposed:
output shape `(1, 32, 4, 64)`, approximately 0.05 s for the tiny probe.

The existing `scripts/sft_hcu_smoke.py` passed single-rank with the DTK env and
host Triton path, reporting:

```json
{"bf16_backward": true, "flash_attention_2_backward": true,
 "deepspeed_zero2_step": true, "device": "BW", "status": "PASS",
 "torch": "2.7.1"}
```

An inline single-rank ZeRO-3 configuration using the same vendor stack also
completed one BF16 optimizer step (`zero_stage: 3`).

An eight-rank launch reached NCCL process-group initialization on all eight
ranks, but the existing smoke then failed before its optimizer step because it
hardcodes `train_batch_size=1`; with world size 8 DeepSpeed computes a zero
micro-batch and raises `AssertionError: Micro batch size per gpu: 0`. This is a
smoke-script arithmetic limitation, not a device/NCCL failure. The production
YAML has a valid global batch (`per_device_train_batch_size=1`, gradient
accumulation 4, world size 8) and ZeRO-3 auto settings.

## Recommended launch preconditions

1. Source `/opt/dtk-26.04/env.sh` in the training shell or launcher.
2. Add/snapshot the matching vendor Triton package into the isolated SFT venv;
   do not install generic upstream Triton over the HCU build. A temporary
   validated fallback is `PYTHONPATH=/usr/local/lib/python3.11/site-packages`.
3. Run a two- or eight-rank one-step LLaMA-Factory smoke with the actual
   production runtime YAML (its batch arithmetic differs from the old smoke)
   before starting the 1000-trajectory run.

