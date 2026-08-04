from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DEFAULT_MODEL_LOAD_LOCK = Path("/tmp/gen_retry_local_model_load.lock")


@contextmanager
def exclusive_model_load() -> Iterator[None]:
    """Serialize transient host-memory peaks while local models load."""

    import fcntl

    lock_path = Path(
        os.environ.get("GEN_RETRY_MODEL_LOAD_LOCK", str(DEFAULT_MODEL_LOAD_LOCK))
    )
    concurrency = int(os.environ.get("GEN_RETRY_MODEL_LOAD_CONCURRENCY", "1"))
    if concurrency <= 0:
        raise ValueError("GEN_RETRY_MODEL_LOAD_CONCURRENCY must be positive")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if concurrency == 1:
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        return

    while True:
        for index in range(concurrency):
            slot_path = lock_path.with_name(f"{lock_path.name}.slot_{index:03d}")
            lock_file = slot_path.open("a+", encoding="utf-8")
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_file.close()
                continue
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            return
        time.sleep(0.05)
