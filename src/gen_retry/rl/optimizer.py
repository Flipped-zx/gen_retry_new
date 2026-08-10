from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.rl.admission import admit_rollout_sample_batch
from gen_retry.rl.config import RlExperimentConfig
from gen_retry.rl.training import build_advantage_batch
from gen_retry.runtime.json_canonical import canonical_json


ADVANTAGE_BATCH_SCHEMA = "rl_advantage_batch_v0_1.schema.json"


@dataclass(frozen=True)
class OptimizerSample:
    group_id: str
    candidate_id: str
    sampled_token_ids: tuple[int, ...]
    assistant_action_mask: tuple[int, ...]
    old_log_probs: tuple[float, ...]
    reference_log_probs: tuple[float, ...]
    advantage: float
    outcome_kind: str


@dataclass(frozen=True)
class OptimizerBatch:
    batch_id: str
    admitted_group_count: int
    admitted_candidate_count: int
    eligible_group_count: int
    zero_variance_group_count: int
    policy_invalid_count: int
    samples: tuple[OptimizerSample, ...]

    @property
    def trained_token_count(self) -> int:
        return sum(sum(sample.assistant_action_mask) for sample in self.samples)


def prepare_optimizer_batch(
    *,
    rollout_payload: dict[str, Any],
    advantage_payload: dict[str, Any],
    artifact_root: Path,
    config: RlExperimentConfig,
) -> OptimizerBatch:
    """Revalidate and join immutable rollout artifacts before tensorization."""

    admission = admit_rollout_sample_batch(
        rollout_payload,
        artifact_root=artifact_root,
        config=config,
    )
    validate_instance(advantage_payload, ADVANTAGE_BATCH_SCHEMA)
    expected_advantages = build_advantage_batch(
        admission.candidate_return_batch,
        config=config.reward,
    )
    if canonical_json(advantage_payload) != canonical_json(expected_advantages):
        raise ValueError(
            "advantage batch does not exactly match the admitted rollout batch"
        )

    rollout_groups = {
        group["group_id"]: group for group in rollout_payload["groups"]
    }
    samples: list[OptimizerSample] = []
    eligible_group_count = 0
    zero_variance_group_count = 0
    for advantage_group in advantage_payload["groups"]:
        if not advantage_group["advantage_stats"]["eligible_for_policy_loss"]:
            zero_variance_group_count += 1
            continue
        eligible_group_count += 1
        rollout_candidates = {
            candidate["candidate_id"]: candidate
            for candidate in rollout_groups[advantage_group["group_id"]][
                "candidates"
            ]
        }
        for advantage_candidate in advantage_group["candidates"]:
            candidate_id = advantage_candidate["candidate_id"]
            rollout_candidate = rollout_candidates[candidate_id]
            token_ids = _load_vector(
                artifact_root,
                rollout_candidate["sampled_token_ids"],
                vector_kind="token_ids",
            )
            action_mask = _load_vector(
                artifact_root,
                rollout_candidate["assistant_action_mask"],
                vector_kind="action_mask",
            )
            old_log_probs = _load_vector(
                artifact_root,
                rollout_candidate["old_log_probs"],
                vector_kind="log_probs",
            )
            reference_log_probs = _load_vector(
                artifact_root,
                rollout_candidate["reference_log_probs"],
                vector_kind="log_probs",
            )
            samples.append(
                OptimizerSample(
                    group_id=advantage_group["group_id"],
                    candidate_id=candidate_id,
                    sampled_token_ids=token_ids,
                    assistant_action_mask=action_mask,
                    old_log_probs=old_log_probs,
                    reference_log_probs=reference_log_probs,
                    advantage=float(advantage_candidate["combined_advantage"]),
                    outcome_kind=str(advantage_candidate["outcome_kind"]),
                )
            )
    zero_variance_fraction = (
        zero_variance_group_count / admission.group_count
        if admission.group_count
        else 0.0
    )
    if (
        zero_variance_fraction
        > config.admission.maximum_zero_variance_group_fraction
    ):
        raise ValueError(
            "zero-variance group fraction exceeds optimization threshold: "
            f"{zero_variance_fraction:.6f} > "
            f"{config.admission.maximum_zero_variance_group_fraction:.6f}; "
            f"freeze the {config.admission.increase_rollouts_to}-rollout amendment "
            "before optimization"
        )
    return OptimizerBatch(
        batch_id=admission.batch_id,
        admitted_group_count=admission.group_count,
        admitted_candidate_count=admission.candidate_count,
        eligible_group_count=eligible_group_count,
        zero_variance_group_count=zero_variance_group_count,
        policy_invalid_count=admission.policy_invalid_count,
        samples=tuple(samples),
    )


def optimizer_metrics(batch: OptimizerBatch) -> dict[str, float | int]:
    admitted = batch.admitted_group_count
    return {
        "rl/admitted_groups": admitted,
        "rl/eligible_groups": batch.eligible_group_count,
        "rl/zero_variance_groups": batch.zero_variance_group_count,
        "rl/zero_variance_group_fraction": (
            batch.zero_variance_group_count / admitted if admitted else 0.0
        ),
        "rl/admitted_candidates": batch.admitted_candidate_count,
        "rl/eligible_candidates": len(batch.samples),
        "rl/policy_invalid_candidates": batch.policy_invalid_count,
        "rl/trainable_action_tokens": batch.trained_token_count,
    }


def _load_vector(
    artifact_root: Path,
    artifact: dict[str, str],
    *,
    vector_kind: str,
) -> tuple[Any, ...]:
    ref = artifact["ref"]
    root = artifact_root.resolve()
    path = (root / ref).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"optimizer artifact escapes root: {ref}") from exc
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
        raise ValueError(f"optimizer artifact SHA256 mismatch: {ref}")
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError(f"optimizer artifact must be a JSON array: {ref}")
    if vector_kind == "token_ids":
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in payload
        ):
            raise ValueError(f"optimizer token ID vector is invalid: {ref}")
        return tuple(payload)
    if vector_kind == "action_mask":
        if any(value not in (0, 1, False, True) for value in payload):
            raise ValueError(f"optimizer action-mask vector is invalid: {ref}")
        return tuple(int(bool(value)) for value in payload)
    if vector_kind != "log_probs":
        raise ValueError(f"unknown optimizer vector kind: {vector_kind}")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in payload
    ):
        raise ValueError(f"optimizer float vector is invalid: {ref}")
    return tuple(float(value) for value in payload)
