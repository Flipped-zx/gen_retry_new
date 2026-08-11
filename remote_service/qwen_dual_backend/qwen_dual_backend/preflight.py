from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any

from . import SERVICE_IDENTITY
from .config import Settings
from .errors import safe_error_summary
from .runtime import RuntimeRegistry


def model_file_audit(path: Path) -> dict[str, Any]:
    required = [
        "model_index.json",
        "scheduler/scheduler_config.json",
        "text_encoder/config.json",
        "tokenizer/tokenizer_config.json",
        "transformer/config.json",
        "vae/config.json",
        "vae/diffusion_pytorch_model.safetensors",
    ]
    indexed_files: set[str] = set()
    index_errors: list[str] = []
    for relative in (
        "text_encoder/model.safetensors.index.json",
        "transformer/diffusion_pytorch_model.safetensors.index.json",
    ):
        index_path = path / relative
        required.append(relative)
        if not index_path.is_file():
            continue
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            prefix = str(Path(relative).parent)
            indexed_files.update(f"{prefix}/{name}" for name in index["weight_map"].values())
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            index_errors.append(f"{relative}: {type(exc).__name__}")
    required.extend(sorted(indexed_files))
    missing = [relative for relative in required if not (path / relative).is_file()]
    return {
        "path": str(path),
        "present": path.is_dir(),
        "required_file_count": len(set(required)),
        "missing_files": sorted(set(missing)),
        "index_errors": index_errors,
        "complete": path.is_dir() and not missing and not index_errors,
    }


def run_preflight(args: argparse.Namespace) -> tuple[dict[str, Any], bool]:
    settings = Settings.from_env()
    settings.ensure_directories()
    registry = RuntimeRegistry(settings)
    report: dict[str, Any] = {
        "service": SERVICE_IDENTITY,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "state_root": str(settings.state_root),
        "versions": registry.versions,
        "accelerator_count": registry.device_count(),
        "accelerators": registry.readiness()["accelerators"],
        "generate": model_file_audit(settings.generate_model_path),
        "edit": model_file_audit(settings.edit_model_path),
        "load_requested": args.load,
        "load_results": [],
    }
    success = (
        report["generate"]["complete"]
        and registry.device_count() >= 1
        and registry.versions.get("torch") is not None
        and registry.versions.get("diffusers") is not None
    )
    if args.load:
        if args.devices == "all":
            device_indices = registry.worker_devices()
        else:
            try:
                device_indices = [int(args.devices)]
            except ValueError:
                report["load_results"].append(
                    {"state": "failed", "safe_error": "devices must be 'all' or an integer"}
                )
                return report, False
        for kind in args.kind:
            unavailable = registry.availability_error(kind)
            if unavailable:
                report["load_results"].append(
                    {
                        "kind": kind,
                        "state": "failed",
                        "safe_error": unavailable.message,
                        "details": unavailable.details,
                    }
                )
                success = False
                continue
            for device_index in device_indices:
                try:
                    registry.runtime(device_index).ensure_loaded(kind)
                    report["load_results"].append(
                        {
                            "kind": kind,
                            "device_index": device_index,
                            "state": "ready",
                            "smoke_test": "passed",
                        }
                    )
                except Exception as exc:
                    report["load_results"].append(
                        {
                            "kind": kind,
                            "device_index": device_index,
                            "state": "failed",
                            "safe_error": safe_error_summary(exc),
                        }
                    )
                    success = False
        report["readiness"] = registry.readiness()
    return report, success


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and optionally load local Qwen models")
    parser.add_argument(
        "--load", action="store_true", help="load the pipeline and run its narrow smoke test"
    )
    parser.add_argument(
        "--kind",
        action="append",
        choices=("generate", "edit"),
        default=None,
        help="model kind to load; may be repeated (default: generate)",
    )
    parser.add_argument(
        "--devices", default="0", help="device index or 'all' (default: 0)"
    )
    args = parser.parse_args()
    args.kind = args.kind or ["generate"]
    report, success = run_preflight(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
