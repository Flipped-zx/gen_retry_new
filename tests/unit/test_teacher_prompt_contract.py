from __future__ import annotations

import json
from pathlib import Path

from gen_retry.agent.instruction_quality import evaluate_instruction_quality
from gen_retry.agent.teacher_client import (
    AVAILABLE_SKILL_IDS,
    OpenAICompatibleTeacherClient,
    TeacherImageRef,
    TEACHER_SYSTEM_PROMPT_TEXT,
    TEACHER_SYSTEM_PROMPT_VERSION,
    teacher_system_prompt_sha256,
)
from gen_retry.phase3.live_runner import (
    Phase3LiveRunner,
    RuntimeActionError,
    _advisory_instruction_quality,
    _execution_instruction,
)
from gen_retry.phase3.model_config import TeacherConfig
from gen_retry.runtime.reducer import AttemptRecord, EpisodeState


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
    b"\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _client() -> OpenAICompatibleTeacherClient:
    return OpenAICompatibleTeacherClient(
        TeacherConfig(
            provider="openai_compatible",
            model_id="gpt-5.5",
            api_key_env="TEACHER_API_KEY",
            base_url_env="TEACHER_BASE_URL",
        )
    )


def _task_spec() -> dict:
    return {
        "schema_version": "0.2",
        "episode_id": "ep_test",
        "original_prompt": "two red cats behind one blue cube",
        "max_image_attempts": 5,
        "constraints": [
            {
                "constraint_id": "c_001",
                "constraint_type": "count",
                "requirement": "Expected answer: two",
                "evaluator_question": "How many cats are there?",
            },
            {
                "constraint_id": "c_002",
                "constraint_type": "position",
                "requirement": "Expected answer: Yes",
                "evaluator_question": "Are the cats behind the cube?",
            },
            {
                "constraint_id": "c_003",
                "constraint_type": "attribute",
                "requirement": "Expected answer: Yes",
                "evaluator_question": "Are the cats red?",
            },
            {
                "constraint_id": "c_004",
                "constraint_type": "attribute",
                "requirement": "Expected answer: Yes",
                "evaluator_question": "Is the cube blue?",
            },
        ],
    }


def _planner_context() -> dict:
    return {
        "task_context": {
            "original_prompt": "two red cats behind one blue cube",
            "max_image_attempts": 5,
            "atom_constraints": [
                {
                    "constraint_id": constraint["constraint_id"],
                    "constraint_type": constraint["constraint_type"],
                    "requirement": constraint["requirement"],
                    "evaluator_question": constraint["evaluator_question"],
                }
                for constraint in _task_spec()["constraints"]
            ],
        },
        "latest_attempt": {
            "attempt_id": "a_001",
            "constraint_results": {
                "passed_constraint_ids": ["c_001"],
                "failed_constraint_ids": ["c_002"],
                "uncertain_constraint_ids": [],
                "observations": [
                    {"constraint_id": "c_001", "status": "pass", "observed_value": "2"},
                    {"constraint_id": "c_002", "status": "fail", "observed_value": "no"},
                ],
            },
        },
        "skill_context": {
            "active_skills": [
                {
                    "skill_id": "counting_and_instance_layout",
                    "target_constraint_ids": ["c_001"],
                    "guidance": "active operators: exact totals; visible gaps",
                    "guidance_level": "summary",
                }
            ]
        },
        "episode_memory": {
            "last_completed_image_round": None,
            "prior_image_rounds": [],
            "best_attempt": {
                "attempt_id": "a_000",
                "constraint_results": {
                    "passed_constraint_ids": ["c_001"],
                    "failed_constraint_ids": ["c_002"],
                    "uncertain_constraint_ids": [],
                    "observations": [
                        {"constraint_id": "c_001", "status": "pass", "observed_value": "2"},
                        {"constraint_id": "c_002", "status": "fail", "observed_value": "no"},
                    ],
                },
            },
        },
        "runtime_state": {
            "remaining_image_budget": 3,
            "available_actions": ["query_skill", "generate_image", "edit_image", "submit_attempt"],
        },
    }


def test_teacher_messages_label_actual_latest_and_best_images(tmp_path: Path) -> None:
    latest = tmp_path / "latest.png"
    best = tmp_path / "best.png"
    latest.write_bytes(PNG_1X1)
    best.write_bytes(PNG_1X1)
    client = _client()

    messages = client._messages(
        planner_context=_planner_context(),
        task_spec=_task_spec(),
        image_refs=[
            TeacherImageRef("latest", "a_001", "img_001", latest),
            TeacherImageRef("best", "a_000", "img_000", best),
        ],
        retrieved_skills=[],
        extra_observations=[],
    )

    assert messages[0]["content"]
    content = messages[1]["content"]
    text = content[0]["text"]
    assert "LATEST_IMAGE: attempt a_001, artifact img_001" in text
    assert "BEST_IMAGE: attempt a_000, artifact img_000" in text
    assert "Latest equals best:" in text
    assert "false" in text
    assert "counting_and_instance_layout" in text
    assert "active operators: exact totals" in text
    assert set(AVAILABLE_SKILL_IDS) == {
        "counting_and_instance_layout",
        "spatial_relation_layout",
        "attribute_entity_binding",
        "local_edit_preservation",
        "action_pose_relation",
        "object_identity_presence",
    }
    assert all(skill_id in messages[0]["content"] for skill_id in AVAILABLE_SKILL_IDS)
    assert "Available query_skill catalog" in text
    assert [part["type"] for part in content].count("image_url") == 2
    assert content[2]["image_url"]["url"].startswith("data:image/png;base64,")
    assert content[4]["image_url"]["url"].startswith("data:image/png;base64,")


def test_teacher_prompt_versions_meaningful_retry_and_verb_retention_policy() -> None:
    assert (
        TEACHER_SYSTEM_PROMPT_VERSION
        == "teacher_system_prompt_v9_meaningful_retry_verb_retention"
    )
    assert "not perform a blind retry" in (
        TEACHER_SYSTEM_PROMPT_TEXT
    )
    assert "Reusing the same action, source attempt, or target constraint set is allowed" in (
        TEACHER_SYSTEM_PROMPT_TEXT
    )
    assert "default source_attempt_id to the reducer-best attempt" in TEACHER_SYSTEM_PROMPT_TEXT
    assert "Do not query action_pose_relation before any evaluated image exists" in (
        TEACHER_SYSTEM_PROMPT_TEXT
    )
    assert "matches the reducer-best passed-atom count" in TEACHER_SYSTEM_PROMPT_TEXT
    assert "Include the passed verb in preserve_constraint_ids" in (
        TEACHER_SYSTEM_PROMPT_TEXT
    )


def test_sanitized_request_records_prompt_hash_and_redacts_paths(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(PNG_1X1)
    client = _client()

    record = client.sanitized_request_record(
        request_id="ep_test_turn_001",
        task_spec=_task_spec(),
        planner_context=_planner_context(),
        planner_context_ref="planner_contexts/planner_context_001.json",
        planner_context_sha256="0" * 64,
        image_refs=[TeacherImageRef("latest", "a_001", "img_001", image)],
        retrieved_skills=[],
        extra_observations=[],
    )

    payload = json.dumps(record)
    assert record["system_prompt_version"] == TEACHER_SYSTEM_PROMPT_VERSION
    assert record["system_prompt_sha256"] == teacher_system_prompt_sha256()
    assert "teacher_text_input" in record
    assert str(image) not in payload
    assert "path_ref_sha256" in payload
    assert "sk-" not in payload


def test_instruction_quality_passes_concrete_edit_and_rejects_vague_edit() -> None:
    concrete = {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_000",
            "target_constraint_ids": ["c_001", "c_002"],
            "preserve_constraint_ids": ["c_003"],
            "instruction": (
                "Edit attempt a_000: remove extra cats so exactly two red cats remain, "
                "fully visible and separated. Reposition both cats behind the blue cube "
                "in the background with the cube in the foreground. Preserve the cube "
                "color and composition. Do not add extra cats or redraw unrelated objects."
            ),
        },
    }
    vague = {
        **concrete,
        "arguments": {
            **concrete["arguments"],
            "instruction": "Modify only the failed parts and preserve all correct evidence.",
        },
    }

    assert evaluate_instruction_quality(concrete, _task_spec(), known_attempt_ids=["a_000"]).verdict == "pass"
    report = evaluate_instruction_quality(vague, _task_spec(), known_attempt_ids=["a_000"])
    assert report.verdict == "reject"
    assert "modify only the failed parts" in report.vague_language_flags


def test_instruction_quality_rejects_missing_entity_attribute_and_prohibition() -> None:
    action = {
        "schema_version": "0.5",
        "action": "generate_image",
        "arguments": {
            "target_constraint_ids": ["c_001", "c_002", "c_003", "c_004"],
            "preserve_constraint_ids": [],
            "instruction": "Create exactly two animals behind one object.",
        },
    }

    report = evaluate_instruction_quality(action, _task_spec(), known_attempt_ids=[])

    assert report.verdict == "reject"
    assert any(item["entity"] == "cats" and not item["covered"] for item in report.required_entity_coverage)
    assert any(item["attribute"] == "red" and not item["covered"] for item in report.attribute_coverage)
    assert report.forbidden_change_coverage["covered"] is False


def test_instruction_quality_rejects_incompatible_counts_and_depth_contradiction() -> None:
    action = {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_000",
            "target_constraint_ids": ["c_001", "c_002"],
            "preserve_constraint_ids": ["c_003", "c_004"],
            "instruction": (
                "Edit attempt a_000: show exactly three red cats behind and in front of "
                "the blue cube. Preserve the cube unchanged. Do not add extra objects."
            ),
        },
    }

    report = evaluate_instruction_quality(action, _task_spec(), known_attempt_ids=["a_000"])

    assert report.verdict == "reject"
    assert report.incompatible_count_flags
    assert report.contradiction_flags


def test_instruction_quality_uses_entity_boundaries_and_ignores_other_entity_counts() -> None:
    task_spec = {
        "original_prompt": "a bird playing with six cows under seven suitcases",
        "constraints": [
            {
                "constraint_id": "c_001",
                "constraint_type": "count",
                "requirement": "Expected answer: one",
                "evaluator_question": "How many birds are in the image?",
            },
            {
                "constraint_id": "c_002",
                "constraint_type": "count",
                "requirement": "Expected answer: six",
                "evaluator_question": "How many cows are in the image?",
            },
            {
                "constraint_id": "c_003",
                "constraint_type": "count",
                "requirement": "Expected answer: seven",
                "evaluator_question": "How many suitcases are in the image?",
            },
        ],
    }
    action = {
        "action": "generate_image",
        "arguments": {
            "target_constraint_ids": ["c_001", "c_002", "c_003"],
            "preserve_constraint_ids": [],
            "instruction": (
                "Create exactly one bird near the six cows and exactly seven suitcases. "
                "Keep all instances uncropped, separated, and fully visible with no extras."
            ),
        },
    }

    report = evaluate_instruction_quality(action, task_spec)

    assert report.incompatible_count_flags == []
    assert report.unsupported_content_flags == []


def test_instruction_quality_ignores_sublayout_and_negated_counts() -> None:
    task_spec = {
        "original_prompt": "six cows under seven suitcases",
        "constraints": [
            {
                "constraint_id": "c_001",
                "constraint_type": "count",
                "requirement": "Expected answer: six",
                "evaluator_question": "How many cows are in the image?",
            },
            {
                "constraint_id": "c_002",
                "constraint_type": "count",
                "requirement": "Expected answer: seven",
                "evaluator_question": "How many suitcases are in the image?",
            },
        ],
    }
    action = {
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_000",
            "target_constraint_ids": ["c_001", "c_002"],
            "preserve_constraint_ids": [],
            "instruction": (
                "Keep exactly six cows total, with three cows in the upper row and "
                "three cows in the lower row. Make exactly seven suitcases total; "
                "do not leave only five suitcases. Redraw the lower-left bird outline "
                "locally. Preserve the layout and do not add duplicates."
            ),
        },
    }

    report = evaluate_instruction_quality(
        action,
        task_spec,
        known_attempt_ids=["a_000"],
    )

    assert report.incompatible_count_flags == []
    assert report.overbroad_edit_flags == []


def test_instruction_quality_rejects_preserve_modify_conflict() -> None:
    action = {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_000",
            "target_constraint_ids": ["c_001"],
            "preserve_constraint_ids": ["c_001"],
            "instruction": (
                "Edit attempt a_000: remove one cat so exactly two red cats remain. "
                "Preserve the cats unchanged. Keep them behind the blue cube in the background. "
                "Do not add extra cats or redraw unrelated objects."
            ),
        },
    }

    report = evaluate_instruction_quality(action, _task_spec(), known_attempt_ids=["a_000"])

    assert report.verdict == "reject"
    assert report.preserve_modify_conflict_flags


def test_instruction_quality_does_not_bind_distant_unchanged_to_target_entity() -> None:
    action = {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_000",
            "target_constraint_ids": ["c_002"],
            "preserve_constraint_ids": ["c_001", "c_003", "c_004"],
            "instruction": (
                "Target operation: move the red cats behind the blue cube. "
                "Spatial grounding: place the cats in the background and keep the cube "
                "in the foreground. Preservation lock: keep exactly two red cats, keep "
                "the blue cube and its color, and keep the overall composition otherwise "
                "unchanged. Forbidden changes: do not add extra cats or cubes and do not "
                "redraw unrelated objects."
            ),
        },
    }

    report = evaluate_instruction_quality(
        action,
        _task_spec(),
        known_attempt_ids=["a_000"],
    )

    assert report.preserve_modify_conflict_flags == []


def test_instruction_quality_parses_full_to_the_right_of_relation() -> None:
    task_spec = {
        "original_prompt": "six bagels to the right of six kangaroos",
        "constraints": [
            {
                "constraint_id": "c_001",
                "constraint_type": "position",
                "requirement": "Expected answer: Yes",
                "evaluator_question": "Are the bagels to the right of the kangaroos?",
            }
        ],
    }
    action = {
        "action": "generate_image",
        "arguments": {
            "target_constraint_ids": ["c_001"],
            "preserve_constraint_ids": [],
            "instruction": (
                "Show six bagels clearly to the right of six kangaroos, with the "
                "kangaroos on the left and bagels on the right. Include no extras."
            ),
        },
    }

    report = evaluate_instruction_quality(action, task_spec)

    entities = {
        item["entity"]
        for item in report.required_entity_coverage
    }
    assert entities == {"bagels", "kangaroos"}


def test_instruction_quality_allows_operation_count_plus_final_count() -> None:
    action = {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_001",
            "instruction": (
                "Target operation: edit attempt a_001 to add exactly one additional "
                "red cats so there are exactly two red cats total, and keep the two "
                "red cats behind the blue cube. Spatial grounding: keep the blue cube "
                "large in the foreground and place both red cats behind the blue cube "
                "in the background, with the cube in front of the cats. Preservation "
                "lock: preserve the blue cube and the red cat color. Forbidden changes: "
                "do not add extra cats, do not add another cube, and do not redraw "
                "unrelated scene elements."
            ),
            "target_constraint_ids": ["c_001", "c_002"],
            "preserve_constraint_ids": ["c_003", "c_004"],
        },
    }

    report = evaluate_instruction_quality(action, _task_spec(), known_attempt_ids=["a_001"])

    assert report.verdict == "pass"
    assert report.incompatible_count_flags == []
    assert report.contradiction_flags == []


def test_bounded_subset_count_repair_remains_an_advisory_linter_finding() -> None:
    task_spec = {
        "original_prompt": "six kangaroos in front of one croissant",
        "constraints": [
            {
                "constraint_id": "c_003",
                "constraint_type": "position",
                "requirement": "Expected answer: Yes",
                "evaluator_question": "Are the kangaroos in front of the croissant?",
            },
            {
                "constraint_id": "c_004",
                "constraint_type": "count",
                "requirement": "Expected answer: six",
                "evaluator_question": "How many kangaroos are shown?",
            },
        ],
    }
    action = {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": "a_002",
            "target_constraint_ids": ["c_004"],
            "preserve_constraint_ids": ["c_003"],
            "instruction": (
                "Edit attempt a_002 only in the kangaroo group so exactly six "
                "kangaroos remain. Preserve the five clear kangaroos unchanged, "
                "replace one ambiguous doubled kangaroo cluster with one solid sixth "
                "kangaroo, and keep all kangaroos in front of the croissant. Do not "
                "add a seventh kangaroo or redraw unrelated objects."
            ),
        },
    }

    quality = _advisory_instruction_quality(
        action,
        task_spec,
        known_attempt_ids=["a_000", "a_001", "a_002"],
    )

    assert quality is not None
    assert quality["enforcement"] == "advisory"
    assert quality["sft_role"] == "environment_metadata"
    assert quality["report"]["preserve_modify_conflict_flags"] == [
        "kangaroos is requested as both unchanged and modified"
    ]
    assert quality["report"]["verdict"] == "reject"
    assert not hasattr(Phase3LiveRunner, "_validate_instruction_quality")


def test_advisory_linter_failure_cannot_block_image_execution(monkeypatch) -> None:
    def fail_checker(*args, **kwargs):
        raise RuntimeError("synthetic checker failure")

    monkeypatch.setattr(
        "gen_retry.phase3.live_runner.evaluate_instruction_quality",
        fail_checker,
    )
    quality = _advisory_instruction_quality(
        {
            "action": "generate_image",
            "arguments": {
                "target_constraint_ids": ["c_001"],
                "preserve_constraint_ids": [],
                "instruction": "Show exactly two red cats behind a blue cube.",
            },
        },
        _task_spec(),
        known_attempt_ids=[],
    )

    assert quality == {
        "enforcement": "advisory",
        "sft_role": "environment_metadata",
        "report": {
            "verdict": "unavailable",
            "checker_error_type": "RuntimeError",
        },
    }


def test_live_runner_reads_native_and_legacy_instruction_fields() -> None:
    native = {
        "action": "generate_image",
        "arguments": {"instruction": "native v0.5 instruction"},
    }
    legacy = {
        "action": "edit_image",
        "arguments": {"edit_instruction": "legacy v0.4 instruction"},
    }

    assert _execution_instruction(native) == "native v0.5 instruction"
    assert _execution_instruction(legacy) == "legacy v0.4 instruction"


def test_runtime_allows_same_route_with_new_intervention_after_regression() -> None:
    runner = Phase3LiveRunner.__new__(Phase3LiveRunner)
    previous_action = _edit_action(source_attempt_id="a_000")
    state = _retry_state(
        previous_action=previous_action,
        latest_transition={
            "fixed": [],
            "regressed": ["c_001"],
            "persistent_failed": ["c_002"],
            "stable_pass": [],
        },
    )

    changed_instruction = _edit_action(source_attempt_id="a_000")
    changed_instruction["arguments"]["instruction"] = (
        "Use a different spatial anchor and separation pattern."
    )

    runner._validate_source_selection_policy(changed_instruction, state)


def test_runtime_does_not_use_action_tuple_as_semantic_equivalence() -> None:
    runner = Phase3LiveRunner.__new__(Phase3LiveRunner)
    previous_action = _edit_action(source_attempt_id="a_000")
    state = _retry_state(
        previous_action=previous_action,
        latest_transition={
            "fixed": [],
            "regressed": [],
            "persistent_failed": ["c_002", "c_003"],
            "stable_pass": ["c_001"],
        },
    )

    runner._validate_source_selection_policy(previous_action, state)


def test_source_policy_rejects_nonbest_source_without_relevant_evidence() -> None:
    runner = Phase3LiveRunner.__new__(Phase3LiveRunner)
    state = _retry_state(
        previous_action=_edit_action(source_attempt_id="a_000"),
        latest_transition={
            "fixed": ["c_001"],
            "regressed": [],
            "persistent_failed": ["c_002"],
            "stable_pass": [],
        },
    )
    action = _edit_action(source_attempt_id="a_001")

    try:
        runner._validate_source_selection_policy(action, state)
    except RuntimeActionError as exc:
        assert exc.error_code == "historical_source_without_constraint_evidence"
    else:
        raise AssertionError("expected historical source evidence rejection")


def test_source_policy_allows_nonbest_source_with_relevant_pass_evidence() -> None:
    runner = Phase3LiveRunner.__new__(Phase3LiveRunner)
    state = _retry_state(
        previous_action=_edit_action(source_attempt_id="a_000"),
        latest_transition={
            "fixed": ["c_001"],
            "regressed": [],
            "persistent_failed": ["c_002"],
            "stable_pass": [],
        },
        source_unique_pass=True,
    )
    action = _edit_action(
        source_attempt_id="a_001",
        preserve_constraint_ids=["c_003"],
    )

    runner._validate_source_selection_policy(action, state)


def _edit_action(
    *,
    source_attempt_id: str,
    preserve_constraint_ids: list[str] | None = None,
) -> dict:
    return {
        "schema_version": "0.5",
        "action": "edit_image",
        "arguments": {
            "source_attempt_id": source_attempt_id,
            "target_constraint_ids": ["c_002"],
            "preserve_constraint_ids": preserve_constraint_ids or ["c_001"],
            "instruction": "Executable test instruction.",
        },
    }


def _retry_state(
    *,
    previous_action: dict,
    latest_transition: dict,
    source_unique_pass: bool = False,
) -> EpisodeState:
    best = AttemptRecord(
        attempt_id="a_000",
        parent_attempt_id=None,
        action_event_id="evt_000",
        action={
            "schema_version": "0.5",
            "action": "generate_image",
            "arguments": {
                "target_constraint_ids": ["c_001", "c_002", "c_003"],
                "preserve_constraint_ids": [],
                "instruction": "Initial test instruction.",
            },
        },
        operation="generate",
        image_artifact_id="img_000",
        constraint_results={
            "c_001": {"status": "pass"},
            "c_002": {"status": "fail"},
            "c_003": {"status": "fail"},
        },
        primary_score=0.5,
    )
    latest = AttemptRecord(
        attempt_id="a_001",
        parent_attempt_id="a_000",
        action_event_id="evt_001",
        action=previous_action,
        operation="edit",
        image_artifact_id="img_001",
        constraint_results={
            "c_001": {"status": "pass"},
            "c_002": {"status": "fail"},
            "c_003": {"status": "pass" if source_unique_pass else "fail"},
        },
        primary_score=0.4,
    )
    return EpisodeState(
        schema_version="0.2",
        episode_id="ep_retry_policy",
        task_spec={"max_image_attempts": 5},
        score_policy={},
        attempts={"a_000": best, "a_001": latest},
        attempt_order=["a_000", "a_001"],
        latest_attempt_id="a_001",
        best_attempt_id="a_000",
        latest_transition=latest_transition,
        remaining_budget=3,
    )
