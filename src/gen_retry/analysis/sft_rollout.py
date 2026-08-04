from __future__ import annotations

import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from gen_retry.agent.sft_planner import SFT_PLANNER_PROVIDER, sft_system_prompt_sha256
from gen_retry.domain.artifacts import validate_artifact_manifest_closure
from gen_retry.protocol.action_parser import ActionParseError, parse_action
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.trajectory_validator import validate_artifact_manifest_semantics
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.reducer import EpisodeState, reduce_events


def analyze_sft_rollouts(
    *,
    run_root: Path,
    episode_ids: list[str],
    artifact_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    if not episode_ids or len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode_ids must be a non-empty unique list")
    episodes = [_analyze_episode(run_root / episode_id) for episode_id in episode_ids]
    planner_outputs = sum(item["planner_output_count"] for item in episodes)
    planner_requests = sum(item["planner_request_count"] for item in episodes)
    format_valid = sum(item["format_valid_count"] for item in episodes)
    first_atoms = sum(item["first"]["passed_atoms"] for item in episodes)
    submitted_atoms = sum(item["submitted"]["passed_atoms"] for item in episodes)
    total_atoms = sum(item["constraint_count"] for item in episodes)
    latencies = [
        latency
        for item in episodes
        for latency in item["planner_latency_seconds"]
    ]
    image_calls = sum(item["image_call_count"] for item in episodes)
    summary = {
        "schema_version": "sft_rollout_canary_v1",
        "status": "PASS",
        "run_root": str(run_root.resolve()),
        "episode_count": len(episodes),
        "episode_ids": episode_ids,
        "format": {
            "planner_output_count": planner_outputs,
            "valid_count": format_valid,
            "valid_rate": format_valid / planner_outputs if planner_outputs else 0.0,
            "format_error_count": sum(item["format_error_count"] for item in episodes),
        },
        "skill": {
            "query_count": sum(item["skill_query_count"] for item in episodes),
            "tool_response_count": sum(
                item["skill_tool_response_count"] for item in episodes
            ),
            "skill_id_counts": dict(
                sorted(
                    Counter(
                        skill_id
                        for item in episodes
                        for skill_id in item["skill_ids"]
                    ).items()
                )
            ),
        },
        "history": {
            "historical_source_attempt_count": sum(
                len(item["historical_source_attempts"]) for item in episodes
            ),
            "historical_source_attempts": [
                source
                for item in episodes
                for source in item["historical_source_attempts"]
            ],
            "non_latest_branch_count": sum(
                item["non_latest_branch_count"] for item in episodes
            ),
            "historical_submission_count": sum(
                item["historical_submission"] for item in episodes
            ),
            "rollback_recovery_episode_count": sum(
                item["rollback_recovery"] for item in episodes
            ),
            "regression_episode_count": sum(
                item["regression_count"] > 0 for item in episodes
            ),
        },
        "geneval2": {
            "first": _aggregate_score(episodes, "first", first_atoms, total_atoms),
            "submitted": _aggregate_score(
                episodes, "submitted", submitted_atoms, total_atoms
            ),
            "passed_atom_gain": submitted_atoms - first_atoms,
            "gm_gain_100": (
                statistics.mean(item["submitted"]["gm"] for item in episodes)
                - statistics.mean(item["first"]["gm"] for item in episodes)
            )
            * 100,
        },
        "all_pass_episode_count": sum(item["all_pass"] for item in episodes),
        "image_call_count": image_calls,
        "mean_image_calls_per_episode": image_calls / len(episodes),
        "action_counts": dict(
            sorted(
                Counter(
                    action
                    for item in episodes
                    for action in item["canonical_action_sequence"]
                ).items()
            )
        ),
        "planner_runtime": {
            "transport_request_count": planner_requests,
            "transport_retry_count": planner_requests - planner_outputs,
            "request_count": len(latencies),
            "latency_mean_seconds": statistics.mean(latencies) if latencies else None,
            "latency_p50_seconds": _percentile(latencies, 0.50),
            "latency_p95_seconds": _percentile(latencies, 0.95),
            "physical_device_counts": dict(
                sorted(
                    Counter(
                        str(device_id)
                        for item in episodes
                        for device_id in item["planner_device_ids"]
                    ).items()
                )
            ),
        },
        "teacher_fallback_used": False,
        "episodes": episodes,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    report_path.write_text(_render_markdown(summary), encoding="utf-8")
    return summary


def _analyze_episode(run_dir: Path) -> dict[str, Any]:
    task_spec = _load_json(run_dir / "task_spec.json")
    validate_instance(task_spec, "task_spec_v0_2.schema.json")
    manifest = _load_json(run_dir / "manifest.json")
    validate_artifact_manifest_semantics(manifest)
    validate_artifact_manifest_closure(manifest, run_dir)
    events = load_events_jsonl(run_dir / "events.jsonl")
    for event in events:
        validate_instance(event, "episode_event_v0_2.schema.json")
    state = reduce_events(events)
    if state.submitted_attempt_id is None:
        raise ValueError(f"{run_dir.name}: episode is not submitted")
    if not 1 <= len(state.attempt_order) <= task_spec["max_image_attempts"]:
        raise ValueError(f"{run_dir.name}: invalid image call count")

    requests = _load_jsonl(run_dir / "planner_requests.jsonl")
    raw_outputs = _load_jsonl(run_dir / "raw_planner_outputs.jsonl")
    _validate_request_output_alignment(run_dir.name, requests, raw_outputs)
    for request in requests:
        if request.get("planner_provider") != SFT_PLANNER_PROVIDER:
            raise ValueError(f"{run_dir.name}: non-SFT planner request found")
        if request.get("planner_context_schema_version") != "0.7":
            raise ValueError(f"{run_dir.name}: non-v0.7 PlannerContext request")
        if request.get("action_protocol_version") != "0.5":
            raise ValueError(f"{run_dir.name}: non-v0.5 action protocol request")
        if request.get("system_prompt_sha256") != sft_system_prompt_sha256():
            raise ValueError(f"{run_dir.name}: training system prompt mismatch")
        if request.get("teacher_fallback_allowed") is not False:
            raise ValueError(f"{run_dir.name}: Teacher fallback is not disabled")
    format_valid = 0
    planner_latencies: list[float] = []
    planner_device_ids: list[int] = []
    for output in raw_outputs:
        if output.get("planner_provider") != SFT_PLANNER_PROVIDER:
            raise ValueError(f"{run_dir.name}: non-SFT raw planner output found")
        if output.get("teacher_fallback_used") is not False:
            raise ValueError(f"{run_dir.name}: Teacher fallback output found")
        try:
            parse_action(output["raw_text"])
        except ActionParseError:
            pass
        else:
            format_valid += 1
        metadata = output.get("response_metadata") or {}
        planner_latencies.append(float(metadata["latency_seconds"]))
        planner_device_ids.append(int(metadata["physical_device_id"]))

    canonical_actions = _load_jsonl(run_dir / "canonical_actions.jsonl")
    if len(canonical_actions) != len(raw_outputs):
        raise ValueError(f"{run_dir.name}: planner output/action count mismatch")
    for record in canonical_actions:
        validate_instance(record["action"], "action_protocol_v0_5.schema.json")
    action_sequence = [record["action"]["action"] for record in canonical_actions]
    skill_queries = [
        record["action"]
        for record in canonical_actions
        if record["action"]["action"] == "query_skill"
    ]
    skill_ids = [
        skill_id
        for action in skill_queries
        for skill_id in action["arguments"]["skill_ids"]
    ]
    skill_responses = sum(event["event_type"] == "skill_returned" for event in events)
    if skill_responses != len(skill_queries):
        raise ValueError(f"{run_dir.name}: query_skill/tool_response mismatch")

    historical_sources: list[dict[str, Any]] = []
    non_latest_branches = 0
    regression_seen = False
    rollback_recovery = False
    for index, event in enumerate(events):
        if event["event_type"] == "memory_reduced" and event["payload"]["transition"][
            "regressed"
        ]:
            regression_seen = True
        if event["event_type"] != "action_validated":
            continue
        action = event["payload"]["action"]
        prefix_state = reduce_events(events[:index])
        if action["action"] == "edit_image":
            source_attempt_id = action["arguments"]["source_attempt_id"]
            if source_attempt_id != prefix_state.latest_attempt_id:
                non_latest_branches += 1
                source = {
                    "episode_id": run_dir.name,
                    "turn_id": event["turn_id"],
                    "source_attempt_id": source_attempt_id,
                    "latest_attempt_id": prefix_state.latest_attempt_id,
                    "best_attempt_id": prefix_state.best_attempt_id,
                }
                historical_sources.append(source)
                if regression_seen:
                    rollback_recovery = True
        elif action["action"] == "submit_attempt":
            if action["arguments"]["selected_attempt_id"] != prefix_state.latest_attempt_id:
                if regression_seen:
                    rollback_recovery = True

    first = state.attempts[state.attempt_order[0]]
    submitted = state.attempts[state.submitted_attempt_id]
    first_score = _attempt_score(first)
    submitted_score = _attempt_score(submitted)
    image_entries = [
        item for item in manifest["artifacts"] if item["artifact_type"] == "image"
    ]
    if len(image_entries) != len(state.attempt_order):
        raise ValueError(f"{run_dir.name}: image manifest/call mismatch")
    for entry in image_entries:
        if entry.get("metadata", {}).get("cache_hit") is not False:
            raise ValueError(f"{run_dir.name}: image cache reuse detected")
        with Image.open(run_dir / entry["uri"]) as image:
            if image.size != (1024, 1024):
                raise ValueError(f"{run_dir.name}: non-1024 image found")

    final_prefix = reduce_events(events[:-1])
    historical_submission = state.submitted_attempt_id != final_prefix.latest_attempt_id
    return {
        "episode_id": run_dir.name,
        "constraint_count": len(task_spec["constraints"]),
        "planner_request_count": len(requests),
        "planner_output_count": len(raw_outputs),
        "format_valid_count": format_valid,
        "format_error_count": sum(event["event_type"] == "format_error" for event in events),
        "canonical_action_sequence": action_sequence,
        "skill_query_count": len(skill_queries),
        "skill_tool_response_count": skill_responses,
        "skill_ids": skill_ids,
        "historical_source_attempts": historical_sources,
        "non_latest_branch_count": non_latest_branches,
        "historical_submission": historical_submission,
        "regression_count": sum(
            event["event_type"] == "memory_reduced"
            and bool(event["payload"]["transition"]["regressed"])
            for event in events
        ),
        "rollback_recovery": rollback_recovery,
        "first": first_score,
        "submitted": submitted_score,
        "all_pass": submitted_score["passed_atoms"] == len(task_spec["constraints"]),
        "image_call_count": len(state.attempt_order),
        "submitted_attempt_id": state.submitted_attempt_id,
        "latest_attempt_id": state.latest_attempt_id,
        "best_attempt_id": state.best_attempt_id,
        "planner_latency_seconds": planner_latencies,
        "planner_device_ids": planner_device_ids,
    }


def _attempt_score(attempt: Any) -> dict[str, Any]:
    confidences = [
        float(result["confidence"]) for result in attempt.constraint_results.values()
    ]
    return {
        "attempt_id": attempt.attempt_id,
        "passed_atoms": attempt.pass_count,
        "am": statistics.mean(confidences),
        "gm": float(attempt.primary_score),
    }


def _validate_request_output_alignment(
    episode_id: str,
    requests: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
) -> None:
    request_ids = [item.get("request_id") for item in requests]
    output_ids = [item.get("request_id") for item in outputs]
    if None in request_ids or None in output_ids:
        raise ValueError(f"{episode_id}: planner record missing request_id")
    if len(output_ids) != len(set(output_ids)):
        raise ValueError(f"{episode_id}: duplicate successful planner output")
    if set(request_ids) != set(output_ids):
        raise ValueError(f"{episode_id}: planner request/output ids mismatch")
    if len(request_ids) < len(output_ids):
        raise ValueError(f"{episode_id}: planner output without request")


def _aggregate_score(
    episodes: list[dict[str, Any]],
    key: str,
    passed_atoms: int,
    total_atoms: int,
) -> dict[str, Any]:
    return {
        "passed_atoms": passed_atoms,
        "total_atoms": total_atoms,
        "pass_rate": passed_atoms / total_atoms,
        "am_100": statistics.mean(item[key]["am"] for item in episodes) * 100,
        "gm_100": statistics.mean(item[key]["gm"] for item in episodes) * 100,
    }


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


def _render_markdown(summary: dict[str, Any]) -> str:
    first = summary["geneval2"]["first"]
    submitted = summary["geneval2"]["submitted"]
    return "\n".join(
        [
            "# SFT Planner Frozen-Test Rollout",
            "",
            f"Status: **{summary['status']}**; episodes: {summary['episode_count']}.",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            f"| Format valid | {summary['format']['valid_count']}/{summary['format']['planner_output_count']} ({summary['format']['valid_rate']:.2%}) |",
            f"| Skill queries / tool responses | {summary['skill']['query_count']} / {summary['skill']['tool_response_count']} |",
            f"| Historical source_attempt_id | {summary['history']['historical_source_attempt_count']} |",
            f"| Non-latest branches | {summary['history']['non_latest_branch_count']} |",
            f"| Rollback recovery episodes | {summary['history']['rollback_recovery_episode_count']} |",
            f"| First Geneval2 atoms | {first['passed_atoms']}/{first['total_atoms']} |",
            f"| Submitted Geneval2 atoms | {submitted['passed_atoms']}/{submitted['total_atoms']} |",
            f"| First / submitted Geneval2 GM | {first['gm_100']:.2f} / {submitted['gm_100']:.2f} |",
            f"| All-pass episodes | {summary['all_pass_episode_count']}/{summary['episode_count']} |",
            f"| Image calls | {summary['image_call_count']} |",
            f"| Planner transport requests / retries | {summary['planner_runtime']['transport_request_count']} / {summary['planner_runtime']['transport_retry_count']} |",
            f"| Planner latency P50 / P95 | {summary['planner_runtime']['latency_p50_seconds']:.2f}s / {summary['planner_runtime']['latency_p95_seconds']:.2f}s |",
            "",
            "Teacher fallback: **not allowed and not used**.",
            "",
        ]
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    values = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object: {path}")
            values.append(value)
    return values
