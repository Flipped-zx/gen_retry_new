#!/usr/bin/env python3
"""Isolated one-image HPSv3 scorer for the live mini-pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(args.official_root))
    from hpsv3 import HPSv3RewardInferencer

    inferencer = HPSv3RewardInferencer(
        config_path=str(args.config),
        checkpoint_path=str(args.checkpoint),
        device="cuda",
    )
    rewards = inferencer.reward(
        prompts=[args.prompt], image_paths=[str(args.image)]
    )
    mu = float(rewards[0][0].item())
    log_sigma = float(rewards[0][1].item())
    try:
        revision = subprocess.check_output(
            ["git", "-C", str(args.official_root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unknown"
    payload = {
        "schema_version": "hpsv3_live_attempt_score_v1",
        "episode_id": args.episode_id,
        "attempt_id": args.attempt_id,
        "prompt_sha256": hashlib.sha256(args.prompt.encode("utf-8")).hexdigest(),
        "image_path": str(args.image),
        "image_sha256": sha256_file(args.image),
        "mu": mu,
        "log_sigma": log_sigma,
        "sigma": math.exp(log_sigma),
        "official_hpsv3_revision": revision,
        "checkpoint_sha256": sha256_file(args.checkpoint),
        "preprocess_version": "official-hpsv3-local-config-v1; min_pixels=max_pixels=200704; sdpa",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"attempt_id": args.attempt_id, "mu": mu}), flush=True)


if __name__ == "__main__":
    main()
