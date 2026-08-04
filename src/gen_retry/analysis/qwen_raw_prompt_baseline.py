from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import (
    artifact_manifest_entry,
    sha256_bytes,
    sha256_file,
    validate_artifact_manifest_closure,
    write_artifact_bytes,
)
from gen_retry.phase3.model_config import load_model_config, select_image_execution_profile
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.tools.geneval2_adapter import LocalGeneval2Adapter
from gen_retry.tools.qwen_image_adapter import QwenImageAdapter


BASELINE_SCHEMA_VERSION = "qwen_raw_prompt_baseline_v1"


def prepare_raw_prompt_baseline(
    *,
    source_run_root: Path,
    episode_ids: list[str],
    output_root: Path,
    plan_output: Path,
    variant_count: int = 5,
    image_steps: int = 50,
    height: int = 1024,
    width: int = 1024,
) -> dict[str, Any]:
    if not episode_ids or len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode_ids must be a non-empty unique list")
    if variant_count != 5:
        raise ValueError("raw-prompt comparison requires exactly five variants")
    if image_steps < 1 or height < 1 or width < 1:
        raise ValueError("image parameters must be positive")
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing non-empty baseline root: {output_root}")

    prepared_inputs: list[tuple[str, Path, dict[str, Any], bytes, str]] = []
    for episode_id in episode_ids:
        source_path = source_run_root / episode_id / "task_spec.json"
        if not source_path.exists():
            raise FileNotFoundError(f"missing source TaskSpec: {source_path}")
        task_spec = json.loads(source_path.read_text(encoding="utf-8"))
        validate_instance(task_spec, "task_spec_v0_2.schema.json")
        if task_spec["episode_id"] != episode_id:
            raise ValueError(f"TaskSpec episode mismatch: {episode_id}")
        task_bytes = canonical_json(task_spec).encode("utf-8")
        task_sha = sha256_bytes(task_bytes)
        prepared_inputs.append(
            (episode_id, source_path, task_spec, task_bytes, task_sha)
        )

    entries: list[dict[str, Any]] = []
    output_root.mkdir(parents=True, exist_ok=True)
    for episode_id, source_path, task_spec, task_bytes, task_sha in prepared_inputs:
        episode_dir = output_root / episode_id
        episode_dir.mkdir(parents=True, exist_ok=True)
        for variant_index in range(variant_count):
            variant_dir = episode_dir / _variant_name(variant_index)
            variant_dir.mkdir(parents=True, exist_ok=True)
            write_artifact_bytes(variant_dir, "task_spec.json", task_bytes)
        entries.append(
            {
                "episode_id": episode_id,
                "source_task_spec": str(source_path.resolve()),
                "task_spec_sha256": task_sha,
                "original_prompt": task_spec["original_prompt"],
                "constraint_count": len(task_spec["constraints"]),
                "variant_indices": list(range(variant_count)),
            }
        )

    plan = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "baseline_type": "qwen_image_original_prompt",
        "source_run_root": str(source_run_root.resolve()),
        "source_read_policy": "task_spec_only",
        "output_root": str(output_root.resolve()),
        "episode_count": len(entries),
        "variant_count": variant_count,
        "seed_policy": "seed_equals_variant_index",
        "prompt_policy": "exact_task_spec_original_prompt_no_rewrite",
        "execution_profile": {
            "profile_id": "qwen_dual_backend",
            "generate_backend": "qwen_image",
            "generate_steps": image_steps,
            "height": height,
            "width": width,
        },
        "fresh_start_policy": {
            "sft_images_imported": False,
            "sft_events_imported": False,
            "sft_geneval2_imported": False,
            "teacher_used": False,
        },
        "episodes": entries,
    }
    plan_bytes = (canonical_json(plan) + "\n").encode("utf-8")
    write_artifact_bytes(output_root, "baseline_plan.json", plan_bytes)
    plan_output.parent.mkdir(parents=True, exist_ok=True)
    plan_output.write_bytes(plan_bytes)
    return plan


def run_raw_prompt_variant(
    *,
    run_root: Path,
    episode_id: str,
    variant_index: int,
) -> dict[str, Any]:
    plan = _read_json(run_root / "baseline_plan.json")
    planned_episodes = {item["episode_id"]: item for item in plan["episodes"]}
    if episode_id not in planned_episodes:
        raise ValueError(f"episode is not in baseline plan: {episode_id}")
    if variant_index not in range(int(plan["variant_count"])):
        raise ValueError(f"variant index outside baseline plan: {variant_index}")
    variant_dir = run_root / episode_id / _variant_name(variant_index)
    result_path = variant_dir / "result.json"
    if result_path.exists():
        return _read_json(result_path)

    task_spec = _read_json(variant_dir / "task_spec.json")
    validate_instance(task_spec, "task_spec_v0_2.schema.json")
    planned = planned_episodes[episode_id]
    task_sha = sha256_bytes(canonical_json(task_spec).encode("utf-8"))
    if task_sha != planned["task_spec_sha256"]:
        raise ValueError(f"{episode_id}: TaskSpec differs from frozen baseline plan")
    if task_spec["original_prompt"] != planned["original_prompt"]:
        raise ValueError(f"{episode_id}: original prompt differs from baseline plan")
    config = select_image_execution_profile(load_model_config(), "qwen_dual_backend")
    execution = config.resolved_image_execution
    backend = execution.generate_backend
    if backend.provider != "local" or backend.backend_id != "qwen_image":
        raise ValueError(
            "raw prompt baseline requires the existing local qwen_image generate backend"
        )
    image_steps = int(plan["execution_profile"]["generate_steps"])
    height = int(plan["execution_profile"]["height"])
    width = int(plan["execution_profile"]["width"])
    seed = int(variant_index)
    attempt_id = "a_000"
    image_artifact_id = "img_000"
    request_id = f"{episode_id}_{_variant_name(variant_index)}_generate"
    generator = QwenImageAdapter(
        provider=backend.provider,
        model_id=backend.model_id,
        model_path=backend.model_path,
        artifact_root=variant_dir,
        height=height,
        width=width,
        num_inference_steps=image_steps,
        true_cfg_scale=backend.true_cfg_scale,
        seed=seed,
    )
    generation = generator.generate(
        request_id=request_id,
        attempt_id=attempt_id,
        image_artifact_id=image_artifact_id,
        instruction=task_spec["original_prompt"],
    )
    evaluator = LocalGeneval2Adapter(
        evaluator_root=config.evaluator.config_path,
        artifact_root=variant_dir,
    )
    report = evaluator.evaluate_to_report(
        task_spec=task_spec,
        attempt_id=attempt_id,
        image_path=variant_dir / generation.artifact_uri,
    )
    task_entry = artifact_manifest_entry(
        artifact_id="task_spec_000",
        artifact_type="task_spec",
        uri="task_spec.json",
        sha256=sha256_file(variant_dir / "task_spec.json"),
        media_type="application/json",
        producer="qwen_raw_prompt_baseline_preparer",
    )
    manifest = {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "artifacts": [task_entry, generation.manifest_entry, report.manifest_entry],
    }
    write_artifact_bytes(
        variant_dir,
        "manifest.json",
        (canonical_json(manifest) + "\n").encode("utf-8"),
    )
    validate_artifact_manifest_closure(manifest, variant_dir)
    results = {item["constraint_id"]: item for item in report.constraint_results}
    confidences = [float(item["confidence"]) for item in results.values()]
    passed = sum(item["status"] == "pass" for item in results.values())
    gm = float(report.primary_score["value"])
    payload = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "episode_id": episode_id,
        "variant_index": variant_index,
        "seed": seed,
        "prompt": task_spec["original_prompt"],
        "constraint_count": len(task_spec["constraints"]),
        "image_call_count": 1,
        "image_ref": generation.artifact_uri,
        "image_sha256": generation.artifact_sha256,
        "geneval2_report_ref": report.report_ref,
        "geneval2_report_sha256": report.report_sha256,
        "passed_atoms": passed,
        "am": sum(confidences) / len(confidences) if confidences else 0.0,
        "gm": gm,
        "all_pass": passed == len(task_spec["constraints"]),
        "execution": {
            "request_id": request_id,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "model_path": str(backend.model_path.resolve()),
            "steps": image_steps,
            "height": height,
            "width": width,
            "cache_hit": bool(generation.metadata.get("cache_hit")),
        },
    }
    write_artifact_bytes(
        variant_dir,
        "result.json",
        (canonical_json(payload) + "\n").encode("utf-8"),
    )
    return payload


def summarize_raw_prompt_baseline(
    *,
    run_root: Path,
    artifact_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    plan = _read_json(run_root / "baseline_plan.json")
    expected_variants = int(plan["variant_count"])
    rows: list[dict[str, Any]] = []
    for episode in plan["episodes"]:
        variants = [
            _read_json(run_root / episode["episode_id"] / _variant_name(index) / "result.json")
            for index in range(expected_variants)
        ]
        if len({item["prompt"] for item in variants}) != 1:
            raise ValueError(f"{episode['episode_id']}: variant prompt mismatch")
        gm_best = max(variants, key=lambda item: (item["gm"], -item["variant_index"]))
        pass_best = max(
            variants,
            key=lambda item: (item["passed_atoms"], item["gm"], -item["variant_index"]),
        )
        rows.append(
            {
                "episode_id": episode["episode_id"],
                "constraint_count": episode["constraint_count"],
                "variants": variants,
                "single": variants[0],
                "best_of_5_gm": gm_best,
                "best_of_5_pass_count": pass_best,
            }
        )
    summary = {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "status": "PASS",
        "run_root": str(run_root.resolve()),
        "episode_count": len(rows),
        "variant_count": expected_variants,
        "prompt_policy": plan["prompt_policy"],
        "execution_profile": plan["execution_profile"],
        "single": _aggregate(rows, "single"),
        "best_of_5_gm": _aggregate(rows, "best_of_5_gm"),
        "best_of_5_pass_count": _aggregate(rows, "best_of_5_pass_count"),
        "total_image_calls": len(rows) * expected_variants,
        "episodes": rows,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _aggregate(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    selected = [row[key] for row in rows]
    total_atoms = sum(int(item["constraint_count"]) for item in rows)
    passed_atoms = sum(int(item["passed_atoms"]) for item in selected)
    return {
        "passed_atoms": passed_atoms,
        "total_atoms": total_atoms,
        "atom_pass_rate": passed_atoms / total_atoms if total_atoms else 0.0,
        "am_100": 100 * sum(float(item["am"]) for item in selected) / len(selected),
        "gm_100": 100 * sum(float(item["gm"]) for item in selected) / len(selected),
        "all_pass_episodes": sum(bool(item["all_pass"]) for item in selected),
        "episode_count": len(selected),
    }


def _render_report(summary: dict[str, Any]) -> str:
    def row(label: str, value: dict[str, Any]) -> str:
        return (
            f"| {label} | {value['passed_atoms']}/{value['total_atoms']} "
            f"({value['atom_pass_rate']:.2%}) | {value['am_100']:.2f} | "
            f"{value['gm_100']:.2f} | {value['all_pass_episodes']}/{value['episode_count']} |"
        )

    return "\n".join(
        [
            "# Qwen Original-Prompt Baseline",
            "",
            f"Status: **{summary['status']}**; episodes: {summary['episode_count']}; "
            f"variants/episode: {summary['variant_count']}.",
            "",
            "| Arm | Passed atoms | AM | GM | All-pass |",
            "| --- | ---: | ---: | ---: | ---: |",
            row("Single raw prompt (variant 0)", summary["single"]),
            row("Best-of-5, highest GM", summary["best_of_5_gm"]),
            row("Best-of-5, pass-count first", summary["best_of_5_pass_count"]),
            "",
            "Prompt input: exact TaskSpec `original_prompt`; no SFT action, Skill, "
            "edit, or Teacher planner is used.",
            "",
        ]
    )


def _variant_name(index: int) -> str:
    return f"variant_{index:03d}"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value
