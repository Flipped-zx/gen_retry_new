from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.score_policy import PRIMARY_POLICY_ID, planner_context_version, score_policy_for_id
from gen_retry.phase3.rollout_prep import _prepare_one_run
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.json_canonical import canonical_json


def prepare_frozen_test_rollouts(
    *,
    source_run_root: Path,
    split_manifest_path: Path,
    output_root: Path,
    summary_output: Path,
    limit: int = 20,
    max_image_attempts: int = 5,
    checkpoint_path: Path,
    execution_profile_id: str = "qwen_dual_backend",
    execution_profile_version: str = "1",
) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be positive")
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing non-empty run root: {output_root}")
    split_bytes = split_manifest_path.read_bytes()
    split_manifest = json.loads(split_bytes)
    if split_manifest.get("format_version") != "sft_split_manifest_v2":
        raise ValueError("unexpected SFT split manifest format")
    if split_manifest.get("prompt_group_cross_split_violations"):
        raise ValueError("SFT split manifest has prompt-group leakage")
    test_episode_ids = sorted(
        (
            episode_id
            for episode_id, split in split_manifest["episode_splits"].items()
            if split == "test"
        ),
        key=_episode_number,
    )
    if len(test_episode_ids) != split_manifest["split_episode_counts"]["test"]:
        raise ValueError("test episode count does not match split manifest")
    selected_episode_ids = test_episode_ids[:limit]
    if len(selected_episode_ids) != limit:
        raise ValueError(f"frozen test split has fewer than {limit} episodes")

    score_policy = score_policy_for_id(PRIMARY_POLICY_ID)
    context_version = planner_context_version(score_policy)
    split_sha256 = sha256_bytes(split_bytes)
    created_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    prepared: list[dict[str, Any]] = []
    source_task_specs: list[dict[str, Any]] = []
    for episode_id in selected_episode_ids:
        source_path = source_run_root / episode_id / "task_spec.json"
        source_bytes = source_path.read_bytes()
        task_spec = json.loads(source_bytes)
        validate_instance(task_spec, "task_spec_v0_2.schema.json")
        if task_spec["episode_id"] != episode_id:
            raise ValueError(f"source TaskSpec episode mismatch: {episode_id}")
        if task_spec["max_image_attempts"] != max_image_attempts:
            raise ValueError(
                f"source TaskSpec budget mismatch for {episode_id}: "
                f"{task_spec['max_image_attempts']}"
            )
        source_canonical_sha256 = sha256_bytes(
            canonical_json(task_spec).encode("utf-8")
        )
        candidate = _candidate_from_task_spec(
            task_spec,
            source_task_spec_sha256=source_canonical_sha256,
            split_manifest_sha256=split_sha256,
        )
        item = _prepare_one_run(
            candidate=candidate,
            output_root=output_root,
            max_image_attempts=max_image_attempts,
            created_at=created_at,
            execution_profile_id=execution_profile_id,
            execution_profile_version=execution_profile_version,
            score_policy=score_policy,
            planner_context_schema_version=context_version,
            selection_artifact_ref=str(split_manifest_path.resolve()),
            selection_artifact_sha256=split_sha256,
        )
        fresh_task_spec = json.loads(
            (output_root / episode_id / "task_spec.json").read_text(encoding="utf-8")
        )
        if canonical_json(fresh_task_spec) != canonical_json(task_spec):
            raise RuntimeError(f"fresh TaskSpec differs from frozen source: {episode_id}")
        prepared.append(item)
        source_task_specs.append(
            {
                "episode_id": episode_id,
                "source_ref": str(source_path.resolve()),
                "canonical_sha256": source_canonical_sha256,
            }
        )

    summary = {
        "schema_version": "0.2",
        "cohort": "flow1000_v9_frozen_sft_test",
        "prepared_count": len(prepared),
        "episode_ids": selected_episode_ids,
        "split_manifest_ref": str(split_manifest_path.resolve()),
        "split_manifest_sha256": split_sha256,
        "source_run_root": str(source_run_root.resolve()),
        "source_read_policy": "task_spec_only",
        "source_task_specs": source_task_specs,
        "fresh_run_root": str(output_root.resolve()),
        "checkpoint_path": str(checkpoint_path.resolve()),
        "planner": {
            "provider": "local_transformers_service",
            "system_prompt": "phase4_sft_system_prompt_action_protocol_v0_5",
            "planner_context_schema_version": context_version,
            "action_protocol_version": "0.5",
            "teacher_fallback_allowed": False,
        },
        "execution_profile": {
            "profile_id": execution_profile_id,
            "profile_version": execution_profile_version,
        },
        "render": {
            "generate_steps": 50,
            "edit_steps": 40,
            "height": 1024,
            "width": 1024,
            "max_image_attempts": max_image_attempts,
        },
        "episodes": prepared,
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    return summary


def _candidate_from_task_spec(
    task_spec: dict[str, Any],
    *,
    source_task_spec_sha256: str,
    split_manifest_sha256: str,
) -> dict[str, Any]:
    episode_id = task_spec["episode_id"]
    rank = _episode_number(episode_id)
    histogram = Counter(
        constraint["constraint_type"] for constraint in task_spec["constraints"]
    )
    return {
        "candidate_id": f"frozen_sft_test_{rank:04d}",
        "prompt_id": f"frozen_sft_test_{rank:04d}",
        "selection_rank": rank,
        "original_prompt": task_spec["original_prompt"],
        "atomic_constraints": task_spec["constraints"],
        "constraint_type_histogram": dict(sorted(histogram.items())),
        "provenance": {
            "source": "flow1000_v9_frozen_sft_test_task_spec",
            "source_episode_id": episode_id,
            "source_task_spec_sha256": source_task_spec_sha256,
            "split_manifest_sha256": split_manifest_sha256,
            "sft_frozen_test_held_out": True,
            "source_read_policy": "task_spec_only",
        },
    }


def _episode_number(episode_id: str) -> int:
    prefix = "phase3_ep_"
    if not episode_id.startswith(prefix) or not episode_id[len(prefix) :].isdigit():
        raise ValueError(f"invalid episode ID: {episode_id}")
    return int(episode_id[len(prefix) :])
