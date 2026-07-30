from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gen_retry.domain.artifacts import validate_artifact_manifest_closure
from gen_retry.domain.score_policy import primary_score_policy
from gen_retry.phase3.rollout_prep import prepare_rollout_runs
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.reducer import reduce_events


def _selected_payload() -> dict:
    return {
        "schema_version": "0.2",
        "selection_method": "unit",
        "selected_count": 1,
        "selected_prompts": [
            {
                "candidate_id": "cand_001",
                "prompt_id": "prompt_001",
                "selection_rank": 1,
                "original_prompt": "two red cubes left of a blue sphere",
                "atomic_constraints": [
                    {
                        "constraint_id": "c_001",
                        "constraint_type": "count",
                        "requirement": "Expected answer: two",
                        "evaluator_question": "How many cubes are in the image?",
                        "priority": 3,
                    },
                    {
                        "constraint_id": "c_002",
                        "constraint_type": "attribute",
                        "requirement": "Expected answer: Yes",
                        "evaluator_question": "Are the cubes red?",
                        "priority": 3,
                    },
                    {
                        "constraint_id": "c_003",
                        "constraint_type": "position",
                        "requirement": "Expected answer: Yes",
                        "evaluator_question": "Are the cubes left of the sphere?",
                        "priority": 3,
                    },
                ],
                "constraint_type_histogram": {"count": 1, "attribute": 1, "position": 1},
                "provenance": {"source": "unit", "source_ref": "unit:1"},
            }
        ],
    }


def test_prepare_rollout_runs_can_limit_existing_selection(tmp_path: Path) -> None:
    payload = _selected_payload()
    second = dict(payload["selected_prompts"][0])
    second.update(
        {
            "candidate_id": "cand_002",
            "prompt_id": "prompt_002",
            "selection_rank": 2,
            "original_prompt": "a green sphere above a red cube",
        }
    )
    payload["selected_prompts"].append(second)
    payload["selected_count"] = 2
    selected_path = tmp_path / "selected_ten_prompts.json"
    selected_path.write_text(json.dumps(payload), encoding="utf-8")

    summary = prepare_rollout_runs(
        selected_prompts_path=selected_path,
        output_root=tmp_path / "runs",
        summary_output=tmp_path / "prepared_rollouts.json",
        limit=1,
    )

    assert summary["prepared_count"] == 1
    assert summary["selected_prompt_limit"] == 1
    assert [episode["episode_id"] for episode in summary["episodes"]] == ["phase3_ep_001"]
    assert (tmp_path / "runs" / "phase3_ep_001" / "task_spec.json").is_file()
    assert not (tmp_path / "runs" / "phase3_ep_002").exists()


def test_prepare_rollout_runs_materializes_fresh_replayable_episode(tmp_path: Path) -> None:
    selected_path = tmp_path / "selected_ten_prompts.json"
    selected_path.write_text(json.dumps(_selected_payload()), encoding="utf-8")
    summary_path = tmp_path / "prepared_rollouts.json"

    summary = prepare_rollout_runs(
        selected_prompts_path=selected_path,
        output_root=tmp_path / "runs",
        summary_output=summary_path,
        max_image_attempts=5,
    )

    assert summary["prepared_count"] == 1
    episode = summary["episodes"][0]
    assert episode["episode_id"] == "phase3_ep_001"
    assert episode["first_live_action_must_not_be_edit"] is True
    run_dir = Path(episode["run_dir"])
    assert (run_dir / "task_spec.json").is_file()
    assert (run_dir / "events.jsonl").is_file()
    assert (run_dir / "planner_contexts" / "planner_context_000.json").is_file()
    assert (run_dir / "manifest.json").is_file()

    task_spec = json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))
    assert task_spec["max_image_attempts"] == 5
    assert task_spec["episode_id"] == "phase3_ep_001"
    assert task_spec["constraints"][2]["constraint_type"] == "position"

    events = load_events_jsonl(run_dir / "events.jsonl")
    assert [event["event_type"] for event in events] == [
        "task_created",
        "planner_context_built",
    ]
    state = reduce_events(events)
    assert state.attempt_order == []
    assert state.best_attempt_id is None
    assert state.remaining_budget == 5

    planner_context = json.loads(
        (run_dir / "planner_contexts" / "planner_context_000.json").read_text(encoding="utf-8")
    )
    assert planner_context["latest_attempt"] is None
    assert planner_context["planner_context_schema_version"] == "0.6"
    assert planner_context["episode_memory"]["best_attempt"] is None
    assert planner_context["runtime_state"]["remaining_image_budget"] == 5
    assert planner_context["runtime_state"]["available_actions"] == ["query_skill", "generate_image"]
    assert planner_context["runtime_state"]["score_policy"] == primary_score_policy()
    assert events[0]["payload"]["score_policy"] == primary_score_policy()
    assert events[1]["payload"]["planner_context_schema_version"] == "0.6"

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    validate_artifact_manifest_closure(manifest, run_dir)
    assert summary_path.is_file()


def test_prepare_rollout_runs_refuses_non_empty_episode_directory(tmp_path: Path) -> None:
    selected_path = tmp_path / "selected_ten_prompts.json"
    selected_path.write_text(json.dumps(_selected_payload()), encoding="utf-8")
    occupied = tmp_path / "runs" / "phase3_ep_001"
    occupied.mkdir(parents=True)
    (occupied / "keep.txt").write_text("user-owned", encoding="utf-8")

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        prepare_rollout_runs(
            selected_prompts_path=selected_path,
            output_root=tmp_path / "runs",
            summary_output=tmp_path / "prepared_rollouts.json",
        )

    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "user-owned"


def test_prepare_rollout_runs_locks_dual_execution_profile(tmp_path: Path) -> None:
    selected_path = tmp_path / "selected_ten_prompts.json"
    selected_path.write_text(json.dumps(_selected_payload()), encoding="utf-8")

    summary = prepare_rollout_runs(
        selected_prompts_path=selected_path,
        output_root=tmp_path / "runs",
        summary_output=tmp_path / "prepared_rollouts.json",
        execution_profile_id="qwen_dual_backend",
        execution_profile_version="1",
    )

    run_dir = Path(summary["episodes"][0]["run_dir"])
    plan = json.loads((run_dir / "rollout_plan.json").read_text(encoding="utf-8"))
    assert plan["execution_profile"] == {
        "profile_id": "qwen_dual_backend",
        "profile_version": "1",
    }
    assert plan["selection_artifact"] == {
        "ref": str(selected_path),
        "sha256": summary["selected_prompts_sha256"],
    }
    assert summary["episodes"][0]["selection_artifact"] == plan[
        "selection_artifact"
    ]


def test_prepare_rollout_runs_filters_exact_prompt_ids(tmp_path: Path) -> None:
    selected_path = tmp_path / "selected.json"
    payload = _selected_payload()
    second = copy.deepcopy(payload["selected_prompts"][0])
    second.update(
        {
            "selection_rank": 8,
            "candidate_id": "candidate_008",
            "prompt_id": "prompt_008",
            "original_prompt": "a second prompt",
        }
    )
    payload["selected_prompts"].append(second)
    selected_path.write_text(json.dumps(payload), encoding="utf-8")

    summary = prepare_rollout_runs(
        selected_prompts_path=selected_path,
        output_root=tmp_path / "runs",
        summary_output=tmp_path / "summary.json",
        prompt_ids=["prompt_008"],
    )

    assert summary["prepared_count"] == 1
    assert summary["selected_prompt_ids"] == ["prompt_008"]
    assert summary["episodes"][0]["episode_id"] == "phase3_ep_008"
    assert not (tmp_path / "runs" / "phase3_ep_001").exists()


def test_prepare_rollout_runs_rejects_unknown_prompt_id(tmp_path: Path) -> None:
    selected_path = tmp_path / "selected.json"
    selected_path.write_text(json.dumps(_selected_payload()), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown prompt_ids"):
        prepare_rollout_runs(
            selected_prompts_path=selected_path,
            output_root=tmp_path / "runs",
            summary_output=tmp_path / "summary.json",
            prompt_ids=["missing"],
        )
