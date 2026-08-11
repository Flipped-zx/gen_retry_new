from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .utils import atomic_write_bytes, atomic_write_json, sha256_file


class StateStore:
    def __init__(self, state_root: Path) -> None:
        self.root = state_root
        self.jobs_root = state_root / "jobs"
        self.artifacts_root = state_root / "artifacts"

    def job_path(self, request_id: str) -> Path:
        return self.jobs_root / f"{request_id}.json"

    def write_job(self, record: dict[str, Any]) -> None:
        atomic_write_json(self.job_path(record["request_id"]), record)

    def load_jobs(self) -> tuple[dict[str, dict[str, Any]], list[str]]:
        records: dict[str, dict[str, Any]] = {}
        errors: list[str] = []
        for path in sorted(self.jobs_root.glob("*.json")):
            try:
                with path.open("rb") as handle:
                    record = json.load(handle)
                request_id = record["request_id"]
                if path.name != f"{request_id}.json":
                    raise ValueError("request_id does not match filename")
                records[request_id] = record
            except Exception as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
        return records, errors

    def source_path(self, request_id: str) -> Path:
        return self.artifacts_root / request_id / "source.png"

    def write_source(self, request_id: str, content: bytes) -> Path:
        path = self.source_path(request_id)
        atomic_write_bytes(path, content)
        return path

    def output_path(self, request_id: str, output_format: str) -> Path:
        suffix = {"png": "png", "jpeg": "jpg", "webp": "webp"}[output_format]
        return self.artifacts_root / request_id / f"output.{suffix}"

    def write_output(self, request_id: str, output_format: str, content: bytes) -> Path:
        path = self.output_path(request_id, output_format)
        atomic_write_bytes(path, content)
        return path

    @staticmethod
    def artifact_is_valid(metadata: dict[str, Any] | None) -> bool:
        if not metadata:
            return False
        try:
            path = Path(metadata["artifact_path"])
            return (
                path.is_file()
                and path.stat().st_size == metadata["bytes"]
                and sha256_file(path) == metadata["sha256"]
            )
        except (KeyError, OSError):
            return False
