from __future__ import annotations

import os
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
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
