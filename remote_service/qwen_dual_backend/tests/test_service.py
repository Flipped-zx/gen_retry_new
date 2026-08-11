from __future__ import annotations

import base64
import io
import sys
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from qwen_dual_backend.app import create_app
from qwen_dual_backend.config import Settings
from qwen_dual_backend.errors import ServiceError
from qwen_dual_backend.jobs import JobManager, public_job
from qwen_dual_backend.runtime import (
    EXPECTED_PIPELINE_CLASSES,
    Accelerator,
    RuntimeRegistry,
)
from qwen_dual_backend.schemas import EditRequest
from qwen_dual_backend.store import StateStore
from qwen_dual_backend.utils import canonical_json, sha256_bytes, utc_now


def png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (32, 24), (10, 20, 30)).save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    generate = tmp_path / "models" / "Qwen-Image-2512"
    edit = tmp_path / "models" / "Qwen-Image-Edit-2511"
    for path, pipeline in (
        (generate, "QwenImagePipeline"),
        (edit, "QwenImageEditPlusPipeline"),
    ):
        path.mkdir(parents=True)
        (path / "model_index.json").write_text(
            "{\\\"_class_name\\\": \\\"" + pipeline + "\\\"}"
        )
    return Settings(
        service_root=tmp_path,
        state_root=tmp_path / "state",
        generate_model_path=generate,
        edit_model_path=edit,
        allowed_staging_root=tmp_path / "state" / "staging",
        bearer_token="test-secret",
        max_workers=1,
    )


class FakeManager:
    def __init__(self, settings: Settings, registry: RuntimeRegistry):
        self.settings = settings
        self.registry = registry
        self.store = StateStore(settings.state_root)
        self.records: dict[str, dict[str, Any]] = {}
        self.recovery_errors: list[str] = []

    def start(self) -> None: pass
    def stop(self) -> None: pass
    def queue_status(self) -> dict[str, int]:
        return {"pending": 0, "capacity": 4, "active": 0, "workers": 1}

    def submit(self, kind: str, payload: dict[str, Any], source_png=None, source_metadata=None):
        digest = sha256_bytes(canonical_json(payload))
        existing = self.records.get(payload["request_id"])
        if existing:
            if existing["payload_sha256"] != digest:
                raise ServiceError(409, "idempotency_conflict", "request_id conflict")
            return existing, True
        result_bytes = png_bytes()
        result_path = self.store.write_output(payload["request_id"], "png", result_bytes)
        source = None
        if kind == "edit":
            assert source_png is not None and source_metadata is not None
            source_path = self.store.write_source(payload["request_id"], source_png)
            source = {**source_metadata, "artifact_path": str(source_path)}
        record = {
            "service": "qwen_dual_backend@1", "request_id": payload["request_id"],
            "kind": kind, "state": "succeeded", "payload_sha256": digest,
            "canonical_payload": payload, "submitted_at": utc_now(),
            "started_at": utc_now(), "completed_at": utc_now(), "timing": {},
            "model": self.registry.model_identity(kind), "source": source, "error": None,
            "result": {
                "artifact_path": str(result_path),
                "result_url": f"/v1/results/{payload['request_id']}",
                "sha256": sha256_bytes(result_bytes), "bytes": len(result_bytes),
                "media_type": "image/png", "width": 32, "height": 24,
                "seed": payload["seed"], "provenance": {"internal": "/secret/path"},
            },
        }
        self.records[payload["request_id"]] = record
        return record, False

    def get(self, request_id: str):
        if request_id not in self.records:
            raise ServiceError(404, "job_not_found", "no job exists", request_id=request_id)
        return self.records[request_id]


@pytest.fixture
def client(settings: Settings):
    registry = RuntimeRegistry(
        settings,
        accelerators=[Accelerator(0, "internal-device", 1234)],
        versions={"torch": "test"},
    )
    registry.set_device_state(0, kind="generate", state="ready")
    manager = FakeManager(settings, registry)
    with TestClient(create_app(settings, registry, manager)) as test_client:
        yield test_client, manager


def auth() -> dict[str, str]:
    return {"Authorization": "Bearer test-secret"}


def generate_payload(request_id="gen-1"):
    return {"request_id": request_id, "prompt": "test", "width": 256, "height": 256,
            "num_inference_steps": 1, "output_format": "png"}


def test_auth_ready_capabilities_and_openapi_are_sanitized(client):
    test_client, _ = client
    assert test_client.get("/v1/capabilities").status_code == 401
    ready = test_client.get("/readyz")
    assert ready.status_code == 200
    capabilities = test_client.get("/v1/capabilities", headers=auth())
    assert capabilities.status_code == 200
    assert capabilities.json()["edit"]["model"]["id"] == "Qwen-Image-Edit-2511"
    schema = test_client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/v1/edit" in schema.json()["paths"]
    combined = ready.text + capabilities.text
    for forbidden in ("/root/", "state_root", "device_name", "artifact_path", "internal-device"):
        assert forbidden not in combined


def test_edit_only_host_can_use_edit_readiness(settings: Settings):
    edit_settings = replace(settings, ready_kind="edit", preload_kind="edit")
    registry = RuntimeRegistry(
        edit_settings,
        accelerators=[Accelerator(0, "internal-device", 1234)],
        versions={"torch": "test"},
    )
    registry.set_device_state(0, kind="edit", state="ready")
    manager = FakeManager(edit_settings, registry)
    with TestClient(create_app(edit_settings, registry, manager)) as test_client:
        response = test_client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["ready_kind"] == "edit"


def test_generate_replay_conflict_404_and_result(client):
    test_client, _ = client
    first = test_client.post("/v1/generate", json=generate_payload(), headers=auth())
    assert first.status_code == 200
    assert first.json()["idempotent_replay"] is False
    assert "artifact_path" not in first.text
    replay = test_client.post("/v1/generate", json=generate_payload(), headers=auth())
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    changed = generate_payload()
    changed["prompt"] = "changed"
    assert test_client.post("/v1/generate", json=changed, headers=auth()).status_code == 409
    assert test_client.get("/v1/jobs/missing", headers=auth()).status_code == 404
    result = test_client.get("/v1/results/gen-1", headers=auth())
    assert result.status_code == 200
    assert result.headers["x-artifact-sha256"] == sha256_bytes(result.content)


def test_edit_validates_source_and_returns_source_and_result_digests(client):
    test_client, manager = client
    source = png_bytes()
    body = generate_payload("edit-1") | {
        "source_attempt_id": "attempt-1",
        "source_image_base64": base64.b64encode(source).decode(),
        "source_image_sha256": sha256_bytes(source),
        "guidance_scale": 1.0,
    }
    response = test_client.post("/v1/edit", json=body, headers=auth())
    assert response.status_code == 200
    data = response.json()
    assert len(data["source"]["sha256"]) == 64
    assert len(data["result"]["sha256"]) == 64
    assert data["source"]["source_attempt_id"] == "attempt-1"
    assert data["source"]["sha256"] == sha256_bytes(source)
    assert data["parameters"]["guidance_scale"] == 1.0
    assert manager.records["edit-1"]["canonical_payload"]["source"]["sha256"] == sha256_bytes(source)
    assert "artifact_path" not in response.text
    invalid = body | {"request_id": "edit-bad", "source_image_base64": "not-base64"}
    assert test_client.post("/v1/edit", json=invalid, headers=auth()).status_code == 422
    mismatch = body | {"request_id": "edit-mismatch", "source_image_sha256": "0" * 64}
    response = test_client.post("/v1/edit", json=mismatch, headers=auth())
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "source_digest_mismatch"


def test_edit_contract_schema_and_pipeline_class():
    schema = EditRequest.model_json_schema()
    assert {"source_image_sha256", "source_attempt_id"} <= set(schema["required"])
    assert schema["properties"]["source_image_sha256"]["pattern"] == "^[0-9a-f]{64}$"
    assert schema["properties"]["guidance_scale"]["minimum"] == 0.0
    assert schema["properties"]["guidance_scale"]["maximum"] == 20.0
    assert EXPECTED_PIPELINE_CLASSES["edit"] == "QwenImageEditPlusPipeline"


def test_edit_runtime_passes_guidance_scale(settings: Settings, monkeypatch, tmp_path: Path):
    registry = RuntimeRegistry(
        settings, accelerators=[Accelerator(0, "fake", 1)], versions={}
    )
    runtime = registry.runtime(0)
    captured: dict[str, Any] = {}

    class FakePipeline:
        def __call__(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(images=[Image.new("RGB", (256, 256))])

    class FakeGenerator:
        def __init__(self, device):
            self.device = device

        def manual_seed(self, seed):
            self.seed = seed
            return self

    monkeypatch.setattr(runtime, "ensure_loaded", lambda kind: FakePipeline())
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(Generator=FakeGenerator, inference_mode=nullcontext),
    )
    source_path = tmp_path / "source.png"
    source_path.write_bytes(png_bytes())
    payload = {
        "prompt": "edit test",
        "negative_prompt": None,
        "width": 256,
        "height": 256,
        "num_inference_steps": 1,
        "true_cfg_scale": 4.0,
        "guidance_scale": 2.5,
        "seed": 7,
    }

    runtime.infer("edit", payload, source_path)

    assert captured["guidance_scale"] == 2.5
    assert captured["true_cfg_scale"] == 4.0
    assert isinstance(captured["image"], Image.Image)


def test_missing_edit_model_is_503_without_path(settings: Settings):
    settings.edit_model_path.rename(settings.edit_model_path.with_name("missing"))
    registry = RuntimeRegistry(settings, accelerators=[Accelerator(0, "hidden", 1)], versions={})
    manager = FakeManager(settings, registry)
    with TestClient(create_app(settings, registry, manager)) as test_client:
        response = test_client.post("/v1/edit", json={}, headers=auth())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "edit_model_unavailable"
    assert str(settings.edit_model_path) not in response.text


def test_public_job_whitelists_nested_metadata(settings: Settings):
    registry = RuntimeRegistry(settings, accelerators=[Accelerator(0, "hidden", 1)], versions={})
    manager = FakeManager(settings, registry)
    record, _ = manager.submit("generate", generate_payload("public-1") | {"seed": 1,
        "negative_prompt": None, "true_cfg_scale": 4.0})
    response = public_job(record)
    assert "artifact_path" not in str(response)
    assert "provenance" not in str(response)
