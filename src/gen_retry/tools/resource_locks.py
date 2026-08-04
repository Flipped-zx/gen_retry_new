from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


LOCK_VERSION = "1"
DEFAULT_LOCK_ROOT = Path("/tmp/gen_retry_resource_locks")


def physical_device_id() -> str:
    explicit = os.environ.get("GEN_RETRY_PHYSICAL_DEVICE_ID")
    if explicit:
        return explicit
    for variable in ("ROCR_VISIBLE_DEVICES", "CUDA_VISIBLE_DEVICES"):
        visible = os.environ.get(variable)
        if visible and "," not in visible:
            return visible
    return "cpu"


@contextmanager
def exclusive_device_execution() -> Iterator[None]:
    """Hold one physical device from model load through final GPU cleanup."""

    device_id = _safe_lock_name(physical_device_id())
    with _exclusive_lock(_lock_root() / f"device_{device_id}.lock", blocking=True):
        yield


@contextmanager
def exclusive_any_device_execution(device_ids: list[int]) -> Iterator[int]:
    """Acquire one currently free physical device for a short shared service call."""

    if not device_ids:
        raise ValueError("device_ids must not be empty")
    normalized = list(dict.fromkeys(device_ids))
    if any(device_id < 0 for device_id in normalized):
        raise ValueError("device IDs must be non-negative")
    while True:
        for device_id in normalized:
            lock = _try_lock(_lock_root() / f"device_{device_id}.lock")
            if lock is None:
                continue
            try:
                yield device_id
            finally:
                _unlock(lock)
            return
        time.sleep(0.05)


@contextmanager
def exclusive_episode_execution(run_dir: Path) -> Iterator[None]:
    """Reject concurrent executors for one append-only episode."""

    with _exclusive_lock(
        run_dir / ".episode_execution.lock",
        blocking=False,
        busy_message=f"episode already has an active executor: {run_dir.name}",
    ):
        yield


@contextmanager
def exclusive_scheduler_execution(run_root: Path) -> Iterator[None]:
    """Reject overlapping GPU schedulers for one rollout root."""

    with _exclusive_lock(
        run_root / ".scheduler_execution.lock",
        blocking=False,
        busy_message=f"run root already has an active scheduler: {run_root}",
    ):
        yield


@contextmanager
def teacher_api_slot() -> Iterator[None]:
    """Bound Teacher requests across all rollout child processes."""

    slot_count = int(os.environ.get("GEN_RETRY_TEACHER_CONCURRENCY", "8"))
    if slot_count <= 0:
        raise ValueError("GEN_RETRY_TEACHER_CONCURRENCY must be positive")
    slot_root = _lock_root() / "teacher_slots"
    slot_root.mkdir(parents=True, exist_ok=True)
    while True:
        for index in range(slot_count):
            lock_path = slot_root / f"slot_{index:03d}.lock"
            lock = _try_lock(lock_path)
            if lock is None:
                continue
            try:
                yield
            finally:
                _unlock(lock)
            return
        time.sleep(0.05)


@contextmanager
def _exclusive_lock(
    path: Path,
    *,
    blocking: bool,
    busy_message: str | None = None,
) -> Iterator[None]:
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = path.open("a+", encoding="utf-8")
    flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
    try:
        try:
            fcntl.flock(lock_file.fileno(), flags)
        except BlockingIOError as exc:
            raise RuntimeError(busy_message or f"resource lock is busy: {path}") from exc
        yield
    finally:
        _unlock(lock_file)


def _try_lock(path: Path):
    import fcntl

    lock_file = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        return None
    return lock_file


def _unlock(lock_file) -> None:
    import fcntl

    if lock_file.closed:
        return
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()


def _lock_root() -> Path:
    return Path(os.environ.get("GEN_RETRY_RESOURCE_LOCK_ROOT", str(DEFAULT_LOCK_ROOT)))


def _safe_lock_name(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)
