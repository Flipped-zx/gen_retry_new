from __future__ import annotations

import hashlib
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_run_relative_uri(uri: str) -> None:
    if not uri:
        raise ValueError("artifact uri must not be empty")
    if uri.startswith("/") or "://" in uri or "\\" in uri or ":" in uri:
        raise ValueError(f"artifact uri must be run-relative POSIX path: {uri}")
    path = PurePosixPath(uri)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"artifact uri must be run-relative POSIX path: {uri}")


def artifact_path(root: Path, uri: str) -> Path:
    validate_run_relative_uri(uri)
    return root.joinpath(*PurePosixPath(uri).parts)


def write_artifact_bytes(root: Path, uri: str, data: bytes) -> str:
    path = artifact_path(root, uri)
    expected_sha256 = sha256_bytes(data)
    if path.exists():
        existing_sha256 = sha256_file(path)
        if existing_sha256 != expected_sha256:
            raise ValueError(f"artifact conflict for {uri}: existing content differs")
        return existing_sha256

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    with tmp_path.open("wb") as fh:
        fh.write(data)
    tmp_path.replace(path)
    return expected_sha256


def validate_artifact_manifest_closure(manifest: dict[str, Any], root: Path) -> None:
    for artifact in manifest.get("artifacts", []):
        uri = artifact["uri"]
        path = artifact_path(root, uri)
        if not path.is_file():
            raise ValueError(f"artifact manifest references missing file: {uri}")
        actual_sha256 = sha256_file(path)
        if actual_sha256 != artifact["sha256"]:
            raise ValueError(
                f"artifact manifest hash mismatch for {uri}: "
                f"expected {artifact['sha256']} got {actual_sha256}"
            )


def artifact_manifest_entry(
    *,
    artifact_id: str,
    artifact_type: str,
    uri: str,
    sha256: str,
    media_type: str,
    producer: str,
    attempt_id: str | None = None,
    created_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_run_relative_uri(uri)
    entry: dict[str, Any] = {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "uri": uri,
        "sha256": sha256,
        "media_type": media_type,
        "producer": producer,
    }
    if attempt_id is not None:
        entry["attempt_id"] = attempt_id
    if created_at is not None:
        entry["created_at"] = created_at
    if metadata is not None:
        entry["metadata"] = metadata
    return entry
