from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.preflight import _package_versions, run_rl_preflight
from gen_retry.rl.tracking import (
    build_wandb_runtime,
    initialize_wandb_run,
    sanitized_tracking_payload,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"


def _config_payload() -> dict[str, object]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def _write_preflight_config(tmp_path: Path) -> Path:
    payload = _config_payload()
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    payload["base_checkpoint"] = str(checkpoint)
    payload["tracking"]["directory"] = str(tmp_path / "wandb")
    for key in (
        "train_manifest",
        "development_manifest",
        "confirmation_manifest",
        "experiment_declaration",
    ):
        path = tmp_path / f"{key}.json"
        path.write_text("{}\n", encoding="utf-8")
        payload["admission"][key] = str(path)
    config_path = tmp_path / "rl.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return config_path


def _model_config(tmp_path: Path) -> SimpleNamespace:
    generate_path = tmp_path / "qwen-image"
    edit_path = tmp_path / "qwen-image-edit"
    geneval2_path = tmp_path / "geneval2"
    for path in (generate_path, edit_path, geneval2_path):
        path.mkdir(exist_ok=True)
    return SimpleNamespace(
        resolved_image_execution=SimpleNamespace(
            profile_id="qwen_dual_backend",
            profile_version="1",
            generate_backend=SimpleNamespace(
                model_id="Qwen-Image-2512",
                model_path=generate_path,
                supports_generate=True,
                supports_edit=False,
            ),
            edit_backend=SimpleNamespace(
                model_id="Qwen-Image-Edit-2511",
                model_path=edit_path,
                supports_generate=False,
                supports_edit=True,
            ),
        ),
        evaluator=SimpleNamespace(config_path=geneval2_path),
    )


def test_naive_experiment_config_freezes_dual_backend_and_staged_topology() -> None:
    config = load_experiment_config(CONFIG_PATH)
    assert config.execution_profile == "qwen_dual_backend@1"
    assert config.rollout.full_rollouts_per_prompt == 4
    assert config.resources.rollout_devices == 8
    assert config.resources.generate_replicas == 2
    assert config.resources.edit_replicas == 2
    assert config.resources.trainer_devices == 8
    assert config.optimization.use_reference_kl is True
    assert config.optimization.reference_kl_coefficient == pytest.approx(0.02)
    assert config.tracking.mode == "offline"


def test_naive_experiment_config_rejects_profile_drift(tmp_path: Path) -> None:
    payload = _config_payload()
    payload["execution_profile"] = "qwen_edit_only@1"
    path = tmp_path / "rl.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="qwen_dual_backend"):
        load_experiment_config(path)


def test_wandb_offline_does_not_require_or_propagate_api_key() -> None:
    tracking = load_experiment_config(CONFIG_PATH).tracking
    runtime = build_wandb_runtime(
        tracking,
        run_suffix="smoke-001",
        environment={"WANDB_API_KEY": "must-not-propagate"},
    )
    assert runtime.enabled is True
    assert runtime.mode == "offline"
    assert runtime.environment["WANDB_MODE"] == "offline"
    assert "WANDB_API_KEY" not in runtime.environment


def test_wandb_online_requires_environment_credential(tmp_path: Path) -> None:
    payload = _config_payload()
    path = tmp_path / "rl.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    config = load_experiment_config(path)
    with pytest.raises(ValueError, match="WANDB_API_KEY"):
        build_wandb_runtime(
            config.tracking,
            run_suffix="pilot",
            environment={"GEN_RETRY_WANDB_MODE": "online"},
        )


def test_wandb_online_override_keeps_api_key_out_of_runtime() -> None:
    tracking = load_experiment_config(CONFIG_PATH).tracking
    runtime = build_wandb_runtime(
        tracking,
        run_suffix="pilot",
        environment={
            "GEN_RETRY_WANDB_MODE": "online",
            "WANDB_API_KEY": "must-not-propagate",
            "WANDB_ENTITY": "test-entity",
        },
    )
    assert runtime.mode == "online"
    assert runtime.entity == "test-entity"
    assert "WANDB_API_KEY" not in runtime.environment


def test_tracking_payload_redacts_nested_secrets() -> None:
    sanitized = sanitized_tracking_payload(
        {
            "learning_rate": 1e-6,
            "WANDB_API_KEY": "secret-value",
            "nested": {"access_token": "token-value", "seed": 42},
        }
    )
    assert sanitized == {
        "learning_rate": 1e-6,
        "WANDB_API_KEY": "REDACTED",
        "nested": {"access_token": "REDACTED", "seed": 42},
    }


def test_wandb_initialization_uses_sanitized_config(tmp_path: Path) -> None:
    payload = _config_payload()
    payload["tracking"]["directory"] = str(tmp_path / "wandb")
    path = tmp_path / "rl.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    tracking = load_experiment_config(path).tracking
    calls: list[dict[str, object]] = []
    fake_wandb = SimpleNamespace(init=lambda **kwargs: calls.append(kwargs) or "run")
    run = initialize_wandb_run(
        tracking,
        run_suffix="smoke",
        run_config={"learning_rate": 1e-6, "api_key": "must-not-log"},
        environment={},
        wandb_module=fake_wandb,
    )
    assert run == "run"
    assert calls[0]["mode"] == "offline"
    assert calls[0]["config"] == {
        "learning_rate": 1e-6,
        "api_key": "REDACTED",
    }


def test_preflight_ready_for_smoke_requires_adapter_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_preflight_config(tmp_path)
    monkeypatch.setattr(
        "gen_retry.rl.preflight.load_model_config",
        lambda _: _model_config(tmp_path),
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.checkpoint_fingerprint",
        lambda _: "sha256:b2377728e0cd748447e27a9583c1456121a20aff84da9468da14e9cb16cd2718",
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight._package_versions",
        lambda: {
            name: "test-version"
            for name in (
                "torch",
                "transformers",
                "ray",
                "wandb",
                "verl",
                "sglang",
                "rllm",
            )
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight._probe_accelerator",
        lambda: {
            "checked": True,
            "available": True,
            "device_count": 8,
            "devices": [],
            "error": None,
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.validate_frozen_rl_data",
        lambda **_: {
            "train": {"selected_count": 1000},
            "development": {"selected_count": 200},
            "confirmation": {"selected_count": 500},
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.probe_live_adapter_evidence",
        lambda **_: (True, "adapter passed", "a" * 64),
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.probe_smoke_report",
        lambda **_: (False, "smoke pending"),
    )
    report = run_rl_preflight(
        config_path=config_path,
        model_config_path=tmp_path / "models.yaml",
        environment={},
    )
    assert report["status"] == "READY_FOR_SMOKE"
    assert report["control_plane_ready"] is True
    assert report["ready_for_smoke"] is True
    assert report["ready_for_optimization"] is False
    assert report["blocked_count"] == 0
    assert report["pending_count"] == 1


def test_preflight_optimization_requires_passing_smoke_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_preflight_config(tmp_path)
    monkeypatch.setattr(
        "gen_retry.rl.preflight.load_model_config",
        lambda _: _model_config(tmp_path),
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.checkpoint_fingerprint",
        lambda _: "sha256:b2377728e0cd748447e27a9583c1456121a20aff84da9468da14e9cb16cd2718",
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight._package_versions",
        lambda: {
            name: "test-version"
            for name in (
                "torch",
                "transformers",
                "ray",
                "wandb",
                "verl",
                "sglang",
                "rllm",
            )
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight._probe_accelerator",
        lambda: {
            "checked": True,
            "available": True,
            "device_count": 8,
            "devices": [],
            "error": None,
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.validate_frozen_rl_data",
        lambda **_: {
            "train": {"selected_count": 1000},
            "development": {"selected_count": 200},
            "confirmation": {"selected_count": 500},
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.probe_live_adapter_evidence",
        lambda **_: (True, "adapter passed", "a" * 64),
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.probe_smoke_report",
        lambda **_: (True, "smoke passed"),
    )
    report = run_rl_preflight(
        config_path=config_path,
        model_config_path=tmp_path / "models.yaml",
        environment={},
    )
    assert report["status"] == "READY_FOR_OPTIMIZATION"
    assert report["ready_for_optimization"] is True


def test_preflight_blocks_missing_framework_and_accelerators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_preflight_config(tmp_path)
    monkeypatch.setattr(
        "gen_retry.rl.preflight.load_model_config",
        lambda _: _model_config(tmp_path),
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.checkpoint_fingerprint",
        lambda _: "sha256:b2377728e0cd748447e27a9583c1456121a20aff84da9468da14e9cb16cd2718",
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight._package_versions",
        lambda: {"torch": "test-version", "verl": None},
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight._probe_accelerator",
        lambda: {
            "checked": True,
            "available": False,
            "device_count": 0,
            "devices": [],
            "error": None,
        },
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.validate_frozen_rl_data",
        lambda **_: {
            "train": {"selected_count": 1000},
            "development": {"selected_count": 200},
            "confirmation": {"selected_count": 500},
        },
    )
    report = run_rl_preflight(
        config_path=config_path,
        model_config_path=tmp_path / "models.yaml",
        environment={},
    )
    assert report["status"] == "BLOCKED"
    blocked_ids = {
        check["check_id"]
        for check in report["checks"]
        if check["status"] == "BLOCKED"
    }
    assert {"package_verl", "accelerator_topology"} <= blocked_ids


def test_package_probe_rejects_empty_namespace_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "gen_retry.rl.preflight._REQUIRED_DISTRIBUTIONS",
        {"wandb": "wandb"},
    )

    def missing_distribution(_: str) -> str:
        from importlib.metadata import PackageNotFoundError

        raise PackageNotFoundError

    monkeypatch.setattr(
        "gen_retry.rl.preflight.importlib.metadata.version",
        missing_distribution,
    )
    monkeypatch.setattr(
        "gen_retry.rl.preflight.importlib.util.find_spec",
        lambda _: SimpleNamespace(loader=None),
    )
    assert _package_versions() == {"wandb": None}
