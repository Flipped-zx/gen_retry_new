from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_bytes, write_artifact_bytes
from gen_retry.runtime.json_canonical import canonical_json


@dataclass(frozen=True)
class FakeImageResult:
    request_id: str
    attempt_id: str
    parent_attempt_id: str | None
    operation: str
    backend: str
    image_artifact_id: str
    artifact_uri: str
    artifact_manifest_ref: str
    artifact_sha256: str
    manifest_entry: dict[str, Any]


class FakeQianwenImageEditAdapter:
    backend = "qianwen_image_edit"

    def __init__(self, *, artifact_root: Path | None = None):
        self.artifact_root = artifact_root

    def generate(self, *, request_id: str, attempt_id: str, image_artifact_id: str) -> FakeImageResult:
        return self._build_result(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=None,
            operation="generate",
            image_artifact_id=image_artifact_id,
        )

    def edit(
        self,
        *,
        request_id: str,
        attempt_id: str,
        source_attempt_id: str,
        image_artifact_id: str,
    ) -> FakeImageResult:
        return self._build_result(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=source_attempt_id,
            operation="edit",
            image_artifact_id=image_artifact_id,
        )

    def _build_result(
        self,
        *,
        request_id: str,
        attempt_id: str,
        parent_attempt_id: str | None,
        operation: str,
        image_artifact_id: str,
    ) -> FakeImageResult:
        artifact_uri = f"artifacts/images/{image_artifact_id}.mock.json"
        artifact_payload = {
            "schema_version": "0.2",
            "request_id": request_id,
            "attempt_id": attempt_id,
            "parent_attempt_id": parent_attempt_id,
            "operation": operation,
            "backend": self.backend,
            "image_artifact_id": image_artifact_id,
        }
        artifact_bytes = canonical_json(artifact_payload).encode("utf-8")
        artifact_sha256 = (
            write_artifact_bytes(self.artifact_root, artifact_uri, artifact_bytes)
            if self.artifact_root is not None
            else sha256_bytes(artifact_bytes)
        )
        manifest_entry = artifact_manifest_entry(
            artifact_id=image_artifact_id,
            attempt_id=attempt_id,
            artifact_type="image",
            uri=artifact_uri,
            sha256=artifact_sha256,
            media_type="application/vnd.gen-retry.mock-image+json",
            producer="fake_qianwen_image_edit_adapter",
            metadata={
                "backend": self.backend,
                "operation": operation,
                "request_id": request_id,
            },
        )
        return FakeImageResult(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=parent_attempt_id,
            operation=operation,
            backend=self.backend,
            image_artifact_id=image_artifact_id,
            artifact_uri=artifact_uri,
            artifact_manifest_ref="artifacts/manifest.json",
            artifact_sha256=artifact_sha256,
            manifest_entry=manifest_entry,
        )
