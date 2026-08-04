from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from gen_retry.agent.sft_planner import (
    TransformersSFTPlanner,
    sft_system_prompt_sha256,
)
from gen_retry.agent.teacher_client import TeacherImageRef
from gen_retry.runtime.json_canonical import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Serve one persistent HuggingFace SFT planner checkpoint."
    )
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--image-max-pixels", type=int, default=262144)
    parser.add_argument("--disable-flash-attention", action="store_true")
    parser.add_argument("--offload-between-requests", action="store_true")
    parser.add_argument(
        "--device-id",
        type=int,
        action="append",
        dest="device_ids",
        help="Physical HCU eligible for transient planner inference; repeatable.",
    )
    args = parser.parse_args()

    planner = TransformersSFTPlanner(
        args.checkpoint,
        image_max_pixels=args.image_max_pixels,
        flash_attention=not args.disable_flash_attention,
        offload_between_requests=args.offload_between_requests,
        device_ids=args.device_ids,
    )
    handler = _handler_for(planner)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        canonical_json(
            {
                "status": "ready",
                "host": args.host,
                "port": args.port,
                "checkpoint_path": str(planner.checkpoint_path),
                "checkpoint_fingerprint": planner.checkpoint_fingerprint,
                "offload_between_requests": planner.offload_between_requests,
                "device_ids": planner.device_ids,
            }
        ),
        flush=True,
    )
    server.serve_forever()


def _handler_for(planner: TransformersSFTPlanner) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/health":
                self._write_json(404, {"error": "not_found"})
                return
            self._write_json(
                200,
                {
                    "checkpoint_path": str(planner.checkpoint_path),
                    "checkpoint_fingerprint": planner.checkpoint_fingerprint,
                    "system_prompt_sha256": sft_system_prompt_sha256(),
                    "planner_context_schema_version": "0.7",
                    "action_protocol_version": "0.5",
                    "model_loaded": True,
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/complete":
                self._write_json(404, {"error": "not_found"})
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                result = planner.complete(
                    request_id=_required_string(payload, "request_id"),
                    task_spec=_required_object(payload, "task_spec"),
                    planner_context=_required_object(payload, "planner_context"),
                    image_refs=_image_refs(payload.get("image_refs")),
                    max_new_tokens=int(payload.get("max_new_tokens", 1400)),
                )
            except Exception as exc:
                self._write_json(
                    500,
                    {"error": type(exc).__name__, "message": str(exc)},
                )
                return
            self._write_json(200, result)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            body = canonical_json(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _image_refs(value: Any) -> list[TeacherImageRef]:
    if not isinstance(value, list):
        raise ValueError("image_refs must be a list")
    refs: list[TeacherImageRef] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("image_refs entries must be objects")
        path = Path(_required_string(item, "path")).resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        refs.append(
            TeacherImageRef(
                role=_required_string(item, "role"),
                attempt_id=_required_string(item, "attempt_id"),
                artifact_id=_required_string(item, "artifact_id"),
                path=path,
            )
        )
    return refs


if __name__ == "__main__":
    main()
