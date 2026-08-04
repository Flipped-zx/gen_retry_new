from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.phase3.live_runner import (
    Phase3LiveRunner,
    RuntimeActionError,
    _compact_operator_summary,
    _pending_image_start,
)
from gen_retry.runtime.planner_view import DEFAULT_SKILL_MANIFEST
from gen_retry.tools.skill_store import LocalSkillStore, SKILL_VERSIONS


ROOT = Path(__file__).resolve().parents[2]


def test_default_skill_manifest_versions_and_content_hashes_match_store() -> None:
    store = LocalSkillStore(ROOT / "skills")
    exposed_ids = {entry["skill_id"] for entry in DEFAULT_SKILL_MANIFEST}

    assert exposed_ids == set(SKILL_VERSIONS)
    assert {
        "action_pose_relation",
        "object_identity_presence",
    } <= exposed_ids
    assert not {
        "attribute_binding",
        "constraint_preservation",
        "counting_edit",
        "counting_layout",
        "spatial_relation",
    } & exposed_ids
    for entry in DEFAULT_SKILL_MANIFEST:
        record = store.get(entry["skill_id"])
        assert record.version == entry["version"]
        assert record.content_sha256 == sha256_bytes(record.content.encode("utf-8"))
        assert "TODO" not in record.content


def test_action_pose_relation_v2_1_encodes_typed_retry_topology() -> None:
    record = LocalSkillStore(ROOT / "skills").get("action_pose_relation")

    assert record.version == "2.1.0"
    assert "### Chasing operator" in record.content
    assert "lateral or three-quarter lateral action lane" in record.content
    assert "### Playing-with operator" in record.content
    assert "### Jumping-over operator" in record.content
    assert "### Verb-pass preservation" in record.content
    assert "Each appears exactly once" in record.content
    assert "storyboard" in record.content


def test_action_pose_relation_manifest_defers_retrieval_until_retry() -> None:
    entry = next(
        item
        for item in DEFAULT_SKILL_MANIFEST
        if item["skill_id"] == "action_pose_relation"
    )

    assert entry["version"] == "2.1.0"
    assert "after an evaluated verb failure or uncertainty" in entry["description"]
    assert "not an initial-generation prefix" in entry["description"]


def test_action_pose_relation_v2_1_survives_compact_round_memory() -> None:
    record = LocalSkillStore(ROOT / "skills").get("action_pose_relation")
    compact = _compact_operator_summary(
        skill_id=record.skill_id,
        version=record.version,
        content_sha256=record.content_sha256,
        content=record.content,
    )

    assert len(record.summary) <= 400
    assert "Chasing uses one lateral pursuer/target pair" in record.summary
    assert len(compact) <= 400
    assert all(
        operator in compact
        for operator in (
            "Chasing",
            "Playing with",
            "Jumping over",
            "Preservation",
            "Layout",
        )
    )


def _runner() -> Phase3LiveRunner:
    runner = Phase3LiveRunner.__new__(Phase3LiveRunner)

    class Store:
        def get(self, skill_id: str):
            return type(
                "Skill",
                (),
                {
                    "skill_id": skill_id,
                    "version": "1.0.0",
                    "content_sha256": "abc123" * 10 + "abcd",
                    "content": (
                        f"# Skill: {skill_id}\n\n"
                        "### Operators\n"
                        "- Use exact totals.\n"
                        "- Keep visible gaps.\n"
                        "- Preserve stable evidence.\n"
                        "- State chasing and facing cues.\n"
                    )
                },
            )()

    runner.skill_store = Store()
    return runner


def _write_skill_observation(run_dir, event_id: str, skills: list[dict]) -> None:
    records = [
        {
            "schema_version": "0.2",
            "event_id": event_id,
            "observation_type": "skill_returned",
            "skills": skills,
        }
    ]
    (run_dir / "tool_observations.jsonl").write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_retrieved_skills_enter_only_direct_next_view_context(tmp_path) -> None:
    runner = _runner()
    content = "# Skill\n\n### Operators\n- Retrieval-time operator.\n"
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "skill_returned",
            "payload": {
                "skills": [
                        {
                            "skill_id": "counting_and_instance_layout",
                            "version": "1.0.0",
                            "content_sha256": sha256_bytes(content.encode("utf-8")),
                        }
                    ]
                },
        },
        {
            "event_id": "evt_0002",
            "event_type": "planner_view_built",
            "input_refs": ["evt_0001"],
        },
        {
            "event_id": "evt_0003",
            "event_type": "memory_reduced",
            "payload": {},
        },
        {
            "event_id": "evt_0004",
            "event_type": "planner_view_built",
            "input_refs": ["evt_0003"],
        },
    ]
    _write_skill_observation(
        tmp_path,
        "evt_0001",
        [
            {
                "skill_id": "counting_and_instance_layout",
                "version": "1.0.0",
                "content_sha256": sha256_bytes(content.encode("utf-8")),
                "content": content,
            }
        ],
    )

    direct = runner._retrieved_skills(tmp_path, events, events[1])
    later = runner._retrieved_skills(tmp_path, events, events[3])

    assert [skill["skill_id"] for skill in direct] == ["counting_and_instance_layout"]
    assert direct[0]["content"] == content
    assert later == []


def test_query_skill_runtime_limits() -> None:
    runner = _runner()
    state = type("State", (), {"attempt_order": ["a_000"], "remaining_budget": 4})()

    too_many = {
        "action": "query_skill",
        "arguments": {
            "skill_ids": [
                "counting_and_instance_layout",
                "spatial_relation_layout",
                "attribute_entity_binding",
                "object_identity_presence",
            ],
            "target_constraint_ids": ["c_001"],
        },
    }
    with pytest.raises(RuntimeActionError, match="at most three"):
        runner._validate_runtime_action(too_many, state, [], events=[])

    repeated = {
        "action": "query_skill",
        "arguments": {
            "skill_ids": ["counting_and_instance_layout"],
            "target_constraint_ids": ["c_001"],
        },
    }
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "skill_returned",
            "payload": {
                "skills": [
                    {
                        "skill_id": "counting_and_instance_layout",
                        "version": "1.0.0",
                    }
                ]
            },
        }
    ]
    with pytest.raises(RuntimeActionError, match="at most once"):
        runner._validate_runtime_action(repeated, state, [], events=events)

    consecutive_events = [
        {
            "event_id": "evt_0001",
            "event_type": "action_validated",
            "payload": {
                "action": {
                    "action": "query_skill",
                    "arguments": {
                        "skill_ids": ["spatial_relation_layout"],
                        "target_constraint_ids": ["c_001"],
                    },
                }
            },
        },
        {
            "event_id": "evt_0002",
            "event_type": "skill_returned",
            "payload": {
                "query_action_event_id": "evt_0001",
                "skills": [
                    {
                        "skill_id": "spatial_relation_layout",
                        "version": "1.0.0",
                    }
                ],
            },
        },
    ]
    novel_second_query = {
        "action": "query_skill",
        "arguments": {
            "skill_ids": ["object_identity_presence"],
            "target_constraint_ids": ["c_001"],
        },
    }
    runner._validate_runtime_action(
        novel_second_query,
        state,
        [],
        events=consecutive_events,
    )

    two_completed_queries = [
        *consecutive_events,
        {
            "event_id": "evt_0003",
            "event_type": "action_validated",
            "payload": {"action": novel_second_query},
        },
        {
            "event_id": "evt_0004",
            "event_type": "skill_returned",
            "payload": {
                "query_action_event_id": "evt_0003",
                "skills": [
                    {
                        "skill_id": "object_identity_presence",
                        "version": "1.0.0",
                    }
                ],
            },
        },
    ]
    third_query = {
        "action": "query_skill",
        "arguments": {
            "skill_ids": ["attribute_entity_binding"],
            "target_constraint_ids": ["c_001"],
        },
    }
    with pytest.raises(RuntimeActionError, match="at most two"):
        runner._validate_runtime_action(
            third_query,
            state,
            [],
            events=two_completed_queries,
        )


def test_query_skill_rejects_new_action_while_tool_response_is_pending() -> None:
    runner = _runner()
    state = type("State", (), {"attempt_order": [], "remaining_budget": 5})()
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "action_validated",
            "payload": {
                "action": {
                    "action": "query_skill",
                    "arguments": {
                        "skill_ids": ["spatial_relation_layout"],
                        "target_constraint_ids": ["c_001"],
                    },
                }
            },
        }
    ]
    action = {
        "action": "query_skill",
        "arguments": {
            "skill_ids": ["object_identity_presence"],
            "target_constraint_ids": ["c_001"],
        },
    }

    with pytest.raises(RuntimeActionError, match="tool response"):
        runner._validate_runtime_action(action, state, [], events=events)


def test_incomplete_query_skill_resumes_tool_response_before_planning(
    tmp_path,
) -> None:
    runner = _runner()
    action_event = {
        "event_id": "evt_0001",
        "event_type": "action_validated",
        "turn_id": "turn_000",
        "payload": {
            "action": {
                "action": "query_skill",
                "arguments": {
                    "skill_ids": ["spatial_relation_layout"],
                    "target_constraint_ids": ["c_001"],
                },
            }
        },
    }
    observed: dict[str, object] = {}

    def execute_skill(run_dir, event):
        observed["action_event"] = event
        return {"event_id": "evt_0002"}

    def build_context(run_dir, *, input_refs):
        observed["input_refs"] = input_refs

    runner._execute_skill = execute_skill
    runner._build_next_planner_context = build_context

    assert runner._recover_incomplete_skill_query(
        tmp_path,
        events=[action_event],
    )
    assert observed == {
        "action_event": action_event,
        "input_refs": ["evt_0002"],
    }


def test_active_skill_operator_retention_and_grounding(tmp_path) -> None:
    runner = _runner()
    state = type("State", (), {"attempt_order": ["a_000"], "remaining_budget": 4})()
    content = (
        "# Skill\n\n"
        "### Operators\n"
        "- Use exact totals.\n"
        "- Keep visible gaps.\n"
        "- Preserve stable evidence.\n"
        "- State chasing and facing cues.\n"
    )
    content_sha = sha256_bytes(content.encode("utf-8"))
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "skill_returned",
            "payload": {
                "skills": [
                    {
                        "skill_id": "counting_and_instance_layout",
                        "version": "1.0.0",
                        "content_sha256": content_sha,
                    }
                ]
            },
        }
    ]
    _write_skill_observation(
        tmp_path,
        "evt_0001",
        [
            {
                "skill_id": "counting_and_instance_layout",
                "version": "1.0.0",
                "content_sha256": content_sha,
                "content": content,
            }
        ],
    )
    summaries = runner._active_skill_operator_summaries(tmp_path, events)

    assert summaries[0]["failure_signature"] == "active_skill_operator:counting_and_instance_layout"
    assert "preferred_action" not in summaries[0]
    assert "Use exact totals" in summaries[0]["summary"]
    assert "chasing and facing" in summaries[0]["summary"]
    assert content_sha[:12] in summaries[0]["summary"]
    assert len(summaries[0]["summary"]) <= 400

    action = {
        "action": "generate_image",
        "arguments": {
            "target_constraint_ids": ["c_001"],
        },
    }
    runner._validate_runtime_action(action, state, [], events=events)


def test_active_skill_operator_summary_uses_retrieval_time_content(tmp_path) -> None:
    runner = _runner()
    content = "# Skill\n\n### Operators\n- Retrieval-time only operator.\n"
    content_sha = sha256_bytes(content.encode("utf-8"))
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "skill_returned",
            "payload": {
                "skills": [
                    {
                        "skill_id": "counting_and_instance_layout",
                        "version": "1.0.0",
                        "content_sha256": content_sha,
                    }
                ]
            },
        }
    ]
    _write_skill_observation(
        tmp_path,
        "evt_0001",
        [
            {
                "skill_id": "counting_and_instance_layout",
                "version": "1.0.0",
                "content_sha256": content_sha,
                "content": content,
            }
        ],
    )

    summaries = runner._active_skill_operator_summaries(tmp_path, events)

    assert "Retrieval-time only operator" in summaries[0]["summary"]
    assert "Use exact totals" not in summaries[0]["summary"]


def test_skill_requery_allows_changed_identity() -> None:
    runner = _runner()

    class ChangedStore:
        def get(self, skill_id: str):
            return type(
                "Skill",
                (),
                {
                    "skill_id": skill_id,
                    "version": "1.0.1",
                    "content_sha256": "def456" * 10 + "def0",
                    "content": "# Skill\n",
                },
            )()

    runner.skill_store = ChangedStore()
    state = type("State", (), {"attempt_order": ["a_000"], "remaining_budget": 4})()
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "skill_returned",
            "payload": {
                "skills": [
                    {
                        "skill_id": "counting_and_instance_layout",
                        "version": "1.0.0",
                        "content_sha256": "abc123" * 10 + "abcd",
                    }
                ]
            },
        }
    ]
    action = {
        "action": "query_skill",
        "arguments": {
            "skill_ids": ["counting_and_instance_layout"],
            "target_constraint_ids": ["c_001"],
        },
    }

    runner._validate_runtime_action(action, state, [], events=events)


def test_pending_image_start_detects_unfinished_attempt() -> None:
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "image_execution_started",
            "payload": {"request_id": "ep_a_000_generate"},
        },
        {
            "event_id": "evt_0002",
            "event_type": "image_execution_completed",
            "payload": {"request_id": "ep_a_000_generate"},
        },
        {
            "event_id": "evt_0003",
            "event_type": "planner_view_built",
            "payload": {},
        },
        {
            "event_id": "evt_0004",
            "event_type": "image_execution_started",
            "payload": {"request_id": "ep_a_001_edit"},
        },
    ]

    assert _pending_image_start(events) == events[-1]


def test_pending_image_start_ignores_completed_attempts() -> None:
    events = [
        {
            "event_id": "evt_0001",
            "event_type": "image_execution_started",
            "payload": {"request_id": "ep_a_000_generate"},
        },
        {
            "event_id": "evt_0002",
            "event_type": "image_execution_completed",
            "payload": {"request_id": "ep_a_000_generate"},
        },
    ]

    assert _pending_image_start(events) is None
