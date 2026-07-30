from __future__ import annotations

import argparse
import os
from pathlib import Path

from gen_retry.agent.teacher_client import OpenAICompatibleTeacherClient
from gen_retry.phase3.live_runner import RuntimeParams
from gen_retry.phase3.model_config import load_model_config
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.tools.geneval2_adapter import LocalGeneval2Adapter
from gen_retry.tools.qianwen_image_edit_adapter import QianwenImageEditAdapter
from gen_retry.tools.qwen_image_adapter import QwenImageAdapter


def run_preflight(
    *,
    output_dir: Path = Path("runs/preflight/phase3_live_preflight"),
    summary_path: Path = Path("artifacts/phase3/live_preflight_summary.json"),
    checkpoint_path: Path = Path("docs/checkpoints/phase3_live_preflight.md"),
    params: RuntimeParams = RuntimeParams(),
    run_image_smoke: bool = False,
) -> dict:
    cfg = load_model_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    env_status = {
        cfg.teacher.api_key_env: "SET" if os.environ.get(cfg.teacher.api_key_env) else "MISSING",
        cfg.teacher.base_url_env: "SET" if os.environ.get(cfg.teacher.base_url_env) else "MISSING",
    }
    teacher = OpenAICompatibleTeacherClient(cfg.teacher)
    teacher_response = teacher.smoke_test()
    teacher_smoke_passed = "ok" in teacher_response.raw_text.lower()

    execution = cfg.resolved_image_execution
    generate_backend = execution.generate_backend
    edit_backend = execution.edit_backend
    generate_steps = (
        params.generate_image_steps
        if params.generate_image_steps is not None
        else generate_backend.num_inference_steps or params.image_steps
    )
    edit_steps = (
        params.edit_image_steps
        if params.edit_image_steps is not None
        else edit_backend.num_inference_steps or params.image_steps
    )
    generate_adapter = QwenImageAdapter(
        provider=generate_backend.provider,
        model_id=generate_backend.model_id,
        model_path=generate_backend.model_path,
        artifact_root=output_dir,
        height=params.image_height,
        width=params.image_width,
        num_inference_steps=generate_steps,
        true_cfg_scale=generate_backend.true_cfg_scale,
        seed=params.image_seed,
    )
    edit_adapter = QianwenImageEditAdapter(
        provider=edit_backend.provider,
        model_id=edit_backend.model_id,
        model_path=edit_backend.model_path,
        artifact_root=output_dir,
        height=params.image_height,
        width=params.image_width,
        num_inference_steps=edit_steps,
        true_cfg_scale=edit_backend.true_cfg_scale,
        guidance_scale=(
            edit_backend.guidance_scale
            if edit_backend.guidance_scale is not None
            else 1.0
        ),
        seed=params.image_seed + 1,
    )
    generation = None
    edit = None
    geneval_report = None
    atom_schema_ok = None
    if run_image_smoke:
        generation = generate_adapter.generate(
            request_id="phase3_smoke_generate",
            attempt_id="a_000",
            image_artifact_id="img_000",
            instruction=(
                "Create exactly one blue cube centered on a plain white background. "
                "Use a simple uncluttered composition with no text."
            ),
        )
        edit = edit_adapter.edit(
            request_id="phase3_smoke_edit",
            attempt_id="a_001",
            source_attempt_id="a_000",
            source_image_path=output_dir / generation.artifact_uri,
            image_artifact_id="img_001",
            instruction=(
                "Change the cube color to red while preserving exactly one cube, "
                "the plain white background, and the centered composition. No text."
            ),
        )
        smoke_task_spec = {
            "schema_version": "0.2",
            "episode_id": "phase3_live_smoke",
            "original_prompt": "one red cube on a plain white background",
            "constraints": [
                {
                    "constraint_id": "c_001",
                    "constraint_type": "count",
                    "requirement": "Expected answer: one",
                    "evaluator_question": "How many cubes are in the image?",
                    "priority": 3,
                },
                {
                    "constraint_id": "c_002",
                    "constraint_type": "attribute",
                    "requirement": "Expected answer: Yes",
                    "evaluator_question": "Is the cube red?",
                    "priority": 3,
                },
                {
                    "constraint_id": "c_003",
                    "constraint_type": "object",
                    "requirement": "Expected answer: Yes",
                    "evaluator_question": "Are there any cubes in the image?",
                    "priority": 3,
                },
            ],
            "max_image_attempts": 2,
        }
        evaluator = LocalGeneval2Adapter(
            evaluator_root=cfg.evaluator.config_path,
            artifact_root=output_dir,
            pass_threshold=params.evaluator_pass_threshold,
            fail_threshold=params.evaluator_fail_threshold,
        )
        geneval_report = evaluator.evaluate_to_report(
            task_spec=smoke_task_spec,
            attempt_id="a_001",
            image_path=output_dir / edit.artifact_uri,
            report_ref="geneval2/smoke_edit_a_001.json",
        )
        atom_schema_ok = all(
            set(result).issuperset({"constraint_id", "status"})
            and result["status"] in {"pass", "fail", "uncertain"}
            for result in geneval_report.constraint_results
        )
    summary = {
        "schema_version": "0.2",
        "preflight_type": "phase3_live_sanitized_config_check",
        "phase3_episode_counted": False,
        "image_smoke_run": run_image_smoke,
        "teacher_env": env_status,
        "teacher": {
            "provider": cfg.teacher.provider,
            "model_id": cfg.teacher.model_id,
            "smoke_passed": teacher_smoke_passed,
            "finish_reason": teacher_response.finish_reason,
            "raw_text_sha256": teacher_response.response_metadata["raw_text_sha256"],
        },
        "image_execution": {
            "profile_id": execution.profile_id,
            "profile_version": execution.profile_version,
            "generate": {
                "provider": generate_backend.provider,
                "model_id": generate_backend.model_id,
                "backend_id": generate_backend.backend_id,
                "model_path_exists": generate_backend.model_path.exists(),
                "uses_http_endpoint": generate_adapter.uses_http_endpoint,
                "render_quality_defaults": {
                    "height": params.image_height,
                    "width": params.image_width,
                    "num_inference_steps": generate_steps,
                    "true_cfg_scale": generate_adapter.true_cfg_scale,
                    "guidance_scale": None,
                },
            },
            "edit": {
                "provider": edit_backend.provider,
                "model_id": edit_backend.model_id,
                "backend_id": edit_backend.backend_id,
                "model_path_exists": edit_backend.model_path.exists(),
                "uses_http_endpoint": edit_adapter.uses_http_endpoint,
                "render_quality_defaults": {
                    "height": params.image_height,
                    "width": params.image_width,
                    "num_inference_steps": edit_steps,
                    "true_cfg_scale": edit_adapter.true_cfg_scale,
                    "guidance_scale": edit_adapter.guidance_scale,
                },
            },
            "generation_smoke": None if generation is None else {
                "request_id": generation.request_id,
                "artifact_uri": generation.artifact_uri,
                "artifact_sha256": generation.artifact_sha256,
                "operation": generation.operation,
            },
            "edit_smoke": None if edit is None else {
                "request_id": edit.request_id,
                "artifact_uri": edit.artifact_uri,
                "artifact_sha256": edit.artifact_sha256,
                "operation": edit.operation,
                "parent_attempt_id": edit.parent_attempt_id,
            },
        },
        "geneval2": {
            "backend_id": cfg.evaluator.backend_id,
            "root_exists": cfg.evaluator.config_path.exists(),
            "report_ref": None if geneval_report is None else geneval_report.report_ref,
            "report_sha256": None if geneval_report is None else geneval_report.report_sha256,
            "normalization": None if geneval_report is None else geneval_report.normalization,
            "atom_schema_ok": atom_schema_ok,
            "constraint_statuses": {} if geneval_report is None else {
                result["constraint_id"]: result["status"]
                for result in geneval_report.constraint_results
            },
        },
        "passed": (
            all(value == "SET" for value in env_status.values())
            and teacher_smoke_passed
            and generate_backend.model_path.exists()
            and edit_backend.model_path.exists()
            and not generate_adapter.uses_http_endpoint
            and not edit_adapter.uses_http_endpoint
            and cfg.evaluator.config_path.exists()
            and (atom_schema_ok is not False)
        ),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(_checkpoint(summary), encoding="utf-8")
    return summary


def _checkpoint(summary: dict) -> str:
    image_smoke = summary["image_smoke_run"]
    atom_status = "not run"
    if image_smoke:
        atom_status = "PASS" if summary["geneval2"]["atom_schema_ok"] else "FAIL"
    lines = [
        "# Phase 3 Live Sanitized Config Check",
        "",
        f"- TEACHER_API_KEY: {summary['teacher_env'].get('TEACHER_API_KEY', 'MISSING')}",
        f"- TEACHER_BASE_URL: {summary['teacher_env'].get('TEACHER_BASE_URL', 'MISSING')}",
        f"- Teacher model ID: {summary['teacher']['model_id']}",
        f"- Teacher smoke: {'PASS' if summary['teacher']['smoke_passed'] else 'FAIL'}",
        f"- Execution profile: {summary['image_execution']['profile_id']}@{summary['image_execution']['profile_version']}",
        f"- Generate provider: {summary['image_execution']['generate']['provider']}",
        f"- Generate model path exists: {'PASS' if summary['image_execution']['generate']['model_path_exists'] else 'FAIL'}",
        f"- Generate adapter uses HTTP endpoint: {summary['image_execution']['generate']['uses_http_endpoint']}",
        f"- Edit provider: {summary['image_execution']['edit']['provider']}",
        f"- Edit model path exists: {'PASS' if summary['image_execution']['edit']['model_path_exists'] else 'FAIL'}",
        f"- Edit adapter uses HTTP endpoint: {summary['image_execution']['edit']['uses_http_endpoint']}",
        f"- Image smoke run: {image_smoke}",
        f"- Generate defaults: {summary['image_execution']['generate']['render_quality_defaults']}",
        f"- Edit defaults: {summary['image_execution']['edit']['render_quality_defaults']}",
        f"- Generation smoke artifact: {summary['image_execution']['generation_smoke']['artifact_uri'] if image_smoke else 'not run'}",
        f"- Edit smoke artifact: {summary['image_execution']['edit_smoke']['artifact_uri'] if image_smoke else 'not run'}",
        f"- Geneval2 atom schema normalization: {atom_status}",
        f"- Counted as Phase 3 episode: {summary['phase3_episode_counted']}",
        f"- Overall preflight: {'PASS' if summary['passed'] else 'FAIL'}",
        "",
        "No credentials or authorization headers are printed or persisted. No image call is made unless explicitly requested with `--run-image-smoke`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("runs/preflight/phase3_live_preflight"))
    parser.add_argument("--summary-path", type=Path, default=Path("artifacts/phase3/live_preflight_summary.json"))
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        default=Path("docs/checkpoints/phase3_live_preflight.md"),
    )
    parser.add_argument("--run-image-smoke", action="store_true")
    parser.add_argument("--image-steps", type=int, default=40)
    parser.add_argument("--image-height", type=int, default=1024)
    parser.add_argument("--image-width", type=int, default=1024)
    args = parser.parse_args()
    summary = run_preflight(
        output_dir=args.output_dir,
        summary_path=args.summary_path,
        checkpoint_path=args.checkpoint_path,
        params=RuntimeParams(
            image_height=args.image_height,
            image_width=args.image_width,
            image_steps=args.image_steps,
        ),
        run_image_smoke=args.run_image_smoke,
    )
    print("TEACHER_API_KEY=" + summary["teacher_env"].get("TEACHER_API_KEY", "MISSING"))
    print("TEACHER_BASE_URL=" + summary["teacher_env"].get("TEACHER_BASE_URL", "MISSING"))
    print("teacher_model_id=" + summary["teacher"]["model_id"])
    print("teacher_smoke=" + ("PASS" if summary["teacher"]["smoke_passed"] else "FAIL"))
    print(
        "execution_profile="
        + summary["image_execution"]["profile_id"]
        + "@"
        + summary["image_execution"]["profile_version"]
    )
    for route in ("generate", "edit"):
        route_summary = summary["image_execution"][route]
        print(
            f"{route}_model_path_exists="
            + ("SET" if route_summary["model_path_exists"] else "MISSING")
        )
        print(f"{route}_adapter_provider=" + route_summary["provider"])
        print(
            f"{route}_adapter_uses_http_endpoint="
            + str(route_summary["uses_http_endpoint"])
        )
    print("image_smoke_run=" + str(summary["image_smoke_run"]))
    print(
        "generate_render_quality_defaults="
        + canonical_json(
            summary["image_execution"]["generate"]["render_quality_defaults"]
        )
    )
    print(
        "edit_render_quality_defaults="
        + canonical_json(
            summary["image_execution"]["edit"]["render_quality_defaults"]
        )
    )
    if summary["image_smoke_run"]:
        print("generation_smoke=PASS")
        print("edit_smoke=PASS")
        print("geneval2_atom_schema=" + ("PASS" if summary["geneval2"]["atom_schema_ok"] else "FAIL"))
    else:
        print("generation_smoke=NOT_RUN")
        print("edit_smoke=NOT_RUN")
        print("geneval2_atom_schema=NOT_RUN")
    print("preflight=" + ("PASS" if summary["passed"] else "FAIL"))


if __name__ == "__main__":
    main()
