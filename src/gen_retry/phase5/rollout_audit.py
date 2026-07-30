from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from gen_retry.agent.instruction_quality import evaluate_instruction_quality
from gen_retry.domain.artifacts import validate_artifact_manifest_closure
from gen_retry.domain.score_policy import (
    planner_context_version,
    score_policy_from_task_payload,
    soft_tifa_geometric_mean,
)
from gen_retry.protocol.action_parser import parse_action
from gen_retry.protocol.reference_validator import validate_action_references
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.trajectory_validator import validate_artifact_manifest_semantics
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_view import DEFAULT_SKILL_MANIFEST
from gen_retry.runtime.reducer import reduce_events


SCHEMA_VERSION = "0.2"
KEY_LIKE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".txt", ".yaml", ".yml"}


def audit_rollout_batch(
    *,
    run_root: Path,
    selection_path: Path,
    artifact_path: Path,
    report_path: Path,
    expected_count: int,
    episode_ids: list[str] | None = None,
) -> dict[str, Any]:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selected = selection["selected_prompts"]
    run_dirs = _select_run_dirs(run_root, episode_ids)
    if len(run_dirs) != expected_count:
        raise ValueError(
            f"expected {expected_count} runs, got {len(run_dirs)}"
        )
    selected_by_prompt_id = {
        candidate["prompt_id"]: candidate for candidate in selected
    }
    selected_for_runs: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        plan = _load_json(run_dir / "rollout_plan.json")
        prompt_id = plan["prompt_id"]
        if prompt_id not in selected_by_prompt_id:
            raise ValueError(
                f"{run_dir.name}: prompt {prompt_id} is absent from selection"
            )
        selected_for_runs.append(selected_by_prompt_id[prompt_id])

    episode_results = [
        _audit_episode(run_dir, candidate)
        for run_dir, candidate in zip(
            run_dirs,
            selected_for_runs,
            strict=True,
        )
    ]
    audited_episode_ids = {run_dir.name for run_dir in run_dirs}
    scheduler_profiles = [
        record
        for record in _load_jsonl_if_exists(run_root / "scheduler_profiles.jsonl")
        if audited_episode_ids.intersection(record.get("episode_ids", []))
    ]
    secret_scan = _scan_for_key_like_text(
        [*run_dirs, artifact_path.parent, report_path.parent]
    )
    if secret_scan["matches"]:
        raise ValueError(
            f"credential-like text found in {secret_scan['matching_file_count']} files"
        )

    total_attempts = sum(item["attempt_count"] for item in episode_results)
    initial_pass = sum(item["initial_pass_count"] for item in episode_results)
    best_pass = sum(item["best_pass_count"] for item in episode_results)
    total_constraints = sum(item["constraint_count"] for item in episode_results)
    all_pass = sum(item["all_constraints_passed"] for item in episode_results)
    first_geneval2_score = sum(
        item["first_agent_geneval2_score"] for item in episode_results
    ) / len(episode_results)
    submitted_geneval2_score = sum(
        item["submitted_geneval2_score"] for item in episode_results
    ) / len(episode_results)
    peak_geneval2_score = sum(
        item["peak_geneval2_score"] for item in episode_results
    ) / len(episode_results)
    first_geneval2_am = sum(
        item["first_agent_geneval2_am"] for item in episode_results
    ) / len(episode_results)
    submitted_geneval2_am = sum(
        item["submitted_geneval2_am"] for item in episode_results
    ) / len(episode_results)
    version_counts = Counter(
        version
        for item in episode_results
        for version in item["teacher_system_prompt_versions"]
    )
    execution_profile_counts = Counter(
        f"{item['execution_profile']['profile_id']}@"
        f"{item['execution_profile']['profile_version']}"
        for item in episode_results
    )
    planner_context_version_counts = Counter(
        item["planner_context_schema_version"]
        for item in episode_results
    )
    score_policy_counts = Counter(
        f"{item['score_policy']['policy_id']}@"
        f"{item['score_policy']['policy_version']}"
        for item in episode_results
    )
    backend_counts = Counter(
        backend
        for item in episode_results
        for backend, count in item["image_backend_counts"].items()
        for _ in range(count)
    )
    canonical_action_counts = Counter(
        action
        for item in episode_results
        for action, count in item["canonical_action_counts"].items()
        for _ in range(count)
    )
    action_backend_counts = Counter(
        f"{attempt['action']}|{attempt['backend']}"
        for item in episode_results
        for attempt in item["attempts"]
    )
    format_error_classification = Counter(
        {
            key: sum(
                item["format_error_classification"].get(key, 0)
                for item in episode_results
            )
            for key in (
                "passes_current_contract",
                "protocol_or_reference_invalid",
                "quality_still_rejected",
            )
        }
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "expected_episode_count": expected_count,
        "validated_episode_count": len(episode_results),
        "selection_tier_counts": dict(
            sorted(
                Counter(
                    candidate["difficulty_tier"]
                    for candidate in selected_for_runs
                ).items()
            )
        ),
        "total_image_attempts": total_attempts,
        "total_constraint_slots": total_constraints,
        "aggregate_initial_pass_count": initial_pass,
        "aggregate_best_pass_count": best_pass,
        "aggregate_initial_pass_rate": initial_pass / total_constraints,
        "aggregate_best_pass_rate": best_pass / total_constraints,
        "aggregate_atom_gain": best_pass - initial_pass,
        "geneval2_score_policy": {
            "name": "Soft-TIFA",
            "per_image_am": "mean(correct_answer_probability)",
            "per_image": (
                "exp(mean(log(max(correct_answer_probability, 1e-300))))"
            ),
            "per_image_gm": (
                "exp(mean(log(max(correct_answer_probability, 1e-300))))"
            ),
            "batch": "arithmetic mean of per-image scores",
            "display_scale": 100,
            "primary_metric": "GM",
            "source_compatibility": (
                "Flow-DPPO local full-vocabulary Geneval2 scorer"
            ),
        },
        "first_agent_geneval2_am": first_geneval2_am,
        "first_agent_geneval2_am_100": first_geneval2_am * 100,
        "submitted_geneval2_am": submitted_geneval2_am,
        "submitted_geneval2_am_100": submitted_geneval2_am * 100,
        "submitted_to_first_geneval2_am_gain_100": (
            submitted_geneval2_am - first_geneval2_am
        )
        * 100,
        "first_agent_geneval2_score": first_geneval2_score,
        "first_agent_geneval2_score_100": first_geneval2_score * 100,
        "submitted_geneval2_score": submitted_geneval2_score,
        "submitted_geneval2_score_100": submitted_geneval2_score * 100,
        "peak_geneval2_score": peak_geneval2_score,
        "peak_geneval2_score_100": peak_geneval2_score * 100,
        "submitted_to_first_geneval2_gain_100": (
            submitted_geneval2_score - first_geneval2_score
        )
        * 100,
        "peak_to_first_geneval2_gain_100": (
            peak_geneval2_score - first_geneval2_score
        )
        * 100,
        "submitted_to_peak_geneval2_gap_100": (
            peak_geneval2_score - submitted_geneval2_score
        )
        * 100,
        "all_constraints_passed_episode_count": all_pass,
        "historical_best_submission_count": sum(
            item["submitted_attempt_id"] != item["latest_attempt_id"]
            for item in episode_results
        ),
        "regression_episode_count": sum(
            item["regression_image_action_count"] > 0
            for item in episode_results
        ),
        "regression_image_action_count": sum(
            item["regression_image_action_count"]
            for item in episode_results
        ),
        "ineffective_image_action_count": sum(
            item["ineffective_image_action_count"]
            for item in episode_results
        ),
        "historical_branch_count": sum(
            item["historical_branch_count"]
            for item in episode_results
        ),
        "canonical_action_counts": dict(sorted(canonical_action_counts.items())),
        "action_backend_counts": dict(sorted(action_backend_counts.items())),
        "format_error_count": sum(item["format_error_count"] for item in episode_results),
        "format_error_classification": dict(format_error_classification),
        "teacher_model_ids": sorted(
            {
                model_id
                for item in episode_results
                for model_id in item["teacher_model_ids"]
            }
        ),
        "teacher_system_prompt_version_counts": dict(sorted(version_counts.items())),
        "planner_context_version_counts": dict(
            sorted(planner_context_version_counts.items())
        ),
        "score_policy_counts": dict(sorted(score_policy_counts.items())),
        "image_runtime": {
            "execution_profile_counts": dict(
                sorted(execution_profile_counts.items())
            ),
            "backend_counts": dict(sorted(backend_counts.items())),
            "width": 1024,
            "height": 1024,
        },
        "scheduler_profiles": scheduler_profiles,
        "credential_scan": {
            "status": "PASS",
            "matching_file_count": 0,
        },
        "episodes": episode_results,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _select_run_dirs(
    run_root: Path,
    episode_ids: list[str] | None,
) -> list[Path]:
    if episode_ids is None:
        return sorted(path for path in run_root.glob("phase3_ep_*") if path.is_dir())
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode_ids must be unique")
    run_dirs = sorted(run_root / episode_id for episode_id in episode_ids)
    missing = [path.name for path in run_dirs if not path.is_dir()]
    if missing:
        raise ValueError("missing rollout directories: " + ", ".join(missing))
    return run_dirs


def _audit_episode(run_dir: Path, selected: dict[str, Any]) -> dict[str, Any]:
    task_spec = _load_json(run_dir / "task_spec.json")
    if task_spec["original_prompt"] != selected["original_prompt"]:
        raise ValueError(f"{run_dir.name}: selected prompt mismatch")
    selected_constraints = selected["atomic_constraints"]
    if task_spec["constraints"] != selected_constraints:
        raise ValueError(f"{run_dir.name}: selected atom rubric mismatch")
    validate_instance(task_spec, "task_spec_v0_2.schema.json")

    manifest = _load_json(run_dir / "manifest.json")
    validate_instance(manifest, "artifact_manifest_v0_2.schema.json")
    validate_artifact_manifest_semantics(manifest)
    validate_artifact_manifest_closure(manifest, run_dir)

    events = load_events_jsonl(run_dir / "events.jsonl")
    for event in events:
        validate_instance(event, "episode_event_v0_2.schema.json")
    state = reduce_events(events)
    plan = _load_json(run_dir / "rollout_plan.json")
    execution_profile = plan.get("execution_profile") or {
        "profile_id": "qwen_image_edit_only",
        "profile_version": "1",
    }
    if state.submitted_attempt_id is None:
        raise ValueError(f"{run_dir.name}: episode is not submitted")
    if state.submitted_attempt_id != state.best_attempt_id:
        raise ValueError(f"{run_dir.name}: submission is not reducer best")
    if not 1 <= len(state.attempt_order) <= task_spec["max_image_attempts"]:
        raise ValueError(f"{run_dir.name}: invalid image attempt count")

    canonical_actions = _load_jsonl(run_dir / "canonical_actions.jsonl")
    for record in canonical_actions:
        validate_instance(record["action"], "action_protocol_v0_5.schema.json")
    image_actions = [
        record["action"]
        for record in canonical_actions
        if record["action"]["action"] in {"generate_image", "edit_image"}
    ]
    canonical_action_sequence = [
        record["action"]["action"] for record in canonical_actions
    ]
    if not image_actions or image_actions[0]["action"] != "generate_image":
        raise ValueError(f"{run_dir.name}: first image action is not fresh generation")
    if "source_attempt_id" in image_actions[0]["arguments"]:
        raise ValueError(f"{run_dir.name}: fresh generation has a source attempt")
    if len(image_actions) != len(state.attempt_order):
        raise ValueError(f"{run_dir.name}: image action/attempt count mismatch")

    event_counts = Counter(event["event_type"] for event in events)
    for event_type in (
        "image_execution_started",
        "image_execution_completed",
        "geneval2_completed",
        "memory_reduced",
        "round_record_persisted",
    ):
        if event_counts[event_type] != len(state.attempt_order):
            raise ValueError(
                f"{run_dir.name}: {event_type} count does not match attempts"
            )
    if event_counts["attempt_submitted"] != 1:
        raise ValueError(f"{run_dir.name}: expected one submission event")

    constraint_ids = {
        constraint["constraint_id"] for constraint in task_spec["constraints"]
    }
    geneval_results = {
        record["attempt_id"]: record
        for record in _load_jsonl(run_dir / "geneval2_results.jsonl")
    }
    if set(geneval_results) != set(state.attempt_order):
        raise ValueError(f"{run_dir.name}: Geneval2 attempt coverage mismatch")
    geneval2_scores: dict[str, float] = {}
    geneval2_am_scores: dict[str, float] = {}
    for attempt_id, result in geneval_results.items():
        observed_ids = {
            item["constraint_id"] for item in result["constraint_results"]
        }
        if observed_ids != constraint_ids:
            raise ValueError(f"{run_dir.name}/{attempt_id}: atom coverage mismatch")
        statuses = {item["status"] for item in result["constraint_results"]}
        if not statuses <= {"pass", "fail", "uncertain"}:
            raise ValueError(f"{run_dir.name}/{attempt_id}: invalid atom status")
        probabilities = [
            float(item["confidence"])
            for item in result["constraint_results"]
        ]
        geneval2_am_scores[attempt_id] = soft_tifa_arithmetic_mean(probabilities)
        geneval2_scores[attempt_id] = soft_tifa_geometric_mean(probabilities)

    artifacts_by_attempt = {
        artifact["attempt_id"]: artifact
        for artifact in manifest["artifacts"]
        if artifact["artifact_type"] == "image"
    }
    if set(artifacts_by_attempt) != set(state.attempt_order):
        raise ValueError(f"{run_dir.name}: image artifact coverage mismatch")
    completions_by_attempt = {
        event["payload"]["attempt_id"]: event["payload"]
        for event in events
        if event["event_type"] == "image_execution_completed"
    }
    image_backend_counts: Counter[str] = Counter()
    for attempt_id, attempt in state.attempts.items():
        artifact = artifacts_by_attempt[attempt_id]
        metadata = artifact["metadata"]
        completion = completions_by_attempt[attempt_id]
        backend = completion["backend"]
        image_backend_counts[backend] += 1
        if metadata.get("provider") != "local":
            raise ValueError(
                f"{run_dir.name}/{attempt_id}: image provider is not local"
            )
        if metadata.get("backend_id", metadata.get("backend")) != backend:
            raise ValueError(
                f"{run_dir.name}/{attempt_id}: image backend mismatch"
            )
        if completion.get("model_id") is not None:
            for key in (
                "model_id",
                "model_revision_or_fingerprint",
                "pipeline_id",
                "adapter_version",
            ):
                if metadata.get(key) != completion[key]:
                    raise ValueError(
                        f"{run_dir.name}/{attempt_id}: image metadata {key} mismatch"
                    )
            if metadata.get("sampling") != completion["sampling"]:
                raise ValueError(
                    f"{run_dir.name}/{attempt_id}: image sampling mismatch"
                )
        sampling = metadata.get("sampling") or {
            "width": metadata.get("width"),
            "height": metadata.get("height"),
        }
        if sampling.get("width") != 1024 or sampling.get("height") != 1024:
            raise ValueError(
                f"{run_dir.name}/{attempt_id}: image dimensions mismatch"
            )
        with Image.open(run_dir / artifact["uri"]) as image:
            if image.size != (1024, 1024):
                raise ValueError(f"{run_dir.name}/{attempt_id}: image size mismatch")
            image.verify()
        if attempt.action["action"] == "edit_image":
            source_id = attempt.action["arguments"]["source_attempt_id"]
            if attempt.parent_attempt_id != source_id:
                raise ValueError(f"{run_dir.name}/{attempt_id}: edit lineage mismatch")
        elif attempt.parent_attempt_id is not None:
            raise ValueError(f"{run_dir.name}/{attempt_id}: generation has a parent")

    round_records = [
        _load_json(path)
        for path in sorted((run_dir / "round_records").glob("round_record_*.json"))
    ]
    if [record["result_attempt_id"] for record in round_records] != state.attempt_order:
        raise ValueError(f"{run_dir.name}: RoundRecord sequence mismatch")
    _audit_planner_context_snapshots(run_dir, events)

    requests = _load_jsonl(run_dir / "planner_requests.jsonl")
    raw_outputs = _load_jsonl(run_dir / "raw_teacher_outputs.jsonl")
    request_ids = [record["request_id"] for record in requests]
    raw_request_ids = [record["request_id"] for record in raw_outputs]
    if set(request_ids) != set(raw_request_ids):
        raise ValueError(f"{run_dir.name}: teacher request/output ID coverage mismatch")
    if len(raw_request_ids) != len(set(raw_request_ids)):
        raise ValueError(f"{run_dir.name}: duplicate persisted teacher raw output")
    canonical_request_ids = {record["request_id"] for record in canonical_actions}
    if not canonical_request_ids <= set(raw_request_ids):
        raise ValueError(f"{run_dir.name}: canonical action has no raw teacher output")
    model_ids = {record["model_id"] for record in raw_outputs}
    if model_ids != {"gpt-5.5"}:
        raise ValueError(f"{run_dir.name}: unexpected teacher model IDs")
    if not all(
        record["redaction"].get("credentials_removed") is True
        for record in raw_outputs
    ):
        raise ValueError(f"{run_dir.name}: raw output redaction marker missing")

    first_attempt = state.attempts[state.attempt_order[0]]
    best_attempt = state.attempts[state.best_attempt_id]
    peak_geneval2_attempt_id = max(
        state.attempt_order,
        key=lambda attempt_id: geneval2_scores[attempt_id],
    )
    format_error_classification = _classify_format_errors(
        run_dir=run_dir,
        task_spec=task_spec,
        events=events,
    )
    attempt_rows = [
        {
            "attempt_id": attempt_id,
            "action": round_records[index]["image_action"]["action"],
            "source_attempt_id": round_records[index]["image_action"][
                "source_attempt_id"
            ],
            "backend": completions_by_attempt[attempt_id]["backend"],
            "model_id": completions_by_attempt[attempt_id].get("model_id"),
            "pass_count": state.attempts[attempt_id].pass_count,
            "geneval2_am": geneval2_am_scores[attempt_id],
            "geneval2_score": geneval2_scores[attempt_id],
            "fixed_constraint_ids": round_records[index]["observed_outcome"][
                "fixed_constraint_ids"
            ],
            "regressed_constraint_ids": round_records[index]["observed_outcome"][
                "regressed_constraint_ids"
            ],
            "persistent_failed_constraint_ids": round_records[index][
                "observed_outcome"
            ]["persistent_failed_constraint_ids"],
            "became_best": round_records[index]["observed_outcome"]["became_best"],
        }
        for index, attempt_id in enumerate(state.attempt_order)
    ]
    regression_image_action_count = sum(
        bool(attempt["regressed_constraint_ids"])
        for attempt in attempt_rows
    )
    ineffective_image_action_count = sum(
        index > 0
        and not attempt["fixed_constraint_ids"]
        and not attempt["regressed_constraint_ids"]
        and not attempt["became_best"]
        for index, attempt in enumerate(attempt_rows)
    )
    historical_branch_count = sum(
        index > 0
        and attempt["action"] == "edit_image"
        and attempt["source_attempt_id"] != state.attempt_order[index - 1]
        for index, attempt in enumerate(attempt_rows)
    )
    return {
        "episode_id": state.episode_id,
        "prompt_id": selected["prompt_id"],
        "difficulty_tier": selected["difficulty_tier"],
        "constraint_count": len(constraint_ids),
        "attempt_count": len(state.attempt_order),
        "initial_pass_count": first_attempt.pass_count,
        "best_pass_count": best_attempt.pass_count,
        "atom_gain": best_attempt.pass_count - first_attempt.pass_count,
        "first_agent_geneval2_am": geneval2_am_scores[first_attempt.attempt_id],
        "submitted_geneval2_am": geneval2_am_scores[state.submitted_attempt_id],
        "first_agent_geneval2_score": geneval2_scores[first_attempt.attempt_id],
        "submitted_geneval2_score": geneval2_scores[state.submitted_attempt_id],
        "peak_geneval2_attempt_id": peak_geneval2_attempt_id,
        "peak_geneval2_score": geneval2_scores[peak_geneval2_attempt_id],
        "submitted_to_first_geneval2_gain": (
            geneval2_scores[state.submitted_attempt_id]
            - geneval2_scores[first_attempt.attempt_id]
        ),
        "all_constraints_passed": best_attempt.pass_count == len(constraint_ids),
        "best_attempt_id": state.best_attempt_id,
        "latest_attempt_id": state.latest_attempt_id,
        "submitted_attempt_id": state.submitted_attempt_id,
        "submitted_reason_code": state.submitted_reason_code,
        "canonical_action_count": len(canonical_actions),
        "canonical_action_sequence": canonical_action_sequence,
        "canonical_action_counts": dict(
            sorted(Counter(canonical_action_sequence).items())
        ),
        "regression_image_action_count": regression_image_action_count,
        "ineffective_image_action_count": ineffective_image_action_count,
        "historical_branch_count": historical_branch_count,
        "interrupted_request_retry_count": len(request_ids) - len(set(request_ids)),
        "format_error_count": event_counts["format_error"],
        "format_error_classification": format_error_classification,
        "teacher_model_ids": sorted(model_ids),
        "teacher_system_prompt_versions": sorted(
            {record["system_prompt_version"] for record in requests}
        ),
        "planner_context_schema_version": planner_context_version(
            state.score_policy
        ),
        "score_policy": state.score_policy,
        "execution_profile": execution_profile,
        "image_backend_counts": dict(sorted(image_backend_counts.items())),
        "manifest_closed": True,
        "planner_context_snapshots_verified": event_counts["planner_context_built"],
        "attempts": attempt_rows,
    }


def _audit_planner_context_snapshots(
    run_dir: Path,
    events: list[dict[str, Any]],
) -> None:
    score_policy = score_policy_from_task_payload(events[0]["payload"])
    expected_context_version = planner_context_version(score_policy)
    for index, event in enumerate(events):
        if event["event_type"] != "planner_context_built":
            continue
        context = _load_json(run_dir / event["payload"]["planner_context_ref"])
        context_version = str(
            event["payload"].get(
                "planner_context_schema_version",
                context.get("planner_context_schema_version", "0.5"),
            )
        )
        if context_version != expected_context_version:
            raise ValueError(
                f"{run_dir.name}: PlannerContext {context_version} disagrees "
                f"with score policy {score_policy['policy_id']}"
            )
        validate_instance(
            context,
            f"planner_context_v{context_version.replace('.', '_')}.schema.json",
        )
        state = reduce_events(events[: index + 1])
        latest = context["latest_attempt"]
        best = context["episode_memory"]["best_attempt"]
        latest_id = latest["attempt_id"] if latest else None
        best_id = best["attempt_id"] if best else None
        if latest_id != state.latest_attempt_id:
            raise ValueError(
                f"{run_dir.name}: PlannerContext latest contains future or stale state"
            )
        if best_id != state.best_attempt_id:
            raise ValueError(
                f"{run_dir.name}: PlannerContext best contains future or stale state"
            )
        if context["runtime_state"]["remaining_image_budget"] != state.remaining_budget:
            raise ValueError(f"{run_dir.name}: PlannerContext budget mismatch")
        if context_version == "0.6" and latest is not None:
            if latest["primary_score"] != state.attempts[latest_id].primary_score:
                raise ValueError(
                    f"{run_dir.name}: PlannerContext primary score mismatch"
                )


def _classify_format_errors(
    *,
    run_dir: Path,
    task_spec: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, int]:
    classification: Counter[str] = Counter()
    available_skill_ids = [
        entry["skill_id"] for entry in DEFAULT_SKILL_MANIFEST
    ]
    for index, event in enumerate(events):
        if event["event_type"] != "format_error":
            continue
        raw_record = _load_json(run_dir / event["payload"]["raw_output_ref"])
        try:
            action = parse_action(raw_record["raw_text"]).action
            state = reduce_events(events[:index])
            validate_action_references(
                action,
                task_spec,
                known_attempt_ids=state.attempt_order,
                available_skill_ids=available_skill_ids,
            )
        except Exception:
            classification["protocol_or_reference_invalid"] += 1
            continue
        if action["action"] not in {"generate_image", "edit_image"}:
            classification["passes_current_contract"] += 1
            continue
        quality = evaluate_instruction_quality(
            action,
            task_spec,
            known_attempt_ids=state.attempt_order,
        )
        if quality.verdict == "pass":
            classification["passes_current_contract"] += 1
        else:
            classification["quality_still_rejected"] += 1
    return {
        key: classification[key]
        for key in (
            "passes_current_contract",
            "protocol_or_reference_invalid",
            "quality_still_rejected",
        )
    }


def _scan_for_key_like_text(roots: list[Path]) -> dict[str, Any]:
    matching_files: set[str] = set()
    matches = 0
    for root in roots:
        if not root.exists():
            continue
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            found = KEY_LIKE_PATTERN.findall(text)
            if found:
                matches += len(found)
                matching_files.add(str(path))
    return {
        "matches": matches,
        "matching_file_count": len(matching_files),
    }


def soft_tifa_arithmetic_mean(probabilities: list[float]) -> float:
    _validate_soft_tifa_probabilities(probabilities)
    return sum(probabilities) / len(probabilities)


def _validate_soft_tifa_probabilities(probabilities: list[float]) -> None:
    if not probabilities:
        raise ValueError("Soft-TIFA score requires at least one probability")
    if any(not math.isfinite(value) or value < 0 or value > 1 for value in probabilities):
        raise ValueError("Soft-TIFA probabilities must be finite values in [0, 1]")


def _render_report(summary: dict[str, Any]) -> str:
    episode_count = summary["validated_episode_count"]
    uses_gm_tiebreak = set(summary["score_policy_counts"]) == {
        "geneval2_pass_count_then_gm@1"
    }
    if uses_gm_tiebreak:
        selection_semantics = (
            "Gen-Retry selects best by passed-atom count, then higher "
            "Soft-TIFA GM, then the earlier Attempt. A trajectory's submitted "
            "GM can still be lower than its peak GM when the peak-GM image "
            "passes fewer atoms."
        )
        planner_score_visibility = (
            "PlannerContext v0.6 exposed the environment-owned GM scalar for "
            "latest/best plus source-aware GM deltas. The Planner did not see "
            "raw confidence vectors or AM; it saw GM together with normalized "
            "atom statuses and observed answers."
        )
    else:
        selection_semantics = (
            "Historical Gen-Retry selects best by passed-atom count and keeps "
            "the earlier Attempt on a tie; it does not rank Attempts by GM. "
            "Submitted GM can therefore be lower than peak GM."
        )
        planner_score_visibility = (
            "The historical Planner did not see confidence values, AM, or GM; "
            "it saw normalized atom statuses and observed answers. AM and GM "
            "are post-hoc environment metrics computed from persisted "
            "probabilities."
        )
    lines = [
        "# Flow-DPPO Rollout Validation",
        "",
        f"- Status: **{summary['status']}**",
        f"- Validated episodes: {episode_count}/{episode_count}",
        (
            "- PlannerContext versions: "
            f"{summary['planner_context_version_counts']}"
        ),
        f"- Score policies: {summary['score_policy_counts']}",
        (
            "- Execution profiles: "
            f"{summary['image_runtime']['execution_profile_counts']}"
        ),
        f"- Image backends: {summary['image_runtime']['backend_counts']}",
        f"- Difficulty mix: {summary['selection_tier_counts']}",
        f"- Evaluated image attempts: {summary['total_image_attempts']}",
        (
        "- Aggregate first Agent attempt atom pass rate: "
            f"{summary['aggregate_initial_pass_count']}/"
            f"{summary['total_constraint_slots']} "
            f"({summary['aggregate_initial_pass_rate']:.1%})"
        ),
        (
        "- Aggregate submitted reducer-best atom pass rate: "
            f"{summary['aggregate_best_pass_count']}/"
            f"{summary['total_constraint_slots']} "
            f"({summary['aggregate_best_pass_rate']:.1%})"
        ),
        f"- Net submitted-over-first atom gain: +{summary['aggregate_atom_gain']}",
        (
            "- Geneval2 Soft-TIFA AM, first Agent attempts: "
            f"{summary['first_agent_geneval2_am_100']:.2f}"
        ),
        (
            "- Geneval2 Soft-TIFA AM, submitted reducer-best attempts: "
            f"{summary['submitted_geneval2_am_100']:.2f} "
            f"({summary['submitted_to_first_geneval2_am_gain_100']:+.2f})"
        ),
        (
            "- Geneval2 Soft-TIFA GM, first Agent attempts: "
            f"{summary['first_agent_geneval2_score_100']:.2f}"
        ),
        (
            "- Geneval2 Soft-TIFA GM, submitted reducer-best attempts: "
            f"{summary['submitted_geneval2_score_100']:.2f} "
            f"({summary['submitted_to_first_geneval2_gain_100']:+.2f})"
        ),
        (
            "- Geneval2 Soft-TIFA GM, per-trajectory peak attempts: "
            f"{summary['peak_geneval2_score_100']:.2f} "
            f"({summary['peak_to_first_geneval2_gain_100']:+.2f})"
        ),
        (
            "- Submitted-to-peak GM gap: "
            f"{summary['submitted_to_peak_geneval2_gap_100']:.2f}"
        ),
        (
            "- Episodes with all atoms passed: "
            f"{summary['all_constraints_passed_episode_count']}/{episode_count}"
        ),
        (
            "- Historical-best submissions: "
            f"{summary['historical_best_submission_count']}/{episode_count}"
        ),
        (
            "- Regression exposure: "
            f"{summary['regression_episode_count']}/{episode_count} episodes, "
            f"{summary['regression_image_action_count']} image actions"
        ),
        (
            "- Ineffective image actions: "
            f"{summary['ineffective_image_action_count']}"
        ),
        f"- Historical edit branches: {summary['historical_branch_count']}",
        f"- Canonical action counts: {summary['canonical_action_counts']}",
        f"- Action/backend counts: {summary['action_backend_counts']}",
        (
            "- Scheduler profiles: "
            f"{len(summary['scheduler_profiles'])} recorded launches"
        ),
        f"- Teacher model IDs: {summary['teacher_model_ids']}",
        (
            "- Rejected raw Teacher turns: "
            f"{summary['format_error_count']} total "
            f"({summary['format_error_classification']['passes_current_contract']} pass "
            "the corrected current validator; "
            f"{summary['format_error_classification']['protocol_or_reference_invalid']} "
            "remain protocol/reference-invalid; "
            f"{summary['format_error_classification']['quality_still_rejected']} "
            "remain instruction-quality-invalid)."
        ),
        (
            "- Credential-like text in audited outputs: "
            f"{summary['credential_scan']['matching_file_count']} files"
        ),
        "",
        "## Score Semantics",
        "",
        "For each image, Geneval2 Soft-TIFA derives AM and GM from the VQA "
        "correct-answer probabilities:",
        "",
        "```text",
        "image_AM = mean(atom_probability)",
        "image_GM = exp(mean(log(max(atom_probability, 1e-300))))",
        "batch_AM = 100 * mean(image_AM)",
        "batch_GM = 100 * mean(image_GM)",
        "```",
        "",
        "AM is the atom-level continuous score; GM is the prompt-level score and "
        "the primary Flow-DPPO reporting metric. Both differ from thresholded atom "
        "pass rate. " + selection_semantics,
        "",
        planner_score_visibility,
        "",
        (
            "When the fifth image both exhausts the image budget and reaches all "
            "constraints, runtime control requires the terminal reason "
            "`best_available_under_budget`. The episode still counts as all-pass; "
            "the reason records why submission became mandatory, not the quality "
            "of the selected image."
        ),
        "",
        "These are actual Soft-TIFA AM/GM scores recomputed from the persisted "
        "local Qwen3-VL correct-answer probabilities. They are not official leaderboard "
        "scores: this batch uses Flow-DPPO training prompts, profile-routed local "
        "image generation at 1024 x 1024, and one trajectory-selected image per "
        "prompt rather than the official 800-prompt benchmark generation protocol.",
        "",
        "## Difficulty Policy",
        "",
        "The tiers are a deterministic local grouping over committed Flow-DPPO "
        "training metadata, scaled from the official Geneval2 atom-count "
        "distribution. They are not official Geneval2 difficulty labels and do "
        "not use post-hoc image outcomes:",
        "",
        "- **Hard:** source `atom_count` 9-10.",
        "- **Medium:** source `atom_count` 6-8.",
        "- **Easy:** source `atom_count` 3-5.",
        f"- This batch mix: {summary['selection_tier_counts']}.",
        "",
        "Within each tier, ranking rewards more metadata atoms, actual VQAs, "
        "distinct skill types, verb/position atoms, high-count atoms, new relation "
        "types, and new entities; repeated entity families are penalized. The actual "
        "VQA count is used because 6,007/20,000 source rows have "
        "`atom_count != len(vqa_list)`.",
        "",
        "## Episode Results",
        "",
        "| Episode | Tier | Attempts | First atoms | First AM | First GM | Submitted atoms | Submitted AM | Submitted GM | Peak GM | Atom gain |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["episodes"]:
        lines.append(
            "| `{episode_id}` | {tier} | {attempts} | {initial}/{constraints} | "
            "{first_am:.2f} | {first_gm:.2f} | {best}/{constraints} (`{submitted}`) | "
            "{submitted_am:.2f} | {submitted_gm:.2f} | "
            "{peak_gm:.2f} (`{peak_id}`) | {gain:+d} |".format(
                episode_id=item["episode_id"],
                tier=item["difficulty_tier"],
                attempts=item["attempt_count"],
                initial=item["initial_pass_count"],
                constraints=item["constraint_count"],
                first_am=item["first_agent_geneval2_am"] * 100,
                first_gm=item["first_agent_geneval2_score"] * 100,
                best=item["best_pass_count"],
                gain=item["atom_gain"],
                submitted=item["submitted_attempt_id"],
                submitted_am=item["submitted_geneval2_am"] * 100,
                submitted_gm=item["submitted_geneval2_score"] * 100,
                peak_gm=item["peak_geneval2_score"] * 100,
                peak_id=item["peak_geneval2_attempt_id"],
            )
        )
    lines.extend(
        [
            "",
            "## Strategy Evidence From Real Trajectories",
            "",
            "The canonical action has no `decision_summary`, so the statements below "
            "show observable input state, selected action, and outcome rather than "
            "claiming an unrecorded hidden rationale.",
            "",
        ]
    )
    lines.extend(_render_strategy_examples(summary))
    lines.extend(
        [
            "",
            "## Invariants",
            "",
            "Every row passed schema validation, manifest hash closure, fresh-start generation, "
            "profile-specific local image-backend provenance and 1024x1024 artifact checks, "
            "complete Geneval2 atom "
            "coverage, source-based edit lineage, complete RoundRecord suffixes, point-in-time "
            "PlannerContext latest/best/budget checks, best-attempt submission, and sanitized "
            "GPT-5.5 output checks.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_strategy_examples(summary: dict[str, Any]) -> list[str]:
    episodes = summary["episodes"]
    examples: list[str] = []
    used: set[tuple[str, str]] = set()

    def add_example(
        title: str,
        episode: dict[str, Any],
        attempt: dict[str, Any],
        details: list[str],
    ) -> None:
        key = (episode["episode_id"], title)
        if key in used:
            return
        used.add(key)
        examples.extend(
            [
                f"### {title}: `{episode['episode_id']}`",
                "",
                *details,
                (
                    f"- Result `{attempt['attempt_id']}`: "
                    f"{attempt['pass_count']}/{episode['constraint_count']} atoms, "
                    f"GM {attempt['geneval2_score'] * 100:.2f}."
                ),
                "",
            ]
        )

    for episode in episodes:
        attempts = episode["attempts"]
        if len(attempts) == 1 and episode["all_constraints_passed"]:
            attempt = attempts[0]
            add_example(
                "Direct First-Attempt Success",
                episode,
                attempt,
                [
                    "- The fresh generation passed every atom.",
                    "- The Agent submitted it without spending retry budget.",
                ],
            )
            break

    for episode in episodes:
        for attempt in episode["attempts"][1:]:
            if attempt["regressed_constraint_ids"]:
                add_example(
                    "Observed Constraint Regression",
                    episode,
                    attempt,
                    [
                        f"- Action: `{attempt['action']}` from "
                        f"`{attempt['source_attempt_id']}`.",
                        "- Fixed atoms: "
                        f"{attempt['fixed_constraint_ids'] or 'none'}.",
                        "- Regressed atoms: "
                        f"{attempt['regressed_constraint_ids']}.",
                        f"- Reducer best after the full episode: "
                        f"`{episode['best_attempt_id']}`.",
                    ],
                )
                break
        if any(attempt["regressed_constraint_ids"] for attempt in episode["attempts"][1:]):
            break

    for episode in episodes:
        attempts = episode["attempts"]
        for index, attempt in enumerate(attempts[1:], 1):
            if (
                attempt["action"] == "edit_image"
                and attempt["source_attempt_id"] != attempts[index - 1]["attempt_id"]
            ):
                add_example(
                    "Historical-Source Branch",
                    episode,
                    attempt,
                    [
                        f"- Latest before the action was "
                        f"`{attempts[index - 1]['attempt_id']}`.",
                        f"- The Agent deliberately edited historical source "
                        f"`{attempt['source_attempt_id']}`.",
                        "- Fixed atoms: "
                        f"{attempt['fixed_constraint_ids'] or 'none'}; "
                        "regressed atoms: "
                        f"{attempt['regressed_constraint_ids'] or 'none'}.",
                    ],
                )
                break
        if any(
            attempt["action"] == "edit_image"
            and attempt["source_attempt_id"] != attempts[index - 1]["attempt_id"]
            for index, attempt in enumerate(attempts[1:], 1)
        ):
            break

    for episode in episodes:
        for attempt in episode["attempts"][1:]:
            if attempt["action"] == "generate_image":
                add_example(
                    "Source-Free Regeneration After Prior Attempts",
                    episode,
                    attempt,
                    [
                        "- The Agent abandoned source-conditioned editing for "
                        "one source-free root generation.",
                        "- Fixed atoms relative to the prior observation: "
                        f"{attempt['fixed_constraint_ids'] or 'none'}; "
                        "regressed atoms: "
                        f"{attempt['regressed_constraint_ids'] or 'none'}.",
                    ],
                )
                break
        if any(
            attempt["action"] == "generate_image"
            for attempt in episode["attempts"][1:]
        ):
            break

    if not examples:
        return ["- No qualifying strategy example was present in this checkpoint."]
    return examples


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _load_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _load_jsonl(path)
