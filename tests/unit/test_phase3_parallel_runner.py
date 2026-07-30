from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

from gen_retry.cli import run_phase3_rollouts_parallel as parallel


def _episodes(count: int) -> list[parallel.EpisodeRun]:
    return [
        parallel.EpisodeRun(
            episode_id=f"phase3_ep_{index:03d}",
            run_dir=Path(f"runs/phase3_ep_{index:03d}"),
        )
        for index in range(1, count + 1)
    ]


def test_fixed_device_workers_never_overlap_on_one_device(
    tmp_path: Path,
    monkeypatch,
) -> None:
    lock = threading.Lock()
    active = {0: 0, 1: 0}
    maximum = {0: 0, 1: 0}
    seen: list[str] = []

    def fake_run_one_episode(*, episode, device, log_dir, **kwargs):
        del kwargs
        with lock:
            active[device.index] += 1
            maximum[device.index] = max(maximum[device.index], active[device.index])
            seen.append(episode.episode_id)
        time.sleep(0.01)
        with lock:
            active[device.index] -= 1
        return parallel.WorkerResult(
            episode_id=episode.episode_id,
            device_index=device.index,
            returncode=0,
            log_path=log_dir / f"{episode.episode_id}.log",
        )

    monkeypatch.setattr(parallel, "_run_one_episode", fake_run_one_episode)
    results = parallel._execute_worker_plan(
        episodes=_episodes(8),
        worker_devices=[
            parallel.DeviceInfo(0, 0, "test"),
            parallel.DeviceInfo(1, 0, "test"),
        ],
        run_root=tmp_path,
        image_steps=40,
        image_height=1024,
        image_width=1024,
        teacher_max_completion_tokens=1400,
        log_dir=tmp_path / "logs",
    )

    assert maximum == {0: 1, 1: 1}
    assert len(seen) == len(set(seen)) == 8
    assert len(results) == 8


def test_failed_episode_does_not_stop_device_worker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    seen: list[str] = []

    def fake_run_one_episode(*, episode, device, log_dir, **kwargs):
        del kwargs
        seen.append(episode.episode_id)
        return parallel.WorkerResult(
            episode_id=episode.episode_id,
            device_index=device.index,
            returncode=7 if len(seen) == 1 else 0,
            log_path=log_dir / f"{episode.episode_id}.log",
        )

    monkeypatch.setattr(parallel, "_run_one_episode", fake_run_one_episode)
    results = parallel._execute_worker_plan(
        episodes=_episodes(3),
        worker_devices=[parallel.DeviceInfo(0, 0, "test")],
        run_root=tmp_path,
        image_steps=40,
        image_height=1024,
        image_width=1024,
        teacher_max_completion_tokens=1400,
        log_dir=tmp_path / "logs",
    )

    assert seen == [episode.episode_id for episode in _episodes(3)]
    assert [result.returncode for result in results] == [7, 0, 0]


def test_child_process_sees_exactly_one_physical_device(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured_env = {}
    captured_command = []

    def fake_subprocess_run(command, *, env, **kwargs):
        del kwargs
        captured_command.extend(command)
        captured_env.update(env)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(parallel.subprocess, "run", fake_subprocess_run)
    result = parallel._run_one_episode(
        episode=_episodes(1)[0],
        run_root=tmp_path,
        device=parallel.DeviceInfo(1, 0, "hy-smi"),
        image_steps=40,
        image_height=1024,
        image_width=1024,
        teacher_max_completion_tokens=1400,
        execution_profile_id="qwen_dual_backend",
        log_dir=tmp_path,
    )

    assert result.returncode == 0
    assert captured_env["ROCR_VISIBLE_DEVICES"] == "1"
    assert "CUDA_VISIBLE_DEVICES" not in captured_env
    assert "HIP_VISIBLE_DEVICES" not in captured_env
    profile_index = captured_command.index("--execution-profile-id")
    assert captured_command[profile_index + 1] == "qwen_dual_backend"
