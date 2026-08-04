from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_retry.tools.resource_locks import exclusive_scheduler_execution


@dataclass(frozen=True)
class BaselineJob:
    episode_id: str
    variant_index: int


def main() -> None:
    parser = argparse.ArgumentParser(description="Run raw-prompt baseline jobs across fixed devices.")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--device-id", type=int, action="append", dest="device_ids", required=True)
    parser.add_argument("--log-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if len(args.device_ids) != len(set(args.device_ids)) or any(item < 0 for item in args.device_ids):
        raise SystemExit("--device-id values must be unique non-negative integers")
    plan = _read_json(args.run_root / "baseline_plan.json")
    jobs = _pending_jobs(args.run_root, plan)
    log_dir = args.log_dir or args.run_root / "parallel_logs"
    print(f"pending_jobs={len(jobs)}")
    print(f"devices={','.join(str(item) for item in args.device_ids)}")
    print(f"log_dir={log_dir}")
    if args.dry_run or not jobs:
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    pending: queue.Queue[BaselineJob] = queue.Queue()
    for job in jobs:
        pending.put(job)
    with exclusive_scheduler_execution(args.run_root):
        with ThreadPoolExecutor(max_workers=len(args.device_ids)) as executor:
            futures = [
                executor.submit(
                    _device_worker,
                    pending=pending,
                    run_root=args.run_root,
                    log_dir=log_dir,
                    device_id=device_id,
                )
                for device_id in args.device_ids
            ]
            results = [result for future in futures for result in future.result()]
    failed = [result for result in results if result[2] != 0]
    for episode_id, variant_index, returncode, log_path in sorted(results):
        print(
            f"{episode_id} variant={variant_index} returncode={returncode} "
            f"log={log_path}",
            flush=True,
        )
    if failed:
        raise SystemExit(f"{len(failed)} raw-prompt baseline jobs failed")


def _pending_jobs(run_root: Path, plan: dict[str, Any]) -> list[BaselineJob]:
    jobs = []
    for episode in plan["episodes"]:
        for variant_index in range(int(plan["variant_count"])):
            result_path = (
                run_root
                / episode["episode_id"]
                / f"variant_{variant_index:03d}"
                / "result.json"
            )
            if not result_path.exists():
                jobs.append(BaselineJob(episode["episode_id"], variant_index))
    return jobs


def _device_worker(
    *,
    pending: queue.Queue[BaselineJob],
    run_root: Path,
    log_dir: Path,
    device_id: int,
) -> list[tuple[str, int, int, Path]]:
    results = []
    while True:
        try:
            job = pending.get_nowait()
        except queue.Empty:
            return results
        try:
            results.append(
                _run_job(
                    job=job,
                    run_root=run_root,
                    log_dir=log_dir,
                    device_id=device_id,
                )
            )
        finally:
            pending.task_done()


def _run_job(
    *,
    job: BaselineJob,
    run_root: Path,
    log_dir: Path,
    device_id: int,
) -> tuple[str, int, int, Path]:
    log_path = log_dir / f"{job.episode_id}_variant_{job.variant_index:03d}.log"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"
    for variable in ("CUDA_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES", "ROCR_VISIBLE_DEVICES"):
        env.pop(variable, None)
    device_value = str(device_id)
    env["GEN_RETRY_PHYSICAL_DEVICE_ID"] = device_value
    env["ROCR_VISIBLE_DEVICES"] = device_value
    command = [
        sys.executable,
        "-m",
        "gen_retry.cli.run_qwen_raw_prompt_baseline",
        "--run-root",
        str(run_root),
        "--episode-id",
        job.episode_id,
        "--variant-index",
        str(job.variant_index),
    ]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"started_at={datetime.now(UTC).isoformat().replace('+00:00', 'Z')}\n"
        )
        handle.write(f"physical_device_id={device_id}\n")
        handle.write(f"command={' '.join(command)}\n\n")
        handle.flush()
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return job.episode_id, job.variant_index, completed.returncode, log_path


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


if __name__ == "__main__":
    main()
