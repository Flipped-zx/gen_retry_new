from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.domain.artifacts import (
    artifact_path,
    sha256_file,
    validate_artifact_manifest_closure,
)
from gen_retry.protocol.trajectory_validator import validate_artifact_manifest_semantics
from gen_retry.tools.fake_geneval2_adapter import FakeGeneval2Adapter
from gen_retry.tools.fake_qianwen_image_edit_adapter import FakeQianwenImageEditAdapter


ROOT = Path(__file__).resolve().parents[2]


def test_fake_adapters_write_idempotent_manifest_closed_artifacts(tmp_path: Path) -> None:
    task_spec = json.loads(
        (ROOT / "tests" / "fixtures" / "task_spec" / "geneval2_minimal.json").read_text(
            encoding="utf-8"
        )
    )
    qianwen = FakeQianwenImageEditAdapter(artifact_root=tmp_path)
    image = qianwen.generate(
        request_id="req_1",
        attempt_id="a_000",
        image_artifact_id="img_000",
    )
    evaluator = FakeGeneval2Adapter(
        {
            "a_000": [
                {"constraint_id": "c_001", "status": "pass"},
                {"constraint_id": "c_002", "status": "pass"},
                {"constraint_id": "c_003", "status": "pass"},
                {"constraint_id": "c_004", "status": "pass"},
            ]
        },
        artifact_root=tmp_path,
    )
    report = evaluator.evaluate_to_report(task_spec=task_spec, attempt_id="a_000")

    manifest = {
        "schema_version": "0.2",
        "episode_id": task_spec["episode_id"],
        "artifacts": [image.manifest_entry, report.manifest_entry],
    }
    validate_artifact_manifest_semantics(manifest)
    validate_artifact_manifest_closure(manifest, tmp_path)
    assert image.artifact_sha256 == sha256_file(artifact_path(tmp_path, image.artifact_uri))
    assert report.report_sha256 == sha256_file(artifact_path(tmp_path, report.report_ref))

    assert qianwen.generate(
        request_id="req_1",
        attempt_id="a_000",
        image_artifact_id="img_000",
    ) == image
    assert evaluator.evaluate_to_report(task_spec=task_spec, attempt_id="a_000") == report

    with pytest.raises(ValueError, match="artifact conflict"):
        qianwen.generate(
            request_id="req_changed",
            attempt_id="a_000",
            image_artifact_id="img_000",
        )


def test_manifest_closure_rejects_nonportable_or_missing_uris(tmp_path: Path) -> None:
    manifest = {
        "schema_version": "0.2",
        "episode_id": "ep_bad_artifact",
        "artifacts": [
            {
                "artifact_id": "img_000",
                "artifact_type": "image",
                "uri": "/tmp/img_000.png",
                "sha256": "a" * 64,
                "media_type": "image/png",
                "producer": "fake_qianwen_image_edit_adapter",
            }
        ],
    }
    with pytest.raises(ValueError, match="run-relative POSIX path"):
        validate_artifact_manifest_closure(manifest, tmp_path)

    manifest["artifacts"][0]["uri"] = "artifacts/images/missing.png"
    with pytest.raises(ValueError, match="missing file"):
        validate_artifact_manifest_closure(manifest, tmp_path)
