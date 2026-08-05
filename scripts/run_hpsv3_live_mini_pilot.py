#!/usr/bin/env python3
"""Run a small real HPS-aware Teacher rollout against existing prompt baselines.

The existing 1k episodes are the baseline arm. This script prepares fresh runs
from the same TaskSpecs, scores every new Attempt with Geneval2 followed by
HPSv3, and exposes HPS only in the next PlannerContext v0.8. It intentionally
uses the exploratory mini-pilot thresholds and is not a policy-admission run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_file
from gen_retry.domain.auxiliary_quality import (
    PROMPT_HASH_POLICY_ID,
    QUALITY_ANCHOR_POLICY_ID,
    DELTA_POLICY_ID,
    quality_risk_for_source_delta,
    risk_policy_sha256,
)
from gen_retry.domain.score_policy import PRIMARY_POLICY_ID, score_policy_for_id
from gen_retry.phase3.live_runner import Phase3LiveRunner, RolloutResult, RuntimeParams
from gen_retry.phase3.model_config import load_model_config, select_image_execution_profile
from gen_retry.phase3.rollout_prep import prepare_rollout_runs
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import build_planner_context_from_events
from gen_retry.runtime.reducer import reduce_events
from gen_retry.tools.resource_locks import exclusive_device_execution


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


def git_revision(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def root_for(attempt_id: str, parents: dict[str, str | None]) -> str:
    current = attempt_id
    seen: set[str] = set()
    while parents.get(current) is not None:
        if current in seen:
            raise ValueError(f"cycle in parent chain at {attempt_id}")
        seen.add(current)
        current = str(parents[current])
    return current


class HPSv3LiveRunner(Phase3LiveRunner):
    """Phase3 runner extension that inserts environment-owned HPS events."""

    def __init__(
        self,
        *,
        official_root: Path,
        config_path: Path,
        checkpoint_path: Path,
        backbone_path: Path,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.official_root = official_root
        self.config_path = config_path
        self.checkpoint_path = checkpoint_path
        self.backbone_path = backbone_path
        self._hps_config_path = Path(
            "artifacts/phase7/hpsv3_live_mini_local_config_v1.yaml"
        ).resolve()
        config_text = config_path.read_text(encoding="utf-8")
        config_text = config_text.replace(
            'model_name_or_path: "Qwen/Qwen2-VL-7B-Instruct"',
            f'model_name_or_path: "{backbone_path}"',
        )
        self._hps_config_path.parent.mkdir(parents=True, exist_ok=True)
        self._hps_config_path.write_text(config_text, encoding="utf-8")
        self._checkpoint_sha256 = sha256_file(checkpoint_path)
        self._revision = git_revision(official_root) or "unknown"
        self._policy_sha256 = risk_policy_sha256(RISK_POLICY)

    def _score_hps_subprocess(
        self,
        *,
        task_spec: dict[str, Any],
        attempt_id: str,
        image_path: Path,
        report_path: Path,
    ) -> None:
        command = [
            "/root/private_data/agentic_image/venvs/hpsv3/bin/python",
            str(Path(__file__).with_name("score_hpsv3_single.py")),
            "--official-root",
            str(self.official_root),
            "--config",
            str(self._hps_config_path),
            "--checkpoint",
            str(self.checkpoint_path),
            "--image",
            str(image_path),
            "--prompt",
            task_spec["original_prompt"],
            "--episode-id",
            task_spec["episode_id"],
            "--attempt-id",
            attempt_id,
            "--output",
            str(report_path),
        ]
        with exclusive_device_execution():
            subprocess.run(command, check=True)

    def _build_next_planner_context(
        self, run_dir: Path, *, input_refs: list[str]
    ) -> dict[str, Any]:
        plan = json.loads((run_dir / "rollout_plan.json").read_text(encoding="utf-8"))
        if str(plan.get("planner_context_schema_version")) == "0.8":
            self._ensure_hps_events(run_dir)
        return super()._build_next_planner_context(run_dir, input_refs=input_refs)

    def _ensure_hps_events(self, run_dir: Path) -> None:
        events = self._events(run_dir)
        state = reduce_events(events)
        quality_attempts = {
            event["payload"]["attempt_id"]
            for event in events
            if event["event_type"] == "auxiliary_quality_completed"
        }
        if not state.attempt_order or len(quality_attempts) == len(state.attempt_order):
            return

        task_spec = json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))
        completions = {
            event["payload"]["attempt_id"]: event
            for event in events
            if event["event_type"] == "image_execution_completed"
        }
        geneval_events = {
            event["payload"]["attempt_id"]: event
            for event in events
            if event["event_type"] == "geneval2_completed"
        }
        parents = {
            attempt_id: event["payload"].get("parent_attempt_id")
            for attempt_id, event in completions.items()
        }
        scored: dict[str, dict[str, Any]] = {}
        for attempt_id in state.attempt_order:
            if attempt_id in quality_attempts:
                quality = next(
                    event["payload"]
                    for event in events
                    if event["event_type"] == "auxiliary_quality_completed"
                    and event["payload"]["attempt_id"] == attempt_id
                )
                scored[attempt_id] = quality
                continue
            completion = completions[attempt_id]
            image_path = self._image_path_for_attempt(run_dir, state, attempt_id)
            prompt = task_spec["original_prompt"]
            report_ref = f"hpsv3/{attempt_id}.json"
            report_path = run_dir / report_ref
            if not report_path.exists():
                self._score_hps_subprocess(
                    task_spec=task_spec,
                    attempt_id=attempt_id,
                    image_path=image_path,
                    report_path=report_path,
                )
            cached = json.loads(report_path.read_text(encoding="utf-8"))
            if (
                cached.get("attempt_id") != attempt_id
                or cached.get("image_sha256") != completion["payload"]["artifact_sha256"]
                or cached.get("prompt_sha256") != sha256_bytes(prompt.encode("utf-8"))
            ):
                raise ValueError(f"stale HPS cache: {report_path}")
            mu = float(cached["mu"])
            log_sigma = float(cached["log_sigma"])
            sigma = float(cached["sigma"])
            source_id = parents[attempt_id]
            source_quality = scored.get(source_id) if source_id else None
            anchor_id = root_for(attempt_id, parents)
            anchor_quality = scored.get(anchor_id)
            delta_source = (
                mu - float(source_quality["mu"])
                if source_quality is not None
                else None
            )
            delta_anchor = (
                mu - float(anchor_quality["mu"])
                if anchor_quality is not None and anchor_id != attempt_id
                else None
            )
            report_payload = {
                "schema_version": "hpsv3_live_attempt_score_v1",
                "episode_id": task_spec["episode_id"],
                "attempt_id": attempt_id,
                "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                "image_path": str(image_path),
                "image_sha256": completion["payload"]["artifact_sha256"],
                "mu": mu,
                "log_sigma": log_sigma,
                "sigma": sigma,
                "official_hpsv3_revision": self._revision,
                "checkpoint_sha256": self._checkpoint_sha256,
                "preprocess_version": "official-hpsv3-local-config-v1; min_pixels=max_pixels=200704; sdpa",
            }
            report_path.parent.mkdir(parents=True, exist_ok=True)
            if not report_path.exists():
                report_path.write_text(
                    json.dumps(report_payload, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8",
                )
            report_sha = sha256_file(report_path)
            payload = {
                "evaluator_id": "hpsv3",
                "evaluator_version": f"official@{self._revision}",
                "checkpoint_ref": str(self.checkpoint_path),
                "checkpoint_sha256": self._checkpoint_sha256,
                "preprocess_version": "official-hpsv3-local-config-v1; min_pixels=max_pixels=200704; sdpa",
                "prompt_hash_policy_id": PROMPT_HASH_POLICY_ID,
                "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                "attempt_id": attempt_id,
                "image_artifact_id": completion["payload"]["image_artifact_id"],
                "image_sha256": completion["payload"]["artifact_sha256"],
                "source_attempt_id": source_id,
                "quality_anchor_attempt_id": None if anchor_id == attempt_id else anchor_id,
                "quality_anchor_policy_id": QUALITY_ANCHOR_POLICY_ID,
                "delta_policy_id": DELTA_POLICY_ID,
                "risk_policy": RISK_POLICY,
                "risk_policy_sha256": self._policy_sha256,
                "status": "success",
                "mu": mu,
                "sigma": sigma,
                "delta_from_source": delta_source,
                "delta_from_anchor": delta_anchor,
                "quality_risk": quality_risk_for_source_delta(delta_source, RISK_POLICY),
                "report_ref": report_ref,
                "report_sha256": report_sha,
                "error_code": None,
            }
            validate_instance(payload, "auxiliary_quality_observation_v0_1.schema.json")
            geneval_event = geneval_events[attempt_id]
            self._append_event(
                run_dir,
                event_type="auxiliary_quality_completed",
                turn_id=geneval_event["turn_id"],
                producer="hpsv3_live_mini_pilot",
                input_refs=[
                    geneval_event["event_id"],
                    completion["payload"]["image_artifact_id"],
                ],
                payload=payload,
            )
            scored[attempt_id] = payload
            quality_attempts.add(attempt_id)
            events = self._events(run_dir)
            state = reduce_events(events)
    def close(self) -> None:
        return None


def build_selected_prompts(source_root: Path, episode_ids: list[str]) -> dict[str, Any]:
    selected = []
    for episode_id in episode_ids:
        task_spec = json.loads(
            (source_root / episode_id / "task_spec.json").read_text(encoding="utf-8")
        )
        histogram: dict[str, int] = {}
        for constraint in task_spec["constraints"]:
            constraint_type = str(constraint["constraint_type"])
            histogram[constraint_type] = histogram.get(constraint_type, 0) + 1
        selected.append(
            {
                "candidate_id": f"hpsv3_mini_{episode_id}",
                "prompt_id": episode_id,
                # Preserve the source episode ID so the fresh arm can be paired
                # directly with the corresponding completed 1k episode.
                "selection_rank": int(episode_id.removeprefix("phase3_ep_")),
                "original_prompt": task_spec["original_prompt"],
                "atomic_constraints": task_spec["constraints"],
                "constraint_type_histogram": histogram,
                "provenance": {
                    "source": "existing_1k_task_spec",
                    "source_run": str(source_root),
                    "source_episode_id": episode_id,
                },
            }
        )
    return {
        "schema_version": "hpsv3_live_mini_selected_prompts_v1",
        "selection_id": "hpsv3_live_mini_same_prompt_v1",
        "selected_prompts": selected,
    }


def upgrade_to_v08(run_dir: Path, auxiliary_config: dict[str, Any]) -> None:
    plan_path = run_dir / "rollout_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["planner_context_schema_version"] = "0.8"
    plan["auxiliary_quality"] = auxiliary_config
    plan_path.write_text(canonical_json(plan) + "\n", encoding="utf-8")
    events_path = run_dir / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    context = build_planner_context_from_events(events[:1], schema_version="0.8")
    context_ref = "planner_contexts/planner_context_000.json"
    context_path = run_dir / context_ref
    context_path.write_text(canonical_json(context) + "\n", encoding="utf-8")
    context_sha = sha256_file(context_path)
    for event in events:
        if event["event_type"] == "planner_context_built":
            event["payload"]["planner_context_schema_version"] = "0.8"
            event["payload"]["planner_context_sha256"] = context_sha
    events_path.write_text(
        "\n".join(canonical_json(event) for event in events) + "\n", encoding="utf-8"
    )
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact in manifest["artifacts"]:
        if artifact["artifact_id"] == "planner_context_000":
            artifact["sha256"] = context_sha
        if artifact["artifact_id"] == "artifact_000":
            artifact["sha256"] = sha256_file(events_path)
    manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--episode-id", action="append", required=True)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument(
        "--backbone",
        type=Path,
        default=Path("/root/private_data/agentic_image/models/Qwen2-VL-7B-Instruct"),
    )
    parser.add_argument("--image-steps", type=int, default=40)
    parser.add_argument("--image-height", type=int, default=1024)
    parser.add_argument("--image-width", type=int, default=1024)
    args = parser.parse_args()

    selected_payload = build_selected_prompts(args.source_root, args.episode_id)
    selected_path = args.summary.with_name("hpsv3_live_mini_selected_prompts_v1.json")
    selected_path.parent.mkdir(parents=True, exist_ok=True)
    selected_path.write_text(
        json.dumps(selected_payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    missing_episode_ids = [
        episode_id
        for episode_id in args.episode_id
        if not (args.run_root / episode_id).exists()
    ]
    if missing_episode_ids:
        prepare_rollout_runs(
            selected_prompts_path=selected_path,
            output_root=args.run_root,
            summary_output=args.summary.with_name("hpsv3_live_mini_prepared_v1.json"),
            max_image_attempts=5,
            prompt_ids=missing_episode_ids,
        )
    auxiliary_config = {
        "evaluator_id": "hpsv3",
        "evaluator_version": f"official@{git_revision(args.official_root) or 'unknown'}",
        "checkpoint_ref": str(args.checkpoint),
        "checkpoint_sha256": sha256_file(args.checkpoint),
        "risk_policy": RISK_POLICY,
        "coverage_policy": "success_for_every_attempt_before_next_v08_context",
    }
    for episode_id in args.episode_id:
        upgrade_to_v08(args.run_root / episode_id, auxiliary_config)

    runner = HPSv3LiveRunner(
        official_root=args.official_root,
        config_path=args.config,
        checkpoint_path=args.checkpoint,
        backbone_path=args.backbone,
        model_config=select_image_execution_profile(
            load_model_config(), "qwen_image_edit_only"
        ),
        runtime_params=RuntimeParams(
            image_steps=args.image_steps,
            image_height=args.image_height,
            image_width=args.image_width,
        ),
    )
    results: list[dict[str, Any]] = []
    try:
        for episode_id in args.episode_id:
            result: RolloutResult = runner.run_episode(args.run_root / episode_id)
            results.append(
                {
                    "episode_id": result.episode_id,
                    "status": result.status,
                    "submitted_attempt_id": result.submitted_attempt_id,
                    "attempts": result.attempts,
                    "events": result.events,
                }
            )
            print(json.dumps(results[-1]), flush=True)
    finally:
        runner.close()
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(
            {
                "schema_version": "hpsv3_live_mini_pilot_v1",
                "baseline_source_root": str(args.source_root),
                "hps_run_root": str(args.run_root),
                "same_prompt_policy": "copied_exact_task_spec_v1",
                "risk_policy": RISK_POLICY,
                "results": results,
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
