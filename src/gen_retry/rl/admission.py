from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_file
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.rl.config import RlExperimentConfig
from gen_retry.rl.credit import AttemptScore
from gen_retry.runtime.json_canonical import canonical_json


ROLLOUT_BATCH_SCHEMA = "rl_rollout_sample_batch_v0_1.schema.json"
TERMINAL_REWARD_SCHEMA = "rl_terminal_reward_v0_1.schema.json"
CANDIDATE_BATCH_SCHEMA = "rl_candidate_return_batch_v0_1.schema.json"


@dataclass(frozen=True)
class RolloutAdmission:
    batch_id: str
    planned_group_count: int
    group_count: int
    excluded_group_count: int
    candidate_count: int
    policy_invalid_count: int
    recovered_infrastructure_retry_count: int
    candidate_return_batch: dict[str, Any]
    group_sha256_by_id: dict[str, str] = field(default_factory=dict)
    candidate_sha256_by_id: dict[str, str] = field(default_factory=dict)
    reward_sha256_by_id: dict[str, str] = field(default_factory=dict)

    @property
    def policy_invalid_fraction(self) -> float:
        return self.policy_invalid_count / self.candidate_count

    @property
    def valid_group_fraction(self) -> float:
        return self.group_count / self.planned_group_count


def admit_rollout_sample_batch(
    payload: dict[str, Any],
    *,
    artifact_root: Path,
    config: RlExperimentConfig,
    expected_policy_revision: str | None = None,
    expected_checkpoint_sha256: str | None = None,
    expected_checkpoint_ref: Path | None = None,
) -> RolloutAdmission:
    """Validate a materialized rollout batch before reward or optimizer use."""

    validate_instance(payload, ROLLOUT_BATCH_SCHEMA)
    artifact_root = artifact_root.resolve()
    group_ids: set[str] = set()
    prompt_ids: set[str] = set()
    candidate_ids: set[str] = set()
    return_groups: list[dict[str, Any]] = []
    policy_invalid_count = 0
    retry_count = 0
    policy_revision = expected_policy_revision or config.policy_revision
    checkpoint_sha256 = expected_checkpoint_sha256 or config.checkpoint_sha256
    checkpoint_ref = expected_checkpoint_ref or config.base_checkpoint

    planned_group_count = payload["planned_group_count"]
    if planned_group_count != len(payload["groups"]) + len(payload["excluded_groups"]):
        raise ValueError(
            "planned group count must equal admitted plus excluded groups"
        )
    for excluded in payload["excluded_groups"]:
        _add_unique(group_ids, excluded["group_id"], "group_id")
        _add_unique(prompt_ids, excluded["prompt_id"], "prompt_id")
        _verify_artifact(
            artifact_root,
            excluded["failure_record"],
            label=f"{excluded['group_id']}.failure_record",
        )

    for group in payload["groups"]:
        group_id = group["group_id"]
        prompt_id = group["prompt_id"]
        _add_unique(group_ids, group_id, "group_id")
        _add_unique(prompt_ids, prompt_id, "prompt_id")
        if group["group_kind"] != "episode":
            raise ValueError("naive GRPO admits only complete episode groups")
        if group["state_id"] != (
            "planner_context_sha256:" + group["canonical_state_sha256"]
        ):
            raise ValueError(f"{group_id}: state ID and canonical state hash disagree")
        if len(group["candidates"]) != config.rollout.full_rollouts_per_prompt:
            raise ValueError(
                f"{group_id}: expected {config.rollout.full_rollouts_per_prompt} "
                f"candidates, found {len(group['candidates'])}"
            )
        if group["policy_revision"] != policy_revision:
            raise ValueError(f"{group_id}: stale or unexpected policy revision")
        if group["sampling_policy_id"] != policy_revision:
            raise ValueError(f"{group_id}: sampling policy ID mismatch")
        if group["policy_checkpoint"]["sha256"] != checkpoint_sha256:
            raise ValueError(f"{group_id}: policy checkpoint fingerprint mismatch")
        if Path(group["policy_checkpoint"]["ref"]) != checkpoint_ref:
            raise ValueError(f"{group_id}: policy checkpoint reference mismatch")
        sampling = group["sampling_config"]
        expected_sampling = {
            "temperature": config.rollout.temperature,
            "top_p": config.rollout.top_p,
            "top_k": config.rollout.top_k,
            "max_action_tokens": config.rollout.max_action_tokens,
            "max_episode_assistant_tokens": (
                config.rollout.max_total_assistant_tokens
            ),
            "seed": config.rollout.seed,
        }
        for name, expected in expected_sampling.items():
            if sampling[name] != expected:
                raise ValueError(
                    f"{group_id}: sampling {name}={sampling[name]!r}, "
                    f"expected {expected!r}"
                )
        sampling_sha256 = _canonical_sha256(sampling)
        if group["sampling_config_sha256"] != sampling_sha256:
            raise ValueError(f"{group_id}: sampling config SHA256 mismatch")

        return_candidates: list[dict[str, Any]] = []
        for candidate in group["candidates"]:
            candidate_id = candidate["candidate_id"]
            _add_unique(candidate_ids, candidate_id, "candidate_id")
            sampled_response_path = _verify_artifact(
                artifact_root,
                candidate["sampled_response"],
                label=f"{candidate_id}.sampled_response",
            )
            if candidate["sample_sha256"] != sha256_file(sampled_response_path):
                raise ValueError(
                    f"{candidate_id}: sample SHA256 does not bind sampled response"
                )
            vectors = {
                name: _load_json_artifact(
                    artifact_root,
                    candidate[name],
                    label=f"{candidate_id}.{name}",
                )
                for name in (
                    "sampled_token_ids",
                    "assistant_action_mask",
                    "old_log_probs",
                    "reference_log_probs",
                )
            }
            _validate_token_vectors(
                candidate_id=candidate_id,
                vectors=vectors,
                trainable_token_count=candidate["trainable_token_count"],
                assistant_action_token_counts=candidate[
                    "assistant_action_token_counts"
                ],
                max_action_tokens=config.rollout.max_action_tokens,
                max_total_assistant_tokens=(
                    config.rollout.max_total_assistant_tokens
                ),
            )
            _verify_artifact(
                artifact_root,
                candidate["rollout_events"],
                label=f"{candidate_id}.rollout_events",
            )
            reward_payload = _load_json_artifact(
                artifact_root,
                candidate["reward_components"],
                label=f"{candidate_id}.reward_components",
            )
            if not isinstance(reward_payload, dict):
                raise ValueError(f"{candidate_id}: reward components must be an object")
            validate_instance(reward_payload, TERMINAL_REWARD_SCHEMA)
            episode_return = _validate_terminal_reward(
                candidate=candidate,
                reward_payload=reward_payload,
                config=config,
            )
            if candidate["outcome_kind"] == "policy_invalid":
                policy_invalid_count += 1
            retry_count += len(candidate["infrastructure_retries"])
            return_candidates.append(
                {
                    "candidate_id": candidate_id,
                    "sample_sha256": candidate["sample_sha256"],
                    "rollout_sample_sha256": _canonical_sha256(candidate),
                    "reward_components_sha256": candidate[
                        "reward_components"
                    ]["sha256"],
                    "trainable_token_count": candidate["trainable_token_count"],
                    "on_policy": True,
                    "outcome_kind": candidate["outcome_kind"],
                    "local_return": 0.0,
                    "episode_return": episode_return,
                }
            )
        return_groups.append(
            {
                "group_id": group_id,
                "group_kind": "episode",
                "state_id": "planner_context_sha256:"
                + group["canonical_state_sha256"],
                "sampling_policy_id": group["sampling_policy_id"],
                "rollout_group_sha256": _canonical_sha256(group),
                "candidates": return_candidates,
            }
        )

    candidate_count = sum(len(group["candidates"]) for group in payload["groups"])
    valid_group_fraction = len(payload["groups"]) / planned_group_count
    if valid_group_fraction < config.admission.minimum_valid_group_fraction:
        raise ValueError(
            "valid-group fraction is below admission threshold: "
            f"{valid_group_fraction:.6f} < "
            f"{config.admission.minimum_valid_group_fraction:.6f}"
        )
    invalid_fraction = policy_invalid_count / candidate_count
    if invalid_fraction > config.admission.maximum_policy_invalid_fraction:
        raise ValueError(
            "policy-invalid fraction exceeds admission threshold: "
            f"{invalid_fraction:.6f} > "
            f"{config.admission.maximum_policy_invalid_fraction:.6f}"
        )
    candidate_return_batch = {
        "schema_version": "0.1",
        "batch_id": payload["batch_id"],
        "reward_policy_id": "geneval2_terminal_outcome@0.1",
        "groups": return_groups,
    }
    validate_instance(candidate_return_batch, CANDIDATE_BATCH_SCHEMA)
    return RolloutAdmission(
        batch_id=payload["batch_id"],
        planned_group_count=planned_group_count,
        group_count=len(payload["groups"]),
        excluded_group_count=len(payload["excluded_groups"]),
        candidate_count=candidate_count,
        policy_invalid_count=policy_invalid_count,
        recovered_infrastructure_retry_count=retry_count,
        candidate_return_batch=candidate_return_batch,
        group_sha256_by_id={
            group["group_id"]: _canonical_sha256(group)
            for group in payload["groups"]
        },
        candidate_sha256_by_id={
            candidate["candidate_id"]: _canonical_sha256(candidate)
            for group in payload["groups"]
            for candidate in group["candidates"]
        },
        reward_sha256_by_id={
            candidate["candidate_id"]: candidate["reward_components"]["sha256"]
            for group in payload["groups"]
            for candidate in group["candidates"]
        },
    )


def validate_rollout_admission(
    payload: dict[str, Any],
    *,
    artifact_root: Path,
    expected_sampling_policy_id: str,
    expected_policy_revision: str,
    expected_checkpoint_sha256: str,
    expected_candidate_counts: dict[str, int],
) -> RolloutAdmission:
    """Generic hash/provenance gate used by backend-adapter replay tests."""

    validate_instance(payload, ROLLOUT_BATCH_SCHEMA)
    root = artifact_root.resolve()
    group_ids: set[str] = set()
    candidate_ids: set[str] = set()
    group_hashes: dict[str, str] = {}
    candidate_hashes: dict[str, str] = {}
    reward_hashes: dict[str, str] = {}
    invalid_count = 0
    retry_count = 0
    if payload["planned_group_count"] != (
        len(payload["groups"]) + len(payload["excluded_groups"])
    ):
        raise ValueError(
            "planned group count must equal admitted plus excluded groups"
        )
    for excluded in payload["excluded_groups"]:
        _add_unique(group_ids, excluded["group_id"], "group_id")
        _verify_artifact(
            root,
            excluded["failure_record"],
            label=f"{excluded['group_id']}.failure_record",
        )
    for group in payload["groups"]:
        group_id = group["group_id"]
        _add_unique(group_ids, group_id, "group_id")
        group_kind = group["group_kind"]
        if group_kind not in expected_candidate_counts:
            raise ValueError(f"{group_id}: unexpected group kind {group_kind}")
        expected_count = expected_candidate_counts[group_kind]
        if len(group["candidates"]) != expected_count:
            raise ValueError(
                f"{group_id}: expected {expected_count} candidates, "
                f"found {len(group['candidates'])}"
            )
        if group["sampling_policy_id"] != expected_sampling_policy_id:
            raise ValueError(f"{group_id}: unexpected sampling policy")
        if group["policy_revision"] != expected_policy_revision:
            raise ValueError(f"{group_id}: stale policy revision")
        if group["policy_checkpoint"]["sha256"] != expected_checkpoint_sha256:
            raise ValueError(f"{group_id}: stale policy checkpoint")
        if group["state_id"] != (
            "planner_context_sha256:" + group["canonical_state_sha256"]
        ):
            raise ValueError(f"{group_id}: state ID and canonical state hash disagree")
        if group["sampling_config_sha256"] != _canonical_sha256(
            group["sampling_config"]
        ):
            raise ValueError(f"{group_id}: sampling config SHA256 mismatch")
        group_hashes[group_id] = _canonical_sha256(group)
        for candidate in group["candidates"]:
            candidate_id = candidate["candidate_id"]
            _add_unique(candidate_ids, candidate_id, "candidate_id")
            response_path = _verify_artifact(
                root,
                candidate["sampled_response"],
                label=f"{candidate_id}.sampled_response",
            )
            if sha256_file(response_path) != candidate["sample_sha256"]:
                raise ValueError(
                    f"{candidate_id}: sample SHA256 does not bind sampled response"
                )
            vectors = {
                name: _load_json_artifact(
                    root,
                    candidate[name],
                    label=f"{candidate_id}.{name}",
                )
                for name in (
                    "sampled_token_ids",
                    "assistant_action_mask",
                    "old_log_probs",
                    "reference_log_probs",
                )
            }
            _validate_token_vectors(
                candidate_id=candidate_id,
                vectors=vectors,
                trainable_token_count=candidate["trainable_token_count"],
                assistant_action_token_counts=candidate[
                    "assistant_action_token_counts"
                ],
                max_action_tokens=group["sampling_config"]["max_action_tokens"],
                max_total_assistant_tokens=group["sampling_config"][
                    "max_episode_assistant_tokens"
                ],
            )
            _verify_artifact(
                root,
                candidate["rollout_events"],
                label=f"{candidate_id}.rollout_events",
            )
            _verify_artifact(
                root,
                candidate["reward_components"],
                label=f"{candidate_id}.reward_components",
            )
            candidate_hashes[candidate_id] = _canonical_sha256(candidate)
            reward_hashes[candidate_id] = candidate["reward_components"]["sha256"]
            invalid_count += int(candidate["outcome_kind"] == "policy_invalid")
            retry_count += len(candidate["infrastructure_retries"])
    candidate_count = len(candidate_ids)
    return RolloutAdmission(
        batch_id=payload["batch_id"],
        planned_group_count=payload["planned_group_count"],
        group_count=len(payload["groups"]),
        excluded_group_count=len(payload["excluded_groups"]),
        candidate_count=candidate_count,
        policy_invalid_count=invalid_count,
        recovered_infrastructure_retry_count=retry_count,
        candidate_return_batch={},
        group_sha256_by_id=group_hashes,
        candidate_sha256_by_id=candidate_hashes,
        reward_sha256_by_id=reward_hashes,
    )


def admit_training_batch(
    rollout_payload: dict[str, Any],
    return_payload: dict[str, Any],
    **admission_kwargs: Any,
) -> RolloutAdmission:
    admission = validate_rollout_admission(
        rollout_payload,
        **admission_kwargs,
    )
    validate_instance(return_payload, CANDIDATE_BATCH_SCHEMA)
    if return_payload["batch_id"] != rollout_payload["batch_id"]:
        raise ValueError("rollout and return batch IDs disagree")
    rollout_groups = {group["group_id"]: group for group in rollout_payload["groups"]}
    if {group["group_id"] for group in return_payload["groups"]} != set(
        rollout_groups
    ):
        raise ValueError("rollout and return group IDs disagree")
    for return_group in return_payload["groups"]:
        group_id = return_group["group_id"]
        rollout_group = rollout_groups[group_id]
        expected_group_fields = {
            "group_kind": rollout_group["group_kind"],
            "state_id": rollout_group["state_id"],
            "sampling_policy_id": rollout_group["sampling_policy_id"],
            "rollout_group_sha256": admission.group_sha256_by_id[group_id],
        }
        for name, expected in expected_group_fields.items():
            if return_group[name] != expected:
                raise ValueError(f"{group_id}: return {name} binding mismatch")
        rollout_candidates = {
            item["candidate_id"]: item for item in rollout_group["candidates"]
        }
        if {item["candidate_id"] for item in return_group["candidates"]} != set(
            rollout_candidates
        ):
            raise ValueError(f"{group_id}: candidate IDs disagree")
        for returned in return_group["candidates"]:
            candidate_id = returned["candidate_id"]
            sampled = rollout_candidates[candidate_id]
            expected_candidate_fields = {
                "sample_sha256": sampled["sample_sha256"],
                "rollout_sample_sha256": admission.candidate_sha256_by_id[
                    candidate_id
                ],
                "reward_components_sha256": admission.reward_sha256_by_id[
                    candidate_id
                ],
                "trainable_token_count": sampled["trainable_token_count"],
                "outcome_kind": sampled["outcome_kind"],
                "on_policy": True,
            }
            for name, expected in expected_candidate_fields.items():
                if returned[name] != expected:
                    raise ValueError(
                        f"{candidate_id}: return {name} binding mismatch"
                    )
    return RolloutAdmission(
        **{
            **admission.__dict__,
            "candidate_return_batch": return_payload,
        }
    )


def _validate_terminal_reward(
    *,
    candidate: dict[str, Any],
    reward_payload: dict[str, Any],
    config: RlExperimentConfig,
) -> float:
    candidate_id = candidate["candidate_id"]
    if reward_payload["candidate_id"] != candidate_id:
        raise ValueError(f"{candidate_id}: reward candidate ID mismatch")
    if reward_payload["outcome_kind"] != candidate["outcome_kind"]:
        raise ValueError(f"{candidate_id}: reward outcome kind mismatch")
    if candidate["outcome_kind"] == "success":
        score_payload = reward_payload["submitted_score"]
        if reward_payload["submitted_attempt_id"] is None or score_payload is None:
            raise ValueError(f"{candidate_id}: success requires a submitted Attempt")
        score = AttemptScore(**score_payload)
        expected_utility = score.utility(
            gm_tie_break_scale=config.reward.gm_tie_break_scale
        )
        expected_penalty = 0.0
        expected_total = expected_utility
    else:
        if (
            reward_payload["submitted_attempt_id"] is not None
            or reward_payload["submitted_score"] is not None
        ):
            raise ValueError(
                f"{candidate_id}: policy-invalid outcome cannot submit an Attempt"
            )
        expected_utility = 0.0
        expected_penalty = config.reward.invalid_action_penalty
        expected_total = -expected_penalty
    for name, actual, expected in (
        ("terminal_utility", reward_payload["terminal_utility"], expected_utility),
        (
            "invalid_action_penalty",
            reward_payload["invalid_action_penalty"],
            expected_penalty,
        ),
        ("total_return", reward_payload["total_return"], expected_total),
    ):
        if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(
                f"{candidate_id}: {name}={actual!r}, expected {expected!r}"
            )
    return float(expected_total)


def _validate_token_vectors(
    *,
    candidate_id: str,
    vectors: dict[str, Any],
    trainable_token_count: int,
    assistant_action_token_counts: list[int],
    max_action_tokens: int,
    max_total_assistant_tokens: int,
) -> None:
    if not all(isinstance(value, list) for value in vectors.values()):
        raise ValueError(f"{candidate_id}: token/log-prob artifacts must be JSON arrays")
    lengths = {len(value) for value in vectors.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise ValueError(f"{candidate_id}: token/log-prob arrays must align")
    token_ids = vectors["sampled_token_ids"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in token_ids):
        raise ValueError(f"{candidate_id}: sampled token IDs must be non-negative integers")
    mask = vectors["assistant_action_mask"]
    if any(value not in (0, 1, False, True) for value in mask):
        raise ValueError(f"{candidate_id}: assistant action mask must contain 0/1")
    if sum(bool(value) for value in mask) != trainable_token_count:
        raise ValueError(f"{candidate_id}: trainable token count disagrees with mask")
    if sum(assistant_action_token_counts) != trainable_token_count:
        raise ValueError(
            f"{candidate_id}: per-action token counts disagree with trainable count"
        )
    if max(assistant_action_token_counts) > max_action_tokens:
        raise ValueError(
            f"{candidate_id}: one assistant action exceeds max_action_tokens"
        )
    if trainable_token_count > max_total_assistant_tokens:
        raise ValueError(
            f"{candidate_id}: cumulative assistant tokens exceed episode limit"
        )
    for name in ("old_log_probs", "reference_log_probs"):
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in vectors[name]
        ):
            raise ValueError(f"{candidate_id}: {name} must contain finite numbers")


def _load_json_artifact(
    root: Path,
    artifact: dict[str, str],
    *,
    label: str,
) -> Any:
    path = _verify_artifact(root, artifact, label=label)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label}: invalid JSON artifact") from exc


def _verify_artifact(
    root: Path,
    artifact: dict[str, str],
    *,
    label: str,
) -> Path:
    ref = Path(artifact["ref"])
    if ref.is_absolute():
        raise ValueError(f"{label}: artifact ref must be relative")
    path = (root / ref).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{label}: artifact ref escapes the artifact root")
    if not path.is_file():
        raise ValueError(f"{label}: missing artifact {ref}")
    actual = sha256_file(path)
    if actual != artifact["sha256"]:
        raise ValueError(f"{label}: SHA256 mismatch")
    return path


def _add_unique(seen: set[str], value: str, label: str) -> None:
    if value in seen:
        raise ValueError(f"duplicate {label}: {value}")
    seen.add(value)


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
