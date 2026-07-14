from __future__ import annotations

import json
from pathlib import Path

from gen_retry.domain.artifacts import validate_artifact_manifest_closure
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
    assert (run_dir / "planner_views" / "planner_view_000.json").is_file()
    assert (run_dir / "manifest.json").is_file()

    task_spec = json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))
    assert task_spec["max_image_attempts"] == 5
    assert task_spec["episode_id"] == "phase3_ep_001"
    assert task_spec["constraints"][2]["constraint_type"] == "position"

    events = load_events_jsonl(run_dir / "events.jsonl")
    assert [event["event_type"] for event in events] == [
        "task_created",
        "planner_view_built",
    ]
    state = reduce_events(events)
    assert state.attempt_order == []
    assert state.best_attempt_id is None
    assert state.remaining_budget == 5

    planner_view = json.loads(
        (run_dir / "planner_views" / "planner_view_000.json").read_text(encoding="utf-8")
    )
    assert planner_view["latest_attempt"] is None
    assert planner_view["best_attempt"] is None
    assert planner_view["visible_images"] == []
    assert planner_view["remaining_budget"] == 5

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    validate_artifact_manifest_closure(manifest, run_dir)
    assert summary_path.is_file()
