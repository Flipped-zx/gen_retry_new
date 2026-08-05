#!/usr/bin/env python3
"""Counterfactual GPT-5.5 decision probe for the frozen HPS mini-pilot.

The probe replays each selected episode only through the declared child
Geneval2 result, adds in-memory HPS observations, and asks the same Teacher
once with PlannerContext v0.7 (G) and once with v0.8 (G+H). It does not execute
the returned action or mutate the historical run.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from gen_retry.agent.teacher_client import OpenAICompatibleTeacherClient, TeacherImageRef
from gen_retry.domain.auxiliary_quality import risk_policy_sha256
from gen_retry.phase3.model_config import load_model_config
from gen_retry.protocol.action_parser import ActionParseError, parse_action
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import (
    build_planner_context_from_events,
    visible_images_from_state,
)
from gen_retry.runtime.reducer import reduce_events


WATCH_BELOW = -0.5
HIGH_BELOW = -1.0
RISK_POLICY = {
    "policy_id": "hpsv3_source_delta_threshold_v1",
    "policy_version": "exploratory-unfrozen-v1",
    "calibration_ref": "artifacts/phase7/hpsv3_mini_pilot_manifest_v1.json",
    "calibration_sha256": "0" * 64,
    "watch_below": WATCH_BELOW,
    "high_below": HIGH_BELOW,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def attempt_number(attempt_id: str) -> int:
    return int(attempt_id.removeprefix("a_"))


def root_for(attempt_id: str, parents: dict[str, str | None]) -> str:
    current = attempt_id
    seen: set[str] = set()
    while parents.get(current) is not None:
        if current in seen:
            raise ValueError(f"cycle in parent chain at {attempt_id}")
        seen.add(current)
        current = str(parents[current])
    return current


def risk_for_delta(delta: float | None) -> str:
    if delta is None:
        return "unknown"
    if delta < HIGH_BELOW:
        return "high"
    if delta < WATCH_BELOW:
        return "watch"
    return "low"


def prefix_through_child(events: list[dict[str, Any]], child_attempt_id: str) -> list[dict[str, Any]]:
    for index, event in enumerate(events):
        if event["event_type"] == "geneval2_completed" and event["payload"]["attempt_id"] == child_attempt_id:
            return copy.deepcopy(events[: index + 1])
    raise ValueError(f"missing child Geneval2 event: {child_attempt_id}")


def add_quality_events(
    events: list[dict[str, Any]],
    *,
    episode_id: str,
    score_by_attempt: dict[str, dict[str, Any]],
    report_ref: str,
    report_sha256: str,
    checkpoint_sha256: str,
    policy_sha256: str,
) -> list[dict[str, Any]]:
    task_spec = events[0]["payload"]["task_spec"]
    completions = {
        event["payload"]["attempt_id"]: event
        for event in events
        if event["event_type"] == "image_execution_completed"
    }
    parents = {
        attempt_id: event["payload"].get("parent_attempt_id")
        for attempt_id, event in completions.items()
    }
    successful_mu = {attempt_id: row["mu"] for attempt_id, row in score_by_attempt.items()}
    output: list[dict[str, Any]] = []
    quality_index = 0
    existing_event_numbers = [
        int(event["event_id"].removeprefix("evt_"))
        for event in events
        if event["event_id"].startswith("evt_")
        and event["event_id"].removeprefix("evt_").isdigit()
    ]
    next_event_number = max(existing_event_numbers, default=0) + 1
    for event in events:
        output.append(event)
        if event["event_type"] != "geneval2_completed":
            continue
        attempt_id = event["payload"]["attempt_id"]
        completion = completions[attempt_id]
        source_id = parents[attempt_id]
        anchor_id = root_for(attempt_id, parents)
        score = score_by_attempt.get(attempt_id)
        delta_source = None
        if score is not None and source_id in successful_mu:
            delta_source = score["mu"] - successful_mu[source_id]
        delta_anchor = None
        if score is not None and anchor_id in successful_mu and anchor_id != attempt_id:
            delta_anchor = score["mu"] - successful_mu[anchor_id]
        if score is None:
            payload = {
                "evaluator_id": "hpsv3",
                "evaluator_version": "official@bd0c5fcb5f587617b0169c07222ab78d01e2f3c2",
                "checkpoint_ref": "models/HPSv3/HPSv3.safetensors",
                "checkpoint_sha256": checkpoint_sha256,
                "preprocess_version": "official-hpsv3-local-config-v1; min_pixels=max_pixels=200704; sdpa",
                "prompt_hash_policy_id": "utf8_exact_original_prompt_sha256_v1",
                "prompt_sha256": sha256_bytes(task_spec["original_prompt"].encode("utf-8")),
                "attempt_id": attempt_id,
                "image_artifact_id": completion["payload"]["image_artifact_id"],
                "image_sha256": completion["payload"]["artifact_sha256"],
                "source_attempt_id": source_id,
                "quality_anchor_attempt_id": None if anchor_id == attempt_id else anchor_id,
                "quality_anchor_policy_id": "lineage_root_v1",
                "delta_policy_id": "child_mu_minus_baseline_mu_v1",
                "risk_policy": RISK_POLICY,
                "risk_policy_sha256": policy_sha256,
                "status": "missing",
                "mu": None,
                "sigma": None,
                "delta_from_source": None,
                "delta_from_anchor": None,
                "quality_risk": "unknown",
                "report_ref": None,
                "report_sha256": None,
                "error_code": "offline_pair_only",
            }
        else:
            payload = {
                "evaluator_id": "hpsv3",
                "evaluator_version": "official@bd0c5fcb5f587617b0169c07222ab78d01e2f3c2",
                "checkpoint_ref": "models/HPSv3/HPSv3.safetensors",
                "checkpoint_sha256": checkpoint_sha256,
                "preprocess_version": "official-hpsv3-local-config-v1; min_pixels=max_pixels=200704; sdpa",
                "prompt_hash_policy_id": "utf8_exact_original_prompt_sha256_v1",
                "prompt_sha256": sha256_bytes(task_spec["original_prompt"].encode("utf-8")),
                "attempt_id": attempt_id,
                "image_artifact_id": completion["payload"]["image_artifact_id"],
                "image_sha256": completion["payload"]["artifact_sha256"],
                "source_attempt_id": source_id,
                "quality_anchor_attempt_id": None if anchor_id == attempt_id else anchor_id,
                "quality_anchor_policy_id": "lineage_root_v1",
                "delta_policy_id": "child_mu_minus_baseline_mu_v1",
                "risk_policy": RISK_POLICY,
                "risk_policy_sha256": policy_sha256,
                "status": "success",
                "mu": score["mu"],
                "sigma": score["sigma"],
                "delta_from_source": delta_source,
                "delta_from_anchor": delta_anchor,
                "quality_risk": risk_for_delta(delta_source),
                "report_ref": report_ref,
                "report_sha256": report_sha256,
                "error_code": None,
            }
        output.append(
            {
                "schema_version": "0.2",
                # Keep synthetic probe events valid under the canonical envelope
                # so the normal reducer/PlannerContext validation remains active.
                "event_id": f"evt_{next_event_number:04d}",
                "episode_id": episode_id,
                "turn_id": event["turn_id"],
                "event_type": "auxiliary_quality_completed",
                "created_at": "2026-08-05T00:00:00Z",
                "producer": "hpsv3_mini_pilot_probe",
                "input_refs": [completion["payload"]["image_artifact_id"]],
                "payload": payload,
            }
        )
        quality_index += 1
        next_event_number += 1
    return output


def build_image_refs(episode_dir: Path, events: list[dict[str, Any]]) -> list[TeacherImageRef]:
    state = reduce_events(events)
    refs: list[TeacherImageRef] = []
    by_artifact = {
        attempt.image_artifact_id: attempt
        for attempt in state.attempts.values()
        if attempt.image_artifact_id
    }
    for visible in visible_images_from_state(state):
        attempt = state.attempts[visible["attempt_id"]]
        path = episode_dir / "images" / f"img_{attempt_number(attempt.attempt_id):03d}.png"
        refs.append(
            TeacherImageRef(
                role=visible["role"],
                attempt_id=visible["attempt_id"],
                artifact_id=visible["artifact_id"],
                path=path,
            )
        )
    return refs


def ask(
    client: OpenAICompatibleTeacherClient,
    *,
    arm: str,
    episode_id: str,
    context: dict[str, Any],
    task_spec: dict[str, Any],
    image_refs: list[TeacherImageRef],
) -> dict[str, Any]:
    response = client.complete(
        request_id=f"hps_mini_{episode_id}_{arm}",
        planner_context=context,
        task_spec=task_spec,
        image_refs=image_refs,
        retrieved_skills=[],
        extra_observations=[],
        max_completion_tokens=1400,
    )
    result: dict[str, Any] = {
        "arm": arm,
        "model_id": response.model_id,
        "finish_reason": response.finish_reason,
        "raw_text_sha256": response.response_metadata.get("raw_text_sha256"),
        "response_metadata": response.response_metadata,
    }
    try:
        result["action"] = parse_action(response.raw_text).action
        result["parse_status"] = "success"
    except ActionParseError as exc:
        result["action"] = None
        result["parse_status"] = "failed"
        result["parse_error"] = str(exc)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--hps-report", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    hps_report = json.loads(args.hps_report.read_text(encoding="utf-8"))
    hps_rows = {
        (row["episode_id"], row["attempt_id"]): row
        for row in hps_report["images"]
    }
    report_sha256 = sha256_file(args.hps_report)
    policy_sha = risk_policy_sha256(RISK_POLICY)
    config = load_model_config()
    client = OpenAICompatibleTeacherClient(config.teacher)
    results: list[dict[str, Any]] = []
    for pair in manifest["pairs"]:
        episode_id = pair["episode_id"]
        episode_dir = args.source_root / episode_id
        task_spec = json.loads((episode_dir / "task_spec.json").read_text(encoding="utf-8"))
        events = load_jsonl(episode_dir / "events.jsonl")
        prefix = prefix_through_child(events, pair["child_attempt_id"])
        scores = {
            attempt_id: hps_rows[(episode_id, attempt_id)]
            for attempt_id in (pair["parent_attempt_id"], pair["child_attempt_id"])
        }
        augmented = add_quality_events(
            prefix,
            episode_id=episode_id,
            score_by_attempt=scores,
            report_ref=str(args.hps_report),
            report_sha256=report_sha256,
            checkpoint_sha256=hps_report["checkpoint_sha256"],
            policy_sha256=policy_sha,
        )
        context_g = build_planner_context_from_events(prefix, schema_version="0.7")
        context_h = build_planner_context_from_events(augmented, schema_version="0.8")
        image_refs = build_image_refs(episode_dir, augmented)
        g = ask(client, arm="G", episode_id=episode_id, context=context_g, task_spec=task_spec, image_refs=image_refs)
        h = ask(client, arm="G+H", episode_id=episode_id, context=context_h, task_spec=task_spec, image_refs=image_refs)
        same_action = g.get("action") is not None and g.get("action") == h.get("action")
        results.append(
            {
                "episode_id": episode_id,
                "stratum": pair["stratum"],
                "parent_attempt_id": pair["parent_attempt_id"],
                "child_attempt_id": pair["child_attempt_id"],
                "prefix_last_event_id": prefix[-1]["event_id"],
                "context_g_sha256": sha256_bytes(canonical_json(context_g).encode("utf-8")),
                "context_h_sha256": sha256_bytes(canonical_json(context_h).encode("utf-8")),
                "hps_quality_risk_visible": context_h["latest_attempt"]["auxiliary_quality"]["quality_risk"],
                "g": g,
                "g_plus_h": h,
                "action_equal": same_action,
            }
        )
        print(f"{episode_id}: G={g['parse_status']} G+H={h['parse_status']} equal={same_action}", flush=True)

    report = {
        "schema_version": "hpsv3_teacher_decision_probe_v1",
        "selection_id": manifest["selection_id"],
        "intervention_status": "counterfactual_decision_only; no image action executed",
        "planner_g": "GPT-5.5 Teacher v9 + PlannerContext v0.7",
        "planner_g_plus_h": "GPT-5.5 Teacher v9 + PlannerContext v0.8 + planner_context_only_hpsv3_advisory_v1",
        "risk_policy_status": "exploratory-unfrozen; not an admission policy",
        "risk_policy": RISK_POLICY,
        "risk_policy_sha256": policy_sha,
        "hps_report": str(args.hps_report),
        "results": results,
        "summary": {
            "episode_count": len(results),
            "g_parse_success": sum(r["g"]["parse_status"] == "success" for r in results),
            "g_plus_h_parse_success": sum(r["g_plus_h"]["parse_status"] == "success" for r in results),
            "action_equal_count": sum(r["action_equal"] for r in results),
            "action_changed_count": sum(not r["action_equal"] for r in results),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
