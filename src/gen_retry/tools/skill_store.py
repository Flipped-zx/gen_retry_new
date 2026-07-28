from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes


SKILL_VERSIONS = {
    "counting_and_instance_layout": "2.0.0",
    "spatial_relation_layout": "2.0.0",
    "attribute_entity_binding": "1.0.0",
    "local_edit_preservation": "2.0.0",
    "action_pose_relation": "1.0.0",
    "object_identity_presence": "1.0.0",
}


@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    version: str
    content: str
    content_ref: str
    content_sha256: str
    summary: str

    def event_payload_entry(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "content_ref": self.content_ref,
            "content_sha256": self.content_sha256,
            "summary": self.summary,
        }


class LocalSkillStore:
    def __init__(self, root: Path = Path("skills"), *, version: str | None = None):
        self.root = root
        self.version = version

    def get_many(self, skill_ids: list[str]) -> list[SkillRecord]:
        return [self.get(skill_id) for skill_id in skill_ids]

    def get(self, skill_id: str) -> SkillRecord:
        path = self.root / skill_id / "SKILL.md"
        if not path.exists():
            raise KeyError(f"unknown skill_id: {skill_id}")
        content = path.read_text(encoding="utf-8")
        return SkillRecord(
            skill_id=skill_id,
            version=self.version or SKILL_VERSIONS.get(skill_id, "0.2.0-deprecated"),
            content=content,
            content_ref=str(path),
            content_sha256=sha256_bytes(content.encode("utf-8")),
            summary=_summary(content),
        )


def _summary(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:400]
    return "Local retry skill guidance."
