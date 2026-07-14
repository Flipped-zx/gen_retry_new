from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.cli.replay_episode import replay
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.tools.fake_geneval2_adapter import FakeGeneval2Adapter
from gen_retry.tools.fake_qianwen_image_edit_adapter import FakeQianwenImageEditAdapter


ROOT = Path(__file__).resolve().parents[2]

EXPECTED_MOCK_CASES = {
    "direct_success": {
        "episode_id": "ep_mock_direct_success",
        "attempt_order": ["a_000"],
        "parents": {"a_000": None},
        "operations": {"a_000": "generate"},
        "best_attempt_id": "a_000",
        "submitted_attempt_id": "a_000",
        "submitted_reason_code": "all_constraints_passed",
        "remaining_budget": 2,
        "latest_transition": {
            "fixed": [],
            "regressed": [],
            "persistent_failed": [],
            "stable_pass": ["c_001", "c_002", "c_003", "c_004"],
        },
    },
    "regenerate": {
        "episode_id": "ep_mock_regenerate",
        "attempt_order": ["a_000", "a_001"],
        "parents": {"a_000": None, "a_001": None},
        "operations": {"a_000": "generate", "a_001": "generate"},
        "best_attempt_id": "a_001",
        "submitted_attempt_id": "a_001",
        "submitted_reason_code": "all_constraints_passed",
        "remaining_budget": 1,
        "latest_transition": {
            "fixed": ["c_001", "c_004"],
            "regressed": [],
            "persistent_failed": [],
            "stable_pass": ["c_002", "c_003"],
        },
    },
    "local_edit": {
        "episode_id": "ep_mock_local_edit",
        "attempt_order": ["a_000", "a_001"],
        "parents": {"a_000": None, "a_001": "a_000"},
        "operations": {"a_000": "generate", "a_001": "edit"},
        "best_attempt_id": "a_001",
        "submitted_attempt_id": "a_001",
        "submitted_reason_code": "all_constraints_passed",
        "remaining_budget": 1,
        "latest_transition": {
            "fixed": ["c_001"],
            "regressed": [],
            "persistent_failed": [],
            "stable_pass": ["c_002", "c_003", "c_004"],
        },
    },
    "branch_recovery": {
        "episode_id": "ep_mock_branch_recovery",
        "attempt_order": ["a_000", "a_001", "a_002"],
        "parents": {"a_000": None, "a_001": "a_000", "a_002": "a_000"},
        "operations": {"a_000": "generate", "a_001": "edit", "a_002": "edit"},
        "best_attempt_id": "a_002",
        "submitted_attempt_id": "a_002",
        "submitted_reason_code": "all_constraints_passed",
        "remaining_budget": 0,
        "latest_transition": {
            "fixed": ["c_001"],
            "regressed": [],
            "persistent_failed": [],
            "stable_pass": ["c_002", "c_003", "c_004"],
        },
    },
    "persistent_failure": {
        "episode_id": "ep_mock_persistent_failure",
        "attempt_order": ["a_000", "a_001"],
        "parents": {"a_000": None, "a_001": "a_000"},
        "operations": {"a_000": "generate", "a_001": "edit"},
        "best_attempt_id": "a_000",
        "submitted_attempt_id": "a_000",
        "submitted_reason_code": "best_available_under_budget",
        "remaining_budget": 1,
        "latest_transition": {
            "fixed": [],
            "regressed": [],
            "persistent_failed": ["c_001", "c_004"],
            "stable_pass": ["c_002", "c_003"],
        },
    },
}


def test_fake_qianwen_adapter_is_deterministic() -> None:
    adapter = FakeQianwenImageEditAdapter()
    first = adapter.generate(request_id="req_1", attempt_id="a_000", image_artifact_id="img_000")
    second = adapter.generate(request_id="req_1", attempt_id="a_000", image_artifact_id="img_000")

    assert first == second
    assert first.backend == "qianwen_image_edit"
    assert first.parent_attempt_id is None
    assert len(first.artifact_sha256) == 64
    int(first.artifact_sha256, 16)


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
    assert {case["case_id"] for case in manifest["cases"]} == set(EXPECTED_MOCK_CASES)

    episode_ids = set()
    for case in manifest["cases"]:
        expected = EXPECTED_MOCK_CASES[case["case_id"]]
        path = ROOT / case["events"]
        first = replay(path)
        second = replay(path)
        state = first["state"]
        assert canonical_json(first["state"]) == canonical_json(second["state"])
        assert state["episode_id"] == expected["episode_id"]
        assert state["attempt_order"] == expected["attempt_order"]
        assert state["best_attempt_id"] == expected["best_attempt_id"]
        assert state["submitted_attempt_id"] == expected["submitted_attempt_id"]
        assert state["submitted_reason_code"] == expected["submitted_reason_code"]
        assert state["remaining_budget"] == expected["remaining_budget"]
        assert {
            attempt_id: state["attempts"][attempt_id]["parent_attempt_id"]
            for attempt_id in state["attempt_order"]
        } == expected["parents"]
        assert {
            attempt_id: state["attempts"][attempt_id]["operation"]
            for attempt_id in state["attempt_order"]
        } == expected["operations"]
        assert {
            key: state["latest_transition"][key]
            for key in ("fixed", "regressed", "persistent_failed", "stable_pass")
        } == expected["latest_transition"]
        episode_ids.add(state["episode_id"])

    assert len(episode_ids) == len(EXPECTED_MOCK_CASES)
