from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.agent.teacher_client import TeacherImageRef, TeacherResponse
from gen_retry.domain.artifacts import sha256_bytes, sha256_file
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.sft.supervision import SYSTEM_PROMPT, render_messages
from gen_retry.tools.model_load_lock import exclusive_model_load
from gen_retry.tools.resource_locks import exclusive_any_device_execution


SFT_SYSTEM_PROMPT_VERSION = "phase4_sft_system_prompt_action_protocol_v0_5"
SFT_PLANNER_PROVIDER = "local_transformers_service"


def sft_system_prompt_sha256() -> str:
    return sha256_bytes(SYSTEM_PROMPT.encode("utf-8"))


def checkpoint_fingerprint(checkpoint_path: Path) -> str:
    checkpoint_path = checkpoint_path.resolve()
    index_path = checkpoint_path / "model.safetensors.index.json"
    config_path = checkpoint_path / "config.json"
    if not index_path.is_file() or not config_path.is_file():
        raise FileNotFoundError(
            f"standard HuggingFace checkpoint is incomplete: {checkpoint_path}"
        )
    return "sha256:" + sha256_bytes(
        (
            sha256_file(index_path)
            + ":"
            + sha256_file(config_path)
        ).encode("ascii")
    )


def build_sft_inference_messages(
    *,
    task_spec: dict[str, Any],
    planner_context: dict[str, Any],
    image_refs: list[TeacherImageRef],
) -> list[dict[str, Any]]:
    """Recreate the frozen training renderer and image-prefix order exactly."""

    visible_images = [
        {
            "artifact_id": ref.artifact_id,
            "attempt_id": ref.attempt_id,
            "role": ref.role,
            "uri": f"images/{ref.artifact_id}.png",
        }
        for ref in image_refs
    ]
    rendered = render_messages(
        task_spec=task_spec,
        planner_context=planner_context,
        visible_images=visible_images,
        target_action=None,
    )
    user_text = rendered[1]["content"]
    if image_refs:
        user_text = "\n" + user_text
    user_content = [
        {"type": "image", "image": str(ref.path.resolve())}
        for ref in image_refs
    ]
    user_content.append({"type": "text", "text": user_text})
    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": rendered[0]["content"]}],
        },
        {"role": "user", "content": user_content},
    ]


@dataclass(frozen=True)
class SFTPlannerHealth:
    checkpoint_path: str
    checkpoint_fingerprint: str
    system_prompt_sha256: str
    planner_context_schema_version: str
    action_protocol_version: str
    model_loaded: bool


class SFTPlannerClient:
    producer_id = "sft_planner_client"
    raw_output_directory = "raw_planner_outputs"
    raw_output_log_name = "raw_planner_outputs.jsonl"

    def __init__(
        self,
        *,
        endpoint_url: str,
        checkpoint_path: Path,
        timeout_seconds: float = 300.0,
    ) -> None:
        self.endpoint_url = endpoint_url.rstrip("/")
        self.checkpoint_path = checkpoint_path.resolve()
        self.timeout_seconds = timeout_seconds
        self._checkpoint_fingerprint = checkpoint_fingerprint(self.checkpoint_path)

    def health(self) -> SFTPlannerHealth:
        payload = self._request("GET", "/health", None)
        health = SFTPlannerHealth(**payload)
        expected = {
            "checkpoint_path": str(self.checkpoint_path),
            "checkpoint_fingerprint": self._checkpoint_fingerprint,
            "system_prompt_sha256": sft_system_prompt_sha256(),
            "planner_context_schema_version": "0.7",
            "action_protocol_version": "0.5",
            "model_loaded": True,
        }
        if health.__dict__ != expected:
            raise RuntimeError(
                "SFT planner health/protocol mismatch: "
                + canonical_json({"expected": expected, "actual": health.__dict__})
            )
        return health

    def complete(
        self,
        *,
        request_id: str,
        planner_context: dict[str, Any] | None = None,
        planner_view: dict[str, Any] | None = None,
        task_spec: dict[str, Any],
        image_refs: list[TeacherImageRef],
        retrieved_skills: list[dict[str, Any]],
        extra_observations: list[str] | None = None,
        max_completion_tokens: int = 1400,
    ) -> TeacherResponse:
        del retrieved_skills, extra_observations
        context = planner_context if planner_context is not None else planner_view or {}
        payload = self._request(
            "POST",
            "/v1/complete",
            {
                "request_id": request_id,
                "task_spec": task_spec,
                "planner_context": context,
                "image_refs": [
                    {
                        "role": ref.role,
                        "attempt_id": ref.attempt_id,
                        "artifact_id": ref.artifact_id,
                        "path": str(ref.path.resolve()),
                    }
                    for ref in image_refs
                ],
                "max_new_tokens": max_completion_tokens,
            },
        )
        return TeacherResponse(
            request_id=request_id,
            model_id=str(self.checkpoint_path),
            raw_text=payload["raw_text"],
            finish_reason=payload.get("finish_reason"),
            response_metadata=payload["response_metadata"],
        )

    def sanitized_request_record(
        self,
        *,
        request_id: str,
        task_spec: dict[str, Any],
        planner_context: dict[str, Any] | None = None,
        planner_context_ref: str | None = None,
        planner_context_sha256: str | None = None,
        planner_view: dict[str, Any] | None = None,
        planner_view_ref: str | None = None,
        planner_view_sha256: str | None = None,
        image_refs: list[TeacherImageRef],
        retrieved_skills: list[dict[str, Any]],
        extra_observations: list[str],
    ) -> dict[str, Any]:
        context = planner_context if planner_context is not None else planner_view or {}
        context_ref = planner_context_ref if planner_context_ref is not None else planner_view_ref
        context_sha = (
            planner_context_sha256
            if planner_context_sha256 is not None
            else planner_view_sha256
        )
        messages = build_sft_inference_messages(
            task_spec=task_spec,
            planner_context=context,
            image_refs=image_refs,
        )
        user_content = messages[1]["content"]
        user_text = next(item["text"] for item in user_content if item["type"] == "text")
        return {
            "schema_version": "0.5",
            "request_id": request_id,
            "planner_provider": SFT_PLANNER_PROVIDER,
            "planner_model_id": str(self.checkpoint_path),
            "checkpoint_fingerprint": self._checkpoint_fingerprint,
            "system_prompt_version": SFT_SYSTEM_PROMPT_VERSION,
            "system_prompt_sha256": sft_system_prompt_sha256(),
            "planner_context_ref": context_ref,
            "planner_context_sha256": context_sha,
            "planner_context_schema_version": str(
                context.get("planner_context_schema_version", "0.7")
            ),
            "action_protocol_version": "0.5",
            "planner_text_input": user_text.lstrip("\n"),
            "visible_images": [
                {
                    "role": ref.role,
                    "attempt_id": ref.attempt_id,
                    "artifact_id": ref.artifact_id,
                    "path_ref_sha256": sha256_bytes(str(ref.path).encode("utf-8")),
                }
                for ref in image_refs
            ],
            "retrieved_skill_ids": [skill["skill_id"] for skill in retrieved_skills],
            "extra_observations": extra_observations,
            "extra_observations_in_model_input": False,
            "teacher_fallback_allowed": False,
        }

    def raw_output_record(self, response: TeacherResponse) -> dict[str, Any]:
        return {
            "schema_version": "0.5",
            "request_id": response.request_id,
            "model_id": response.model_id,
            "planner_provider": SFT_PLANNER_PROVIDER,
            "raw_text": response.raw_text,
            "finish_reason": response.finish_reason,
            "response_metadata": response.response_metadata,
            "teacher_fallback_used": False,
        }

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        data = None if payload is None else canonical_json(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"SFT planner service request failed: {path}: {exc}") from exc
        if not isinstance(result, dict):
            raise RuntimeError("SFT planner service returned a non-object response")
        return result


class TransformersSFTPlanner:
    """One persistently loaded HuggingFace checkpoint for rollout inference."""

    def __init__(
        self,
        checkpoint_path: Path,
        *,
        image_max_pixels: int = 262144,
        flash_attention: bool = True,
        offload_between_requests: bool = False,
        device_ids: list[int] | None = None,
    ) -> None:
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        self.checkpoint_path = checkpoint_path.resolve()
        self.checkpoint_fingerprint = checkpoint_fingerprint(self.checkpoint_path)
        self._lock = threading.Lock()
        self.offload_between_requests = offload_between_requests
        self.device_ids = device_ids or list(range(torch.cuda.device_count()))
        with exclusive_model_load():
            self.processor = AutoProcessor.from_pretrained(
                str(self.checkpoint_path),
                max_pixels=image_max_pixels,
                local_files_only=True,
            )
            model_args: dict[str, Any] = {
                "dtype": torch.bfloat16,
                "local_files_only": True,
            }
            if not self.offload_between_requests:
                model_args["device_map"] = "auto"
            if flash_attention:
                model_args["attn_implementation"] = "flash_attention_2"
            self.model = Qwen3VLForConditionalGeneration.from_pretrained(
                str(self.checkpoint_path),
                **model_args,
            )
        self.model.eval()
        self.loaded_at_monotonic = time.monotonic()

    def complete(
        self,
        *,
        request_id: str,
        task_spec: dict[str, Any],
        planner_context: dict[str, Any],
        image_refs: list[TeacherImageRef],
        max_new_tokens: int,
    ) -> dict[str, Any]:
        if str(planner_context.get("planner_context_schema_version")) != "0.7":
            raise ValueError("SFT planner requires PlannerContext v0.7")
        if max_new_tokens < 1 or max_new_tokens > 1400:
            raise ValueError("max_new_tokens must be in [1, 1400]")
        messages = build_sft_inference_messages(
            task_spec=task_spec,
            planner_context=planner_context,
            image_refs=image_refs,
        )
        with self._lock:
            if self.offload_between_requests:
                with exclusive_any_device_execution(self.device_ids) as device_id:
                    return self._generate_offloaded(
                        request_id=request_id,
                        messages=messages,
                        max_new_tokens=max_new_tokens,
                        device_id=device_id,
                    )
            return self._generate(
                request_id=request_id,
                messages=messages,
                max_new_tokens=max_new_tokens,
                device_id=None,
            )

    def _generate_offloaded(
        self,
        *,
        request_id: str,
        messages: list[dict[str, Any]],
        max_new_tokens: int,
        device_id: int,
    ) -> dict[str, Any]:
        import gc
        import torch

        device = torch.device(f"cuda:{device_id}")
        self.model.to(device)
        try:
            return self._generate(
                request_id=request_id,
                messages=messages,
                max_new_tokens=max_new_tokens,
                device_id=device_id,
            )
        finally:
            self.model.to("cpu")
            gc.collect()
            torch.cuda.synchronize(device)
            torch.cuda.empty_cache()

    def _generate(
        self,
        *,
        request_id: str,
        messages: list[dict[str, Any]],
        max_new_tokens: int,
        device_id: int | None,
    ) -> dict[str, Any]:
        import torch

        started = time.monotonic()
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.model.device)
        prompt_tokens = int(inputs["input_ids"].shape[1])
        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                use_cache=True,
            )
        generated_ids = output_ids[:, prompt_tokens:]
        raw_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]
        completion_tokens = int(generated_ids.shape[1])
        finish_reason = "length" if completion_tokens >= max_new_tokens else "stop"
        elapsed = time.monotonic() - started
        del output_ids
        del generated_ids
        del inputs
        return {
            "request_id": request_id,
            "raw_text": raw_text,
            "finish_reason": finish_reason,
            "response_metadata": {
                "planner_provider": SFT_PLANNER_PROVIDER,
                "checkpoint_fingerprint": self.checkpoint_fingerprint,
                "system_prompt_sha256": sft_system_prompt_sha256(),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_seconds": elapsed,
                "persistent_model_uptime_seconds": time.monotonic()
                - self.loaded_at_monotonic,
                "physical_device_id": device_id,
                "offload_between_requests": self.offload_between_requests,
                "do_sample": False,
                "teacher_fallback_used": False,
                "raw_text_sha256": sha256_bytes(raw_text.encode("utf-8")),
            },
        }
