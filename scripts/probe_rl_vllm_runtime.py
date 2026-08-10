from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from importlib.metadata import version
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the frozen SFT policy with the vendor vLLM runtime."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.75)
    return parser.parse_args()


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    args = _parse_args()
    os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
    started = time.monotonic()
    report: dict[str, object] = {
        "probe_type": "vendor_vllm_single_device_model_smoke",
        "model": str(args.model.resolve()),
        "status": "FAIL",
    }

    try:
        import torch
        from transformers import AutoProcessor
        from vllm import LLM, SamplingParams

        report.update(
            {
                "device_count": torch.cuda.device_count(),
                "torch": torch.__version__,
                "torch_hip": torch.version.hip,
                "verl": version("verl"),
                "vllm": version("vllm"),
            }
        )
        processor = AutoProcessor.from_pretrained(
            args.model,
            trust_remote_code=True,
            fix_mistral_regex=True,
        )
        messages = [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": "You are a runtime smoke-test assistant."}
                ],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": "Reply with exactly OK."}],
            },
        ]
        prompt = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        engine = LLM(
            model=str(args.model.resolve()),
            tensor_parallel_size=1,
            dtype="bfloat16",
            max_model_len=args.max_model_len,
            max_num_seqs=1,
            gpu_memory_utilization=args.gpu_memory_utilization,
            enforce_eager=True,
            disable_log_stats=True,
        )
        report["model_load_seconds"] = round(time.monotonic() - started, 3)
        outputs = engine.generate(
            [prompt],
            SamplingParams(temperature=0.0, max_tokens=args.max_tokens),
            use_tqdm=False,
        )
        report.update(
            {
                "output_text": outputs[0].outputs[0].text,
                "status": "PASS",
                "total_seconds": round(time.monotonic() - started, 3),
            }
        )
    except Exception as exc:
        report.update(
            {
                "error": f"{type(exc).__name__}: {exc}",
                "total_seconds": round(time.monotonic() - started, 3),
            }
        )
        traceback.print_exc()

    _write_report(args.output, report)
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
