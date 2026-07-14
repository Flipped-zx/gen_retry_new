from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FakeImageResult:
    request_id: str
    attempt_id: str
    parent_attempt_id: str | None
    operation: str
    backend: str
    image_artifact_id: str
    artifact_manifest_ref: str
    artifact_sha256: str


class FakeQianwenImageEditAdapter:
    backend = "qianwen_image_edit"

    def generate(self, *, request_id: str, attempt_id: str, image_artifact_id: str) -> FakeImageResult:
        return FakeImageResult(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=None,
            operation="generate",
            backend=self.backend,
            image_artifact_id=image_artifact_id,
            artifact_manifest_ref="artifacts/manifest.json",
            artifact_sha256=_fake_hash(image_artifact_id),
        )

    def edit(
        self,
        *,
        request_id: str,
        attempt_id: str,
        source_attempt_id: str,
        image_artifact_id: str,
    ) -> FakeImageResult:
        return FakeImageResult(
            request_id=request_id,
            attempt_id=attempt_id,
            parent_attempt_id=source_attempt_id,
            operation="edit",
            backend=self.backend,
            image_artifact_id=image_artifact_id,
            artifact_manifest_ref="artifacts/manifest.json",
            artifact_sha256=_fake_hash(image_artifact_id),
        )


def _fake_hash(value: str) -> str:
    return (value.replace("_", "") + "0" * 64)[:64]
