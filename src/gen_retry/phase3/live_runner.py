from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_retry.agent.teacher_client import (
    OpenAICompatibleTeacherClient,
    TeacherImageRef,
    TeacherResponse,
    redacted_raw_output_record,
)
from gen_retry.agent.instruction_quality import evaluate_instruction_quality
from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_file, sha256_bytes
from gen_retry.domain.score_policy import (
    legacy_score_policy,
    planner_context_version,
    score_policy_from_task_payload,
)
from gen_retry.phase3.model_config import ModelConfig, load_model_config
from gen_retry.protocol.action_parser import ActionParseError, parse_action
from gen_retry.protocol.reference_validator import ActionReferenceError, validate_action_references
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.trajectory_validator import validate_artifact_manifest_semantics
from gen_retry.runtime.event_io import AppendOnlyEventStore, load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import (
    build_planner_context_from_events,
    build_round_records_from_events,
    visible_images_from_state,
)
from gen_retry.runtime.planner_view import DEFAULT_SKILL_MANIFEST
from gen_retry.runtime.reducer import EpisodeState, reduce_events
from gen_retry.tools.geneval2_adapter import LocalGeneval2Adapter
from gen_retry.tools.image_execution_profile import resolve_execution_route
from gen_retry.tools.qianwen_image_edit_adapter import QianwenImageEditAdapter
from gen_retry.tools.qwen_image_adapter import QwenImageAdapter
from gen_retry.tools.resource_locks import exclusive_episode_execution
from gen_retry.tools.skill_store import LocalSkillStore


@dataclass(frozen=True)
class RuntimeParams:
    image_height: int = 1024
    image_width: int = 1024
    image_steps: int = 40
    generate_image_steps: int | None = None
    edit_image_steps: int | None = None
    image_seed: int = 0
    teacher_max_completion_tokens: int = 1400
    max_format_repairs: int = 3
    evaluator_pass_threshold: float = 0.50
    evaluator_fail_threshold: float = 0.20


@dataclass(frozen=True)
class RolloutResult:
    episode_id: str
    run_dir: Path
    status: str
    submitted_attempt_id: str | None
    attempts: int
    events: int


class Phase3LiveRunner:
    def __init__(
        self,
        *,
        model_config: ModelConfig | None = None,
        runtime_params: RuntimeParams | None = None,
    ):
        self.model_config = model_config or load_model_config()
        self.params = runtime_params or RuntimeParams()
        self.teacher = OpenAICompatibleTeacherClient(self.model_config.teacher)
        self.skill_store = LocalSkillStore()

    def run_all(self, run_root: Path = Path("runs/phase3")) -> list[RolloutResult]:
        results = []
        for run_dir in sorted(path for path in run_root.iterdir() if path.is_dir()):
            if (run_dir / "task_spec.json").exists():
                results.append(self.run_episode(run_dir))
        return results

    def run_episode(self, run_dir: Path) -> RolloutResult:
        with exclusive_episode_execution(run_dir):
            return self._run_episode_locked(run_dir)

    def _run_episode_locked(self, run_dir: Path) -> RolloutResult:
        task_spec = json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))
        episode_id = task_spec["episode_id"]
        self._validate_execution_profile_lock(run_dir)
        self._validate_score_policy_lock(run_dir)
        events = self._events(run_dir)
        state = reduce_events(events)
        if state.submitted_attempt_id is not None:
            return RolloutResult(
                episode_id=episode_id,
                run_dir=run_dir,
                status="already_submitted",
                submitted_attempt_id=state.submitted_attempt_id,
                attempts=len(state.attempt_order),
                events=len(events),
            )

        repair_count = 0
        while state.submitted_attempt_id is None:
            if len(state.attempt_order) >= task_spec["max_image_attempts"] and state.best_attempt_id is None:
                raise RuntimeError(f"{episode_id}: budget exhausted without an attempt to submit")

            events = self._events(run_dir)
            state = reduce_events(events)
            if self._recover_incomplete_skill_query(run_dir, events=events):
                events = self._events(run_dir)
                state = reduce_events(events)
                continue
            if self._recover_incomplete_image_round(
                run_dir,
                task_spec=task_spec,
                events=events,
                state=state,
            ):
                events = self._events(run_dir)
                state = reduce_events(events)
                continue
            planner_context_event = self._latest_event(events, "planner_context_built")
            if self._planner_context_consumed(events, planner_context_event):
                self._build_next_planner_context(run_dir, input_refs=[events[-1]["event_id"]])
                continue
            planner_context_ref = planner_context_event["payload"]["planner_context_ref"]
            planner_context_sha = planner_context_event["payload"]["planner_context_sha256"]
            planner_context = json.loads((run_dir / planner_context_ref).read_text(encoding="utf-8"))
            turn_id = planner_context_event["turn_id"]
            request_id = f"{episode_id}_{turn_id}"
            extra_observations = self._extra_observations(state, events)
            image_refs = self._teacher_image_refs(run_dir, state)
            retrieved_skills: list[dict[str, Any]] = []
            self._append_jsonl(
                run_dir / "planner_requests.jsonl",
                self.teacher.sanitized_request_record(
                    request_id=request_id,
                    task_spec=task_spec,
                    planner_context=planner_context,
                    planner_context_ref=planner_context_ref,
                    planner_context_sha256=planner_context_sha,
                    image_refs=image_refs,
                    retrieved_skills=retrieved_skills,
                    extra_observations=extra_observations,
                ),
            )
            response = self._teacher_response(
                request_id=request_id,
                planner_context=planner_context,
                task_spec=task_spec,
                image_refs=image_refs,
                retrieved_skills=retrieved_skills,
                extra_observations=extra_observations,
            )
            raw_record = redacted_raw_output_record(response)
            raw_ref = f"raw_teacher_outputs/{request_id}.json"
            raw_sha = self._write_json_artifact(run_dir, raw_ref, raw_record)
            self._upsert_manifest_entry(
                run_dir,
                artifact_manifest_entry(
                    artifact_id=f"raw_{self._turn_number(turn_id):03d}",
                    artifact_type="raw_model_output",
                    uri=raw_ref,
                    sha256=raw_sha,
                    media_type="application/json",
                    producer="teacher_client",
                    metadata={"request_id": request_id, "model_id": response.model_id},
                ),
            )
            self._append_jsonl(run_dir / "raw_teacher_outputs.jsonl", raw_record)
            output_event = self._append_event(
                run_dir,
                event_type="planner_output_recorded",
                turn_id=turn_id,
                producer="teacher_client",
                input_refs=[planner_context_event["event_id"]],
                payload={"raw_output_ref": raw_ref, "raw_output_sha256": raw_sha},
            )

            try:
                action = parse_action(response.raw_text).action
                validate_action_references(
                    action,
                    task_spec,
                    known_attempt_ids=state.attempt_order,
                    available_skill_ids=[entry["skill_id"] for entry in DEFAULT_SKILL_MANIFEST],
                )
                self._validate_runtime_action(
                    action,
                    state,
                    retrieved_skills,
                    events=self._events(run_dir),
                )
                self._validate_instruction_quality(action, task_spec, state)
            except (ActionParseError, ActionReferenceError, RuntimeActionError) as exc:
                repair_count += 1
                error_event = self._append_event(
                    run_dir,
                    event_type="format_error",
                    turn_id=turn_id,
                    producer="action_parser",
                    input_refs=[output_event["event_id"]],
                    payload={
                        "error_code": getattr(exc, "error_code", "invalid_action"),
                        "message": str(exc),
                        "retryable": repair_count <= self.params.max_format_repairs,
                        "raw_output_ref": raw_ref,
                    },
                )
                if repair_count > self.params.max_format_repairs:
                    raise RuntimeError(f"{episode_id}: teacher produced repeated invalid actions") from exc
                self._build_next_planner_context(run_dir, input_refs=[error_event["event_id"]])
                continue

            repair_count = 0
            action_event = self._append_event(
                run_dir,
                event_type="action_validated",
                turn_id=turn_id,
                producer="action_parser",
                input_refs=[output_event["event_id"]],
                payload={"action": action},
            )
            self._append_jsonl(
                run_dir / "canonical_actions.jsonl",
                {
                    "schema_version": "0.5",
                    "request_id": request_id,
                    "action_event_id": action_event["event_id"],
                    "turn_id": turn_id,
                    "action": action,
                },
            )

            if action["action"] == "query_skill":
                skill_event = self._execute_skill(run_dir, action_event)
                self._build_next_planner_context(run_dir, input_refs=[skill_event["event_id"]])
            elif action["action"] == "submit_attempt":
                submit_event = self._append_event(
                    run_dir,
                    event_type="attempt_submitted",
                    turn_id=turn_id,
                    producer="phase3_live_runner",
                    input_refs=[action_event["event_id"]],
                    payload={
                        "submit_action_event_id": action_event["event_id"],
                        "selected_attempt_id": action["arguments"]["selected_attempt_id"],
                        "reason_code": action["arguments"]["reason_code"],
                    },
                )
                events = self._events(run_dir)
                state = reduce_events(events)
                self._write_state_and_submission(run_dir, state, submit_event)
            else:
                self._execute_image_attempt(run_dir, task_spec, state, action_event)

            events = self._events(run_dir)
            state = reduce_events(events)

        return RolloutResult(
            episode_id=episode_id,
            run_dir=run_dir,
            status="submitted",
            submitted_attempt_id=state.submitted_attempt_id,
            attempts=len(state.attempt_order),
            events=len(self._events(run_dir)),
        )

    def _teacher_response(
        self,
        *,
        request_id: str,
        planner_context: dict[str, Any],
        task_spec: dict[str, Any],
        image_refs: list[TeacherImageRef],
        retrieved_skills: list[dict[str, Any]],
        extra_observations: list[str],
    ) -> TeacherResponse:
        return self.teacher.complete(
            request_id=request_id,
            planner_context=planner_context,
            task_spec=task_spec,
            image_refs=image_refs,
            retrieved_skills=retrieved_skills,
            extra_observations=extra_observations,
            max_completion_tokens=self.params.teacher_max_completion_tokens,
        )

    def _execute_skill(self, run_dir: Path, action_event: dict[str, Any]) -> dict[str, Any]:
        action = action_event["payload"]["action"]
        args = action["arguments"]
        skills = self.skill_store.get_many(args["skill_ids"])
        payload = {
            "query_action_event_id": action_event["event_id"],
            "skill_ids": args["skill_ids"],
            "target_constraint_ids": args["target_constraint_ids"],
            "skills": [skill.event_payload_entry() for skill in skills],
        }
        event = self._append_event(
            run_dir,
            event_type="skill_returned",
            turn_id=action_event["turn_id"],
            producer="local_skill_store",
            input_refs=[action_event["event_id"]],
            payload=payload,
        )
        self._append_jsonl_once(
            run_dir / "tool_observations.jsonl",
            {
                "schema_version": "0.2",
                "event_id": event["event_id"],
                "observation_type": "skill_returned",
                "skills": [
                    {
                        **skill.event_payload_entry(),
                        "content": skill.content,
                    }
                    for skill in skills
                ],
            },
        )
        return event

    def _execute_image_attempt(
        self,
        run_dir: Path,
        task_spec: dict[str, Any],
        state: EpisodeState,
        action_event: dict[str, Any],
        *,
        existing_start_event: dict[str, Any] | None = None,
    ) -> None:
        action = action_event["payload"]["action"]
        execution_profile = self.model_config.resolved_image_execution
        route = resolve_execution_route(execution_profile, action["action"])
        attempt_number = len(state.attempt_order)
        attempt_id = f"a_{attempt_number:03d}"
        image_artifact_id = f"img_{attempt_number:03d}"
        operation = route.operation
        request_id = f"{task_spec['episode_id']}_{attempt_id}_{operation}"
        source_attempt_id = action["arguments"].get("source_attempt_id")
        source_image_path = (
            self._image_path_for_attempt(run_dir, state, source_attempt_id)
            if source_attempt_id
            else None
        )
        source_artifact_sha256 = (
            sha256_file(source_image_path) if source_image_path is not None else None
        )
        num_inference_steps = self._image_steps_for_route(route.operation, route.backend)
        output_path = run_dir / f"images/{image_artifact_id}.png"
        if route.backend.backend_id == "qwen_image":
            adapter = QwenImageAdapter(
                provider=route.backend.provider,
                model_id=route.backend.model_id,
                model_path=route.backend.model_path,
                artifact_root=run_dir,
                height=self.params.image_height,
                width=self.params.image_width,
                num_inference_steps=num_inference_steps,
                true_cfg_scale=route.backend.true_cfg_scale,
                seed=self.params.image_seed + attempt_number,
            )
            adapter_metadata = adapter.execution_metadata(cache_hit=output_path.exists())
        elif route.backend.backend_id == "qianwen_image_edit":
            adapter = QianwenImageEditAdapter(
                provider=route.backend.provider,
                model_id=route.backend.model_id,
                model_path=route.backend.model_path,
                artifact_root=run_dir,
                height=self.params.image_height,
                width=self.params.image_width,
                num_inference_steps=num_inference_steps,
                true_cfg_scale=route.backend.true_cfg_scale,
                guidance_scale=(
                    route.backend.guidance_scale
                    if route.backend.guidance_scale is not None
                    else 1.0
                ),
                seed=self.params.image_seed + attempt_number,
            )
            adapter_metadata = adapter.execution_metadata(
                cache_hit=output_path.exists(),
                internal_generation_canvas=operation == "generate",
            )
        else:
            raise RuntimeError(
                f"unsupported routed image backend: {route.backend.backend_id}"
            )
        provenance_payload = {
            "execution_profile_id": execution_profile.profile_id,
            "execution_profile_version": execution_profile.profile_version,
            "logical_action": action["action"],
            "model_id": adapter_metadata["model_id"],
            "model_revision_or_fingerprint": adapter_metadata[
                "model_revision_or_fingerprint"
            ],
            "pipeline_id": adapter_metadata["pipeline_id"],
            "adapter_version": adapter_metadata["adapter_version"],
            "sampling": adapter_metadata["sampling"],
        }
        start_payload = {
            "request_id": request_id,
            "operation": operation,
            "backend": route.backend.backend_id,
            **provenance_payload,
        }
        if source_attempt_id:
            start_payload["source_attempt_id"] = source_attempt_id
            start_payload["source_artifact_sha256"] = source_artifact_sha256
        if existing_start_event is not None:
            if existing_start_event["payload"] != start_payload:
                raise RuntimeError(
                    "pending image start does not match action-derived request: "
                    f"{existing_start_event['payload']['request_id']}"
                )
            start_event = existing_start_event
        else:
            start_event = self._append_event(
                run_dir,
                event_type="image_execution_started",
                turn_id=action_event["turn_id"],
                producer=route.producer,
                input_refs=[action_event["event_id"]],
                payload=start_payload,
            )
        if operation == "generate":
            image_result = adapter.generate(
                request_id=request_id,
                attempt_id=attempt_id,
                image_artifact_id=image_artifact_id,
                instruction=_execution_instruction(action),
            )
        else:
            image_result = adapter.edit(
                request_id=request_id,
                attempt_id=attempt_id,
                source_attempt_id=source_attempt_id,
                source_image_path=source_image_path,
                image_artifact_id=image_artifact_id,
                instruction=_execution_instruction(action),
            )
        self._upsert_manifest_entry(run_dir, image_result.manifest_entry)
        complete_payload = {
            "request_id": request_id,
            "attempt_id": attempt_id,
            "parent_attempt_id": image_result.parent_attempt_id,
            "operation": operation,
            "backend": route.backend.backend_id,
            **provenance_payload,
            "image_artifact_id": image_artifact_id,
            "artifact_manifest_ref": image_result.artifact_manifest_ref,
            "artifact_sha256": image_result.artifact_sha256,
        }
        if source_attempt_id:
            complete_payload["source_attempt_id"] = source_attempt_id
            complete_payload["source_artifact_sha256"] = source_artifact_sha256
        complete_event = self._append_event(
            run_dir,
            event_type="image_execution_completed",
            turn_id=action_event["turn_id"],
            producer=route.producer,
            input_refs=[start_event["event_id"]],
            payload=complete_payload,
        )
        self._append_jsonl(
            run_dir / "tool_observations.jsonl",
            {
                "schema_version": "0.2",
                "event_id": complete_event["event_id"],
                "observation_type": "image_execution_completed",
                "request_id": request_id,
                "attempt_id": attempt_id,
                "image_artifact_id": image_artifact_id,
                "metadata": {
                    "execution_profile_id": execution_profile.profile_id,
                    "execution_profile_version": execution_profile.profile_version,
                    "logical_action": action["action"],
                    **image_result.metadata,
                },
            },
        )
        geneval_event = self._evaluate_completed_image(
            run_dir,
            task_spec=task_spec,
            action_event=action_event,
            complete_event=complete_event,
        )
        self._complete_evaluated_round(
            run_dir,
            action_event=action_event,
            geneval_event=geneval_event,
        )

    def _validate_execution_profile_lock(self, run_dir: Path) -> None:
        plan_path = run_dir / "rollout_plan.json"
        if not plan_path.exists():
            raise RuntimeError(f"missing rollout execution profile: {plan_path}")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        expected = plan.get("execution_profile") or {
            "profile_id": "qwen_image_edit_only",
            "profile_version": "1",
        }
        actual = self.model_config.resolved_image_execution
        if (
            expected.get("profile_id") != actual.profile_id
            or str(expected.get("profile_version")) != actual.profile_version
        ):
            raise RuntimeError(
                "execution profile mismatch: "
                f"run={expected.get('profile_id')}@{expected.get('profile_version')} "
                f"runtime={actual.profile_id}@{actual.profile_version}"
            )

    def _validate_score_policy_lock(self, run_dir: Path) -> None:
        plan_path = run_dir / "rollout_plan.json"
        if not plan_path.exists():
            raise RuntimeError(f"missing rollout score policy: {plan_path}")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        expected_policy = plan.get("score_policy") or legacy_score_policy()
        expected_context_version = str(
            plan.get(
                "planner_context_schema_version",
                planner_context_version(expected_policy),
            )
        )
        events = self._events(run_dir)
        if not events or events[0]["event_type"] != "task_created":
            raise RuntimeError("rollout has no initial task_created event")
        actual_policy = score_policy_from_task_payload(events[0]["payload"])
        actual_context_version = planner_context_version(actual_policy)
        if (
            expected_policy != actual_policy
            or expected_context_version != actual_context_version
        ):
            raise RuntimeError(
                "score policy mismatch: "
                f"run={expected_policy.get('policy_id')}@"
                f"{expected_policy.get('policy_version')}/context-{expected_context_version} "
                f"events={actual_policy.get('policy_id')}@"
                f"{actual_policy.get('policy_version')}/context-{actual_context_version}"
            )

    def _image_steps_for_route(self, operation: str, backend: Any) -> int:
        explicit = (
            self.params.generate_image_steps
            if operation == "generate"
            else self.params.edit_image_steps
        )
        if explicit is not None:
            return explicit
        profile_default = backend.num_inference_steps
        if profile_default is not None:
            return profile_default
        return self.params.image_steps

    def _evaluate_completed_image(
        self,
        run_dir: Path,
        *,
        task_spec: dict[str, Any],
        action_event: dict[str, Any],
        complete_event: dict[str, Any],
    ) -> dict[str, Any]:
        attempt_id = complete_event["payload"]["attempt_id"]
        evaluator = LocalGeneval2Adapter(
            evaluator_root=self.model_config.evaluator.config_path,
            artifact_root=run_dir,
            pass_threshold=self.params.evaluator_pass_threshold,
            fail_threshold=self.params.evaluator_fail_threshold,
        )
        report = evaluator.evaluate_to_report(
            task_spec=task_spec,
            attempt_id=attempt_id,
            image_path=self._validated_completion_image_path(run_dir, complete_event),
        )
        self._upsert_manifest_entry(run_dir, report.manifest_entry)
        geneval_event = self._append_event(
            run_dir,
            event_type="geneval2_completed",
            turn_id=action_event["turn_id"],
            producer="local_geneval2_adapter",
            input_refs=[complete_event["event_id"]],
            payload={
                "attempt_id": attempt_id,
                "constraint_results": report.constraint_results,
                "primary_score": report.primary_score,
                "report_ref": report.report_ref,
                "report_sha256": report.report_sha256,
            },
        )
        self._ensure_geneval_observation(run_dir, geneval_event)
        return geneval_event

    def _complete_evaluated_round(
        self,
        run_dir: Path,
        *,
        action_event: dict[str, Any],
        geneval_event: dict[str, Any],
    ) -> None:
        events_after_eval = self._events(run_dir)
        state_after_eval = reduce_events(events_after_eval)
        transition = {
            key: state_after_eval.latest_transition[key]
            for key in ("fixed", "regressed", "persistent_failed", "stable_pass")
        }
        memory_event = self._append_event(
            run_dir,
            event_type="memory_reduced",
            turn_id=action_event["turn_id"],
            producer="state_reducer",
            input_refs=[geneval_event["event_id"]],
            payload={
                "latest_attempt_id": state_after_eval.latest_attempt_id,
                "best_attempt_id": state_after_eval.best_attempt_id,
                "transition": transition,
                "remaining_budget": state_after_eval.remaining_budget,
            },
        )
        round_record_event = self._persist_latest_round_record(
            run_dir,
            turn_id=action_event["turn_id"],
            input_refs=[memory_event["event_id"]],
        )
        self._write_state(run_dir, reduce_events(self._events(run_dir)))
        self._build_next_planner_context(run_dir, input_refs=[round_record_event["event_id"]])

    def _recover_incomplete_image_round(
        self,
        run_dir: Path,
        *,
        task_spec: dict[str, Any],
        events: list[dict[str, Any]],
        state: EpisodeState,
    ) -> bool:
        chain = _latest_image_round_chain(events)
        if chain is None:
            return False

        start_event = chain["start"]
        action_event = _event_by_id(events, start_event["input_refs"][0])
        complete_event = chain["complete"]
        if complete_event is None:
            self._execute_image_attempt(
                run_dir,
                task_spec,
                state,
                action_event,
                existing_start_event=start_event,
            )
            return True
        self._ensure_image_completion_observation(run_dir, complete_event)

        geneval_event = chain["geneval"]
        if geneval_event is None:
            geneval_event = self._evaluate_completed_image(
                run_dir,
                task_spec=task_spec,
                action_event=action_event,
                complete_event=complete_event,
            )
            self._complete_evaluated_round(
                run_dir,
                action_event=action_event,
                geneval_event=geneval_event,
            )
            return True
        self._ensure_geneval_observation(run_dir, geneval_event)

        if chain["planner_context"] is not None:
            return False

        memory_event = chain["memory"]
        if memory_event is None:
            self._complete_evaluated_round(
                run_dir,
                action_event=action_event,
                geneval_event=geneval_event,
            )
            return True

        round_record_event = chain["round_record"]
        if round_record_event is None:
            round_record_event = self._persist_latest_round_record(
                run_dir,
                turn_id=action_event["turn_id"],
                input_refs=[memory_event["event_id"]],
            )
            self._write_state(run_dir, reduce_events(self._events(run_dir)))
            self._build_next_planner_context(
                run_dir,
                input_refs=[round_record_event["event_id"]],
            )
            return True

        self._write_state(run_dir, reduce_events(self._events(run_dir)))
        self._build_next_planner_context(
            run_dir,
            input_refs=[round_record_event["event_id"]],
        )
        return True

    def _validated_completion_image_path(
        self,
        run_dir: Path,
        complete_event: dict[str, Any],
    ) -> Path:
        payload = complete_event["payload"]
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        entry = next(
            (
                artifact
                for artifact in manifest.get("artifacts", [])
                if artifact["artifact_id"] == payload["image_artifact_id"]
            ),
            None,
        )
        if entry is None:
            raise RuntimeError(
                "completed image has no manifest entry: "
                f"{payload['image_artifact_id']}"
            )
        image_path = run_dir / entry["uri"]
        if not image_path.is_file():
            raise FileNotFoundError(f"completed image artifact is missing: {image_path}")
        actual_sha256 = sha256_file(image_path)
        if actual_sha256 != payload["artifact_sha256"] or actual_sha256 != entry["sha256"]:
            raise RuntimeError(
                "completed image artifact hash mismatch: "
                f"{payload['image_artifact_id']}"
            )
        return image_path

    def _ensure_image_completion_observation(
        self,
        run_dir: Path,
        complete_event: dict[str, Any],
    ) -> None:
        payload = complete_event["payload"]
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        entry = next(
            artifact
            for artifact in manifest.get("artifacts", [])
            if artifact["artifact_id"] == payload["image_artifact_id"]
        )
        self._append_jsonl_once(
            run_dir / "tool_observations.jsonl",
            {
                "schema_version": "0.2",
                "event_id": complete_event["event_id"],
                "observation_type": "image_execution_completed",
                "request_id": payload["request_id"],
                "attempt_id": payload["attempt_id"],
                "image_artifact_id": payload["image_artifact_id"],
                "metadata": entry.get("metadata", {}),
            },
        )

    def _ensure_geneval_observation(
        self,
        run_dir: Path,
        geneval_event: dict[str, Any],
    ) -> None:
        payload = geneval_event["payload"]
        report_path = run_dir / payload["report_ref"]
        report_payload = json.loads(report_path.read_text(encoding="utf-8"))
        self._append_jsonl_once(
            run_dir / "geneval2_results.jsonl",
            {
                "schema_version": "0.2",
                "event_id": geneval_event["event_id"],
                "attempt_id": payload["attempt_id"],
                "report_ref": payload["report_ref"],
                "report_sha256": payload["report_sha256"],
                "normalization": report_payload["normalization"],
                "constraint_results": payload["constraint_results"],
                "primary_score": payload.get("primary_score"),
            },
        )

    def _build_next_planner_context(self, run_dir: Path, *, input_refs: list[str]) -> dict[str, Any]:
        events = self._events(run_dir)
        next_index = self._next_planner_context_index(events)
        score_policy = score_policy_from_task_payload(events[0]["payload"])
        context_version = planner_context_version(score_policy)
        planner_context = build_planner_context_from_events(
            events,
            task_spec_ref="task_spec.json",
            schema_version=context_version,
        )
        ref = f"planner_contexts/planner_context_{next_index:03d}.json"
        sha = self._write_json_artifact(run_dir, ref, planner_context)
        event = self._append_event(
            run_dir,
            event_type="planner_context_built",
            turn_id=f"turn_{next_index:03d}",
            producer="planner_context_builder",
            input_refs=input_refs,
            payload={
                "planner_context_ref": ref,
                "planner_context_sha256": sha,
                "planner_context_schema_version": context_version,
            },
        )
        self._upsert_manifest_entry(
            run_dir,
            artifact_manifest_entry(
                artifact_id=f"planner_context_{next_index:03d}",
                artifact_type="planner_context",
                uri=ref,
                sha256=sha,
                media_type="application/json",
                producer="planner_context_builder",
            ),
        )
        return event

    def _persist_latest_round_record(
        self,
        run_dir: Path,
        *,
        turn_id: str | None,
        input_refs: list[str],
    ) -> dict[str, Any]:
        round_records = build_round_records_from_events(self._events(run_dir))
        if not round_records:
            raise RuntimeError("cannot persist RoundRecord before any completed image round")
        round_record = round_records[-1]
        round_index = int(round_record["round_id"].split("_", 1)[1])
        ref = f"round_records/round_record_{round_index:03d}.json"
        sha = self._write_json_artifact(run_dir, ref, round_record)
        self._upsert_manifest_entry(
            run_dir,
            artifact_manifest_entry(
                artifact_id=f"round_record_{round_index:03d}",
                artifact_type="round_record",
                uri=ref,
                sha256=sha,
                media_type="application/json",
                producer="round_record_builder",
                metadata={
                    "round_id": round_record["round_id"],
                    "result_attempt_id": round_record["result_attempt_id"],
                },
            ),
        )
        return self._append_event(
            run_dir,
            event_type="round_record_persisted",
            turn_id=turn_id,
            producer="round_record_builder",
            input_refs=input_refs,
            payload={
                "round_id": round_record["round_id"],
                "result_attempt_id": round_record["result_attempt_id"],
                "round_record_ref": ref,
                "round_record_sha256": sha,
            },
        )

    def _append_event(
        self,
        run_dir: Path,
        *,
        event_type: str,
        turn_id: str | None,
        producer: str,
        input_refs: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = {
            "schema_version": "0.2",
            "event_id": self._next_event_id(run_dir),
            "episode_id": json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))[
                "episode_id"
            ],
            "turn_id": turn_id,
            "event_type": event_type,
            "created_at": _now(),
            "producer": producer,
            "input_refs": input_refs,
            "payload": payload,
        }
        validate_instance(event, "episode_event_v0_2.schema.json")
        AppendOnlyEventStore(run_dir / "events.jsonl").append(event)
        self._refresh_event_manifest_entry(run_dir)
        return event

    def _write_state_and_submission(
        self,
        run_dir: Path,
        state: EpisodeState,
        submit_event: dict[str, Any],
    ) -> None:
        self._write_state(run_dir, state)
        submission = {
            "schema_version": "0.2",
            "episode_id": state.episode_id,
            "submit_event_id": submit_event["event_id"],
            "submitted_attempt_id": state.submitted_attempt_id,
            "reason_code": state.submitted_reason_code,
            "best_attempt_id": state.best_attempt_id,
            "attempt_order": state.attempt_order,
        }
        (run_dir / "submission.json").write_text(canonical_json(submission) + "\n", encoding="utf-8")

    def _write_state(self, run_dir: Path, state: EpisodeState) -> None:
        (run_dir / "episode_state.json").write_text(
            canonical_json(state.to_dict()) + "\n",
            encoding="utf-8",
        )

    def _upsert_manifest_entry(self, run_dir: Path, entry: dict[str, Any]) -> None:
        manifest_path = run_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifacts = {
            artifact["artifact_id"]: artifact
            for artifact in manifest.get("artifacts", [])
        }
        artifacts[entry["artifact_id"]] = entry
        manifest["artifacts"] = [artifacts[key] for key in sorted(artifacts)]
        validate_artifact_manifest_semantics(manifest)
        manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")

    def _refresh_event_manifest_entry(self, run_dir: Path) -> None:
        self._upsert_manifest_entry(
            run_dir,
            artifact_manifest_entry(
                artifact_id="artifact_000",
                artifact_type="event_log",
                uri="events.jsonl",
                sha256=sha256_file(run_dir / "events.jsonl"),
                media_type="application/x-ndjson",
                producer="phase3_live_runner",
            ),
        )

    def _teacher_image_refs(
        self,
        run_dir: Path,
        state: EpisodeState,
    ) -> list[TeacherImageRef]:
        refs = []
        artifact_paths = self._artifact_paths(run_dir)
        visible_images = visible_images_from_state(state)
        for image in visible_images:
            artifact_id = image["artifact_id"]
            refs.append(
                TeacherImageRef(
                    role=image["role"],
                    attempt_id=image["attempt_id"],
                    artifact_id=artifact_id,
                    path=artifact_paths[artifact_id],
                )
            )
        return refs

    def _retrieved_skills(
        self,
        run_dir: Path,
        events: list[dict[str, Any]],
        planner_context_event: dict[str, Any],
    ) -> list[dict[str, Any]]:
        event_by_id = {event["event_id"]: event for event in events}
        observations_by_event = _skill_observations_by_event_id(run_dir)
        skills = []
        for input_ref in planner_context_event.get("input_refs", []):
            event = event_by_id.get(input_ref)
            if event and event["event_type"] == "skill_returned":
                for skill in event["payload"]["skills"]:
                    content, content_source = _retrieval_time_skill_content(
                        run_dir,
                        skill,
                        observations_by_event.get(event["event_id"], {}),
                    )
                    skills.append({**skill, "content": content, "content_source": content_source})
        return skills

    def _extra_observations(self, state: EpisodeState, events: list[dict[str, Any]]) -> list[str]:
        observations = []
        if state.remaining_budget == 0 and state.best_attempt_id is not None:
            observations.append(
                "Budget is exhausted; submit the best available attempt with "
                "reason_code exactly best_available_under_budget. Do not use "
                "budget_exhausted_best_available."
            )
        if not state.attempt_order:
            observations.append("No image attempts exist yet; do not edit or submit.")
        last_event = events[-1]
        if last_event["event_type"] == "format_error":
            if last_event["payload"].get("error_code") != "consecutive_query_skill":
                observations.append(
                    "Previous output was rejected by the action schema: "
                    + last_event["payload"]["message"]
                )
        return observations

    def _validate_runtime_action(
        self,
        action: dict[str, Any],
        state: EpisodeState,
        retrieved_skills: list[dict[str, Any]],
        *,
        events: list[dict[str, Any]],
    ) -> None:
        action_type = action["action"]
        if not state.attempt_order and action_type in {"edit_image", "submit_attempt"}:
            raise RuntimeActionError("invalid_initial_action", "first live action cannot edit or submit")
        if state.remaining_budget == 0 and action_type != "submit_attempt":
            raise RuntimeActionError("budget_exhausted", "no image attempts remain; submit an attempt")
        if action_type in {"generate_image", "edit_image"} and state.remaining_budget <= 0:
            raise RuntimeActionError("budget_exhausted", "image attempt budget is exhausted")
        if action_type in {"generate_image", "edit_image"}:
            self._validate_retry_closure_policy(action, state)
        if action_type == "query_skill":
            skill_ids = action["arguments"].get("skill_ids", [])
            if len(skill_ids) > 3:
                raise RuntimeActionError("too_many_skills", "query_skill may request at most three skills")
            if len(skill_ids) != len(set(skill_ids)):
                raise RuntimeActionError("duplicate_skill_query", "query_skill cannot request the same skill twice")
            already_active = {
                _skill_identity_from_event_payload(skill)
                for event in events
                if event["event_type"] == "skill_returned"
                for skill in event["payload"]["skills"]
            }
            requested = {_resolved_skill_identity(self.skill_store.get(skill_id)) for skill_id in skill_ids}
            repeated = sorted(
                identity[0]
                for identity in requested
                if identity in already_active
                or any(
                    active[2] == ""
                    and active[0] == identity[0]
                    and active[1] == identity[1]
                    for active in already_active
                )
            )
            if repeated:
                raise RuntimeActionError(
                    "duplicate_skill_retrieval",
                    "same Skill ID/version/hash may be retrieved at most once per episode by default: "
                    + ", ".join(repeated),
                )
            active_round_events = _events_in_active_image_round(events)
            returned_query_ids = {
                event["payload"]["query_action_event_id"]
                for event in active_round_events
                if event["event_type"] == "skill_returned"
                and event["payload"].get("query_action_event_id")
            }
            pending_query_ids = [
                event["event_id"]
                for event in active_round_events
                if event["event_type"] == "action_validated"
                and event["payload"]["action"]["action"] == "query_skill"
                and event["event_id"] not in returned_query_ids
            ]
            if pending_query_ids:
                raise RuntimeActionError(
                    "pending_skill_query",
                    "a validated query_skill must receive its tool response "
                    "before another planner action",
                )
            if len(returned_query_ids) >= 2:
                raise RuntimeActionError(
                    "round_skill_query_limit",
                    "at most two successful query_skill interactions are "
                    "allowed per image-producing round",
                )

    def _validate_retry_closure_policy(
        self,
        action: dict[str, Any],
        state: EpisodeState,
    ) -> None:
        if not state.attempt_order:
            return

        arguments = action["arguments"]
        best_attempt_id = getattr(state, "best_attempt_id", None)
        if action["action"] == "edit_image" and best_attempt_id is not None:
            source_attempt_id = arguments["source_attempt_id"]
            if source_attempt_id != best_attempt_id:
                source = state.attempts[source_attempt_id]
                best = state.attempts[best_attempt_id]
                relevant_constraint_ids = set(arguments["target_constraint_ids"])
                relevant_constraint_ids.update(
                    arguments.get("preserve_constraint_ids", [])
                )
                evidence_ids = sorted(
                    constraint_id
                    for constraint_id in relevant_constraint_ids
                    if source.constraint_results[constraint_id]["status"] == "pass"
                    and best.constraint_results[constraint_id]["status"] != "pass"
                )
                if not evidence_ids:
                    raise RuntimeActionError(
                        "historical_source_without_constraint_evidence",
                        "edit_image must default to reducer-best source "
                        f"{best_attempt_id}; historical source {source_attempt_id} "
                        "has no relevant passed constraint that best lacks",
                    )

        transition = getattr(state, "latest_transition", None)
        latest_attempt_id = getattr(state, "latest_attempt_id", None)
        if transition is None or latest_attempt_id is None:
            return
        regressive = bool(transition["regressed"])
        no_progress = (
            not transition["fixed"]
            and not transition["regressed"]
            and latest_attempt_id != best_attempt_id
        )
        if not regressive and not no_progress:
            return

        previous_action = state.attempts[latest_attempt_id].action
        if _retry_strategy_key(action) == _retry_strategy_key(previous_action):
            raise RuntimeActionError(
                "repeated_failed_retry_strategy",
                "after a regressive or no-progress result, do not repeat the same "
                "action/source/target strategy; change the source, action type, or "
                "target_constraint_ids",
            )

    def _recover_incomplete_skill_query(
        self,
        run_dir: Path,
        *,
        events: list[dict[str, Any]],
    ) -> bool:
        returned_query_ids = {
            event["payload"]["query_action_event_id"]
            for event in events
            if event["event_type"] == "skill_returned"
            and event["payload"].get("query_action_event_id")
        }
        pending = [
            event
            for event in _events_in_active_image_round(events)
            if event["event_type"] == "action_validated"
            and event["payload"]["action"]["action"] == "query_skill"
            and event["event_id"] not in returned_query_ids
        ]
        if not pending:
            return False
        action_event = pending[-1]
        skill_event = self._execute_skill(run_dir, action_event)
        self._build_next_planner_context(
            run_dir,
            input_refs=[skill_event["event_id"]],
        )
        return True

    def _validate_instruction_quality(
        self,
        action: dict[str, Any],
        task_spec: dict[str, Any],
        state: EpisodeState,
    ) -> None:
        if action["action"] not in {"generate_image", "edit_image"}:
            return
        quality = evaluate_instruction_quality(
            action,
            task_spec,
            known_attempt_ids=state.attempt_order,
        )
        if quality.verdict != "pass":
            raise RuntimeActionError(
                "instruction_quality_rejected",
                "image instruction quality verdict must be pass before execution: "
                + canonical_json(quality.to_dict()),
            )

    def _image_path_for_attempt(
        self,
        run_dir: Path,
        state: EpisodeState,
        attempt_id: str,
    ) -> Path:
        artifact_id = state.attempts[attempt_id].image_artifact_id
        return self._artifact_paths(run_dir)[artifact_id]

    def _artifact_paths(self, run_dir: Path) -> dict[str, Path]:
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        return {
            artifact["artifact_id"]: run_dir / artifact["uri"]
            for artifact in manifest["artifacts"]
        }

    def _active_skill_operator_summaries(self, run_dir: Path, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        summaries: dict[str, dict[str, Any]] = {}
        observations_by_event = _skill_observations_by_event_id(run_dir)
        for event in events:
            if event["event_type"] != "skill_returned":
                continue
            for skill in event["payload"]["skills"]:
                content, content_source = _retrieval_time_skill_content(
                    run_dir,
                    skill,
                    observations_by_event.get(event["event_id"], {}),
                )
                version = skill["version"]
                content_sha256 = skill.get("content_sha256", "")
                key = f"{skill['skill_id']}@{version}:{content_sha256}"
                summaries[skill["skill_id"]] = {
                    "experience_id": f"skill:{key[:96]}",
                    "failure_signature": f"active_skill_operator:{skill['skill_id']}",
                    "support_count": 1,
                    "summary": _compact_operator_summary(
                        skill_id=skill["skill_id"],
                        version=version,
                        content_sha256=content_sha256,
                        content=content,
                        content_source=content_source,
                    ),
                }
        return list(summaries.values())

    def _events(self, run_dir: Path) -> list[dict[str, Any]]:
        return load_events_jsonl(run_dir / "events.jsonl")

    def _next_event_id(self, run_dir: Path) -> str:
        events = []
        if (run_dir / "events.jsonl").exists():
            events = self._events(run_dir)
        max_event = max((int(event["event_id"][4:]) for event in events), default=0)
        return f"evt_{max_event + 1:04d}"

    def _next_planner_context_index(self, events: list[dict[str, Any]]) -> int:
        return 1 + max(
            (
                int(event["payload"]["planner_context_ref"].rsplit("_", 1)[1].split(".", 1)[0])
                for event in events
                if event["event_type"] == "planner_context_built"
            ),
            default=-1,
        )

    def _turn_number(self, turn_id: str) -> int:
        return int(turn_id.split("_", 1)[1])

    def _latest_event(self, events: list[dict[str, Any]], event_type: str) -> dict[str, Any]:
        for event in reversed(events):
            if event["event_type"] == event_type:
                return event
        raise KeyError(f"no event of type {event_type}")

    def _planner_context_consumed(
        self,
        events: list[dict[str, Any]],
        planner_context_event: dict[str, Any],
    ) -> bool:
        planner_context_event_id = planner_context_event["event_id"]
        return any(
            event["event_type"] == "planner_output_recorded"
            and planner_context_event_id in event.get("input_refs", [])
            for event in events
        )

    def _write_json_artifact(self, run_dir: Path, uri: str, payload: dict[str, Any]) -> str:
        path = run_dir / uri
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
        return sha256_file(path)

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(payload))
            fh.write("\n")

    def _append_jsonl_once(
        self,
        path: Path,
        payload: dict[str, Any],
        *,
        identity_key: str = "event_id",
    ) -> None:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                existing = json.loads(line)
                if existing.get(identity_key) == payload.get(identity_key):
                    return
        self._append_jsonl(path, payload)


class RuntimeActionError(ValueError):
    def __init__(self, error_code: str, message: str):
        super().__init__(message)
        self.error_code = error_code


def _latest_validated_action(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        if event["event_type"] == "action_validated":
            return event["payload"]["action"]
    return None


def _pending_image_start(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    completed_request_ids = {
        event["payload"]["request_id"]
        for event in events
        if event["event_type"] == "image_execution_completed"
    }
    for event in reversed(events):
        if event["event_type"] != "image_execution_started":
            continue
        if event["payload"]["request_id"] not in completed_request_ids:
            return event
    return None


def _latest_image_round_chain(
    events: list[dict[str, Any]],
) -> dict[str, dict[str, Any] | None] | None:
    start_event = next(
        (
            event
            for event in reversed(events)
            if event["event_type"] == "image_execution_started"
        ),
        None,
    )
    if start_event is None:
        return None
    complete_event = next(
        (
            event
            for event in events
            if event["event_type"] == "image_execution_completed"
            and start_event["event_id"] in event.get("input_refs", [])
        ),
        None,
    )
    geneval_event = (
        _dependent_event(events, complete_event, "geneval2_completed")
        if complete_event is not None
        else None
    )
    memory_event = (
        _dependent_event(events, geneval_event, "memory_reduced")
        if geneval_event is not None
        else None
    )
    round_record_event = (
        _dependent_event(events, memory_event, "round_record_persisted")
        if memory_event is not None
        else None
    )
    planner_context_event = (
        _dependent_event(events, round_record_event, "planner_context_built")
        if round_record_event is not None
        else None
    )
    return {
        "start": start_event,
        "complete": complete_event,
        "geneval": geneval_event,
        "memory": memory_event,
        "round_record": round_record_event,
        "planner_context": planner_context_event,
    }


def _dependent_event(
    events: list[dict[str, Any]],
    parent: dict[str, Any],
    event_type: str,
) -> dict[str, Any] | None:
    return next(
        (
            event
            for event in events
            if event["event_type"] == event_type
            and parent["event_id"] in event.get("input_refs", [])
        ),
        None,
    )


def _events_in_active_image_round(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    start_index = 0
    for index, event in enumerate(events):
        if event["event_type"] == "geneval2_completed":
            start_index = index + 1
    return events[start_index:]


def _event_by_id(events: list[dict[str, Any]], event_id: str) -> dict[str, Any]:
    for event in events:
        if event["event_id"] == event_id:
            return event
    raise KeyError(f"no event with id {event_id}")


def _compact_operator_summary(
    *,
    skill_id: str,
    version: str,
    content_sha256: str,
    content: str,
    content_source: str = "retrieval_observation",
) -> str:
    bullets: list[str] = []
    in_operators = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_operators:
                break
            in_operators = stripped.lower() == "### operators"
            continue
        if in_operators and stripped.startswith("- "):
            bullets.append(_shorten_operator(stripped[2:].rstrip(".")))
    if not bullets:
        bullets = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")][:2]
    header = f"{skill_id} v{version} hash={content_sha256[:12]} active operators"
    if content_source != "retrieval_observation":
        header += f" ({content_source})"
    header += ": "
    return _join_compact_bullets(header, bullets, max_len=400)


def _shorten_operator(text: str, limit: int = 56) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _join_compact_bullets(header: str, bullets: list[str], *, max_len: int) -> str:
    if not bullets:
        return header[:max_len].rstrip()
    separator = "; "
    numbered = [f"{index + 1}. {bullet}" for index, bullet in enumerate(bullets)]
    fixed_len = len(header) + len(separator) * (len(numbered) - 1)
    budget = max_len - fixed_len
    if budget <= 0:
        compact = [f"{index + 1}" for index in range(len(numbered))]
    else:
        per_bullet = max(8, budget // len(numbered))
        compact = [_shorten_operator(bullet, per_bullet) for bullet in numbered]
        while len(header + separator.join(compact)) > max_len and per_bullet > 8:
            per_bullet -= 1
            compact = [_shorten_operator(bullet, per_bullet) for bullet in numbered]
        if len(header + separator.join(compact)) > max_len:
            compact = [f"{index + 1}" for index in range(len(numbered))]
    text = header + separator.join(compact)
    if len(text) <= max_len:
        return text.rstrip(" ;")
    return header[:max_len].rstrip(" ;")


def _skill_observations_by_event_id(run_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    path = run_dir / "tool_observations.jsonl"
    if not path.exists():
        return {}
    observations: dict[str, dict[str, dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("observation_type") != "skill_returned":
            continue
        observations[record["event_id"]] = {
            skill["skill_id"]: skill
            for skill in record.get("skills", [])
        }
    return observations


def _retrieval_time_skill_content(
    run_dir: Path,
    skill: dict[str, Any],
    observed_skills: dict[str, dict[str, Any]],
) -> tuple[str, str]:
    observed = observed_skills.get(skill["skill_id"])
    expected_sha = skill.get("content_sha256")
    if observed and observed.get("content") and observed.get("content_sha256") == expected_sha:
        content = observed["content"]
        if not expected_sha or sha256_bytes(content.encode("utf-8")) == expected_sha:
            return content, "retrieval_observation"
    content_ref = skill.get("content_ref")
    if content_ref:
        path = run_dir / content_ref
        if not path.exists():
            path = Path(content_ref)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if not expected_sha or sha256_bytes(content.encode("utf-8")) == expected_sha:
                return content, "hash_verified_content_ref"
    return skill.get("summary", "Skill content unavailable for hash-stable operator retention."), "content_unavailable"


def _skill_identity_from_event_payload(skill: dict[str, Any]) -> tuple[str, str, str]:
    return (skill["skill_id"], skill["version"], skill.get("content_sha256", ""))


def _resolved_skill_identity(skill: Any) -> tuple[str, str, str]:
    return (skill.skill_id, skill.version, skill.content_sha256)


def _retry_strategy_key(action: dict[str, Any]) -> tuple[str, str | None, tuple[str, ...]]:
    arguments = action["arguments"]
    return (
        action["action"],
        arguments.get("source_attempt_id"),
        tuple(sorted(arguments.get("target_constraint_ids", []))),
    )


def _execution_instruction(action: dict[str, Any]) -> str:
    arguments = action["arguments"]
    instruction = (
        arguments.get("instruction")
        or arguments.get("generation_instruction")
        or arguments.get("edit_instruction")
    )
    if not instruction:
        raise RuntimeActionError(
            "missing_instruction",
            "image action does not contain an executable instruction",
        )
    return instruction


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
