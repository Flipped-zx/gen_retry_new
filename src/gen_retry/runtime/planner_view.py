from __future__ import annotations

from typing import Any

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.reducer import EpisodeState, AttemptRecord, default_tool_manifest
from gen_retry.tools.skill_store import SKILL_VERSIONS


DEFAULT_SKILL_MANIFEST = [
    {
        "skill_id": "counting_and_instance_layout",
        "version": SKILL_VERSIONS["counting_and_instance_layout"],
        "description": "Exact cardinality for generation and local count repair.",
    },
    {
        "skill_id": "spatial_relation_layout",
        "version": SKILL_VERSIONS["spatial_relation_layout"],
        "description": "Static frame, depth, support, containment, and occlusion relations.",
    },
    {
        "skill_id": "attribute_entity_binding",
        "version": SKILL_VERSIONS["attribute_entity_binding"],
        "description": "Bind color, material, texture, and identity attributes to the correct entity.",
    },
    {
        "skill_id": "local_edit_preservation",
        "version": SKILL_VERSIONS["local_edit_preservation"],
        "description": "Four-part local edit instructions that preserve passed evidence.",
    },
    {
        "skill_id": "action_pose_relation",
        "version": SKILL_VERSIONS["action_pose_relation"],
        "description": (
            "Targeted verb topology and verb-pass preservation after an evaluated "
            "verb failure or uncertainty; not an initial-generation prefix."
        ),
    },
    {
        "skill_id": "object_identity_presence",
        "version": SKILL_VERSIONS["object_identity_presence"],
        "description": "Recognizable object identity, presence, full visibility, and no substitutions.",
    },
]


def build_planner_view(
    state: EpisodeState,
    *,
    task_spec_ref: str = "embedded:task_spec",
    skill_manifest: list[dict[str, Any]] | None = None,
    retrieved_experiences: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    latest_attempt = (
        state.attempts[state.latest_attempt_id] if state.latest_attempt_id else None
    )
    best_attempt = state.attempts[state.best_attempt_id] if state.best_attempt_id else None
    visible_images = []
    if latest_attempt is not None:
        visible_images.append(_image_ref(latest_attempt, "latest"))
    if best_attempt is not None:
        best_ref = _image_ref(best_attempt, "best")
        if best_ref not in visible_images:
            visible_images.append(best_ref)

    view = {
        "schema_version": "0.2",
        "episode_id": state.episode_id,
        "task_spec_ref": task_spec_ref,
        "visible_images": visible_images,
        "latest_attempt": _attempt_summary(latest_attempt) if latest_attempt else None,
        "best_attempt": _attempt_summary(best_attempt) if best_attempt else None,
        "latest_transition": state.latest_transition,
        "constraint_state": _constraint_state(state),
        "compact_history": [
            _attempt_summary(state.attempts[attempt_id])
            for attempt_id in state.attempt_order
        ],
        "remaining_budget": state.remaining_budget,
        "tool_manifest": default_tool_manifest(),
        "skill_manifest": skill_manifest if skill_manifest is not None else DEFAULT_SKILL_MANIFEST,
        "retrieved_experiences": retrieved_experiences or [],
    }
    validate_instance(view, "planner_view_v0_2.schema.json")
    return view


def _attempt_summary(attempt: AttemptRecord) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "parent_attempt_id": attempt.parent_attempt_id,
        "image_artifact_id": attempt.image_artifact_id,
        "action_type": attempt.action["action"],
        "passed_constraint_ids": attempt.passed_constraint_ids,
        "failed_constraint_ids": attempt.failed_constraint_ids,
    }


def _image_ref(attempt: AttemptRecord, role: str) -> dict[str, str]:
    return {
        "artifact_id": attempt.image_artifact_id,
        "display_id": attempt.image_artifact_id.upper(),
        "role": role,
        "attempt_id": attempt.attempt_id,
    }


def _constraint_state(state: EpisodeState) -> dict[str, dict[str, Any]]:
    constraints: dict[str, dict[str, Any]] = {
        constraint["constraint_id"]: {"status": "not_evaluated", "attempt_ids": []}
        for constraint in state.task_spec["constraints"]
    }
    for attempt_id in state.attempt_order:
        attempt = state.attempts[attempt_id]
        for constraint_id, result in attempt.constraint_results.items():
            entry: dict[str, Any] = {
                "status": result["status"],
                "attempt_ids": constraints[constraint_id]["attempt_ids"] + [attempt_id],
            }
            if "observed" in result:
                entry["latest_observed"] = result["observed"]
            constraints[constraint_id] = entry
    return constraints
