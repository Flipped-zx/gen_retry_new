from __future__ import annotations

import argparse
import os
import queue
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_retry.phase3.model_config import (
    load_model_config,
    select_image_execution_profile,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.reducer import reduce_events


@dataclass(frozen=True)
class DeviceInfo:
    index: int
    vram_percent: int | None
    source: str


@dataclass(frozen=True)
class EpisodeRun:
    episode_id: str
    run_dir: Path


@dataclass(frozen=True)
class WorkerResult:
    episode_id: str
    device_index: int | None
    returncode: int
    log_path: Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Phase 3 rollouts with resource-aware episode-level parallelism."
    )
    parser.add_argument("--run-root", type=Path, default=Path("runs/phase3_hq5"))
    parser.add_argument("--episode-id", action="append", dest="episode_ids")
    parser.add_argument("--image-steps", type=int, default=40)
    parser.add_argument("--generate-image-steps", type=int)
    parser.add_argument("--edit-image-steps", type=int)
    parser.add_argument("--image-height", type=int, default=1024)
    parser.add_argument("--image-width", type=int, default=1024)
    parser.add_argument("--teacher-max-completion-tokens", type=int, default=1400)
    parser.add_argument("--max-workers", type=int)
    parser.add_argument("--max-start-vram-percent", type=int, default=15)
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--allow-low-quality", action="store_true")
    parser.add_argument("--include-submitted", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-dir", type=Path)
    parser.add_argument(
        "--execution-profile-id",
        choices=["qwen_dual_backend", "qwen_image_edit_only"],
    )
    args = parser.parse_args()

    if not args.allow_low_quality:
        _enforce_quality_floor(args.image_steps, args.image_height, args.image_width)

    config = select_image_execution_profile(
        load_model_config(),
        args.execution_profile_id,
    )
    _preflight_config(config)
    episodes = _episode_runs(
        run_root=args.run_root,
        episode_ids=args.episode_ids,
        include_submitted=args.include_submitted,
    )
    if not episodes:
        print("no pending episodes")
        return

    devices = _detect_devices()
    eligible_devices = [
        device
        for device in devices
        if device.vram_percent is None or device.vram_percent <= args.max_start_vram_percent
    ]
    execution = config.resolved_image_execution
    if {
        execution.generate_backend.provider,
        execution.edit_backend.provider,
    } == {"local"}:
        if not eligible_devices and not args.allow_cpu:
            raise SystemExit(
                "no eligible GPU devices found; refusing local Qwen rollout without --allow-cpu"
            )
        if args.allow_cpu and not eligible_devices:
            worker_devices: list[DeviceInfo | None] = [None]
        else:
            worker_devices = eligible_devices
            if args.max_workers is not None:
                worker_devices = worker_devices[: args.max_workers]
    else:
        max_workers = args.max_workers or 1
        worker_devices = [None for _ in range(max_workers)]

    if not worker_devices:
        raise SystemExit("worker plan is empty")

    log_dir = args.log_dir or args.run_root / "parallel_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    _print_plan(
        episodes=episodes,
        worker_devices=worker_devices,
        image_steps=args.image_steps,
        generate_image_steps=args.generate_image_steps,
        edit_image_steps=args.edit_image_steps,
        image_height=args.image_height,
        image_width=args.image_width,
        log_dir=log_dir,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        return

    results = _execute_worker_plan(
        episodes=episodes,
        worker_devices=worker_devices,
        run_root=args.run_root,
        image_steps=args.image_steps,
        generate_image_steps=args.generate_image_steps,
        edit_image_steps=args.edit_image_steps,
        image_height=args.image_height,
        image_width=args.image_width,
        teacher_max_completion_tokens=args.teacher_max_completion_tokens,
        execution_profile_id=args.execution_profile_id,
        log_dir=log_dir,
    )
    for result in results:
        print(
            f"{result.episode_id}: returncode={result.returncode}; "
            f"device={result.device_index if result.device_index is not None else 'cpu'}; "
            f"log={result.log_path}"
        )

    failed = [result for result in results if result.returncode != 0]
    if failed:
        failed_ids = ", ".join(result.episode_id for result in failed)
        raise SystemExit(f"failed episodes: {failed_ids}")


def _enforce_quality_floor(image_steps: int, image_height: int, image_width: int) -> None:
    if image_steps < 40 or image_height < 1024 or image_width < 1024:
        raise SystemExit(
            "refusing low-quality rollout params; use at least 40 steps and 1024 x 1024 "
            "or pass --allow-low-quality for an explicit diagnostic run"
        )


def _preflight_config(config: Any) -> None:
    api_key_state = "SET" if os.environ.get(config.teacher.api_key_env) else "MISSING"
    base_url_state = "SET" if os.environ.get(config.teacher.base_url_env) else "MISSING"
    print(f"{config.teacher.api_key_env}={api_key_state}")
    print(f"{config.teacher.base_url_env}={base_url_state}")
    print(f"teacher_model_id={config.teacher.model_id}")
    execution = config.resolved_image_execution
    print(
        "execution_profile="
        f"{execution.profile_id}@{execution.profile_version}"
    )
    for operation, backend in (
        ("generate", execution.generate_backend),
        ("edit", execution.edit_backend),
    ):
        print(f"{operation}_image_provider={backend.provider}")
        print(f"{operation}_image_backend={backend.backend_id}")
        print(f"{operation}_image_model_path_exists={backend.model_path.exists()}")
    if api_key_state != "SET" or base_url_state != "SET":
        raise SystemExit("teacher environment is incomplete")
    for operation, backend in (
        ("generate", execution.generate_backend),
        ("edit", execution.edit_backend),
    ):
        if backend.provider != "local":
            raise SystemExit(
                f"unsupported {operation} image provider for this runner: {backend.provider}"
            )
        if not backend.model_path.exists():
            raise SystemExit(f"missing {operation} model path: {backend.model_path}")


def _episode_runs(
    *,
    run_root: Path,
    episode_ids: list[str] | None,
    include_submitted: bool,
) -> list[EpisodeRun]:
    if episode_ids:
        candidates = [run_root / episode_id for episode_id in episode_ids]
    else:
        candidates = sorted(path for path in run_root.glob("phase3_ep_*") if path.is_dir())
    episodes: list[EpisodeRun] = []
    for run_dir in candidates:
        task_spec_path = run_dir / "task_spec.json"
        if not task_spec_path.exists():
            raise SystemExit(f"missing task_spec.json in {run_dir}")
        episode_id = run_dir.name
        if not include_submitted and _is_submitted(run_dir):
            continue
        episodes.append(EpisodeRun(episode_id=episode_id, run_dir=run_dir))
    return episodes


def _is_submitted(run_dir: Path) -> bool:
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        return False
    state = reduce_events(load_events_jsonl(events_path))
    return state.submitted_attempt_id is not None


def _detect_devices() -> list[DeviceInfo]:
    devices = _detect_devices_with_hy_smi()
    if devices:
        return devices
    return _detect_devices_with_torch()


def _detect_devices_with_hy_smi() -> list[DeviceInfo]:
    if shutil.which("hy-smi") is None:
        return []
    try:
        completed = subprocess.run(
            ["hy-smi"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    devices: list[DeviceInfo] = []
    for line in completed.stdout.splitlines():
        columns = line.split()
        if len(columns) < 6 or not columns[0].isdigit():
            continue
        vram_percent = None
        if columns[5].endswith("%"):
            try:
                vram_percent = int(columns[5][:-1])
            except ValueError:
                vram_percent = None
        devices.append(
            DeviceInfo(
                index=int(columns[0]),
                vram_percent=vram_percent,
                source="hy-smi",
            )
        )
    return devices


def _detect_devices_with_torch() -> list[DeviceInfo]:
    try:
        import torch

        if not torch.cuda.is_available():
            return []
        return [
            DeviceInfo(index=index, vram_percent=None, source="torch")
            for index in range(torch.cuda.device_count())
        ]
    except Exception:
        return []


def _print_plan(
    *,
    episodes: list[EpisodeRun],
    worker_devices: list[DeviceInfo | None],
    image_steps: int,
    generate_image_steps: int | None = None,
    edit_image_steps: int | None = None,
    image_height: int,
    image_width: int,
    log_dir: Path,
    dry_run: bool,
) -> None:
    device_labels = [
        (
            f"{device.source}:{device.index}"
            + (
                f"({device.vram_percent}% vram)"
                if device is not None and device.vram_percent is not None
                else ""
            )
        )
        if device is not None
        else "cpu"
        for device in worker_devices
    ]
    print(f"episodes={len(episodes)}")
    print(f"workers={len(worker_devices)}")
    print(f"worker_devices={','.join(device_labels)}")
    print(f"render_params=steps:{image_steps},height:{image_height},width:{image_width}")
    print(
        "profile_step_overrides="
        f"generate:{generate_image_steps},edit:{edit_image_steps}"
    )
    print(f"log_dir={log_dir}")
    print(f"dry_run={dry_run}")


def _run_one_episode(
    *,
    episode: EpisodeRun,
    run_root: Path,
    device: DeviceInfo | None,
    image_steps: int,
    generate_image_steps: int | None = None,
    edit_image_steps: int | None = None,
    image_height: int,
    image_width: int,
    teacher_max_completion_tokens: int,
    execution_profile_id: str | None = None,
    log_dir: Path,
) -> WorkerResult:
    log_path = log_dir / f"{episode.episode_id}.log"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "src" if not existing_pythonpath else f"src{os.pathsep}{existing_pythonpath}"
    for variable in (
        "CUDA_VISIBLE_DEVICES",
        "HIP_VISIBLE_DEVICES",
        "ROCR_VISIBLE_DEVICES",
    ):
        env.pop(variable, None)
    if device is not None:
        device_value = str(device.index)
        if device.source == "hy-smi":
            env["ROCR_VISIBLE_DEVICES"] = device_value
        else:
            env["CUDA_VISIBLE_DEVICES"] = device_value
    command = [
        sys.executable,
        "-m",
        "gen_retry.cli.run_phase3_rollouts",
        "--run-root",
        str(run_root),
        "--episode-id",
        episode.episode_id,
        "--image-steps",
        str(image_steps),
        "--image-height",
        str(image_height),
        "--image-width",
        str(image_width),
        "--teacher-max-completion-tokens",
        str(teacher_max_completion_tokens),
    ]
    if generate_image_steps is not None:
        command.extend(["--generate-image-steps", str(generate_image_steps)])
    if edit_image_steps is not None:
        command.extend(["--edit-image-steps", str(edit_image_steps)])
    if execution_profile_id is not None:
        command.extend(["--execution-profile-id", execution_profile_id])
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"run_started_at={datetime.now(UTC).isoformat().replace('+00:00', 'Z')}\n"
        )
        log_file.write(f"episode_id={episode.episode_id}\n")
        log_file.write(f"device={device.index if device is not None else 'cpu'}\n")
        log_file.write(
            "visible_devices="
            f"{env.get('ROCR_VISIBLE_DEVICES', env.get('CUDA_VISIBLE_DEVICES', 'cpu'))}\n"
        )
        log_file.write(f"command={' '.join(command)}\n\n")
        log_file.flush()
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    return WorkerResult(
        episode_id=episode.episode_id,
        device_index=device.index if device is not None else None,
        returncode=completed.returncode,
        log_path=log_path,
    )


def _execute_worker_plan(
    *,
    episodes: list[EpisodeRun],
    worker_devices: list[DeviceInfo | None],
    run_root: Path,
    image_steps: int,
    generate_image_steps: int | None = None,
    edit_image_steps: int | None = None,
    image_height: int,
    image_width: int,
    teacher_max_completion_tokens: int,
    execution_profile_id: str | None = None,
    log_dir: Path,
) -> list[WorkerResult]:
    pending: queue.Queue[EpisodeRun] = queue.Queue()
    for episode in episodes:
        pending.put(episode)

    results: list[WorkerResult] = []
    with ThreadPoolExecutor(max_workers=len(worker_devices)) as executor:
        futures = [
            executor.submit(
                _run_device_worker,
                pending=pending,
                run_root=run_root,
                device=device,
                image_steps=image_steps,
                generate_image_steps=generate_image_steps,
                edit_image_steps=edit_image_steps,
                image_height=image_height,
                image_width=image_width,
                teacher_max_completion_tokens=teacher_max_completion_tokens,
                execution_profile_id=execution_profile_id,
                log_dir=log_dir,
            )
            for device in worker_devices
        ]
        for future in futures:
            results.extend(future.result())
    return sorted(results, key=lambda result: result.episode_id)


def _run_device_worker(
    *,
    pending: queue.Queue[EpisodeRun],
    run_root: Path,
    device: DeviceInfo | None,
    image_steps: int,
    generate_image_steps: int | None = None,
    edit_image_steps: int | None = None,
    image_height: int,
    image_width: int,
    teacher_max_completion_tokens: int,
    execution_profile_id: str | None = None,
    log_dir: Path,
) -> list[WorkerResult]:
    results: list[WorkerResult] = []
    while True:
        try:
            episode = pending.get_nowait()
        except queue.Empty:
            return results
        try:
            result = _run_one_episode(
                episode=episode,
                run_root=run_root,
                device=device,
                image_steps=image_steps,
                generate_image_steps=generate_image_steps,
                edit_image_steps=edit_image_steps,
                image_height=image_height,
                image_width=image_width,
                teacher_max_completion_tokens=teacher_max_completion_tokens,
                execution_profile_id=execution_profile_id,
                log_dir=log_dir,
            )
            results.append(result)
        finally:
            pending.task_done()


if __name__ == "__main__":
    main()
