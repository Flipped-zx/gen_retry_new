from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.phase3.model_config import TeacherConfig
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_view import DEFAULT_SKILL_MANIFEST


TEACHER_SYSTEM_PROMPT_VERSION = "teacher_system_prompt_v5_planner_io_v0_5_skill_catalog"
AVAILABLE_SKILL_IDS = tuple(entry["skill_id"] for entry in DEFAULT_SKILL_MANIFEST)


TEACHER_SYSTEM_PROMPT_TEXT = (
    "You are a verifier-grounded multimodal image retry planner for Gen-Retry v3. "
    "Your goal is to maximize the best valid image attempt under the remaining "
    "image-attempt budget. Output exactly one canonical action JSON object and no "
    "prose or chain-of-thought. Skills provide operational guidance for constructing "
    "the image action instruction; Skills do not decide whether "
    "to generate, edit, branch from best, continue, or submit. Use visible images "
    "and Geneval2 atom feedback together. Do not invent unsupported visual "
    "observations. Compare latest and best images when they differ before selecting "
    "an edit source. Use fixed, regressed, persistent, and stable-pass history. Do "
    "not repeat a materially equivalent ineffective instruction unless the new "
    "instruction contains a concrete change. When using query_skill, select skill_ids "
    "only from this exact catalog: "
    + ", ".join(AVAILABLE_SKILL_IDS)
    + ". Follow action_protocol_v0_5 exactly."
)


def teacher_system_prompt_sha256() -> str:
    return sha256_bytes(TEACHER_SYSTEM_PROMPT_TEXT.encode("utf-8"))


@dataclass(frozen=True)
class TeacherImageRef:
    role: str
    attempt_id: str
    artifact_id: str
    path: Path


@dataclass(frozen=True)
class TeacherResponse:
    request_id: str
    model_id: str
    raw_text: str
    finish_reason: str | None
    response_metadata: dict[str, Any]


class OpenAICompatibleTeacherClient:
    def __init__(self, config: TeacherConfig, *, timeout_seconds: float = 180.0):
        if config.provider != "openai_compatible":
            raise ValueError(f"unsupported teacher provider: {config.provider}")
        self.config = config
        self.timeout_seconds = timeout_seconds

    def smoke_test(self) -> TeacherResponse:
        return self.complete(
            request_id="teacher_smoke",
            planner_context={},
            task_spec={},
            image_refs=[],
            retrieved_skills=[],
            extra_observations=[
                "Sanitized connectivity smoke test. Return exactly {\"status\":\"ok\"}."
            ],
            max_completion_tokens=32,
        )

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
        from openai import OpenAI

        api_key = os.environ.get(self.config.api_key_env)
        base_url = os.environ.get(self.config.base_url_env)
        if not api_key:
            raise RuntimeError(f"{self.config.api_key_env} is missing")
        if not base_url:
            raise RuntimeError(f"{self.config.base_url_env} is missing")
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.timeout_seconds,
            max_retries=1,
        )
        messages = self._messages(
            planner_context=planner_context if planner_context is not None else planner_view or {},
            task_spec=task_spec,
            image_refs=image_refs,
            retrieved_skills=retrieved_skills,
            extra_observations=extra_observations or [],
        )
        response = client.chat.completions.create(
            model=self.config.model_id,
            messages=messages,
            max_completion_tokens=max_completion_tokens,
        )
        choice = response.choices[0]
        raw_text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        response_metadata = {
            "id": getattr(response, "id", None),
            "created": getattr(response, "created", None),
            "usage": usage.model_dump() if hasattr(usage, "model_dump") else None,
            "raw_text_sha256": sha256_bytes(raw_text.encode("utf-8")),
        }
        return TeacherResponse(
            request_id=request_id,
            model_id=self.config.model_id,
            raw_text=raw_text,
            finish_reason=choice.finish_reason,
            response_metadata=response_metadata,
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
        context_sha = planner_context_sha256 if planner_context_sha256 is not None else planner_view_sha256
        return {
            "schema_version": "0.5",
            "request_id": request_id,
            "teacher_provider": self.config.provider,
            "teacher_model_id": self.config.model_id,
            "system_prompt_version": TEACHER_SYSTEM_PROMPT_VERSION,
            "system_prompt_sha256": teacher_system_prompt_sha256(),
            "planner_context_ref": context_ref,
            "planner_context_sha256": context_sha,
            "teacher_text_input": self.build_teacher_text_input(
                planner_context=context,
                task_spec=task_spec,
                image_refs=image_refs,
                retrieved_skills=retrieved_skills,
                extra_observations=extra_observations,
            ),
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
        }

    def build_teacher_text_input(
        self,
        *,
        planner_context: dict[str, Any] | None = None,
        planner_view: dict[str, Any] | None = None,
        task_spec: dict[str, Any],
        image_refs: list[TeacherImageRef],
        retrieved_skills: list[dict[str, Any]],
        extra_observations: list[str],
    ) -> str:
        context = planner_context if planner_context is not None else planner_view or {}
        latest = _latest_attempt_summary(context)
        best = _best_attempt_summary(context)
        latest_equals_best = (
            latest is not None
            and best is not None
            and latest.get("attempt_id") == best.get("attempt_id")
        )
        image_labels = [
            {
                "label": _image_label(ref, latest_equals_best=latest_equals_best),
                "role": ref.role,
                "attempt_id": ref.attempt_id,
                "artifact_id": ref.artifact_id,
            }
            for ref in image_refs
        ]
        return "\n\n".join(
            [
                "You are the Phase 3 teacher policy for Gen-Retry v3.",
                "System policy:",
                canonical_json(
                    {
                        "version": TEACHER_SYSTEM_PROMPT_VERSION,
                        "sha256": teacher_system_prompt_sha256(),
                    }
                ),
                "Role:",
                (
                    "Verifier-grounded multimodal image retry planner. Maximize the "
                    "best valid attempt under the remaining budget."
                ),
                "Return exactly one JSON object matching action_protocol_v0_5. "
                "No markdown, no prose, no environment facts, no paths, no scores.",
                "The top-level object must have exactly these keys: "
                "schema_version, action, arguments. Never use a top-level "
                "instructions field.",
                "Allowed actions: query_skill, generate_image, edit_image, submit_attempt.",
                "query_skill requires arguments.skill_ids as an array and "
                "arguments.target_constraint_ids as an array. Never use skill_id singular "
                "and never add a query field.",
                "A query_skill action may request at most three skills. Do not request the "
                "same skill twice in one query. Do not query a Skill ID/version/hash "
                "that is already active unless the Skill changed or a required operator "
                "is demonstrably absent. A repeated failure of the same capability is "
                "not enough reason to retrieve the same Skill again. Do not emit "
                "query_skill immediately after a successful query_skill response. Apply "
                "retrieved operators in the next image action.",
                "Available query_skill catalog (use only these exact IDs):",
                canonical_json(DEFAULT_SKILL_MANIFEST),
                "generate_image and edit_image are Planner Actions. Their arguments "
                "must contain the action plan and the exact executable text sent to "
                "Qwen-Image-Edit.",
                "For generate_image and edit_image, include target_constraint_ids, "
                "preserve_constraint_ids, and the final executable instruction in "
                "arguments.instruction. Do not include decision_summary, diagnosis_summary, "
                "mode, strategy_tags, "
                "skill_ids_used, diagnostic_hypotheses, interventions, repair_plan, "
                "or change.",
                "Generation instructions must include relevant exact entities/counts, "
                "entity-specific attributes, layout, relation/depth cues, visibility, "
                "separation, and no extras or fused/cropped/reflected instances.",
                "Edit instructions must include four semantic blocks: target operation, "
                "spatial grounding, preservation lock, and forbidden changes. Do not rely "
                "only on vague phrases such as 'fix the failed parts' or 'preserve all "
                "correct evidence'.",
                "Use edit_image only with a source_attempt_id already present in "
                "PlannerContext latest_attempt or episode_memory. "
                "Use visible LATEST_IMAGE and BEST_IMAGE inputs; never decide from a path "
                "string alone. Compare latest and best when they differ before choosing "
                "source_attempt_id. Do not blindly continue from the latest attempt.",
                "If remaining_image_budget is 0, submit the best available attempt with "
                "reason_code exactly best_available_under_budget.",
                "Allowed submit reason_code values are exactly: all_constraints_passed, "
                "best_available_under_budget, no_productive_action_remaining. Never use "
                "budget_exhausted_best_available.",
                "Valid templates:",
                canonical_json(
                    [
                        {
                            "schema_version": "0.5",
                            "action": "query_skill",
                            "arguments": {
                                "skill_ids": ["counting_and_instance_layout"],
                                "target_constraint_ids": ["c_001"],
                            },
                        },
                        {
                            "schema_version": "0.5",
                            "action": "generate_image",
                            "arguments": {
                                "target_constraint_ids": ["c_001", "c_002"],
                                "preserve_constraint_ids": [],
                                "instruction": (
                                    "Create exactly two red cats total behind one blue cube. "
                                    "Keep both cats fully visible and separated in the background, "
                                    "place the cube in the foreground, and do not include extra, "
                                    "cropped, fused, reflected, or background cats."
                                ),
                            },
                        },
                        {
                            "schema_version": "0.5",
                            "action": "edit_image",
                            "arguments": {
                                "source_attempt_id": "a_000",
                                "target_constraint_ids": ["c_001"],
                                "preserve_constraint_ids": ["c_002"],
                                "instruction": (
                                    "Edit attempt a_000 only in the cat group: remove extra cats "
                                    "so exactly two red cats remain, fully visible and separated "
                                    "behind the foreground cube. Preserve the cube color, cube "
                                    "position, background, and all passed non-target constraints. "
                                    "Do not add extra cats, redraw unrelated objects, or change "
                                    "the scene composition."
                                ),
                            },
                        },
                        {
                            "schema_version": "0.5",
                            "action": "submit_attempt",
                            "arguments": {
                                "selected_attempt_id": "a_000",
                                "reason_code": "all_constraints_passed"
                            },
                        },
                        {
                            "schema_version": "0.5",
                            "action": "submit_attempt",
                            "arguments": {
                                "selected_attempt_id": "a_000",
                                "reason_code": "best_available_under_budget"
                            },
                        },
                    ]
                ),
                "PlannerContext:",
                canonical_json(context) if context else "{}",
                "Visible image labels:",
                canonical_json(image_labels),
                "Latest equals best:",
                canonical_json(latest_equals_best),
                "Active Skills:",
                canonical_json(_active_skill_operators(context))
                if context
                else "[]",
                "Extra observations:",
                canonical_json(extra_observations),
            ]
        )

    def _messages(
        self,
        *,
        planner_context: dict[str, Any] | None = None,
        planner_view: dict[str, Any] | None = None,
        task_spec: dict[str, Any],
        image_refs: list[TeacherImageRef],
        retrieved_skills: list[dict[str, Any]],
        extra_observations: list[str],
    ) -> list[dict[str, Any]]:
        text = self.build_teacher_text_input(
            planner_context=planner_context if planner_context is not None else planner_view or {},
            task_spec=task_spec,
            image_refs=image_refs,
            retrieved_skills=retrieved_skills,
            extra_observations=extra_observations,
        )
        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        context = planner_context if planner_context is not None else planner_view or {}
        latest = _latest_attempt_summary(context)
        best = _best_attempt_summary(context)
        latest_equals_best = (
            latest is not None
            and best is not None
            and latest.get("attempt_id") == best.get("attempt_id")
        )
        for image_ref in image_refs:
            content.append(
                {
                    "type": "text",
                    "text": _image_label(image_ref, latest_equals_best=latest_equals_best),
                }
            )
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": _image_data_url(image_ref.path),
                    },
                }
            )
        return [
            {
                "role": "system",
                "content": TEACHER_SYSTEM_PROMPT_TEXT,
            },
            {"role": "user", "content": content},
        ]


def redacted_raw_output_record(response: TeacherResponse) -> dict[str, Any]:
    return {
        "schema_version": "0.5",
        "request_id": response.request_id,
        "model_id": response.model_id,
        "raw_text": response.raw_text,
        "redaction": {
            "credentials_removed": True,
            "redaction_rules": [
                "No authorization headers or API keys are persisted by the teacher client."
            ],
        },
        "finish_reason": response.finish_reason,
        "response_metadata": response.response_metadata,
    }


def _image_data_url(path: Path) -> str:
    media_type = "image/png"
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        media_type = "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{data}"


def _image_label(image_ref: TeacherImageRef, *, latest_equals_best: bool) -> str:
    label = "LATEST_IMAGE" if image_ref.role == "latest" else image_ref.role.upper() + "_IMAGE"
    if image_ref.role == "best" and latest_equals_best:
        label = "BEST_IMAGE_SAME_AS_LATEST"
    return f"{label}: attempt {image_ref.attempt_id}, artifact {image_ref.artifact_id}"


def _latest_attempt_summary(context: dict[str, Any]) -> dict[str, Any] | None:
    observation = context.get("latest_attempt") or context.get("latest_observation")
    if observation:
        return {
            "attempt_id": observation["attempt_id"],
            "passed_constraint_ids": observation["constraint_results"]["passed_constraint_ids"],
            "failed_constraint_ids": observation["constraint_results"]["failed_constraint_ids"],
        }
    return None


def _best_attempt_summary(context: dict[str, Any]) -> dict[str, Any] | None:
    best = context.get("episode_memory", {}).get("best_attempt")
    if best:
        constraint_results = best.get("constraint_results")
        if constraint_results is None and best.get("constraint_results_ref") == "latest_attempt":
            return _latest_attempt_summary(context)
        return {
            "attempt_id": best["attempt_id"],
            "passed_constraint_ids": constraint_results["passed_constraint_ids"],
            "failed_constraint_ids": constraint_results["failed_constraint_ids"],
        }
    return None


def _active_skill_operators(context: dict[str, Any]) -> list[dict[str, Any]]:
    return context.get("skill_context", {}).get("active_skills", [])
