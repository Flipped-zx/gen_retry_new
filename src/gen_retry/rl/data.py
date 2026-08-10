from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from gen_retry.domain.artifacts import sha256_file
from gen_retry.phase5.flow_dppo_selection import (
    FLOW_DPPO_COMMIT,
    FLOW_DPPO_DATASET_REF,
    FLOW_DPPO_DATASET_SHA256,
    build_flow_dppo_heldout_boundary,
    flow_dppo_candidate_from_row,
    flow_dppo_selection_coverage,
    load_flow_dppo_rows,
)
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.rl.config import RlExperimentConfig
from gen_retry.runtime.json_canonical import canonical_json


PROMPT_MANIFEST_SCHEMA = "rl_prompt_manifest_v0_1.schema.json"
EXPERIMENT_DECLARATION_SCHEMA = "rl_experiment_declaration_v0_1.schema.json"
SPLIT_ORDER = ("confirmation", "development", "train")
DEFAULT_SPLIT_COUNTS = {
    "train": 1000,
    "development": 200,
    "confirmation": 500,
}


def build_naive_grpo_prompt_manifests(
    *,
    dataset_path: Path,
    heldout_dataset_path: Path,
    excluded_selection_paths: list[Path],
    split_counts: Mapping[str, int] = DEFAULT_SPLIT_COUNTS,
    seed: int = 42,
) -> dict[str, dict[str, Any]]:
    if set(split_counts) != set(SPLIT_ORDER):
        raise ValueError(f"split_counts must contain {sorted(SPLIT_ORDER)}")
    if any(isinstance(value, bool) or value <= 0 for value in split_counts.values()):
        raise ValueError("all split counts must be positive integers")

    rows, source_sha256 = load_flow_dppo_rows(dataset_path)
    if source_sha256 != FLOW_DPPO_DATASET_SHA256:
        raise ValueError(
            "Flow-DPPO dataset fingerprint mismatch: "
            f"{source_sha256} != {FLOW_DPPO_DATASET_SHA256}"
        )
    boundary = build_flow_dppo_heldout_boundary(rows, heldout_dataset_path)
    if boundary["heldout_row_count"] != 800:
        raise ValueError("the frozen official Geneval2 boundary must contain 800 rows")

    excluded_rows: set[str] = set()
    excluded_prompts: set[str] = set()
    exclusion_records: list[dict[str, Any]] = []
    for path in excluded_selection_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        selected = payload.get("selected_prompts")
        if not isinstance(selected, list):
            raise ValueError(f"excluded selection has no selected_prompts: {path}")
        for candidate in selected:
            excluded_rows.add(str(candidate["source_row_sha256"]))
            excluded_prompts.add(str(candidate["original_prompt"]).strip().lower())
        exclusion_records.append(
            {
                "ref": str(path),
                "sha256": sha256_file(path),
                "selected_count": len(selected),
            }
        )

    eligible = []
    for row in rows:
        normalized_prompt = row["prompt"].strip().lower()
        if normalized_prompt in boundary["heldout_prompts"]:
            continue
        if row["_semantic_family_id"] in boundary["heldout_family_ids"]:
            continue
        if row["_row_sha256"] in excluded_rows:
            continue
        if normalized_prompt in excluded_prompts:
            continue
        row = dict(row)
        row["_rl_semantic_family_id"] = _rl_semantic_family_id(row)
        eligible.append(row)

    representatives = _one_result_blind_row_per_family(eligible, seed=seed)
    required = sum(split_counts.values())
    if len(representatives) < required:
        raise ValueError(
            f"need {required} family-distinct prompts, found {len(representatives)}"
        )
    tier_counts = Counter(_difficulty_band(row) for row in representatives)
    available_by_tier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in representatives:
        available_by_tier[_difficulty_band(row)].append(row)

    manifests: dict[str, dict[str, Any]] = {}
    assigned_families: set[str] = set()
    for split in SPLIT_ORDER:
        count = int(split_counts[split])
        quotas = _proportional_quotas(tier_counts, count)
        selected_rows: list[dict[str, Any]] = []
        for tier in ("easy", "medium", "hard"):
            pool = [
                row
                for row in available_by_tier[tier]
                if row["_rl_semantic_family_id"] not in assigned_families
            ]
            pool.sort(
                key=lambda row: _stable_digest(
                    seed, split, row["_row_sha256"]
                )
            )
            if len(pool) < quotas[tier]:
                raise ValueError(
                    f"{split}: need {quotas[tier]} {tier} families, found {len(pool)}"
                )
            selected_rows.extend(pool[: quotas[tier]])
        selected_rows.sort(
            key=lambda row: _stable_digest(seed, split, row["_row_sha256"])
        )
        selected_prompts = []
        for rank, row in enumerate(selected_rows, start=1):
            row = dict(row)
            row["_selection_score"] = 0
            row["_selection_reason"] = {
                "policy": "result_blind_family_distinct_stratified_hash_v1",
                "seed": seed,
                "split": split,
                "stable_rank_sha256": _stable_digest(
                    seed, split, row["_row_sha256"]
                ),
            }
            candidate = flow_dppo_candidate_from_row(
                row,
                selection_rank=rank,
                source_commit=FLOW_DPPO_COMMIT,
                source_file_sha256=source_sha256,
            )
            candidate["rl_semantic_family_id"] = row[
                "_rl_semantic_family_id"
            ]
            selected_prompts.append(candidate)
            assigned_families.add(row["_rl_semantic_family_id"])

        manifest = {
            "schema_version": "0.1",
            "manifest_id": f"naive_grpo_{split}_v0_1_s{seed}",
            "split": split,
            "selection_method": (
                "flow_dppo_result_blind_family_distinct_stratified_hash_v1"
            ),
            "seed": seed,
            "selected_count": len(selected_prompts),
            "tier_counts": dict(
                sorted(Counter(item["difficulty_tier"] for item in selected_prompts).items())
            ),
            "source": {
                "repository": "Tencent-Hunyuan/UniRL",
                "commit": FLOW_DPPO_COMMIT,
                "dataset_ref": FLOW_DPPO_DATASET_REF,
                "dataset_sha256": source_sha256,
                "dataset_row_count": len(rows),
            },
            "boundaries": {
                "official_geneval2_held_out": True,
                "official_geneval2_ref": str(heldout_dataset_path),
                "official_geneval2_sha256": boundary[
                    "heldout_dataset_sha256"
                ],
                "official_geneval2_row_count": boundary["heldout_row_count"],
                "official_semantic_family_rows_excluded": boundary[
                    "semantic_family_overlap_rows"
                ],
                "prior_selection_records": exclusion_records,
                "prior_source_rows_excluded": len(excluded_rows),
                "eligible_source_rows": len(eligible),
                "eligible_rl_families": len(representatives),
                "rl_family_definition": (
                    "sorted evaluator-derived entities + sorted relation phrases + "
                    "ordered skills + actual VQA count"
                ),
                "cross_split_rl_family_disjoint": True,
                "selection_is_image_result_blind": True,
            },
            "selected_prompts": selected_prompts,
            "coverage": flow_dppo_selection_coverage(selected_prompts),
        }
        validate_instance(manifest, PROMPT_MANIFEST_SCHEMA)
        manifests[split] = manifest
    _validate_split_disjointness(manifests)
    return manifests


def build_naive_grpo_experiment_declaration(
    *,
    config: RlExperimentConfig,
    config_path: Path,
    manifest_paths: Mapping[str, Path],
) -> dict[str, Any]:
    split_records: dict[str, dict[str, Any]] = {}
    for split, path in manifest_paths.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        validate_instance(payload, PROMPT_MANIFEST_SCHEMA)
        if payload["split"] != split:
            raise ValueError(f"manifest split mismatch for {split}: {path}")
        split_records[split] = {
            "ref": str(path),
            "sha256": sha256_file(path),
            "selected_count": payload["selected_count"],
            "manifest_id": payload["manifest_id"],
        }
    declaration = {
        "schema_version": "0.1",
        "experiment_id": "naive_geneval2_grpo_v0_1_s42",
        "method": f"{config.method_id}@{config.method_version}",
        "config": {"ref": str(config_path), "sha256": sha256_file(config_path)},
        "policy": {
            "revision": config.policy_revision,
            "checkpoint_sha256": config.checkpoint_sha256,
            "planner_context_schema_version": config.planner_context_schema_version,
            "action_protocol_version": config.action_protocol_version,
        },
        "execution_profile": config.execution_profile,
        "reward_policy": (
            f"{config.reward.reward_policy_id}@{config.reward.reward_policy_version}"
        ),
        "splits": split_records,
        "rollout": {
            "seed": config.rollout.seed,
            "rollouts_per_prompt": config.rollout.full_rollouts_per_prompt,
            "temperature": config.rollout.temperature,
            "top_p": config.rollout.top_p,
            "top_k": config.rollout.top_k,
            "max_image_attempts": config.rollout.max_image_attempts,
            "max_action_tokens": config.rollout.max_action_tokens,
            "max_episode_assistant_tokens": (
                config.rollout.max_total_assistant_tokens
            ),
        },
        "optimization": {
            "learning_rate": config.trainer.learning_rate,
            "ppo_epochs": config.trainer.ppo_epochs,
            "train_epochs": config.trainer.train_epochs,
            "reference_kl_coefficient": (
                config.optimization.reference_kl_coefficient
            ),
            "clip_ratio_low": config.optimization.clip_ratio_low,
            "clip_ratio_high": config.optimization.clip_ratio_high,
        },
        "stopping_and_scale": {
            "smoke_prompts": config.admission.smoke_prompts,
            "pilot_prompts": config.admission.pilot_prompts,
            "minimum_trainable_prompts": config.admission.minimum_trainable_prompts,
            "first_efficacy_prompts": config.admission.first_efficacy_prompts,
            "conditional_expand_to_prompts": config.admission.expand_to_prompts,
            "minimum_valid_group_fraction": (
                config.admission.minimum_valid_group_fraction
            ),
            "maximum_zero_variance_group_fraction": (
                config.admission.maximum_zero_variance_group_fraction
            ),
            "maximum_policy_invalid_fraction": (
                config.admission.maximum_policy_invalid_fraction
            ),
            "increase_rollouts_to": config.admission.increase_rollouts_to,
        },
        "primary_metrics": [
            "submitted_geneval2_pass_count",
            "submitted_geneval2_soft_tifa_gm",
            "all_atoms_pass_rate",
            "image_calls_per_episode",
        ],
        "official_geneval2_800_reserved_for_one_time_external_evaluation": True,
    }
    validate_instance(declaration, EXPERIMENT_DECLARATION_SCHEMA)
    return declaration


def validate_frozen_rl_data(
    *, config: RlExperimentConfig, config_path: Path
) -> dict[str, Any]:
    declaration_path = config.admission.experiment_declaration
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    validate_instance(declaration, EXPERIMENT_DECLARATION_SCHEMA)
    if declaration["method"] != f"{config.method_id}@{config.method_version}":
        raise ValueError("experiment declaration method does not match config")
    if declaration["config"]["ref"] != str(config_path):
        raise ValueError("experiment declaration config ref mismatch")
    if declaration["config"]["sha256"] != sha256_file(config_path):
        raise ValueError("experiment declaration config SHA256 mismatch")
    if declaration["policy"]["checkpoint_sha256"] != config.checkpoint_sha256:
        raise ValueError("experiment declaration checkpoint SHA256 mismatch")
    if declaration["policy"]["revision"] != config.policy_revision:
        raise ValueError("experiment declaration policy revision mismatch")
    if declaration["policy"]["planner_context_schema_version"] != (
        config.planner_context_schema_version
    ):
        raise ValueError("experiment declaration PlannerContext mismatch")
    if declaration["policy"]["action_protocol_version"] != (
        config.action_protocol_version
    ):
        raise ValueError("experiment declaration Action protocol mismatch")
    if declaration["execution_profile"] != config.execution_profile:
        raise ValueError("experiment declaration execution profile mismatch")
    expected_reward_policy = (
        f"{config.reward.reward_policy_id}@{config.reward.reward_policy_version}"
    )
    if declaration["reward_policy"] != expected_reward_policy:
        raise ValueError("experiment declaration reward policy mismatch")
    expected_rollout = {
        "seed": config.rollout.seed,
        "rollouts_per_prompt": config.rollout.full_rollouts_per_prompt,
        "temperature": config.rollout.temperature,
        "top_p": config.rollout.top_p,
        "top_k": config.rollout.top_k,
        "max_image_attempts": config.rollout.max_image_attempts,
        "max_action_tokens": config.rollout.max_action_tokens,
        "max_episode_assistant_tokens": config.rollout.max_total_assistant_tokens,
    }
    if declaration["rollout"] != expected_rollout:
        raise ValueError("experiment declaration rollout parameters mismatch")
    expected_optimization = {
        "learning_rate": config.trainer.learning_rate,
        "ppo_epochs": config.trainer.ppo_epochs,
        "train_epochs": config.trainer.train_epochs,
        "reference_kl_coefficient": (
            config.optimization.reference_kl_coefficient
        ),
        "clip_ratio_low": config.optimization.clip_ratio_low,
        "clip_ratio_high": config.optimization.clip_ratio_high,
    }
    if declaration["optimization"] != expected_optimization:
        raise ValueError("experiment declaration optimization parameters mismatch")
    expected_stopping = {
        "smoke_prompts": config.admission.smoke_prompts,
        "pilot_prompts": config.admission.pilot_prompts,
        "minimum_trainable_prompts": config.admission.minimum_trainable_prompts,
        "first_efficacy_prompts": config.admission.first_efficacy_prompts,
        "conditional_expand_to_prompts": config.admission.expand_to_prompts,
        "minimum_valid_group_fraction": (
            config.admission.minimum_valid_group_fraction
        ),
        "maximum_zero_variance_group_fraction": (
            config.admission.maximum_zero_variance_group_fraction
        ),
        "maximum_policy_invalid_fraction": (
            config.admission.maximum_policy_invalid_fraction
        ),
        "increase_rollouts_to": config.admission.increase_rollouts_to,
    }
    if declaration["stopping_and_scale"] != expected_stopping:
        raise ValueError("experiment declaration stopping parameters mismatch")

    expected_paths = {
        "train": config.admission.train_manifest,
        "development": config.admission.development_manifest,
        "confirmation": config.admission.confirmation_manifest,
    }
    manifests: dict[str, dict[str, Any]] = {}
    for split, path in expected_paths.items():
        record = declaration["splits"][split]
        if record["ref"] != str(path):
            raise ValueError(f"{split} manifest ref does not match config")
        if record["sha256"] != sha256_file(path):
            raise ValueError(f"{split} manifest SHA256 mismatch")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        validate_instance(manifest, PROMPT_MANIFEST_SCHEMA)
        if manifest["split"] != split:
            raise ValueError(f"{split} manifest declares the wrong split")
        if manifest["selected_count"] != len(manifest["selected_prompts"]):
            raise ValueError(f"{split} manifest selected_count mismatch")
        if record["selected_count"] != manifest["selected_count"]:
            raise ValueError(f"{split} declaration count mismatch")
        tier_histogram = Counter(
            prompt["difficulty_tier"]
            for prompt in manifest["selected_prompts"]
        )
        observed_tiers = {
            tier: tier_histogram[tier] for tier in ("easy", "medium", "hard")
        }
        if manifest["tier_counts"] != observed_tiers:
            raise ValueError(f"{split} manifest tier counts mismatch")
        for prompt in manifest["selected_prompts"]:
            if prompt["provenance"]["source_file_sha256"] != (
                manifest["source"]["dataset_sha256"]
            ):
                raise ValueError(f"{split} prompt source-file SHA256 mismatch")
            if prompt["provenance"]["source_row_sha256"] != (
                prompt["source_row_sha256"]
            ):
                raise ValueError(f"{split} prompt source-row SHA256 mismatch")
        manifests[split] = manifest
    _validate_split_disjointness(manifests)
    _validate_shared_boundaries_and_exclusions(manifests)
    if manifests["train"]["selected_count"] < config.admission.expand_to_prompts:
        raise ValueError("train manifest cannot support conditional expansion")
    return {
        split: {
            "selected_count": manifest["selected_count"],
            "sha256": declaration["splits"][split]["sha256"],
        }
        for split, manifest in manifests.items()
    }


def _one_result_blind_row_per_family(
    rows: list[dict[str, Any]], *, seed: int
) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[row["_rl_semantic_family_id"]].append(row)
    return [
        min(
            family_rows,
            key=lambda row: _stable_digest(seed, "family", row["_row_sha256"]),
        )
        for _, family_rows in sorted(by_family.items())
    ]


def _rl_semantic_family_id(row: dict[str, Any]) -> str:
    payload = {
        "entities": sorted(row["_features"]["entities"]),
        "relation_phrases": sorted(row["_features"]["relation_phrases"]),
        "ordered_skills": [str(skill) for skill in row["skills"]],
        "actual_vqa_count": len(row["vqa_list"]),
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"rlsf_{digest[:16]}"


def _difficulty_band(row: dict[str, Any]) -> str:
    atom_count = int(row["atom_count"])
    if atom_count <= 5:
        return "easy"
    if atom_count <= 8:
        return "medium"
    return "hard"


def _proportional_quotas(
    tier_counts: Mapping[str, int], total: int
) -> dict[str, int]:
    available = sum(tier_counts.values())
    exact = {
        tier: total * tier_counts.get(tier, 0) / available
        for tier in ("easy", "medium", "hard")
    }
    quotas = {tier: math.floor(value) for tier, value in exact.items()}
    remainder = total - sum(quotas.values())
    order = sorted(
        exact,
        key=lambda tier: (exact[tier] - quotas[tier], tier),
        reverse=True,
    )
    for tier in order[:remainder]:
        quotas[tier] += 1
    return quotas


def _stable_digest(seed: int, namespace: str, value: str) -> str:
    return hashlib.sha256(f"{seed}:{namespace}:{value}".encode("utf-8")).hexdigest()


def _validate_split_disjointness(
    manifests: Mapping[str, Mapping[str, Any]],
) -> None:
    seen_rows: set[str] = set()
    seen_prompts: set[str] = set()
    seen_families: set[str] = set()
    for split in ("train", "development", "confirmation"):
        for prompt in manifests[split]["selected_prompts"]:
            row = prompt["source_row_sha256"]
            normalized_prompt = prompt["original_prompt"].strip().lower()
            family = prompt["rl_semantic_family_id"]
            if row in seen_rows or normalized_prompt in seen_prompts:
                raise ValueError(f"{split} overlaps an earlier split by prompt row")
            if family in seen_families:
                raise ValueError(f"{split} overlaps an earlier split by RL family")
            seen_rows.add(row)
            seen_prompts.add(normalized_prompt)
            seen_families.add(family)


def _validate_shared_boundaries_and_exclusions(
    manifests: Mapping[str, Mapping[str, Any]],
) -> None:
    source_records = {
        canonical_json(manifest["source"]) for manifest in manifests.values()
    }
    if len(source_records) != 1:
        raise ValueError("RL prompt manifests do not share one source dataset")
    boundary_keys = (
        "official_geneval2_ref",
        "official_geneval2_sha256",
        "official_geneval2_row_count",
        "prior_selection_records",
        "rl_family_definition",
    )
    boundary_records = {
        canonical_json(
            {key: manifest["boundaries"][key] for key in boundary_keys}
        )
        for manifest in manifests.values()
    }
    if len(boundary_records) != 1:
        raise ValueError("RL prompt manifests do not share one data boundary")

    boundary = next(iter(manifests.values()))["boundaries"]
    heldout_path = Path(boundary["official_geneval2_ref"])
    if not heldout_path.is_file():
        raise ValueError("official Geneval2 boundary file is missing")
    if sha256_file(heldout_path) != boundary["official_geneval2_sha256"]:
        raise ValueError("official Geneval2 boundary SHA256 mismatch")

    excluded_rows: set[str] = set()
    excluded_prompts: set[str] = set()
    for record in boundary["prior_selection_records"]:
        path = Path(record["ref"])
        if not path.is_file():
            raise ValueError(f"prior selection is missing: {path}")
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"prior selection SHA256 mismatch: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        selected = payload.get("selected_prompts")
        if not isinstance(selected, list) or len(selected) != record["selected_count"]:
            raise ValueError(f"prior selection count mismatch: {path}")
        for prompt in selected:
            excluded_rows.add(str(prompt["source_row_sha256"]))
            excluded_prompts.add(str(prompt["original_prompt"]).strip().lower())
    for split, manifest in manifests.items():
        for prompt in manifest["selected_prompts"]:
            if prompt["source_row_sha256"] in excluded_rows:
                raise ValueError(f"{split} reuses a prior selected source row")
            if prompt["original_prompt"].strip().lower() in excluded_prompts:
                raise ValueError(f"{split} reuses a prior selected prompt")
