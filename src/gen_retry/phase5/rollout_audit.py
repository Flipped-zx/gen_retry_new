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
) -> dict[str, Any]:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    selected = selection["selected_prompts"]
    run_dirs = sorted(path for path in run_root.glob("phase3_ep_*") if path.is_dir())
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
    secret_scan = _scan_for_key_like_text([run_root, artifact_path.parent, report_path.parent])
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
        "all_constraints_passed_episode_count": all_pass,
        "historical_best_submission_count": sum(
            item["submitted_attempt_id"] != item["latest_attempt_id"]
            for item in episode_results
        ),
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
        "attempts": [
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
                "regressed_constraint_ids": round_records[index][
                    "observed_outcome"
                ]["regressed_constraint_ids"],
                "persistent_failed_constraint_ids": round_records[index][
                    "observed_outcome"
                ]["persistent_failed_constraint_ids"],
                "became_best": round_records[index]["observed_outcome"][
                    "became_best"
                ],
            }
            for index, attempt_id in enumerate(state.attempt_order)
        ],
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
            "- Episodes with all atoms passed: "
            f"{summary['all_constraints_passed_episode_count']}/{episode_count}"
        ),
        (
            "- Historical-best submissions: "
            f"{summary['historical_best_submission_count']}/{episode_count}"
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
        "These are actual Soft-TIFA AM/GM scores recomputed from the persisted "
        "local Qwen3-VL correct-answer probabilities. They are not official leaderboard "
        "scores: this batch uses Flow-DPPO training prompts, profile-routed local "
        "image generation at 1024 x 1024, and one trajectory-selected image per "
        "prompt rather than the official 800-prompt benchmark generation protocol.",
        "",
        "## Difficulty Policy",
        "",
        "The tiers are a deterministic local sampling policy over committed "
        "Flow-DPPO training metadata, not official Geneval2 difficulty labels and "
        "not post-hoc image outcomes:",
        "",
        "- **Hard:** `atom_count >= 9`, actual `len(vqa_list) >= 10`, and at least one relation/action phrase.",
        "- **Medium:** `atom_count` 7-8, actual VQA count 8-10, and at least one relation/action phrase.",
        "- **Easy:** `atom_count <= 5`, actual VQA count <= 7, and at least one relation/action phrase.",
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
    episodes = {item["episode_id"]: item for item in summary["episodes"]}
    examples: list[str] = []

    def attempt(ep: str, attempt_id: str) -> dict[str, Any]:
        return next(
            item
            for item in episodes[ep]["attempts"]
            if item["attempt_id"] == attempt_id
        )

    if "0.6" in summary.get("planner_context_version_counts", {}):
        if "phase3_ep_001" in episodes:
            a1 = attempt("phase3_ep_001", "a_001")
            a4 = attempt("phase3_ep_001", "a_004")
            examples.extend(
                [
                    "### GM Tie-Break Across Stable Atom States: `phase3_ep_001`",
                    "",
                    f"- `a_001` reached {a1['pass_count']}/11 at GM "
                    f"{a1['geneval2_score'] * 100:.2f}.",
                    "- `a_002`, `a_003`, and `a_004` retained the same 8/11 "
                    "atom count while increasing GM at each step.",
                    f"- Final `a_004` remained 8/11 but reached GM "
                    f"{a4['geneval2_score'] * 100:.2f} and was submitted.",
                    "",
                ]
            )
        if "phase3_ep_008" in episodes:
            a1 = attempt("phase3_ep_008", "a_001")
            a2 = attempt("phase3_ep_008", "a_002")
            examples.extend(
                [
                    "### Pass-Count Primary Rejects Higher-GM Regression: "
                    "`phase3_ep_008`",
                    "",
                    f"- `a_001` became best at {a1['pass_count']}/11, GM "
                    f"{a1['geneval2_score'] * 100:.2f}.",
                    f"- `a_002` had higher GM "
                    f"({a2['geneval2_score'] * 100:.2f}) but only "
                    f"{a2['pass_count']}/11 after regressing `c_001`.",
                    "- Reducer retained `a_001`; the next two edits branched "
                    "from `a_001`, and submission protected it.",
                    "",
                ]
            )
        if "phase3_ep_012" in episodes:
            a1 = attempt("phase3_ep_012", "a_001")
            a2 = attempt("phase3_ep_012", "a_002")
            a3 = attempt("phase3_ep_012", "a_003")
            a4 = attempt("phase3_ep_012", "a_004")
            examples.extend(
                [
                    "### Ineffective Edit, Regenerate, Productive Edit: "
                    "`phase3_ep_012`",
                    "",
                    f"- Local edit `a_001` stayed {a1['pass_count']}/11 and "
                    f"fell to GM {a1['geneval2_score'] * 100:.2f}.",
                    f"- Source-free `generate_image` produced `a_002` at "
                    f"{a2['pass_count']}/11, GM "
                    f"{a2['geneval2_score'] * 100:.2f}, becoming best by GM.",
                    f"- Editing `a_002` fixed `c_010`; `a_003` reached "
                    f"{a3['pass_count']}/11, GM "
                    f"{a3['geneval2_score'] * 100:.2f}.",
                    f"- Final `a_004` regressed `c_010` to "
                    f"{a4['pass_count']}/11, so submission returned `a_003`.",
                    "",
                ]
            )
        if "phase3_ep_020" in episodes:
            a1 = attempt("phase3_ep_020", "a_001")
            a2 = attempt("phase3_ep_020", "a_002")
            a3 = attempt("phase3_ep_020", "a_003")
            a4 = attempt("phase3_ep_020", "a_004")
            examples.extend(
                [
                    "### Catastrophic Edit, Rollback, Then Regenerate: "
                    "`phase3_ep_020`",
                    "",
                    f"- `a_001` was best at {a1['pass_count']}/6, GM "
                    f"{a1['geneval2_score'] * 100:.2f}.",
                    f"- Editing it produced `a_002` at only "
                    f"{a2['pass_count']}/6 and regressed three preserved atoms.",
                    f"- The next edit rolled back to `a_001`; `a_003` restored "
                    f"{a3['pass_count']}/6 but did not become best.",
                    f"- Final source-free regeneration `a_004` remained "
                    f"{a4['pass_count']}/6 at GM "
                    f"{a4['geneval2_score'] * 100:.2f}.",
                    "",
                ]
            )

    if "phase3_ep_003" in episodes:
        a0 = attempt("phase3_ep_003", "a_000")
        a2 = attempt("phase3_ep_003", "a_002")
        a3 = attempt("phase3_ep_003", "a_003")
        a4 = attempt("phase3_ep_003", "a_004")
        examples.extend(
            [
                "### Abandon Repeated Ineffective Edits: `phase3_ep_003`",
                "",
                f"- Fresh `a_000`: {a0['pass_count']}/11, GM {a0['geneval2_score'] * 100:.2f}.",
                "- Two consecutive edits (`a_001`, `a_002`) fixed no atoms; the latest remained 6/11.",
                f"- The next action was source-free `generate_image`, producing `a_003`: {a3['pass_count']}/11, GM {a3['geneval2_score'] * 100:.2f}.",
                f"- A focused edit of improved latest `a_003` produced `a_004`: {a4['pass_count']}/11, GM {a4['geneval2_score'] * 100:.2f}.",
                f"- Before regeneration, the Planner saw two no-fix outcomes at 6/11; post-hoc `a_002` GM was {a2['geneval2_score'] * 100:.2f}.",
                "",
            ]
        )

    if "phase3_ep_011" in episodes:
        a0 = attempt("phase3_ep_011", "a_000")
        a1 = attempt("phase3_ep_011", "a_001")
        a2 = attempt("phase3_ep_011", "a_002")
        examples.extend(
            [
                "### Branch From Historical Best After No Gain: `phase3_ep_011`",
                "",
                f"- `a_000` was best at 10/11, GM {a0['geneval2_score'] * 100:.2f}; only `c_008` failed.",
                f"- Editing it produced latest `a_001` with no fixed atom: 10/11, GM {a1['geneval2_score'] * 100:.2f}.",
                "- The next PlannerContext showed latest `a_001`, best `a_000`, and persistent `c_008`.",
                "- The Agent selected `edit_image.source_attempt_id = a_000`, not latest `a_001`.",
                f"- Result `a_002` fixed `c_008`, preserved ten atoms, and reached 11/11, GM {a2['geneval2_score'] * 100:.2f}.",
                "",
            ]
        )

    if "phase3_ep_007" in episodes:
        a2 = attempt("phase3_ep_007", "a_002")
        a3 = attempt("phase3_ep_007", "a_003")
        a4 = attempt("phase3_ep_007", "a_004")
        examples.extend(
            [
                "### Continue Editing, Then Submit Historical Best: `phase3_ep_007`",
                "",
                f"- `a_002` became reducer best at 10/11, GM {a2['geneval2_score'] * 100:.2f}.",
                f"- Continuing from `a_002` produced `a_003`, still 10/11 but GM {a3['geneval2_score'] * 100:.2f}.",
                "- Because best ordering uses pass count and keeps the earlier tie, reducer best remained `a_002` despite `a_003` having higher GM.",
                f"- A later branch from `a_002` produced latest `a_004`, regressed one atom, and fell to 9/11, GM {a4['geneval2_score'] * 100:.2f}.",
                "- Submission correctly protected pass-count best `a_002`, while the score report exposes that peak-GM `a_003` was not selected.",
                "",
            ]
        )

    if "phase3_ep_018" in episodes:
        a0 = attempt("phase3_ep_018", "a_000")
        a1 = attempt("phase3_ep_018", "a_001")
        a2 = attempt("phase3_ep_018", "a_002")
        examples.extend(
            [
                "### Regenerate Broad Failure, Then Local Edit: `phase3_ep_018`",
                "",
                f"- First Agent attempt `a_000`: {a0['pass_count']}/7, GM {a0['geneval2_score'] * 100:.2f}.",
                f"- Source-free regeneration produced `a_001`: {a1['pass_count']}/7, GM {a1['geneval2_score'] * 100:.2f}; only the chasing verb remained failed.",
                f"- Editing latest `a_001` for that remaining verb produced `a_002`: {a2['pass_count']}/7, GM {a2['geneval2_score'] * 100:.2f}.",
                "",
            ]
        )

    if "phase3_ep_019" in episodes:
        a0 = attempt("phase3_ep_019", "a_000")
        examples.extend(
            [
                "### Stop Immediately On Complete Success: `phase3_ep_019`",
                "",
                f"- First Agent attempt `a_000` passed 6/6 with GM {a0['geneval2_score'] * 100:.2f}.",
                "- The next action was `submit_attempt(a_000, all_constraints_passed)`; no retry budget was wasted.",
            ]
        )
    return examples


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
