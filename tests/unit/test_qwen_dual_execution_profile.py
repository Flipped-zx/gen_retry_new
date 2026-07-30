from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.phase3.live_runner import Phase3LiveRunner
from gen_retry.phase3.model_config import (
    EvaluatorConfig,
    ImageBackendConfig,
    ImageExecutionConfig,
    ModelConfig,
    TeacherConfig,
    select_image_execution_profile,
)
from gen_retry.tools.image_execution_profile import (
    resolve_execution_route,
    validate_execution_profile,
)
from gen_retry.tools.qianwen_image_edit_adapter import QianwenImageEditAdapter
from gen_retry.tools.qwen_image_adapter import QwenImageAdapter


def _backend(
    tmp_path: Path,
    *,
    backend_id: str,
    model_id: str,
    supports_generate: bool,
    supports_edit: bool,
    steps: int,
) -> ImageBackendConfig:
    model_path = tmp_path / model_id
    model_path.mkdir()
    (model_path / "model_index.json").write_text(
        json.dumps({"_class_name": model_id}),
        encoding="utf-8",
    )
    return ImageBackendConfig(
        provider="local",
        backend_id=backend_id,
        model_id=model_id,
        model_path=model_path,
        supports_generate=supports_generate,
        supports_edit=supports_edit,
        num_inference_steps=steps,
        true_cfg_scale=4.0,
        guidance_scale=1.0 if supports_edit else None,
    )


def _model_config(tmp_path: Path) -> ModelConfig:
    generate = _backend(
        tmp_path,
        backend_id="qwen_image",
        model_id="Qwen-Image-2512",
        supports_generate=True,
        supports_edit=False,
        steps=50,
    )
    edit = _backend(
        tmp_path,
        backend_id="qianwen_image_edit",
        model_id="Qwen-Image-Edit-2511",
        supports_generate=False,
        supports_edit=True,
        steps=40,
    )
    return ModelConfig(
        teacher=TeacherConfig(
            provider="openai_compatible",
            model_id="gpt-5.5",
            api_key_env="TEACHER_API_KEY",
            base_url_env="TEACHER_BASE_URL",
        ),
        image_backend=edit,
        image_execution=ImageExecutionConfig(
            profile_id="qwen_dual_backend",
            profile_version="1",
            generate_backend=generate,
            edit_backend=edit,
        ),
        evaluator=EvaluatorConfig(
            backend_id="geneval2",
            config_path=tmp_path / "geneval2",
        ),
    )


def test_dual_profile_routes_logical_actions_without_planner_backend_field(
    tmp_path: Path,
) -> None:
    config = _model_config(tmp_path).resolved_image_execution

    generate = resolve_execution_route(config, "generate_image")
    edit = resolve_execution_route(config, "edit_image")

    assert generate.operation == "generate"
    assert generate.backend.backend_id == "qwen_image"
    assert generate.backend.num_inference_steps == 50
    assert edit.operation == "edit"
    assert edit.backend.backend_id == "qianwen_image_edit"
    assert edit.backend.num_inference_steps == 40


def test_dual_profile_rejects_swapped_backends(tmp_path: Path) -> None:
    valid = _model_config(tmp_path).resolved_image_execution
    invalid = ImageExecutionConfig(
        profile_id="qwen_dual_backend",
        profile_version="1",
        generate_backend=valid.edit_backend,
        edit_backend=valid.generate_backend,
    )

    with pytest.raises(ValueError, match="generate route"):
        validate_execution_profile(invalid)


def test_adapters_expose_complete_provenance_without_loading_models(
    tmp_path: Path,
) -> None:
    config = _model_config(tmp_path).resolved_image_execution
    generate = QwenImageAdapter(
        provider="local",
        model_id=config.generate_backend.model_id,
        model_path=config.generate_backend.model_path,
        artifact_root=tmp_path,
    )
    edit = QianwenImageEditAdapter(
        provider="local",
        model_id=config.edit_backend.model_id,
        model_path=config.edit_backend.model_path,
        artifact_root=tmp_path,
    )

    generate_metadata = generate.execution_metadata(cache_hit=False)
    edit_metadata = edit.execution_metadata(
        cache_hit=False,
        internal_generation_canvas=False,
    )

    assert generate_metadata["pipeline_id"] == "QwenImagePipeline"
    assert generate_metadata["sampling"]["num_inference_steps"] == 50
    assert generate_metadata["sampling"]["guidance_scale"] is None
    assert generate_metadata["model_revision_or_fingerprint"].startswith(
        "model_index_sha256:"
    )
    assert edit_metadata["pipeline_id"] == "QwenImageEditPlusPipeline"
    assert edit_metadata["sampling"]["num_inference_steps"] == 40
    assert edit_metadata["internal_generation_canvas"] is False


def test_runner_rejects_resume_under_a_different_execution_profile(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "phase3_ep_001"
    run_dir.mkdir()
    (run_dir / "rollout_plan.json").write_text(
        json.dumps(
            {
                "execution_profile": {
                    "profile_id": "qwen_image_edit_only",
                    "profile_version": "1",
                }
            }
        ),
        encoding="utf-8",
    )
    runner = Phase3LiveRunner(model_config=_model_config(tmp_path))

    with pytest.raises(RuntimeError, match="execution profile mismatch"):
        runner._validate_execution_profile_lock(run_dir)


def test_runner_accepts_matching_execution_profile(tmp_path: Path) -> None:
    run_dir = tmp_path / "phase3_ep_001"
    run_dir.mkdir()
    (run_dir / "rollout_plan.json").write_text(
        json.dumps(
            {
                "execution_profile": {
                    "profile_id": "qwen_dual_backend",
                    "profile_version": "1",
                }
            }
        ),
        encoding="utf-8",
    )
    runner = Phase3LiveRunner(model_config=_model_config(tmp_path))

    runner._validate_execution_profile_lock(run_dir)


def test_runtime_can_select_legacy_profile_without_changing_action_schema(
    tmp_path: Path,
) -> None:
    dual = _model_config(tmp_path)

    legacy = select_image_execution_profile(dual, "qwen_image_edit_only")

    assert legacy.resolved_image_execution.profile_id == "qwen_image_edit_only"
    assert legacy.resolved_image_execution.generate_backend.backend_id == (
        "qianwen_image_edit"
    )
    assert legacy.resolved_image_execution.edit_backend.backend_id == (
        "qianwen_image_edit"
    )
