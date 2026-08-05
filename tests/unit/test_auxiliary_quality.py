from __future__ import annotations

import pytest

from gen_retry.domain.auxiliary_quality import (
    compact_quality_fields,
    validate_auxiliary_quality_observation,
)
from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.domain.score_policy import canonical_primary_score, primary_score_policy
from gen_retry.runtime.planner_context import build_planner_context_from_events
from gen_retry.runtime.reducer import reduce_events
from gen_retry.runtime.event_io import load_events_jsonl
from pathlib import Path


def _observation(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "evaluator_id": "hpsv3",
        "evaluator_version": "1.0.0",
        "checkpoint_ref": "MizzenAI/HPSv3@main",
        "checkpoint_sha256": "a" * 64,
        "preprocess_version": "official-hpsv3",
        "prompt_sha256": "b" * 64,
        "attempt_id": "a_000",
        "image_artifact_id": "img_000",
        "image_sha256": "c" * 64,
        "source_attempt_id": None,
        "quality_anchor_attempt_id": "a_000",
        "status": "success",
        "mu": 0.72,
        "sigma": 0.03,
        "delta_from_source": None,
        "delta_from_anchor": 0.0,
        "quality_risk": "low",
        "report_ref": "reports/hpsv3/a_000.json",
        "report_sha256": "d" * 64,
        "error_code": None,
    }
    value.update(overrides)
    return value


def test_quality_observation_validates_and_compacts() -> None:
    observation = _observation()
    validate_auxiliary_quality_observation(observation)

    assert compact_quality_fields(observation) == {
        "evaluator_id": "hpsv3",
        "evaluator_version": "1.0.0",
        "attempt_id": "a_000",
        "source_attempt_id": None,
        "quality_anchor_attempt_id": "a_000",
        "status": "success",
        "mu": 0.72,
        "sigma": 0.03,
        "delta_from_source": None,
        "delta_from_anchor": 0.0,
        "quality_risk": "low",
    }


def test_quality_delta_requires_a_declared_baseline() -> None:
    with pytest.raises(ValueError, match="delta_from_source"):
        validate_auxiliary_quality_observation(
            _observation(delta_from_source=-0.08)
        )


def test_failed_quality_result_does_not_smuggle_a_score() -> None:
    with pytest.raises(Exception):
        validate_auxiliary_quality_observation(
            _observation(status="failed", mu=0.2, sigma=None, error_code="oom")
        )


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
    events.append(
        {
            "schema_version": "0.2",
            "event_id": "evt_0010",
            "episode_id": "ep_demo_001",
            "turn_id": "turn_000",
            "event_type": "auxiliary_quality_completed",
            "created_at": "2026-07-14T06:00:00Z",
            "producer": "hpsv3_adapter",
            "input_refs": ["img_000"],
            "payload": _observation(
                prompt_sha256=sha256_bytes(
                    events[0]["payload"]["task_spec"]["original_prompt"].encode("utf-8")
                )
            ),
        }
    )

    state = reduce_events(events)
    context = build_planner_context_from_events(events, schema_version="0.8")

    assert state.best_attempt_id == "a_000"
    assert state.attempts["a_000"].auxiliary_quality["mu"] == 0.72
    assert context["latest_attempt"]["auxiliary_quality"]["delta_from_anchor"] == 0.0
    assert context["episode_memory"]["quality_history"][0]["attempt_id"] == "a_000"
