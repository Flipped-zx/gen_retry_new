from __future__ import annotations

import json
from pathlib import Path

from gen_retry.protocol.schema_loader import check_all_schemas, validate_instance


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def test_all_versioned_schemas_are_valid() -> None:
    checked = check_all_schemas()
    assert {path.name for path in checked} == {
        "action_protocol_v0_2.schema.json",
        "action_protocol_v0_3.schema.json",
        "action_protocol_v0_4.schema.json",
        "action_protocol_v0_5.schema.json",
        "artifact_manifest_v0_2.schema.json",
        "episode_event_v0_2.schema.json",
        "planner_context_v0_3.schema.json",
        "planner_context_v0_4.schema.json",
        "planner_context_v0_5.schema.json",
        "planner_context_v0_6.schema.json",
        "planner_context_v0_7.schema.json",
        "planner_view_v0_2.schema.json",
        "rl_advantage_batch_v0_1.schema.json",
        "rl_candidate_return_batch_v0_1.schema.json",
        "rl_experiment_declaration_v0_1.schema.json",
        "rl_live_adapter_evidence_v0_1.schema.json",
        "rl_prompt_manifest_v0_1.schema.json",
        "rl_rollout_sample_batch_v0_1.schema.json",
        "rl_runtime_check_report_v0_1.schema.json",
        "rl_smoke_report_v0_1.schema.json",
        "rl_terminal_reward_v0_1.schema.json",
        "task_spec_v0_2.schema.json",
    }


def test_task_spec_fixture_validates() -> None:
    fixture = ROOT / "tests" / "fixtures" / "task_spec" / "geneval2_minimal.json"
    validate_instance(load_json(fixture), "task_spec_v0_2.schema.json")


def test_artifact_manifest_fixture_validates() -> None:
    fixture = ROOT / "tests" / "fixtures" / "artifacts" / "demo_manifest.json"
    validate_instance(load_json(fixture), "artifact_manifest_v0_2.schema.json")


def test_rl_candidate_return_fixture_validates() -> None:
    fixture = ROOT / "tests" / "fixtures" / "rl" / "candidate_return_batch_minimal.json"
    validate_instance(load_json(fixture), "rl_candidate_return_batch_v0_1.schema.json")


def test_rl_rollout_sample_fixture_validates() -> None:
    fixture = ROOT / "tests" / "fixtures" / "rl" / "rollout_sample_batch_minimal.json"
    validate_instance(load_json(fixture), "rl_rollout_sample_batch_v0_1.schema.json")


def test_rl_data_freeze_fixtures_validate() -> None:
    prompt_manifest = ROOT / "tests" / "fixtures" / "rl_prompt_manifests" / "minimal.json"
    declaration = ROOT / "tests" / "fixtures" / "rl_experiment_declarations" / "minimal.json"
    validate_instance(load_json(prompt_manifest), "rl_prompt_manifest_v0_1.schema.json")
    validate_instance(load_json(declaration), "rl_experiment_declaration_v0_1.schema.json")
