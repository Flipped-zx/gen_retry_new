"""Canonical validation and compact planner fields for auxiliary HPSv3 scores."""

from __future__ import annotations

import json
import math
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.protocol.schema_loader import validate_instance


QUALITY_SCHEMA = "auxiliary_quality_observation_v0_1.schema.json"
PROMPT_HASH_POLICY_ID = "utf8_exact_original_prompt_sha256_v1"
QUALITY_ANCHOR_POLICY_ID = "lineage_root_v1"
DELTA_POLICY_ID = "child_mu_minus_baseline_mu_v1"
QUALITY_DECISION_POLICY_ID = "planner_context_only_hpsv3_advisory_v1"


def risk_policy_sha256(policy: dict[str, Any]) -> str:
    canonical = json.dumps(
        policy,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(canonical)


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
    risk_policy = observation["risk_policy"]
    for threshold_name in ("watch_below", "high_below"):
        if not math.isfinite(float(risk_policy[threshold_name])):
            raise ValueError(f"quality risk {threshold_name} must be finite")
    if risk_policy["high_below"] >= risk_policy["watch_below"]:
        raise ValueError("quality risk high_below must be lower than watch_below")
    if observation["risk_policy_sha256"] != risk_policy_sha256(risk_policy):
        raise ValueError("quality risk policy fingerprint does not match its canonical payload")
    if status == "success" and mu is None:
        raise ValueError("successful HPSv3 observation requires mu")
    if status != "success":
        forbidden = (
            mu,
            sigma,
            observation["delta_from_source"],
            observation["delta_from_anchor"],
        )
        if any(value is not None for value in forbidden):
            raise ValueError("failed or missing HPSv3 observation cannot contain scores or deltas")
        if observation["quality_risk"] != "unknown":
            raise ValueError("failed or missing HPSv3 observation requires unknown quality risk")
    report_ref = observation["report_ref"]
    report_sha256 = observation["report_sha256"]
    if (report_ref is None) != (report_sha256 is None):
        raise ValueError("auxiliary quality report_ref and report_sha256 must be both set or both null")
    if observation["source_attempt_id"] is None and observation["delta_from_source"] is not None:
        raise ValueError("delta_from_source requires source_attempt_id")
    if observation["quality_anchor_attempt_id"] is None and observation["delta_from_anchor"] is not None:
        raise ValueError("delta_from_anchor requires quality_anchor_attempt_id")


def quality_risk_for_source_delta(
    delta_from_source: float | None,
    risk_policy: dict[str, Any],
) -> str:
    if delta_from_source is None:
        return "unknown"
    if delta_from_source < risk_policy["high_below"]:
        return "high"
    if delta_from_source < risk_policy["watch_below"]:
        return "watch"
    return "low"


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
        "quality_anchor_policy_id": observation["quality_anchor_policy_id"],
        "delta_policy_id": observation["delta_policy_id"],
        "risk_policy_id": observation["risk_policy"]["policy_id"],
        "risk_policy_version": observation["risk_policy"]["policy_version"],
        "risk_policy_sha256": observation["risk_policy_sha256"],
        "status": observation["status"],
        "mu": observation["mu"],
        "sigma": observation["sigma"],
        "delta_from_source": observation["delta_from_source"],
        "delta_from_anchor": observation["delta_from_anchor"],
        "quality_risk": observation.get("quality_risk", "unknown"),
    }
