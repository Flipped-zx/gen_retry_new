"""Canonical validation and compact planner fields for auxiliary HPSv3 scores."""

from __future__ import annotations

import math
from typing import Any

from gen_retry.protocol.schema_loader import validate_instance


QUALITY_SCHEMA = "auxiliary_quality_observation_v0_1.schema.json"


def validate_auxiliary_quality_observation(observation: dict[str, Any]) -> None:
    """Validate an environment-owned HPSv3 observation and its baseline semantics."""

    validate_instance(observation, QUALITY_SCHEMA)
    status = observation["status"]
    mu = observation["mu"]
    sigma = observation["sigma"]
    for field in ("mu", "sigma", "delta_from_source", "delta_from_anchor"):
        value = observation[field]
        if value is not None and not math.isfinite(float(value)):
            raise ValueError(f"auxiliary quality {field} must be finite or null")
    if sigma is not None and sigma < 0:
        raise ValueError("auxiliary quality sigma must be non-negative")
    if status == "success" and mu is None:
        raise ValueError("successful HPSv3 observation requires mu")
    if status != "success" and (mu is not None or sigma is not None):
        raise ValueError("failed or missing HPSv3 observation cannot contain scores")
    if observation["source_attempt_id"] is None and observation["delta_from_source"] is not None:
        raise ValueError("delta_from_source requires source_attempt_id")
    if observation["quality_anchor_attempt_id"] is None and observation["delta_from_anchor"] is not None:
        raise ValueError("delta_from_anchor requires quality_anchor_attempt_id")


def compact_quality_fields(observation: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return the small, non-provenance view safe to expose to a Planner."""

    if observation is None:
        return None
    validate_auxiliary_quality_observation(observation)
    return {
        "evaluator_id": observation["evaluator_id"],
        "evaluator_version": observation["evaluator_version"],
        "attempt_id": observation["attempt_id"],
        "source_attempt_id": observation["source_attempt_id"],
        "quality_anchor_attempt_id": observation["quality_anchor_attempt_id"],
        "status": observation["status"],
        "mu": observation["mu"],
        "sigma": observation["sigma"],
        "delta_from_source": observation["delta_from_source"],
        "delta_from_anchor": observation["delta_from_anchor"],
        "quality_risk": observation.get("quality_risk", "unknown"),
    }
