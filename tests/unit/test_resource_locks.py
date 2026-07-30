from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from gen_retry.tools.resource_locks import (
    exclusive_device_execution,
    exclusive_episode_execution,
    exclusive_scheduler_execution,
    teacher_api_slot,
)


def test_device_lock_serializes_same_physical_device(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GEN_RETRY_RESOURCE_LOCK_ROOT", str(tmp_path / "locks"))
    monkeypatch.setenv("GEN_RETRY_PHYSICAL_DEVICE_ID", "3")
    guard = threading.Lock()
    active = 0
    maximum = 0

    def worker() -> None:
        nonlocal active, maximum
        with exclusive_device_execution():
            with guard:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.02)
            with guard:
                active -= 1

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert maximum == 1


def test_teacher_slots_bound_cross_worker_activity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GEN_RETRY_RESOURCE_LOCK_ROOT", str(tmp_path / "locks"))
    monkeypatch.setenv("GEN_RETRY_TEACHER_CONCURRENCY", "2")
    guard = threading.Lock()
    active = 0
    maximum = 0

    def worker() -> None:
        nonlocal active, maximum
        with teacher_api_slot():
            with guard:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.02)
            with guard:
                active -= 1

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert maximum == 2


@pytest.mark.parametrize(
    ("lock_factory", "lock_path"),
    [
        (lambda path: exclusive_episode_execution(path), "phase3_ep_001"),
        (lambda path: exclusive_scheduler_execution(path), "run_root"),
    ],
)
def test_nonblocking_execution_locks_reject_duplicate_owner(
    tmp_path: Path,
    lock_factory,
    lock_path: str,
) -> None:
    target = tmp_path / lock_path
    target.mkdir()

    with lock_factory(target):
        with pytest.raises(RuntimeError, match="active"):
            with lock_factory(target):
                pass
