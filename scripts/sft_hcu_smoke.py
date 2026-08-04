from __future__ import annotations

import json
import os

import torch


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "HCU device is unavailable; run this inside an allocated HCU job"
        )
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    torch.cuda.set_device(local_rank)
    device = torch.device("cuda", local_rank)

    left = torch.randn(64, 64, device=device, dtype=torch.bfloat16, requires_grad=True)
    right = torch.randn(64, 64, device=device, dtype=torch.bfloat16, requires_grad=True)
    left.matmul(right).float().mean().backward()
    torch.cuda.synchronize()

    from flash_attn import flash_attn_func

    query = torch.randn(
        1, 32, 4, 64, device=device, dtype=torch.bfloat16, requires_grad=True
    )
    key = torch.randn_like(query, requires_grad=True)
    value = torch.randn_like(query, requires_grad=True)
    flash_attn_func(query, key, value).float().mean().backward()
    torch.cuda.synchronize()

    import deepspeed

    # DeepSpeed expects the global batch to be at least one per worker.
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    train_batch_size = max(world_size, 1)
    model = torch.nn.Linear(64, 64, bias=False)
    engine, _, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        config={
            "train_batch_size": train_batch_size,
            "train_micro_batch_size_per_gpu": 1,
            "gradient_accumulation_steps": 1,
            "bf16": {"enabled": True},
            "zero_optimization": {"stage": 2},
            "optimizer": {
                "type": "AdamW",
                "params": {"lr": 1e-5, "betas": [0.9, 0.95]},
            },
        },
    )
    loss = (
        engine(torch.randn(1, 64, device=device, dtype=torch.bfloat16)).float().mean()
    )
    engine.backward(loss)
    engine.step()
    torch.cuda.synchronize()
    if local_rank == 0:
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "torch": torch.__version__,
                    "device": torch.cuda.get_device_name(local_rank),
                    "bf16_backward": True,
                    "flash_attention_2_backward": True,
                    "deepspeed_zero2_step": True,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
