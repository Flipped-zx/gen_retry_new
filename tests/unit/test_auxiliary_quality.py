from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.auxiliary_quality import (
    compact_quality_fields,
    risk_policy_sha256,
    validate_auxiliary_quality_observation,
)
from gen_retry.domain.score_policy import canonical_primary_score, primary_score_policy
from gen_retry.protocol.trajectory_validator import (
    ProtocolValidationError,
    validate_trajectory_events,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.planner_context import build_planner_context_from_events
from gen_retry.runtime.reducer import reduce_events


RISK_POLICY = {
    "policy_id": "hpsv3_source_delta_threshold_v1",
    "policy_version": "calibration-example-1",
    "calibration_ref": "artifacts/hpsv3/calibration.json",
    "calibration_sha256": "e" * 64,
    "watch_below": -0.02,
    "high_below": -0.08,
}


def _observation(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "evaluator_id": "hpsv3",
        "evaluator_version": "1.0.0",
        "checkpoint_ref": "MizzenAI/HPSv3@main",
        "checkpoint_sha256": "a" * 64,
        "preprocess_version": "official-hpsv3",
        "prompt_hash_policy_id": "utf8_exact_original_prompt_sha256_v1",
        "prompt_sha256": "b" * 64,
        "attempt_id": "a_000",
        "image_artifact_id": "img_000",
        "image_sha256": "c" * 64,
        "source_attempt_id": None,
        "quality_anchor_attempt_id": None,
        "quality_anchor_policy_id": "lineage_root_v1",
        "delta_policy_id": "child_mu_minus_baseline_mu_v1",
        "risk_policy": copy.deepcopy(RISK_POLICY),
        "risk_policy_sha256": risk_policy_sha256(RISK_POLICY),
        "status": "success",
        "mu": 0.72,
        "sigma": 0.03,
        "delta_from_source": None,
        "delta_from_anchor": None,
        "quality_risk": "unknown",
        "report_ref": "reports/hpsv3/a_000.json",
        "report_sha256": "d" * 64,
        "error_code": None,
    }
    value.update(overrides)
    return value


def _quality_event(
    events: list[dict[str, Any]],
    *,
    event_id: str,
    attempt_id: str = "a_000",
    image_artifact_id: str = "img_000",
    **observation_overrides: object,
) -> dict[str, Any]:
    task_spec = events[0]["payload"]["task_spec"]
    completion = next(
        event
        for event in events
        if event["event_type"] == "image_execution_completed"
        and event["payload"]["attempt_id"] == attempt_id
    )
    quality_payload = _observation(
        attempt_id=attempt_id,
        image_artifact_id=image_artifact_id,
        image_sha256=completion["payload"]["artifact_sha256"],
        prompt_sha256=sha256_bytes(task_spec["original_prompt"].encode("utf-8")),
    )
    quality_payload.update(observation_overrides)
    return {
        "schema_version": "0.2",
        "event_id": event_id,
        "episode_id": events[0]["episode_id"],
        "turn_id": "turn_000",
        "event_type": "auxiliary_quality_completed",
        "created_at": "2026-07-14T06:00:00Z",
        "producer": "hpsv3_adapter",
        "input_refs": [image_artifact_id],
        "payload": quality_payload,
    }


def _example_events_with_root_quality() -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "examples/one_episode_trajectory.jsonl")
    root_quality = _quality_event(events, event_id="evt_0900")
    geneval_index = next(
        index
        for index, event in enumerate(events)
        if event["event_type"] == "geneval2_completed"
        and event["payload"]["attempt_id"] == "a_000"
    )
    events.insert(geneval_index + 1, root_quality)
    return events


def test_quality_observation_validates_and_compacts() -> None:
    observation = _observation()
    validate_auxiliary_quality_observation(observation)

    assert compact_quality_fields(observation) == {
        "evaluator_id": "hpsv3",
        "evaluator_version": "1.0.0",
        "attempt_id": "a_000",
        "source_attempt_id": None,
        "quality_anchor_attempt_id": None,
        "quality_anchor_policy_id": "lineage_root_v1",
        "delta_policy_id": "child_mu_minus_baseline_mu_v1",
        "risk_policy_id": "hpsv3_source_delta_threshold_v1",
        "risk_policy_version": "calibration-example-1",
        "risk_policy_sha256": risk_policy_sha256(RISK_POLICY),
        "status": "success",
        "mu": 0.72,
        "sigma": 0.03,
        "delta_from_source": None,
        "delta_from_anchor": None,
        "quality_risk": "unknown",
    }


def test_quality_delta_requires_a_declared_baseline() -> None:
    with pytest.raises(ValueError, match="delta_from_source"):
        validate_auxiliary_quality_observation(_observation(delta_from_source=-0.08))


def test_failed_quality_result_does_not_smuggle_a_score() -> None:
    with pytest.raises(Exception):
        validate_auxiliary_quality_observation(
            _observation(
                status="failed",
                mu=0.2,
                sigma=None,
                quality_risk="unknown",
                error_code="oom",
            )
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "status": "failed",
            "mu": None,
            "sigma": None,
            "delta_from_source": -0.1,
            "quality_risk": "unknown",
            "error_code": "oom",
        },
        {
            "status": "missing",
            "mu": None,
            "sigma": None,
            "quality_risk": "high",
            "report_ref": None,
            "report_sha256": None,
            "error_code": "not_scored",
        },
    ],
)
def test_non_success_quality_result_cannot_pollute_context(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(Exception):
        validate_auxiliary_quality_observation(_observation(**overrides))


def test_quality_event_reduces_without_changing_geneval2_best_order() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    events[0]["payload"]["score_policy"] = primary_score_policy()
    geneval = next(event for event in events if event["event_type"] == "geneval2_completed")
    for result, confidence in zip(
        geneval["payload"]["constraint_results"], [0.1, 0.8, 0.9, 0.7], strict=True
    ):
        result["confidence"] = confidence
    geneval["payload"]["primary_score"] = canonical_primary_score(
        geneval["payload"]["constraint_results"]
    )
    events.append(_quality_event(events, event_id="evt_0010"))

    state = reduce_events(events)
    context = build_planner_context_from_events(events, schema_version="0.8")

    assert state.best_attempt_id == "a_000"
    assert state.attempts["a_000"].auxiliary_quality["mu"] == 0.72
    assert context["latest_attempt"]["auxiliary_quality"]["delta_from_anchor"] is None
    assert context["episode_memory"]["quality_history"][0]["attempt_id"] == "a_000"
    assert context["runtime_state"]["auxiliary_quality_decision"] == {
        "policy_id": "planner_context_only_hpsv3_advisory_v1",
        "application": "planner_context_only",
        "primary_objective": "geneval2",
        "intervention_skill_id": "local_edit_preservation",
        "hidden_source_filter": False,
    }


def test_quality_event_before_geneval2_is_rejected() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    quality = _quality_event(events, event_id="evt_0090")
    geneval_index = next(
        index for index, event in enumerate(events) if event["event_type"] == "geneval2_completed"
    )
    events.insert(geneval_index, quality)

    with pytest.raises(ProtocolValidationError, match="auxiliary_quality_before_geneval2"):
        validate_trajectory_events(events)


def test_v08_context_cannot_hide_a_missing_quality_event() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    events[0]["payload"]["score_policy"] = primary_score_policy()
    geneval = next(event for event in events if event["event_type"] == "geneval2_completed")
    for result, confidence in zip(
        geneval["payload"]["constraint_results"], [0.1, 0.8, 0.9, 0.7], strict=True
    ):
        result["confidence"] = confidence
    geneval["payload"]["primary_score"] = canonical_primary_score(
        geneval["payload"]["constraint_results"]
    )
    events.insert(
        next(index for index, event in enumerate(events) if event["event_type"] == "memory_reduced"),
        {
            "schema_version": "0.2",
            "event_id": "evt_0090",
            "episode_id": "ep_demo_001",
            "turn_id": "turn_000",
            "event_type": "planner_context_built",
            "created_at": "2026-07-14T06:00:00Z",
            "producer": "planner_context_builder",
            "input_refs": ["evt_0007"],
            "payload": {
                "planner_context_ref": "contexts/v08.json",
                "planner_context_sha256": "f" * 64,
                "planner_context_schema_version": "0.8",
            },
        },
    )

    with pytest.raises(
        ProtocolValidationError,
        match="planner_context_missing_auxiliary_quality",
    ):
        validate_trajectory_events(events)


def test_v08_context_accepts_an_explicit_missing_quality_event() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    events[0]["payload"]["score_policy"] = primary_score_policy()
    geneval = next(event for event in events if event["event_type"] == "geneval2_completed")
    for result, confidence in zip(
        geneval["payload"]["constraint_results"], [0.1, 0.8, 0.9, 0.7], strict=True
    ):
        result["confidence"] = confidence
    geneval["payload"]["primary_score"] = canonical_primary_score(
        geneval["payload"]["constraint_results"]
    )
    events.append(
        _quality_event(
            events,
            event_id="evt_0090",
            status="missing",
            mu=None,
            sigma=None,
            delta_from_source=None,
            delta_from_anchor=None,
            quality_risk="unknown",
            report_ref=None,
            report_sha256=None,
            error_code="not_scored",
        )
    )
    events.append(
        {
            "schema_version": "0.2",
            "event_id": "evt_0091",
            "episode_id": "ep_demo_001",
            "turn_id": "turn_001",
            "event_type": "planner_context_built",
            "created_at": "2026-07-14T06:00:00Z",
            "producer": "planner_context_builder",
            "input_refs": ["evt_0090"],
            "payload": {
                "planner_context_ref": "contexts/v08.json",
                "planner_context_sha256": "f" * 64,
                "planner_context_schema_version": "0.8",
            },
        }
    )

    validate_trajectory_events(events)
    context = build_planner_context_from_events(events, schema_version="0.8")
    assert context["latest_attempt"]["auxiliary_quality"]["status"] == "missing"
    assert context["latest_attempt"]["auxiliary_quality"]["quality_risk"] == "unknown"


def test_duplicate_quality_event_is_rejected() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    events.extend(
        [
            _quality_event(events, event_id="evt_0090"),
            _quality_event(events, event_id="evt_0091"),
        ]
    )

    with pytest.raises(ProtocolValidationError, match="duplicate_auxiliary_quality_result"):
        validate_trajectory_events(events)


def test_quality_image_digest_must_match_execution_artifact() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    events.append(_quality_event(events, event_id="evt_0090", image_sha256="0" * 64))

    with pytest.raises(
        ProtocolValidationError,
        match="auxiliary_quality_image_digest_mismatch",
    ):
        validate_trajectory_events(events)


def test_self_quality_anchor_is_rejected() -> None:
    root = Path(__file__).resolve().parents[2]
    events = load_events_jsonl(root / "tests/fixtures/events/one_attempt_events.jsonl")
    events.append(
        _quality_event(
            events,
            event_id="evt_0090",
            quality_anchor_attempt_id="a_000",
            delta_from_anchor=0.0,
        )
    )

    with pytest.raises(ProtocolValidationError, match="auxiliary_quality_anchor_mismatch"):
        validate_trajectory_events(events)


def test_sibling_or_future_quality_anchor_is_rejected() -> None:
    events = _example_events_with_root_quality()
    child_quality = _quality_event(
        events,
        event_id="evt_0901",
        attempt_id="a_001",
        image_artifact_id="img_001",
        source_attempt_id="a_000",
        quality_anchor_attempt_id="a_002",
        mu=0.65,
        delta_from_source=-0.07,
        delta_from_anchor=-0.07,
        quality_risk="watch",
    )
    geneval_index = next(
        index
        for index, event in enumerate(events)
        if event["event_type"] == "geneval2_completed"
        and event["payload"]["attempt_id"] == "a_001"
    )
    events.insert(geneval_index + 1, child_quality)

    with pytest.raises(ProtocolValidationError) as excinfo:
        validate_trajectory_events(events)

    message = str(excinfo.value)
    assert "unknown_quality_anchor" in message
    assert "auxiliary_quality_anchor_mismatch" in message


def test_known_sibling_quality_anchor_is_rejected() -> None:
    events = _example_events_with_root_quality()
    sibling_quality = _quality_event(
        events,
        event_id="evt_0902",
        attempt_id="a_002",
        image_artifact_id="img_002",
        source_attempt_id="a_000",
        quality_anchor_attempt_id="a_001",
        mu=0.65,
        delta_from_source=-0.07,
        delta_from_anchor=None,
        quality_risk="watch",
    )
    geneval_index = next(
        index
        for index, event in enumerate(events)
        if event["event_type"] == "geneval2_completed"
        and event["payload"]["attempt_id"] == "a_002"
    )
    events.insert(geneval_index + 1, sibling_quality)

    with pytest.raises(ProtocolValidationError, match="auxiliary_quality_anchor_mismatch"):
        validate_trajectory_events(events)


def test_valid_child_deltas_and_risk_replay() -> None:
    events = _example_events_with_root_quality()
    child_quality = _quality_event(
        events,
        event_id="evt_0901",
        attempt_id="a_001",
        image_artifact_id="img_001",
        source_attempt_id="a_000",
        quality_anchor_attempt_id="a_000",
        mu=0.65,
        delta_from_source=-0.07,
        delta_from_anchor=-0.07,
        quality_risk="watch",
    )
    geneval_index = next(
        index
        for index, event in enumerate(events)
        if event["event_type"] == "geneval2_completed"
        and event["payload"]["attempt_id"] == "a_001"
    )
    events.insert(geneval_index + 1, child_quality)

    state = reduce_events(events)

    assert state.attempts["a_001"].auxiliary_quality["delta_from_source"] == -0.07
    assert state.attempts["a_001"].auxiliary_quality["quality_risk"] == "watch"


def test_delta_must_equal_child_mu_minus_baseline_mu() -> None:
    events = _example_events_with_root_quality()
    child_quality = _quality_event(
        events,
        event_id="evt_0901",
        attempt_id="a_001",
        image_artifact_id="img_001",
        source_attempt_id="a_000",
        quality_anchor_attempt_id="a_000",
        mu=0.65,
        delta_from_source=-0.01,
        delta_from_anchor=-0.01,
        quality_risk="low",
    )
    geneval_index = next(
        index
        for index, event in enumerate(events)
        if event["event_type"] == "geneval2_completed"
        and event["payload"]["attempt_id"] == "a_001"
    )
    events.insert(geneval_index + 1, child_quality)

    with pytest.raises(ProtocolValidationError, match="auxiliary_quality_delta_mismatch"):
        validate_trajectory_events(events)
