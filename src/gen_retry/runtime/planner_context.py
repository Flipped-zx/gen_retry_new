from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.auxiliary_quality import (
    QUALITY_DECISION_POLICY_ID,
    compact_quality_fields,
)
from gen_retry.domain.score_policy import (
    PRIMARY_POLICY_ID,
    candidate_is_better,
    primary_score_value,
    score_policy_from_task_payload,
)
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.planner_view import DEFAULT_SKILL_MANIFEST
from gen_retry.runtime.reducer import AttemptRecord, EpisodeState, default_tool_manifest, reduce_events


PASS = "pass"
UNCERTAIN = "uncertain"


def load_skill_observations(
    run_dir: Path,
) -> dict[str, dict[str, dict[str, Any]]]:
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
            skill["skill_id"]: skill for skill in record.get("skills", [])
        }
    return observations


def build_planner_context_from_events(
    events: list[dict[str, Any]],
    *,
    task_spec_ref: str = "embedded:task_spec",
    skill_manifest: list[dict[str, Any]] | None = None,
    schema_version: str = "0.5",
    skill_observations: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build a planner input from an event prefix.

    The public context intentionally exposes only five protocol sections. Round
    and step IDs remain internal bookkeeping so future evaluator outcomes cannot
    enter the current planner call.
    """

    if not events:
        raise ValueError("cannot build PlannerContext without events")
    if schema_version not in {"0.4", "0.5", "0.6", "0.7", "0.8"}:
        raise ValueError(f"unsupported PlannerContext schema version: {schema_version}")
    state = reduce_events(events)
    timeline = _round_timeline(events, skill_observations=skill_observations)
    if schema_version == "0.4":
        context = {
            "task_context": _task_context(state.task_spec),
            "latest_observation": _observation(
                state,
                state.latest_attempt_id,
                include_status=False,
            ),
            "skill_context": _skill_context(timeline),
            "episode_memory": _episode_memory_v04(timeline["completed_rounds"], state),
            "runtime_state": _runtime_state(state),
        }
    elif schema_version == "0.5":
        context = {
            "task_context": _task_context(state.task_spec),
            "latest_attempt": _observation(
                state,
                state.latest_attempt_id,
                include_status=True,
            ),
            "skill_context": _skill_context(timeline),
            "episode_memory": _episode_memory_v05(timeline["completed_rounds"], state),
            "runtime_state": _runtime_state(state),
        }
    else:
        if state.score_policy["policy_id"] != PRIMARY_POLICY_ID:
            raise ValueError(
                f"PlannerContext v{schema_version} requires the primary "
                "Geneval2 score policy"
            )
        context = {
            "planner_context_schema_version": schema_version,
            "task_context": _task_context(state.task_spec),
            "latest_attempt": _observation(
                state,
                state.latest_attempt_id,
                include_status=True,
                include_primary_score=True,
                include_auxiliary_quality=schema_version == "0.8",
            ),
            "skill_context": _skill_context(timeline),
            "episode_memory": (
                _episode_memory_v08(timeline["completed_rounds"], state)
                if schema_version == "0.8"
                else (
                    _episode_memory_v07(timeline["completed_rounds"], state)
                    if schema_version == "0.7"
                    else _episode_memory_v06(timeline["completed_rounds"], state)
                )
            ),
            "runtime_state": _runtime_state(
                state,
                include_score_policy=True,
                include_auxiliary_quality_policy=schema_version == "0.8",
            ),
        }
    validate_instance(context, f"planner_context_v{schema_version.replace('.', '_')}.schema.json")
    return context


def build_round_records_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _round_timeline(events)["completed_rounds"]


def visible_images_from_state(state: EpisodeState) -> list[dict[str, str]]:
    refs = []
    if state.latest_attempt_id:
        refs.append(_image_ref(state.attempts[state.latest_attempt_id], "latest"))
    if state.best_attempt_id:
        best = _image_ref(state.attempts[state.best_attempt_id], "best")
        if state.best_attempt_id != state.latest_attempt_id:
            refs.append(best)
        best_attempt = state.attempts[state.best_attempt_id]
        for attempt_id in state.attempt_order:
            if attempt_id in {state.latest_attempt_id, state.best_attempt_id}:
                continue
            attempt = state.attempts[attempt_id]
            if attempt.pass_count != best_attempt.pass_count:
                continue
            has_unique_pass = any(
                result["status"] == PASS
                and best_attempt.constraint_results[constraint_id]["status"] != PASS
                for constraint_id, result in attempt.constraint_results.items()
            )
            if has_unique_pass:
                refs.append(_image_ref(attempt, "historical_candidate"))
    return refs


def _round_timeline(
    events: list[dict[str, Any]],
    *,
    skill_observations: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    task_spec_event = next((event for event in events if event["event_type"] == "task_created"), None)
    if task_spec_event is None:
        raise ValueError("task_created event is required")
    task_spec = task_spec_event["payload"]["task_spec"]
    score_policy = score_policy_from_task_payload(task_spec_event["payload"])
    constraints = {constraint["constraint_id"] for constraint in task_spec.get("constraints", [])}
    constraints_by_id = {
        constraint["constraint_id"]: constraint
        for constraint in task_spec.get("constraints", [])
    }

    attempts: dict[str, AttemptRecord] = {}
    latest_attempt_id: str | None = None
    best_attempt: AttemptRecord | None = None
    action_by_event_id: dict[str, dict[str, Any]] = {}
    action_event_by_request_id: dict[str, str] = {}
    completion_by_attempt_id: dict[str, dict[str, Any]] = {}
    query_targets_by_event_id: dict[str, dict[str, Any]] = {}
    active_skills: dict[str, dict[str, Any]] = {}
    current_round = _new_active_round(0, latest_attempt_id)
    completed_rounds: list[dict[str, Any]] = []

    for event in events:
        event_type = event["event_type"]
        payload = event["payload"]

        if event_type == "action_validated":
            action = payload["action"]
            action_by_event_id[event["event_id"]] = action
            if action["action"] == "query_skill":
                if current_round.get("image_action") is not None:
                    raise ValueError("query_skill cannot be added after terminal image action")
                targets = action["arguments"]["target_constraint_ids"]
                query_targets_by_event_id[event["event_id"]] = {
                    "target_constraint_ids": targets,
                    "action_schema_version": action.get("schema_version", "0.2"),
                }
                for skill_id in action["arguments"]["skill_ids"]:
                    current_round["skill_queries"].append(
                        {
                            "skill_id": skill_id,
                            "target_constraint_ids": _skill_target_ids(
                                skill_id,
                                targets,
                                constraints_by_id,
                                legacy_spatial_verbs=(
                                    action.get("schema_version", "0.2") != "0.5"
                                ),
                            ),
                        }
                    )
            elif action["action"] in {"generate_image", "edit_image"}:
                if current_round.get("image_action") is not None:
                    raise ValueError("round already has a terminal image action")
                current_round["image_action"] = _image_action_record(action)

        elif event_type == "skill_returned":
            query_info = query_targets_by_event_id.get(
                payload["query_action_event_id"],
                {
                    "target_constraint_ids": payload.get("target_constraint_ids", []),
                    "action_schema_version": "0.2",
                },
            )
            query_targets = query_info["target_constraint_ids"]
            for skill in payload["skills"]:
                skill_id = skill["skill_id"]
                active_skills[skill_id] = {
                    "skill_id": skill_id,
                    "target_constraint_ids": _skill_target_ids(
                        skill_id,
                        query_targets,
                        constraints_by_id,
                        legacy_spatial_verbs=skill.get("version", "1.0.0").startswith("1."),
                    ),
                    "summary": skill.get("summary", ""),
                    "full_guidance": _skill_guidance(
                        skill,
                        observed_skill=(skill_observations or {})
                        .get(event["event_id"], {})
                        .get(skill_id),
                    ),
                    "retrieved_round_index": len(completed_rounds),
                }

        elif event_type == "image_execution_started":
            action_event_id = next(
                (ref for ref in event.get("input_refs", []) if ref in action_by_event_id),
                None,
            )
            if action_event_id is not None:
                action_event_by_request_id[payload["request_id"]] = action_event_id

        elif event_type == "image_execution_completed":
            completion_by_attempt_id[payload["attempt_id"]] = event

        elif event_type == "geneval2_completed":
            completion = completion_by_attempt_id[payload["attempt_id"]]
            action_event_id = action_event_by_request_id[completion["payload"]["request_id"]]
            action = action_by_event_id[action_event_id]
            if current_round.get("image_action") is None:
                current_round["image_action"] = _image_action_record(action)
            constraint_results = {
                result["constraint_id"]: result
                for result in payload["constraint_results"]
            }
            attempt = AttemptRecord(
                attempt_id=payload["attempt_id"],
                parent_attempt_id=completion["payload"]["parent_attempt_id"],
                action_event_id=action_event_id,
                action=action,
                operation=completion["payload"]["operation"],
                image_artifact_id=completion["payload"]["image_artifact_id"],
                constraint_results=constraint_results,
                primary_score=primary_score_value(payload, score_policy),
            )

            comparison_attempt = _comparison_attempt(
                action=action,
                latest_attempt_id=latest_attempt_id,
                attempts=attempts,
            )
            previous_pass_count = comparison_attempt.pass_count if comparison_attempt else 0
            current_pass_count = attempt.pass_count
            became_best = (
                best_attempt is None
                or candidate_is_better(
                    candidate_pass_count=attempt.pass_count,
                    candidate_primary_score=attempt.primary_score,
                    current_pass_count=best_attempt.pass_count,
                    current_primary_score=best_attempt.primary_score,
                    score_policy=score_policy,
                )
            )
            observed_outcome = _observed_outcome(
                previous=comparison_attempt,
                current=attempt,
                constraints=constraints,
                became_best=became_best,
            )

            attempts[attempt.attempt_id] = attempt
            latest_attempt_id = attempt.attempt_id
            if became_best:
                best_attempt = attempt

            primary_score_delta = (
                attempt.primary_score - comparison_attempt.primary_score
                if comparison_attempt is not None
                and attempt.primary_score is not None
                and comparison_attempt.primary_score is not None
                else None
            )

            round_value = {
                "score_delta": (current_pass_count - previous_pass_count)
                / max(1, len(constraints)),
                "net_atom_gain": len(observed_outcome["fixed_constraint_ids"])
                - len(observed_outcome["regressed_constraint_ids"]),
                "became_best": became_best,
            }
            if score_policy["policy_id"] == PRIMARY_POLICY_ID:
                round_value["primary_score_delta"] = primary_score_delta

            round_record = {
                "round_id": current_round["round_id"],
                "start_observation_ref": {"attempt_id": current_round["start_attempt_id"]},
                "skill_queries": deepcopy(current_round["skill_queries"]),
                "image_action": current_round["image_action"],
                "result_attempt_id": attempt.attempt_id,
                "observed_outcome": observed_outcome,
                "value": round_value,
            }
            completed_rounds.append(round_record)
            current_round = _new_active_round(len(completed_rounds), latest_attempt_id)

    return {
        "completed_rounds": completed_rounds,
        "active_round": current_round,
        "active_skills": active_skills,
        "current_round_index": len(completed_rounds),
    }


def _new_active_round(index: int, start_attempt_id: str | None) -> dict[str, Any]:
    return {
        "round_id": f"r_{index:03d}",
        "start_attempt_id": start_attempt_id,
        "skill_queries": [],
        "image_action": None,
    }


def _task_context(task_spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "original_prompt": task_spec.get("original_prompt", ""),
        "max_image_attempts": task_spec["max_image_attempts"],
        "atom_constraints": [
            {
                "constraint_id": constraint["constraint_id"],
                "constraint_type": constraint.get("constraint_type", ""),
                "requirement": constraint.get("requirement", ""),
                "evaluator_question": constraint.get("evaluator_question"),
            }
            for constraint in task_spec.get("constraints", [])
        ],
    }


def _skill_context(timeline: dict[str, Any]) -> dict[str, Any]:
    active_round_has_query = bool(timeline["active_round"]["skill_queries"])
    current_round_index = timeline["current_round_index"]
    active_skills = []
    for skill in timeline["active_skills"].values():
        is_fresh = active_round_has_query and skill["retrieved_round_index"] == current_round_index
        active_skills.append(
            {
                "skill_id": skill["skill_id"],
                "target_constraint_ids": skill["target_constraint_ids"],
                "guidance": skill["full_guidance"] if is_fresh else skill["summary"],
                "guidance_level": "full" if is_fresh else "summary",
            }
        )
    return {"active_skills": sorted(active_skills, key=lambda item: item["skill_id"])}


def _skill_target_ids(
    skill_id: str,
    query_target_ids: list[str],
    constraints_by_id: dict[str, dict[str, Any]],
    *,
    legacy_spatial_verbs: bool = False,
) -> list[str]:
    type_groups = {
        "counting": {"count"},
        "spatial_relation": {"position", "relation", "spatial"},
        "action_pose": {"verb"},
        "attribute": {"attribute"},
        "object_identity": {"object"},
        "preservation": {
            "attribute",
            "object",
            "count",
            "position",
            "verb",
            "relation",
            "spatial",
        },
    }
    if legacy_spatial_verbs:
        type_groups["spatial_relation"] = {"position", "relation", "spatial", "verb"}
    matched_types: set[str] = set()
    for marker, constraint_types in type_groups.items():
        if marker in skill_id:
            matched_types |= constraint_types
    if not matched_types:
        return sorted(query_target_ids)
    matched = sorted(
        constraint_id
        for constraint_id in query_target_ids
        if constraints_by_id.get(constraint_id, {}).get("constraint_type") in matched_types
    )
    return matched or sorted(query_target_ids)


def _skill_guidance(
    skill: dict[str, Any],
    *,
    observed_skill: dict[str, Any] | None = None,
) -> str:
    expected_sha = skill.get("content_sha256")
    for candidate in (skill.get("content"), (observed_skill or {}).get("content")):
        if candidate and (
            not expected_sha
            or sha256_bytes(candidate.encode("utf-8")) == expected_sha
        ):
            return candidate
    content_ref = skill.get("content_ref")
    if content_ref:
        path = Path(content_ref)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if (
                not expected_sha
                or sha256_bytes(content.encode("utf-8")) == expected_sha
            ):
                return content
    return skill.get("summary", "")


def _image_action_record(action: dict[str, Any]) -> dict[str, Any]:
    args = action["arguments"]
    instruction = (
        args.get("instruction")
        or args.get("generation_instruction")
        or args.get("edit_instruction")
    )
    record = {
        "action": action["action"],
        "source_attempt_id": args.get("source_attempt_id") if action["action"] == "edit_image" else None,
        "target_constraint_ids": args["target_constraint_ids"],
        "preserve_constraint_ids": args["preserve_constraint_ids"],
        "instruction": instruction,
    }
    if action.get("schema_version") != "0.5":
        diagnosis = args.get("diagnosis_summary")
        if diagnosis is None and "diagnostic_hypotheses" in args:
            diagnosis = _diagnosis_from_legacy_hypotheses(args.get("diagnostic_hypotheses", []))
        record["decision_summary"] = args.get("decision_summary", "")
        record["diagnosis_summary"] = diagnosis
    return record


def _diagnosis_from_legacy_hypotheses(hypotheses: list[dict[str, Any]]) -> str | None:
    parts = []
    for hypothesis in hypotheses:
        text = hypothesis.get("hypothesis")
        if text:
            parts.append(text)
    return " ".join(parts) if parts else None


def _comparison_attempt(
    *,
    action: dict[str, Any],
    latest_attempt_id: str | None,
    attempts: dict[str, AttemptRecord],
) -> AttemptRecord | None:
    if action["action"] == "edit_image":
        return attempts[action["arguments"]["source_attempt_id"]]
    if latest_attempt_id is None:
        return None
    return attempts[latest_attempt_id]


def _observed_outcome(
    *,
    previous: AttemptRecord | None,
    current: AttemptRecord,
    constraints: set[str],
    became_best: bool,
) -> dict[str, Any]:
    if previous is None:
        return {
            "comparison_attempt_id": None,
            "fixed_constraint_ids": [],
            "regressed_constraint_ids": [],
            "persistent_failed_constraint_ids": [],
            "preserved_constraint_ids": [],
            "initial_passed_constraint_ids": _status_ids(current, PASS),
            "initial_failed_constraint_ids": sorted(
                cid
                for cid, result in current.constraint_results.items()
                if result["status"] not in {PASS, UNCERTAIN}
            ),
            "initial_uncertain_constraint_ids": _status_ids(current, UNCERTAIN),
            "new_uncertain_constraint_ids": [],
            "became_best": became_best,
        }

    fixed = sorted(
        cid
        for cid in constraints
        if current.constraint_results[cid]["status"] == PASS
        and previous.constraint_results[cid]["status"] != PASS
    )
    regressed = sorted(
        cid
        for cid in constraints
        if current.constraint_results[cid]["status"] != PASS
        and previous.constraint_results[cid]["status"] == PASS
    )
    persistent_failed = sorted(
        cid
        for cid in constraints
        if current.constraint_results[cid]["status"] != PASS
        and previous.constraint_results[cid]["status"] != PASS
    )
    preserved = sorted(
        cid
        for cid in constraints
        if current.constraint_results[cid]["status"] == PASS
        and previous.constraint_results[cid]["status"] == PASS
    )
    new_uncertain = sorted(
        cid
        for cid in constraints
        if current.constraint_results[cid]["status"] == UNCERTAIN
        and previous.constraint_results[cid]["status"] != UNCERTAIN
    )
    return {
        "comparison_attempt_id": previous.attempt_id,
        "fixed_constraint_ids": fixed,
        "regressed_constraint_ids": regressed,
        "persistent_failed_constraint_ids": persistent_failed,
        "preserved_constraint_ids": preserved,
        "initial_passed_constraint_ids": [],
        "initial_failed_constraint_ids": [],
        "initial_uncertain_constraint_ids": [],
        "new_uncertain_constraint_ids": new_uncertain,
        "became_best": became_best,
    }


def _status_ids(attempt: AttemptRecord, status: str) -> list[str]:
    return sorted(
        constraint_id
        for constraint_id, result in attempt.constraint_results.items()
        if result["status"] == status
    )


def _observation(
    state: EpisodeState,
    attempt_id: str | None,
    *,
    include_status: bool,
    include_primary_score: bool = False,
    include_auxiliary_quality: bool = False,
) -> dict[str, Any] | None:
    if attempt_id is None:
        return None
    attempt = state.attempts[attempt_id]
    observation = {
        "attempt_id": attempt.attempt_id,
        "constraint_results": _constraint_results(attempt, include_status=include_status),
    }
    if include_primary_score:
        if attempt.primary_score is None:
            raise ValueError("PlannerContext v0.6 requires attempt primary scores")
        observation["primary_score"] = attempt.primary_score
    if include_auxiliary_quality:
        quality = compact_quality_fields(attempt.auxiliary_quality)
        if quality is not None:
            observation["auxiliary_quality"] = quality
    return observation


def _constraint_results(
    attempt: AttemptRecord,
    *,
    include_status: bool,
) -> dict[str, Any]:
    return {
        "passed_constraint_ids": attempt.passed_constraint_ids,
        "failed_constraint_ids": sorted(
            cid
            for cid, result in attempt.constraint_results.items()
            if result["status"] not in {PASS, UNCERTAIN}
        ),
        "uncertain_constraint_ids": _status_ids(attempt, UNCERTAIN),
        "observations": [
            _constraint_observation(
                constraint_id,
                result,
                include_status=include_status,
            )
            for constraint_id, result in sorted(attempt.constraint_results.items())
        ],
    }


def _constraint_observation(
    constraint_id: str,
    result: dict[str, Any],
    *,
    include_status: bool,
) -> dict[str, Any]:
    observation = {
        "constraint_id": constraint_id,
        "observed_value": _observed_value(result),
    }
    if include_status:
        observation["status"] = result["status"]
    return observation


def _observed_value(result: dict[str, Any]) -> str | int | float | bool | None:
    observed = result.get("observed")
    if observed is None or isinstance(observed, (str, int, float, bool)):
        return observed
    return str(observed)[:400]


def _image_ref(attempt: AttemptRecord, role: str) -> dict[str, str]:
    return {
        "artifact_id": attempt.image_artifact_id,
        "role": role,
        "attempt_id": attempt.attempt_id,
    }


def _episode_memory_v04(rounds: list[dict[str, Any]], state: EpisodeState) -> dict[str, Any]:
    recent_round = _recent_round(rounds[-1]) if rounds else None
    earlier = [_round_summary(round_record) for round_record in rounds[:-1]]
    return {
        "recent_round": recent_round,
        "earlier_rounds": earlier,
        "best_attempt": _best_attempt_memory_v04(state),
    }


def _episode_memory_v05(rounds: list[dict[str, Any]], state: EpisodeState) -> dict[str, Any]:
    last_completed = _last_completed_image_round_v05(rounds[-1]) if rounds else None
    prior = [_prior_image_round_v05(round_record, state) for round_record in rounds[:-1]]
    return {
        "last_completed_image_round": last_completed,
        "prior_image_rounds": prior,
        "best_attempt": _best_attempt_memory_v05(state),
    }


def _episode_memory_v06(
    rounds: list[dict[str, Any]],
    state: EpisodeState,
) -> dict[str, Any]:
    last_completed = _last_completed_image_round_v06(rounds[-1]) if rounds else None
    prior = [_prior_image_round_v06(round_record, state) for round_record in rounds[:-1]]
    return {
        "last_completed_image_round": last_completed,
        "prior_image_rounds": prior,
        "best_attempt": _best_attempt_memory_v06(state),
    }


def _episode_memory_v07(
    rounds: list[dict[str, Any]],
    state: EpisodeState,
) -> dict[str, Any]:
    last_completed = _last_completed_image_round_v06(rounds[-1]) if rounds else None
    prior = [_prior_image_round_v07(round_record, state) for round_record in rounds[:-1]]
    return {
        "last_completed_image_round": last_completed,
        "prior_image_rounds": prior,
        "best_attempt": _best_attempt_memory_v06(state),
    }


def _episode_memory_v08(
    rounds: list[dict[str, Any]],
    state: EpisodeState,
) -> dict[str, Any]:
    last_completed = _last_completed_image_round_v06(rounds[-1]) if rounds else None
    prior = [_prior_image_round_v07(round_record, state) for round_record in rounds[:-1]]
    return {
        "last_completed_image_round": last_completed,
        "prior_image_rounds": prior,
        "best_attempt": _best_attempt_memory_v08(state),
        "quality_history": [
            quality
            for attempt_id in state.attempt_order
            if (quality := compact_quality_fields(state.attempts[attempt_id].auxiliary_quality))
            is not None
        ],
    }


def _recent_round(round_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_queries": round_record["skill_queries"],
        "image_action": round_record["image_action"],
        "result_attempt_id": round_record["result_attempt_id"],
        "observed_outcome": round_record["observed_outcome"],
    }


def _round_summary(round_record: dict[str, Any]) -> dict[str, Any]:
    image_action = round_record["image_action"]
    return {
        "action": image_action["action"],
        "source_attempt_id": image_action["source_attempt_id"],
        "result_attempt_id": round_record["result_attempt_id"],
        "decision_summary": image_action["decision_summary"],
        "target_constraint_ids": image_action["target_constraint_ids"],
        "preserve_constraint_ids": image_action["preserve_constraint_ids"],
        "outcome_summary": {
            "fixed_constraint_ids": round_record["observed_outcome"]["fixed_constraint_ids"],
            "regressed_constraint_ids": round_record["observed_outcome"]["regressed_constraint_ids"],
            "persistent_failed_constraint_ids": round_record["observed_outcome"][
                "persistent_failed_constraint_ids"
            ],
            "became_best": round_record["observed_outcome"]["became_best"],
        },
    }


def _last_completed_image_round_v05(round_record: dict[str, Any]) -> dict[str, Any]:
    action = round_record["image_action"]
    outcome = round_record["observed_outcome"]
    baseline_attempt_id = outcome["comparison_attempt_id"]
    if baseline_attempt_id is None:
        observed_outcome = {
            "baseline_attempt_id": None,
            "initial_failed_constraint_ids": outcome["initial_failed_constraint_ids"],
            "initial_uncertain_constraint_ids": outcome["initial_uncertain_constraint_ids"],
            "became_best": outcome["became_best"],
        }
    else:
        observed_outcome = {
            "baseline_attempt_id": baseline_attempt_id,
            "fixed_constraint_ids": outcome["fixed_constraint_ids"],
            "regressed_constraint_ids": outcome["regressed_constraint_ids"],
            "persistent_failed_constraint_ids": outcome["persistent_failed_constraint_ids"],
            "preserved_constraint_ids": outcome["preserved_constraint_ids"],
            "new_uncertain_constraint_ids": outcome["new_uncertain_constraint_ids"],
            "became_best": outcome["became_best"],
        }
    return {
        "skill_queries": round_record["skill_queries"],
        "image_action": {
            "action": action["action"],
            "source_attempt_id": action["source_attempt_id"],
            "target_constraint_ids": action["target_constraint_ids"],
            "preserve_constraint_ids": action["preserve_constraint_ids"],
            "instruction": action["instruction"],
        },
        "result_attempt_id": round_record["result_attempt_id"],
        "observed_outcome": observed_outcome,
    }


def _last_completed_image_round_v06(round_record: dict[str, Any]) -> dict[str, Any]:
    result = _last_completed_image_round_v05(round_record)
    result["observed_outcome"]["primary_score_delta"] = round_record["value"][
        "primary_score_delta"
    ]
    return result


def _prior_image_round_v05(
    round_record: dict[str, Any],
    state: EpisodeState,
) -> dict[str, Any]:
    image_action = round_record["image_action"]
    result_attempt = state.attempts[round_record["result_attempt_id"]]
    outcome = round_record["observed_outcome"]
    return {
        "action": image_action["action"],
        "source_attempt_id": image_action["source_attempt_id"],
        "result_attempt_id": round_record["result_attempt_id"],
        "target_constraint_ids": image_action["target_constraint_ids"],
        "preserve_constraint_ids": image_action["preserve_constraint_ids"],
        "outcome_summary": {
            "result_failed_constraint_ids": sorted(
                constraint_id
                for constraint_id, result in result_attempt.constraint_results.items()
                if result["status"] not in {PASS, UNCERTAIN}
            ),
            "result_uncertain_constraint_ids": _status_ids(result_attempt, UNCERTAIN),
            "fixed_constraint_ids": outcome["fixed_constraint_ids"],
            "regressed_constraint_ids": outcome["regressed_constraint_ids"],
            "became_best": outcome["became_best"],
        },
    }


def _prior_image_round_v06(
    round_record: dict[str, Any],
    state: EpisodeState,
) -> dict[str, Any]:
    result = _prior_image_round_v05(round_record, state)
    result["outcome_summary"]["baseline_attempt_id"] = round_record[
        "observed_outcome"
    ]["comparison_attempt_id"]
    result["outcome_summary"]["primary_score_delta"] = round_record["value"][
        "primary_score_delta"
    ]
    return result


def _prior_image_round_v07(
    round_record: dict[str, Any],
    state: EpisodeState,
) -> dict[str, Any]:
    result = _prior_image_round_v06(round_record, state)
    result["instruction"] = round_record["image_action"]["instruction"]
    return result


def _best_attempt_memory_v04(state: EpisodeState) -> dict[str, Any] | None:
    if state.best_attempt_id is None:
        return None
    best_attempt = state.attempts[state.best_attempt_id]
    return {
        "attempt_id": best_attempt.attempt_id,
        "same_as_latest": best_attempt.attempt_id == state.latest_attempt_id,
        "constraint_results": _constraint_results(best_attempt, include_status=False),
    }


def _best_attempt_memory_v05(state: EpisodeState) -> dict[str, Any] | None:
    if state.best_attempt_id is None:
        return None
    best_attempt = state.attempts[state.best_attempt_id]
    if best_attempt.attempt_id == state.latest_attempt_id:
        return {
            "attempt_id": best_attempt.attempt_id,
            "constraint_results_ref": "latest_attempt",
        }
    return {
        "attempt_id": best_attempt.attempt_id,
        "constraint_results": _constraint_results(best_attempt, include_status=True),
    }


def _best_attempt_memory_v06(state: EpisodeState) -> dict[str, Any] | None:
    if state.best_attempt_id is None:
        return None
    best_attempt = state.attempts[state.best_attempt_id]
    if best_attempt.attempt_id == state.latest_attempt_id:
        return {
            "attempt_id": best_attempt.attempt_id,
            "constraint_results_ref": "latest_attempt",
        }
    if best_attempt.primary_score is None:
        raise ValueError("PlannerContext v0.6 requires best-attempt primary score")
    return {
        "attempt_id": best_attempt.attempt_id,
        "primary_score": best_attempt.primary_score,
        "constraint_results": _constraint_results(best_attempt, include_status=True),
    }


def _best_attempt_memory_v08(state: EpisodeState) -> dict[str, Any] | None:
    result = _best_attempt_memory_v06(state)
    if result is None or state.best_attempt_id == state.latest_attempt_id:
        return result
    quality = compact_quality_fields(
        state.attempts[state.best_attempt_id].auxiliary_quality
    )
    if quality is not None:
        result["auxiliary_quality"] = quality
    return result


def _runtime_state(
    state: EpisodeState,
    *,
    include_score_policy: bool = False,
    include_auxiliary_quality_policy: bool = False,
) -> dict[str, Any]:
    if state.remaining_budget == 0:
        available_actions = ["submit_attempt"] if state.best_attempt_id is not None else []
    elif state.attempt_order:
        available_actions = ["query_skill", "generate_image", "edit_image", "submit_attempt"]
    else:
        available_actions = ["query_skill", "generate_image"]
    runtime_state = {
        "remaining_image_budget": state.remaining_budget,
        "available_actions": available_actions,
    }
    if include_score_policy:
        runtime_state["score_policy"] = deepcopy(state.score_policy)
    if include_auxiliary_quality_policy:
        runtime_state["auxiliary_quality_decision"] = {
            "policy_id": QUALITY_DECISION_POLICY_ID,
            "application": "planner_context_only",
            "primary_objective": "geneval2",
            "intervention_skill_id": "local_edit_preservation",
            "hidden_source_filter": False,
        }
    return runtime_state


def default_skill_manifest() -> list[dict[str, Any]]:
    return DEFAULT_SKILL_MANIFEST


def planner_context_tool_manifest() -> list[dict[str, str]]:
    return default_tool_manifest()
