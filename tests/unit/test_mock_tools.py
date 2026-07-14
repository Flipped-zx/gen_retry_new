from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.cli.replay_episode import replay
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.tools.fake_geneval2_adapter import FakeGeneval2Adapter
from gen_retry.tools.fake_qianwen_image_edit_adapter import FakeQianwenImageEditAdapter


ROOT = Path(__file__).resolve().parents[2]


def test_fake_qianwen_adapter_is_deterministic() -> None:
    adapter = FakeQianwenImageEditAdapter()
    first = adapter.generate(request_id="req_1", attempt_id="a_000", image_artifact_id="img_000")
    second = adapter.generate(request_id="req_1", attempt_id="a_000", image_artifact_id="img_000")

    assert first == second
    assert first.backend == "qianwen_image_edit"
    assert first.parent_attempt_id is None


def test_fake_geneval2_adapter_requires_full_constraint_coverage() -> None:
    task_spec = json.loads(
        (ROOT / "tests" / "fixtures" / "task_spec" / "geneval2_minimal.json").read_text(
            encoding="utf-8"
        )
    )
    adapter = FakeGeneval2Adapter(
        {
            "a_000": [
                {"constraint_id": "c_001", "status": "pass"},
            ]
        }
    )

    with pytest.raises(ValueError, match="constraint coverage mismatch"):
        adapter.evaluate(task_spec=task_spec, attempt_id="a_000")


def test_all_mock_episode_fixtures_replay_deterministically() -> None:
    manifest = json.loads(
        (ROOT / "tests" / "fixtures" / "mock_episodes" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(manifest["cases"]) == 5

    for case in manifest["cases"]:
        path = ROOT / case["events"]
        first = replay(path)
        second = replay(path)
        assert canonical_json(first["state"]) == canonical_json(second["state"])
        assert first["state"]["episode_id"] == "ep_demo_001"
