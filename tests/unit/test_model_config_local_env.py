from __future__ import annotations

from pathlib import Path

from gen_retry.phase3.model_config import load_model_config


def test_model_config_loads_ignored_teacher_environment_without_overriding_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_dir = tmp_path / "configs" / "models"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "local.yaml"
    config_path.write_text(
        "\n".join(
            [
                "teacher:",
                "  provider: openai_compatible",
                "  model_id: gpt-5.5",
                "  api_key_env: TEACHER_API_KEY",
                "  base_url_env: TEACHER_BASE_URL",
                "image_backend:",
                "  provider: local",
                "  backend_id: qianwen_image_edit",
                "  model_id: Qwen-Image-Edit-2511",
                "  model_path: /tmp/qwen",
                "  supports:",
                "    generate: true",
                "    edit: true",
                "evaluator:",
                "  backend_id: geneval2",
                "  config_path: /tmp/geneval2",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / ".env.teacher.local").write_text(
        "TEACHER_API_KEY=local-test-key\n"
        "TEACHER_BASE_URL='http://teacher.test/v1'\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TEACHER_API_KEY", raising=False)
    monkeypatch.setenv("TEACHER_BASE_URL", "http://shell-wins.test/v1")

    config = load_model_config(config_path)

    assert config.teacher.model_id == "gpt-5.5"
    assert os_environ("TEACHER_API_KEY") == "local-test-key"
    assert os_environ("TEACHER_BASE_URL") == "http://shell-wins.test/v1"


def os_environ(name: str) -> str | None:
    import os

    return os.environ.get(name)
