from __future__ import annotations

import base64
import binascii
import hmac
import io
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from . import SERVICE_IDENTITY, SERVICE_NAME, SERVICE_VERSION
from .config import Settings
from .errors import ServiceError
from .jobs import JobManager, public_job
from .runtime import RuntimeRegistry
from .schemas import EditRequest, GenerateRequest, RequestId, validation_errors
from .store import StateStore
from .utils import derived_seed, sha256_bytes, utc_now


def _normalize_source(
    raw: bytes, settings: Settings, representation: str, source_attempt_id: str
) -> tuple[bytes, dict[str, Any]]:
    if not raw:
        raise ServiceError(422, "empty_source_image", "source image is empty")
    if len(raw) > settings.max_source_bytes:
        raise ServiceError(
            413,
            "source_image_too_large",
            "source image exceeds the configured byte limit",
            details={"max_source_bytes": settings.max_source_bytes},
        )
    try:
        with Image.open(io.BytesIO(raw)) as opened:
            opened.load()
            width, height = opened.size
            if width <= 0 or height <= 0 or width * height > settings.max_source_pixels:
                raise ServiceError(
                    422,
                    "source_dimensions_invalid",
                    "source image dimensions exceed the configured pixel limit",
                    details={"max_source_pixels": settings.max_source_pixels},
                )
            normalized = ImageOps.exif_transpose(opened).convert("RGB")
            output = io.BytesIO()
            normalized.save(output, format="PNG", compress_level=6)
    except ServiceError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ServiceError(
            422,
            "source_image_invalid",
            "source image could not be decoded safely",
            details={"type": type(exc).__name__},
        ) from exc
    content = output.getvalue()
    return content, {
        "source_attempt_id": source_attempt_id,
        "representation": representation,
        "sha256": sha256_bytes(raw),
        "normalized_sha256": sha256_bytes(content),
        "bytes": len(content),
        "width": normalized.width,
        "height": normalized.height,
        "normalized_format": "png",
    }


def _read_staged_source(path_text: str, settings: Settings) -> bytes:
    candidate = Path(path_text)
    if not candidate.is_absolute():
        candidate = settings.allowed_staging_root / candidate
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(settings.allowed_staging_root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ServiceError(
            422,
            "staged_path_not_allowed",
            "staged source must be a regular file under the configured staging root",
        ) from exc
    if not resolved.is_file():
        raise ServiceError(
            422,
            "staged_path_invalid",
            "staged source is not a regular file",
        )
    if resolved.stat().st_size > settings.max_source_bytes:
        raise ServiceError(
            413,
            "source_image_too_large",
            "staged source exceeds the configured byte limit",
            details={"max_source_bytes": settings.max_source_bytes},
        )
    with resolved.open("rb") as handle:
        return handle.read(settings.max_source_bytes + 1)


def _decode_base64_source(value: str, settings: Settings) -> bytes:
    encoded = value
    if value.startswith("data:"):
        header, separator, encoded = value.partition(",")
        if not separator or ";base64" not in header:
            raise ServiceError(422, "source_base64_invalid", "invalid base64 data URL")
    if len(encoded) > ((settings.max_source_bytes + 2) // 3) * 4 + 16:
        raise ServiceError(
            413,
            "source_image_too_large",
            "base64 source exceeds the configured byte limit",
        )
    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ServiceError(
            422, "source_base64_invalid", "source_image_base64 is not valid base64"
        ) from exc


def _canonical_inference(request: GenerateRequest | EditRequest, kind: str) -> dict[str, Any]:
    excluded = {"source_image_base64", "source_staged_path", "source_image_sha256"}
    payload = request.model_dump(mode="json", exclude=excluded)
    payload["kind"] = kind
    if payload["seed"] is None:
        payload["seed"] = derived_seed(payload["request_id"])
    return payload


def _validate_resource_limits(payload: dict[str, Any], settings: Settings) -> None:
    pixels = payload["width"] * payload["height"]
    if pixels > settings.max_image_pixels:
        raise ServiceError(
            422,
            "image_dimensions_too_large",
            "requested dimensions exceed the configured pixel limit",
            request_id=payload["request_id"],
            details={"requested_pixels": pixels, "max_image_pixels": settings.max_image_pixels},
        )


def create_app(
    settings: Settings | None = None,
    registry: RuntimeRegistry | None = None,
    manager: JobManager | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_directories()
    registry = registry or RuntimeRegistry(settings)
    manager = manager or JobManager(settings, registry)
    store = manager.store

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        manager.start()
        app.state.started_at = utc_now()
        app.state.started_monotonic = time.monotonic()
        try:
            yield
        finally:
            manager.stop()

    app = FastAPI(
        title=SERVICE_IDENTITY,
        version=SERVICE_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.registry = registry
    app.state.manager = manager

    @app.middleware("http")
    async def request_limits_and_auth(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length is None:
                error = ServiceError(
                    411, "content_length_required", "Content-Length is required"
                )
                return JSONResponse(error.body(), status_code=error.status_code)
            try:
                length = int(content_length)
            except ValueError:
                length = -1
            if length < 0 or length > settings.max_body_bytes:
                error = ServiceError(
                    413,
                    "request_body_too_large",
                    "request body exceeds the configured byte limit",
                    details={"max_body_bytes": settings.max_body_bytes},
                )
                return JSONResponse(error.body(), status_code=error.status_code)
        if settings.bearer_token and request.url.path.startswith("/v1/"):
            authorization = request.headers.get("authorization", "")
            expected = f"Bearer {settings.bearer_token}"
            if not hmac.compare_digest(authorization, expected):
                error = ServiceError(
                    401,
                    "authentication_required",
                    "a valid bearer token is required",
                )
                return JSONResponse(
                    error.body(),
                    status_code=error.status_code,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return await call_next(request)

    @app.exception_handler(ServiceError)
    async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(exc.body(), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        error = ServiceError(
            422,
            "request_validation_failed",
            "request schema validation failed",
            details={"errors": validation_errors(exc.errors())},
        )
        return JSONResponse(error.body(), status_code=422)

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": SERVICE_IDENTITY,
            "pid": os.getpid(),
            "started_at": app.state.started_at,
            "uptime_seconds": round(time.monotonic() - app.state.started_monotonic, 3),
        }

    @app.get("/readyz")
    async def readyz() -> JSONResponse:
        readiness = registry.public_readiness()
        readiness.update(
            {
                "service": SERVICE_IDENTITY,
                "ready": readiness[settings.ready_kind]["ready"],
                "ready_kind": settings.ready_kind,
                "queue": manager.queue_status(),
                "state_recovery_error_count": len(manager.recovery_errors),
            }
        )
        return JSONResponse(readiness, status_code=200 if readiness["ready"] else 503)

    @app.get("/v1/capabilities")
    async def capabilities() -> dict[str, Any]:
        readiness = registry.public_readiness()
        return {
            "service": SERVICE_IDENTITY,
            "asynchronous": True,
            "idempotency": {"key": "request_id", "same_payload": "replay", "different_payload_status": 409},
            "limits": {
                "width": {"min": 256, "max": 1664, "multiple_of": 16},
                "height": {"min": 256, "max": 1664, "multiple_of": 16},
                "max_pixels": settings.max_image_pixels,
                "num_inference_steps": {"min": 1, "max": 100},
                "output_formats": ["png", "jpeg", "webp"],
            },
            "generate": readiness["generate"],
            "edit": readiness["edit"],
        }

    @app.post("/v1/generate")
    async def generate(request: GenerateRequest) -> JSONResponse:
        payload = _canonical_inference(request, "generate")
        _validate_resource_limits(payload, settings)
        record, replay = manager.submit("generate", payload)
        response = public_job(record)
        response["idempotent_replay"] = replay
        status_code = 202 if record["state"] in {"queued", "running"} else 200
        return JSONResponse(response, status_code=status_code)

    @app.post("/v1/edit")
    async def edit(request: Request) -> JSONResponse:
        unavailable = registry.availability_error("edit")
        if unavailable:
            raise unavailable
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        source_upload: UploadFile | None = None
        try:
            if content_type == "application/json":
                raw_body = await request.json()
                if not isinstance(raw_body, dict):
                    raise ServiceError(422, "request_validation_failed", "JSON body must be an object")
                edit_request = EditRequest.model_validate(raw_body)
            elif content_type == "multipart/form-data":
                form = await request.form(
                    max_files=1, max_fields=20, max_part_size=settings.max_source_bytes + 1
                )
                values: dict[str, Any] = {}
                seen: set[str] = set()
                for key, value in form.multi_items():
                    if key in seen:
                        raise ServiceError(
                            422,
                            "duplicate_form_field",
                            f"multipart field {key!r} may appear only once",
                        )
                    seen.add(key)
                    if key == "source_image" and isinstance(value, UploadFile):
                        source_upload = value
                    else:
                        values[key] = value
                edit_request = EditRequest.model_validate(
                    values, context={"source_upload": source_upload is not None}
                )
            else:
                raise ServiceError(
                    415,
                    "unsupported_media_type",
                    "edit requests must use application/json or multipart/form-data",
                )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc

        if source_upload is not None:
            raw_source = await source_upload.read(settings.max_source_bytes + 1)
            representation = "multipart_upload"
        elif edit_request.source_image_base64 is not None:
            raw_source = _decode_base64_source(
                edit_request.source_image_base64, settings
            )
            representation = "base64"
        else:
            assert edit_request.source_staged_path is not None
            raw_source = _read_staged_source(edit_request.source_staged_path, settings)
            representation = "staged_path"

        source_png, source_metadata = _normalize_source(
            raw_source, settings, representation, edit_request.source_attempt_id
        )
        if not hmac.compare_digest(
            source_metadata["sha256"], edit_request.source_image_sha256
        ):
            raise ServiceError(
                422,
                "source_digest_mismatch",
                "source image does not match source_image_sha256",
                retryable=False,
                request_id=edit_request.request_id,
            )
        payload = _canonical_inference(edit_request, "edit")
        payload["source"] = {
            key: source_metadata[key]
            for key in (
                "source_attempt_id",
                "sha256",
                "normalized_sha256",
                "bytes",
                "width",
                "height",
            )
        }
        _validate_resource_limits(payload, settings)
        record, replay = manager.submit(
            "edit", payload, source_png=source_png, source_metadata=source_metadata
        )
        response = public_job(record)
        response["idempotent_replay"] = replay
        status_code = 202 if record["state"] in {"queued", "running"} else 200
        return JSONResponse(response, status_code=status_code)

    @app.get("/v1/jobs/{request_id}")
    async def get_job(request_id: RequestId) -> dict[str, Any]:
        return public_job(manager.get(request_id))

    @app.get("/v1/results/{request_id}")
    async def get_result(request_id: RequestId) -> FileResponse:
        record = manager.get(request_id)
        if record["state"] != "succeeded" or not record.get("result"):
            raise ServiceError(
                409,
                "result_not_ready",
                "job does not have a successful result",
                retryable=record["state"] in {"queued", "running"},
                request_id=request_id,
                details={"state": record["state"]},
            )
        if not store.artifact_is_valid(record["result"]):
            raise ServiceError(
                410,
                "result_artifact_unavailable",
                "result artifact is missing or failed checksum validation",
                request_id=request_id,
            )
        result = record["result"]
        suffix = Path(result["artifact_path"]).suffix
        return FileResponse(
            result["artifact_path"],
            media_type=result["media_type"],
            filename=f"{request_id}{suffix}",
            content_disposition_type="inline",
            headers={
                "ETag": f'"{result["sha256"]}"',
                "X-Artifact-SHA256": result["sha256"],
            },
        )

    return app


app = create_app()
