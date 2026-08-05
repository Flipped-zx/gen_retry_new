#!/usr/bin/env python3
"""Score a frozen edit-stress pair manifest with the official HPSv3 runner.

This is an offline diagnostic. It does not append trajectory events, alter
Geneval2 state, choose a best attempt, or apply an uncalibrated risk policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_revision(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_prompt(task_spec: Path) -> str:
    payload = json.loads(task_spec.read_text(encoding="utf-8"))
    prompt = payload.get("original_prompt")
    if not isinstance(prompt, str) or not prompt:
        raise ValueError(f"missing original_prompt in {task_spec}")
    return prompt


def score_records(
    manifest: dict[str, Any],
    *,
    source_root: Path,
    config_path: Path,
    checkpoint_path: Path,
    official_root: Path,
    device: str,
    batch_size: int,
) -> dict[str, Any]:
    if batch_size != 1:
        raise ValueError("mini-pilot runner currently requires --batch-size 1")
    sys.path.insert(0, str(official_root))
    from hpsv3 import HPSv3RewardInferencer

    inferencer = HPSv3RewardInferencer(
        config_path=str(config_path), checkpoint_path=str(checkpoint_path), device=device
    )
    rows: list[dict[str, Any]] = []
    pairs = manifest["pairs"]
    for pair in pairs:
        episode_dir = source_root / pair["episode_id"]
        prompt = load_prompt(episode_dir / "task_spec.json")
        prompt_sha256 = sha256_text(prompt)
        image_rows = []
        for role, attempt_id in (("parent", pair["parent_attempt_id"]), ("child", pair["child_attempt_id"])):
            image_path = episode_dir / "images" / f"img_{int(attempt_id[2:]):03d}.png"
            if not image_path.exists():
                raise FileNotFoundError(image_path)
            rewards = inferencer.reward(prompts=[prompt], image_paths=[str(image_path)])
            raw_mu = float(rewards[0][0].item())
            raw_log_sigma = float(rewards[0][1].item())
            row = {
                "episode_id": pair["episode_id"],
                "stratum": pair["stratum"],
                "depth": pair["depth"],
                "difficulty": pair["difficulty"],
                "role": role,
                "attempt_id": attempt_id,
                "parent_attempt_id": None if role == "parent" else pair["parent_attempt_id"],
                "image_path": str(image_path),
                "image_sha256": sha256_file(image_path),
                "prompt_sha256": prompt_sha256,
                "status": "success",
                "mu": raw_mu,
                "log_sigma": raw_log_sigma,
                "sigma": math.exp(raw_log_sigma),
            }
            rows.append(row)
            image_rows.append(row)
        parent, child = image_rows
        pair["hpsv3_parent_mu"] = parent["mu"]
        pair["hpsv3_child_mu"] = child["mu"]
        pair["delta_hpsv3"] = child["mu"] - parent["mu"]
        pair["hpsv3_parent_sigma"] = parent["sigma"]
        pair["hpsv3_child_sigma"] = child["sigma"]

    by_stratum: dict[str, list[float]] = {}
    for pair in pairs:
        by_stratum.setdefault(pair["stratum"], []).append(pair["delta_hpsv3"])
    summary = {
        key: {
            "pair_count": len(values),
            "delta_hpsv3_mean": sum(values) / len(values),
            "delta_hpsv3_values": values,
            "delta_hpsv3_negative_count": sum(value < 0 for value in values),
        }
        for key, values in sorted(by_stratum.items())
    }
    return {
        "schema_version": "hpsv3_edit_stress_diagnostic_v1",
        "selection_id": manifest["selection_id"],
        "source_run": manifest["source_run"],
        "prompt_policy": manifest["prompt_policy"],
        "official_hpsv3_revision": git_revision(official_root),
        "config_path": str(config_path),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "preprocess_version": "official-hpsv3-local-config-v1; min_pixels=max_pixels=200704; sdpa",
        "device": device,
        "batch_size": batch_size,
        "scored_at_utc": datetime.now(timezone.utc).isoformat(),
        "interpretation": {
            "mu": "HPSv3 first output, the preference score used for deltas",
            "log_sigma": "HPSv3 second output before uncertainty transform",
            "sigma": "exp(log_sigma); uncertainty only, never a quality score",
            "risk_policy": "not calibrated; no high/watch labels emitted",
        },
        "images": rows,
        "pairs": pairs,
        "summary_by_stratum": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = score_records(
        manifest,
        source_root=args.source_root,
        config_path=args.config,
        checkpoint_path=args.checkpoint,
        official_root=args.official_root,
        device=args.device,
        batch_size=args.batch_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "images": len(report["images"]), "pairs": len(report["pairs"])}, indent=2))


if __name__ == "__main__":
    main()
