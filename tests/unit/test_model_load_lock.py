from __future__ import annotations

import threading
import time
from pathlib import Path

from gen_retry.tools.model_load_lock import exclusive_model_load


def test_model_load_lock_serializes_concurrent_load_sections(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GEN_RETRY_MODEL_LOAD_LOCK", str(tmp_path / "model.lock"))
    state_lock = threading.Lock()
    active = 0
    maximum = 0

    def worker() -> None:
        nonlocal active, maximum
        with exclusive_model_load():
            with state_lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.02)
            with state_lock:
                active -= 1

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert maximum == 1
