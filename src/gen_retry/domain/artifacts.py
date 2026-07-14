from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_manifest_entry(
    *,
    artifact_id: str,
    artifact_type: str,
    uri: str,
    sha256: str,
    media_type: str,
    producer: str,
    attempt_id: str | None = None,
) -> dict[str, str]:
    entry = {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "uri": uri,
        "sha256": sha256,
        "media_type": media_type,
        "producer": producer,
    }
    if attempt_id is not None:
        entry["attempt_id"] = attempt_id
    return entry
