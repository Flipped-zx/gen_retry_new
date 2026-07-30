from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gen_retry.domain.score_policy import (
    PRIMARY_POLICY_ID,
    planner_context_version,
    score_policy_for_id,
)
from gen_retry.domain.artifacts import (
    artifact_manifest_entry,
    sha256_bytes,
    validate_artifact_manifest_closure,
    write_artifact_bytes,
)
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.trajectory_validator import validate_artifact_manifest_semantics
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import build_planner_context_from_events
from gen_retry.runtime.reducer import reduce_events


DEFAULT_CREATED_AT = "2026-07-14T00:00:00Z"


def prepare_rollout_runs(
    *,
    selected_prompts_path: Path,
    output_root: Path,
    summary_output: Path,
    max_image_attempts: int = 5,
    created_at: str = DEFAULT_CREATED_AT,
    limit: int | None = None,
    prompt_ids: list[str] | None = None,
    score_policy_id: str = PRIMARY_POLICY_ID,
    execution_profile_id: str = "qwen_image_edit_only",
    execution_profile_version: str = "1",
) -> dict[str, Any]:
    selected_payload = json.loads(selected_prompts_path.read_text(encoding="utf-8"))
    score_policy = score_policy_for_id(score_policy_id)
    context_version = planner_context_version(score_policy)
    selected = selected_payload["selected_prompts"]
    if prompt_ids:
        if len(prompt_ids) != len(set(prompt_ids)):
            raise ValueError("prompt_ids must be unique")
        requested = set(prompt_ids)
        selected = [
            candidate for candidate in selected if candidate["prompt_id"] in requested
        ]
        found = {candidate["prompt_id"] for candidate in selected}
        missing = sorted(requested - found)
        if missing:
            raise ValueError("unknown prompt_ids: " + ", ".join(missing))
    if limit is not None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        selected = selected[:limit]
    prepared = [
        _prepare_one_run(
            candidate=candidate,
            output_root=output_root,
            max_image_attempts=max_image_attempts,
            created_at=created_at,
            execution_profile_id=execution_profile_id,
            execution_profile_version=execution_profile_version,
            score_policy=score_policy,
            planner_context_schema_version=context_version,
        )
        for candidate in selected
    ]
    summary = {
        "schema_version": "0.2",
        "prepared_count": len(prepared),
        "selected_prompts_ref": str(selected_prompts_path),
        "selected_prompt_limit": limit,
        "selected_prompt_ids": prompt_ids,
        "max_image_attempts": max_image_attempts,
        "created_at": created_at,
        "execution_profile": {
            "profile_id": execution_profile_id,
            "profile_version": execution_profile_version,
        },
        "planner_context_schema_version": context_version,
        "score_policy": score_policy,
        "fresh_start_policy": {
            "legacy_images_imported": False,
            "legacy_attempts_parented": False,
            "first_live_action_requirement": (
                "query_skill followed by fresh generate_image, or fresh generate_image"
            ),
        },
        "episodes": prepared,
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    return summary


def _prepare_one_run(
    *,
    candidate: dict[str, Any],
    output_root: Path,
    max_image_attempts: int,
    created_at: str,
    execution_profile_id: str,
    execution_profile_version: str,
    score_policy: dict[str, Any],
    planner_context_schema_version: str,
) -> dict[str, Any]:
    episode_id = f"phase3_ep_{int(candidate['selection_rank']):03d}"
    run_dir = output_root / episode_id
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(
            f"refusing to overwrite non-empty rollout directory: {run_dir}"
        )
    run_dir.mkdir(parents=True, exist_ok=True)

    task_spec = _task_spec_from_selected_candidate(
        candidate,
        episode_id=episode_id,
        max_image_attempts=max_image_attempts,
    )
    task_spec_bytes = canonical_json(task_spec).encode("utf-8")
    task_spec_sha = write_artifact_bytes(run_dir, "task_spec.json", task_spec_bytes)

    task_event = {
        "schema_version": "0.2",
        "event_id": "evt_0001",
        "episode_id": episode_id,
        "turn_id": None,
        "event_type": "task_created",
        "created_at": created_at,
        "producer": "phase3_rollout_preparer",
        "input_refs": [],
        "payload": {
            "task_spec": task_spec,
            "score_policy": score_policy,
        },
    }
    state = reduce_events([task_event])
    planner_context = build_planner_context_from_events(
        [task_event],
        task_spec_ref="task_spec.json",
        schema_version=planner_context_schema_version,
    )
    planner_context_bytes = canonical_json(planner_context).encode("utf-8")
    planner_context_sha = write_artifact_bytes(
        run_dir,
        "planner_contexts/planner_context_000.json",
        planner_context_bytes,
    )

    planner_context_event = {
        "schema_version": "0.2",
        "event_id": "evt_0002",
        "episode_id": episode_id,
        "turn_id": "turn_000",
        "event_type": "planner_context_built",
        "created_at": created_at,
        "producer": "planner_context_builder",
        "input_refs": ["evt_0001"],
        "payload": {
            "planner_context_ref": "planner_contexts/planner_context_000.json",
            "planner_context_sha256": planner_context_sha,
            "planner_context_schema_version": planner_context_schema_version,
        },
    }
    events_bytes = (
        canonical_json(task_event)
        + "\n"
        + canonical_json(planner_context_event)
        + "\n"
    ).encode("utf-8")
    events_sha = write_artifact_bytes(run_dir, "events.jsonl", events_bytes)
    state_with_view_event = reduce_events(load_events_jsonl(run_dir / "events.jsonl"))
    write_artifact_bytes(
        run_dir,
        "episode_state.json",
        canonical_json(state_with_view_event.to_dict()).encode("utf-8"),
    )
    write_artifact_bytes(
        run_dir,
        "rollout_plan.json",
        canonical_json(
            _rollout_plan(
                candidate,
                episode_id,
                max_image_attempts,
                execution_profile_id=execution_profile_id,
                execution_profile_version=execution_profile_version,
                score_policy=score_policy,
                planner_context_schema_version=planner_context_schema_version,
            )
        ).encode("utf-8"),
    )
    _write_empty_jsonl_scaffold(run_dir)

    manifest = {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "artifacts": [
            artifact_manifest_entry(
                artifact_id="task_spec_000",
                artifact_type="task_spec",
                uri="task_spec.json",
                sha256=task_spec_sha,
                media_type="application/json",
                producer="phase3_rollout_preparer",
                created_at=created_at,
            ),
            artifact_manifest_entry(
                artifact_id="planner_context_000",
                artifact_type="planner_context",
                uri="planner_contexts/planner_context_000.json",
                sha256=planner_context_sha,
                media_type="application/json",
                producer="planner_context_builder",
                created_at=created_at,
            ),
            artifact_manifest_entry(
                artifact_id="artifact_000",
                artifact_type="event_log",
                uri="events.jsonl",
                sha256=events_sha,
                media_type="application/x-ndjson",
                producer="phase3_rollout_preparer",
                created_at=created_at,
            ),
        ],
    }
    validate_artifact_manifest_semantics(manifest)
    manifest_sha = write_artifact_bytes(
        run_dir,
        "manifest.json",
        canonical_json(manifest).encode("utf-8"),
    )
    validate_artifact_manifest_closure(manifest, run_dir)

    return {
        "episode_id": episode_id,
        "run_dir": str(run_dir),
        "candidate_id": candidate["candidate_id"],
        "prompt_id": candidate["prompt_id"],
        "selection_rank": candidate["selection_rank"],
        "original_prompt": candidate["original_prompt"],
        "constraint_count": len(task_spec["constraints"]),
        "constraint_type_histogram": candidate["constraint_type_histogram"],
        "task_spec_sha256": task_spec_sha,
        "events_sha256": events_sha,
        "planner_context_sha256": planner_context_sha,
        "manifest_sha256": manifest_sha,
        "first_live_turn_id": "turn_000",
        "first_live_action_must_not_be_edit": True,
        "execution_profile": {
            "profile_id": execution_profile_id,
            "profile_version": execution_profile_version,
        },
        "planner_context_schema_version": planner_context_schema_version,
        "score_policy": score_policy,
    }


def _task_spec_from_selected_candidate(
    candidate: dict[str, Any],
    *,
    episode_id: str,
    max_image_attempts: int,
) -> dict[str, Any]:
    task_spec = {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "original_prompt": candidate["original_prompt"],
        "constraints": [
            {
                "constraint_id": constraint["constraint_id"],
                "constraint_type": constraint["constraint_type"],
                "requirement": constraint["requirement"],
                "evaluator_question": constraint.get("evaluator_question"),
                "priority": constraint.get("priority", 3),
            }
            for constraint in candidate["atomic_constraints"]
        ],
        "max_image_attempts": max_image_attempts,
    }
    validate_instance(task_spec, "task_spec_v0_2.schema.json")
    return task_spec


def _rollout_plan(
    candidate: dict[str, Any],
    episode_id: str,
    max_image_attempts: int,
    *,
    execution_profile_id: str,
    execution_profile_version: str,
    score_policy: dict[str, Any],
    planner_context_schema_version: str,
) -> dict[str, Any]:
    return {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "candidate_id": candidate["candidate_id"],
        "prompt_id": candidate["prompt_id"],
        "selection_rank": candidate["selection_rank"],
        "max_image_attempts": max_image_attempts,
        "original_prompt": candidate["original_prompt"],
        "execution_profile": {
            "profile_id": execution_profile_id,
            "profile_version": execution_profile_version,
        },
        "planner_context_schema_version": planner_context_schema_version,
        "score_policy": score_policy,
        "fresh_start_policy": {
            "initial_attempt_history": [],
            "initial_best_attempt_id": None,
            "source_image": None,
            "allowed_first_actions": ["query_skill", "generate_image"],
            "disallowed_first_action": "edit_image",
        },
        "provenance": candidate["provenance"],
    }


def _write_empty_jsonl_scaffold(run_dir: Path) -> None:
    for uri in (
        "planner_requests.jsonl",
        "raw_teacher_outputs.jsonl",
        "canonical_actions.jsonl",
        "tool_observations.jsonl",
        "geneval2_results.jsonl",
    ):
        write_artifact_bytes(run_dir, uri, b"")
    (run_dir / "images").mkdir(parents=True, exist_ok=True)
