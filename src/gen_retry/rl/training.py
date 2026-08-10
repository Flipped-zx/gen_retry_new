from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.rl.credit import CreditCandidate, RewardConfig, combine_group_advantages
from gen_retry.rl.objective import ObjectiveConfig
from gen_retry.runtime.json_canonical import canonical_json


CANDIDATE_BATCH_SCHEMA = "rl_candidate_return_batch_v0_1.schema.json"
ADVANTAGE_BATCH_SCHEMA = "rl_advantage_batch_v0_1.schema.json"


def load_reward_config(path: Path) -> RewardConfig:
    payload = _load_config_mapping(path)
    reward = payload.get("reward")
    if not isinstance(reward, dict):
        raise ValueError("RL config must contain a reward mapping")
    return RewardConfig.from_mapping(reward)


def load_objective_config(path: Path) -> ObjectiveConfig:
    payload = _load_config_mapping(path)
    optimization = payload.get("optimization")
    if not isinstance(optimization, dict):
        raise ValueError("RL config must contain an optimization mapping")
    return ObjectiveConfig.from_mapping(optimization)


def _load_config_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError("RL reward config must be a mapping")
    return payload


def build_advantage_batch(
    payload: dict[str, Any],
    *,
    config: RewardConfig,
) -> dict[str, Any]:
    validate_instance(payload, CANDIDATE_BATCH_SCHEMA)
    expected_policy_id = (
        f"{config.reward_policy_id}@{config.reward_policy_version}"
    )
    if payload["reward_policy_id"] != expected_policy_id:
        raise ValueError(
            "candidate batch reward policy does not match the loaded config: "
            f"{payload['reward_policy_id']} != {expected_policy_id}"
        )
    groups: list[dict[str, Any]] = []
    for group in payload["groups"]:
        candidates = tuple(
            CreditCandidate(
                candidate_id=item["candidate_id"],
                state_id=group["state_id"],
                sampling_policy_id=group["sampling_policy_id"],
                sample_sha256=item["sample_sha256"],
                rollout_sample_sha256=item["rollout_sample_sha256"],
                reward_components_sha256=item["reward_components_sha256"],
                trainable_token_count=item["trainable_token_count"],
                on_policy=item["on_policy"],
                outcome_kind=item["outcome_kind"],
                local_return=item["local_return"],
                episode_return=item["episode_return"],
            )
            for item in group["candidates"]
        )
        advantages = combine_group_advantages(
            candidates,
            group_kind=group["group_kind"],
            config=config,
        )
        by_id = {
            item.candidate_id: item for item in advantages.candidates
        }
        groups.append(
            {
                "group_id": group["group_id"],
                "group_kind": group["group_kind"],
                "state_id": group["state_id"],
                "sampling_policy_id": group["sampling_policy_id"],
                "rollout_group_sha256": group["rollout_group_sha256"],
                "advantage_stats": {
                    "local_return_std": advantages.local_return_std,
                    "episode_return_std": advantages.episode_return_std,
                    "combined_advantage_std": (
                        advantages.combined_advantage_std
                    ),
                    "terminal_weight": advantages.terminal_weight,
                    "eligible_for_policy_loss": (
                        advantages.eligible_for_policy_loss
                    ),
                },
                "candidates": [
                    {
                        **item,
                        "local_advantage": by_id[item["candidate_id"]].local_advantage,
                        "episode_advantage": by_id[
                            item["candidate_id"]
                        ].episode_advantage,
                        "combined_advantage": by_id[
                            item["candidate_id"]
                        ].combined_advantage,
                    }
                    for item in group["candidates"]
                ],
            }
        )
    source_sha256 = hashlib.sha256(
        canonical_json(payload).encode("utf-8")
    ).hexdigest()
    output = {
        "schema_version": "0.1",
        "batch_id": payload["batch_id"],
        "reward_policy": config.to_dict(),
        "source_batch_sha256": source_sha256,
        "groups": groups,
    }
    validate_instance(output, ADVANTAGE_BATCH_SCHEMA)
    return output


def load_advantage_batch(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("RL advantage batch must be a JSON object")
    return payload


def write_advantage_batch(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
