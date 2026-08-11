from __future__ import annotations

import copy
import io
import queue
import threading
import time
from pathlib import Path
from typing import Any

from PIL import Image

from . import SERVICE_IDENTITY
from .config import Settings
from .errors import ServiceError, safe_error_summary
from .runtime import RuntimeRegistry
from .store import StateStore
from .utils import canonical_json, sha256_bytes, utc_now


_MIME_TYPES = {"png": "image/png", "jpeg": "image/jpeg", "webp": "image/webp"}


def encode_image(image: Image.Image, output_format: str) -> bytes:
    buffer = io.BytesIO()
    if output_format == "png":
        image.save(buffer, format="PNG", compress_level=6)
    elif output_format == "jpeg":
        image.convert("RGB").save(buffer, format="JPEG", quality=95, optimize=True)
    elif output_format == "webp":
        image.convert("RGB").save(buffer, format="WEBP", quality=95, method=6)
    else:
        raise ValueError(f"unsupported output format: {output_format}")
    return buffer.getvalue()


class JobManager:
    def __init__(
        self,
        settings: Settings,
        registry: RuntimeRegistry,
        store: StateStore | None = None,
    ) -> None:
        self.settings = settings
        self.registry = registry
        self.store = store or StateStore(settings.state_root)
        self._queue: queue.Queue[str | None] = queue.Queue(maxsize=settings.queue_size)
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._submit_lock = threading.Lock()
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self.recovery_errors: list[str] = []
        self.started = False

    def start(self) -> None:
        if self.started:
            return
        records, self.recovery_errors = self.store.load_jobs()
        recoverable: list[str] = []
        with self._lock:
            self._records = records
            for request_id, record in self._records.items():
                state = record.get("state")
                if state == "succeeded" and not self.store.artifact_is_valid(
                    record.get("result")
                ):
                    self._fail_record(
                        record,
                        "artifact_missing_or_corrupt",
                        "persisted result artifact is missing or does not match its checksum",
                        retryable=False,
                    )
                    self.store.write_job(record)
                elif state in {"queued", "running"}:
                    record["state"] = "queued"
                    record["recovery_count"] = int(record.get("recovery_count", 0)) + 1
                    record["updated_at"] = utc_now()
                    record["device"] = None
                    self.store.write_job(record)
                    recoverable.append(request_id)

        for request_id in recoverable:
            try:
                self._queue.put_nowait(request_id)
            except queue.Full:
                with self._lock:
                    record = self._records[request_id]
                    self._fail_record(
                        record,
                        "recovery_queue_saturated",
                        "job could not be restored because the recovery queue is full",
                        retryable=True,
                    )
                    self.store.write_job(record)

        for device_index in self.registry.worker_devices():
            thread = threading.Thread(
                target=self._worker,
                args=(device_index,),
                name=f"qwen-device-{device_index}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)
        self.started = True

        preload_kind = self.settings.preload_kind
        if self.settings.preload_models and not self.registry.availability_error(preload_kind):
            for device_index in self.registry.worker_devices():
                threading.Thread(
                    target=self._preload,
                    args=(device_index, preload_kind),
                    name=f"qwen-preload-{device_index}",
                    daemon=True,
                ).start()

    def stop(self) -> None:
        self._stop.set()
        for _ in self._threads:
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                break
        for thread in self._threads:
            thread.join(timeout=2)

    def _preload(self, device_index: int, kind: str) -> None:
        try:
            self.registry.runtime(device_index).ensure_loaded(kind)
        except Exception:
            return

    def submit(
        self,
        kind: str,
        canonical_payload: dict[str, Any],
        source_png: bytes | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], bool]:
        request_id = canonical_payload["request_id"]
        payload_hash = sha256_bytes(canonical_json(canonical_payload))
        with self._submit_lock:
            with self._lock:
                existing = self._records.get(request_id)
                if existing is not None:
                    if existing.get("payload_sha256") != payload_hash:
                        raise ServiceError(
                            409,
                            "idempotency_conflict",
                            "request_id already exists with a different canonical payload",
                            retryable=False,
                            request_id=request_id,
                            details={
                                "existing_payload_sha256": existing.get("payload_sha256"),
                                "incoming_payload_sha256": payload_hash,
                            },
                        )
                    return copy.deepcopy(existing), True

                unavailable = self.registry.availability_error(kind)
                if unavailable:
                    unavailable.request_id = request_id
                    raise unavailable
                if self._queue.full():
                    raise ServiceError(
                        429,
                        "queue_saturated",
                        "all pending job slots are occupied",
                        retryable=True,
                        request_id=request_id,
                        details={"queue_capacity": self.settings.queue_size},
                    )

                submitted_at = utc_now()
                record: dict[str, Any] = {
                    "schema_version": 1,
                    "service": SERVICE_IDENTITY,
                    "request_id": request_id,
                    "kind": kind,
                    "state": "queued",
                    "payload_sha256": payload_hash,
                    "canonical_payload": canonical_payload,
                    "prompt_sha256": sha256_bytes(canonical_payload["prompt"].encode("utf-8")),
                    "submitted_at": submitted_at,
                    "submitted_at_epoch": time.time(),
                    "updated_at": submitted_at,
                    "started_at": None,
                    "completed_at": None,
                    "recovery_count": 0,
                    "attempts": 0,
                    "model": self.registry.model_identity(kind),
                    "versions": dict(self.registry.versions),
                    "device": None,
                    "source": None,
                    "timing": None,
                    "result": None,
                    "error": None,
                }
                if kind == "edit":
                    if source_png is None or source_metadata is None:
                        raise RuntimeError("normalized edit source is required")
                    source_path = self.store.write_source(request_id, source_png)
                    record["source"] = {
                        **source_metadata,
                        "artifact_path": str(source_path),
                    }
                self.store.write_job(record)
                self._records[request_id] = record
                self._queue.put_nowait(request_id)
                return copy.deepcopy(record), False

    def get(self, request_id: str) -> dict[str, Any]:
        with self._lock:
            record = self._records.get(request_id)
            if record is None:
                raise ServiceError(
                    404,
                    "job_not_found",
                    "no job exists for request_id",
                    retryable=False,
                    request_id=request_id,
                )
            return copy.deepcopy(record)

    def queue_status(self) -> dict[str, int]:
        with self._lock:
            running = sum(1 for item in self._records.values() if item.get("state") == "running")
        return {
            "pending": self._queue.qsize(),
            "capacity": self.settings.queue_size,
            "active": running,
            "workers": len(self._threads),
        }

    def _worker(self, device_index: int) -> None:
        while not self._stop.is_set():
            try:
                request_id = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if request_id is None:
                self._queue.task_done()
                return
            try:
                self._execute(request_id, device_index)
            finally:
                self._queue.task_done()

    def _execute(self, request_id: str, device_index: int) -> None:
        with self._lock:
            record = self._records.get(request_id)
            if record is None or record.get("state") != "queued":
                return
            queue_seconds = max(0.0, time.time() - record["submitted_at_epoch"])
            if queue_seconds > self.settings.queue_timeout_seconds:
                self._fail_record(
                    record,
                    "queue_timeout",
                    "job exceeded the configured queue wait timeout",
                    retryable=True,
                    timing={"queue_seconds": round(queue_seconds, 3)},
                )
                self.store.write_job(record)
                return
            record["state"] = "running"
            record["started_at"] = utc_now()
            record["updated_at"] = record["started_at"]
            record["attempts"] = int(record.get("attempts", 0)) + 1
            record["device"] = {
                "index": device_index,
                "name": self.registry.device_state(device_index)["device_name"],
            }
            record["error"] = None
            self.store.write_job(record)
            kind = record["kind"]
            payload = copy.deepcopy(record["canonical_payload"])
            source_path = Path(record["source"]["artifact_path"]) if record["source"] else None

        inference_started = time.perf_counter()
        try:
            image, runtime_provenance = self.registry.runtime(device_index).infer(
                kind, payload, source_path
            )
            inference_seconds = time.perf_counter() - inference_started
            if inference_seconds > self.settings.inference_timeout_seconds:
                raise ServiceError(
                    504,
                    "inference_timeout",
                    "model call exceeded the configured inference timeout",
                    retryable=True,
                    request_id=request_id,
                    details={
                        "timeout_seconds": self.settings.inference_timeout_seconds,
                        "elapsed_seconds": round(inference_seconds, 3),
                    },
                )
            output_format = payload["output_format"]
            content = encode_image(image, output_format)
            artifact_path = self.store.write_output(request_id, output_format, content)
            result = {
                "artifact_path": str(artifact_path),
                "result_url": f"/v1/results/{request_id}",
                "sha256": sha256_bytes(content),
                "bytes": len(content),
                "media_type": _MIME_TYPES[output_format],
                "width": image.width,
                "height": image.height,
                "seed": payload["seed"],
                "provenance": {
                    "service": SERVICE_IDENTITY,
                    "request_id": request_id,
                    "request_payload_sha256": record["payload_sha256"],
                    "prompt_sha256": record["prompt_sha256"],
                    "model": record["model"],
                    "versions": record["versions"],
                    "parameters": {
                        "width": payload["width"],
                        "height": payload["height"],
                        "seed": payload["seed"],
                        "num_inference_steps": payload["num_inference_steps"],
                        "true_cfg_scale": payload["true_cfg_scale"],
                        "output_format": output_format,
                    },
                    "source": record["source"],
                    "runtime": runtime_provenance,
                },
            }
            completed_at = utc_now()
            with self._lock:
                current = self._records[request_id]
                current["state"] = "succeeded"
                current["completed_at"] = completed_at
                current["updated_at"] = completed_at
                current["timing"] = {
                    "queue_seconds": round(queue_seconds, 3),
                    "inference_seconds": round(inference_seconds, 3),
                    "total_seconds": round(queue_seconds + inference_seconds, 3),
                }
                current["result"] = result
                current["error"] = None
                self.store.write_job(current)
        except Exception as exc:
            inference_seconds = time.perf_counter() - inference_started
            with self._lock:
                current = self._records[request_id]
                if isinstance(exc, ServiceError):
                    error = {
                        "code": exc.code,
                        "message": exc.message,
                        "retryable": exc.retryable,
                        "summary": exc.details.get("summary"),
                    }
                else:
                    error = {
                        "code": "inference_failed",
                        "message": "model inference failed",
                        "retryable": True,
                        "summary": safe_error_summary(exc),
                    }
                current["state"] = "failed"
                current["completed_at"] = utc_now()
                current["updated_at"] = current["completed_at"]
                current["timing"] = {
                    "queue_seconds": round(queue_seconds, 3),
                    "inference_seconds": round(inference_seconds, 3),
                    "total_seconds": round(queue_seconds + inference_seconds, 3),
                }
                current["error"] = error
                self.store.write_job(current)

    @staticmethod
    def _fail_record(
        record: dict[str, Any],
        code: str,
        message: str,
        retryable: bool,
        timing: dict[str, Any] | None = None,
    ) -> None:
        record["state"] = "failed"
        record["completed_at"] = utc_now()
        record["updated_at"] = record["completed_at"]
        record["timing"] = timing
        record["error"] = {
            "code": code,
            "message": message,
            "retryable": retryable,
            "summary": None,
        }


def public_job(record: dict[str, Any]) -> dict[str, Any]:
    payload = record["canonical_payload"]
    response: dict[str, Any] = {
        "service": record["service"],
        "request_id": record["request_id"],
        "kind": record["kind"],
        "state": record["state"],
        "request_payload_sha256": record["payload_sha256"],
        "submitted_at": record["submitted_at"],
        "started_at": record.get("started_at"),
        "completed_at": record.get("completed_at"),
        "timing": record.get("timing"),
        "model": {
            "id": Path(record["model"]["path"]).name,
            "pipeline_class": record["model"].get("pipeline_class"),
            "model_index_sha256": record["model"].get("model_index_sha256"),
        },
        "parameters": {
            "width": payload["width"],
            "height": payload["height"],
            "seed": payload["seed"],
            "num_inference_steps": payload["num_inference_steps"],
            "true_cfg_scale": payload["true_cfg_scale"],
            "output_format": payload["output_format"],
        },
        "source": _public_source(record.get("source")),
        "result": _public_result(record.get("result")),
        "error": record.get("error"),
    }
    if record["kind"] == "edit":
        response["parameters"]["guidance_scale"] = payload["guidance_scale"]
    return response


def _public_source(source: dict[str, Any] | None) -> dict[str, Any] | None:
    if source is None:
        return None
    return {
        key: source.get(key)
        for key in (
            "source_attempt_id", "sha256", "normalized_sha256", "bytes", "width", "height",
            "normalized_format",
        )
        if source.get(key) is not None
    }


def _public_result(result: dict[str, Any] | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        key: result.get(key)
        for key in (
            "result_url", "sha256", "bytes", "media_type", "width", "height", "seed",
        )
        if result.get(key) is not None
    }
