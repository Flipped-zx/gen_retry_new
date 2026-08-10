from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from gen_retry.rl.config import RlExperimentConfig
from gen_retry.runtime.json_canonical import canonical_json


@dataclass(frozen=True)
class VerlAdapterPlan:
    adapter_id: str
    upstream_reference: str
    hydra_overrides: tuple[str, ...]
    gen_retry_contract: dict[str, Any]
    stock_runtime_blockers: tuple[str, ...]
    plan_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_verl_adapter_plan(config: RlExperimentConfig) -> VerlAdapterPlan:
    """Map frozen Gen-Retry settings onto the inspected rLLM/verl surface."""

    trainer = config.trainer
    rollout = config.rollout
    optimization = config.optimization
    overrides = (
        "algorithm.adv_estimator=grpo",
        "algorithm.use_kl_in_reward=False",
        f"data.train_batch_size={rollout.prompt_batch_size}",
        f"data.max_prompt_length={rollout.max_context_tokens}",
        f"data.max_response_length={rollout.max_total_assistant_tokens}",
        f"data.seed={rollout.seed}",
        f"actor_rollout_ref.model.path={config.base_checkpoint}",
        f"actor_rollout_ref.rollout.name={trainer.rollout_engine}",
        "actor_rollout_ref.rollout.mode=async",
        f"actor_rollout_ref.rollout.dtype={trainer.dtype}",
        (
            "actor_rollout_ref.rollout.tensor_model_parallel_size="
            f"{trainer.rollout_tensor_parallel_size}"
        ),
        (
            "actor_rollout_ref.rollout.gpu_memory_utilization="
            f"{trainer.rollout_gpu_memory_utilization}"
        ),
        f"actor_rollout_ref.rollout.temperature={rollout.temperature}",
        f"actor_rollout_ref.rollout.top_p={rollout.top_p}",
        f"actor_rollout_ref.rollout.top_k={rollout.top_k}",
        f"actor_rollout_ref.rollout.n={rollout.full_rollouts_per_prompt}",
        "actor_rollout_ref.rollout.calculate_log_probs=True",
        (
            "actor_rollout_ref.actor.ppo_mini_batch_size="
            f"{trainer.prompt_mini_batch_size}"
        ),
        (
            "actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu="
            f"{trainer.ppo_micro_batch_per_device}"
        ),
        f"actor_rollout_ref.actor.ppo_epochs={trainer.ppo_epochs}",
        f"actor_rollout_ref.actor.optim.lr={trainer.learning_rate}",
        "actor_rollout_ref.actor.use_kl_loss=True",
        (
            "actor_rollout_ref.actor.kl_loss_coef="
            f"{optimization.reference_kl_coefficient}"
        ),
        f"actor_rollout_ref.actor.clip_ratio={optimization.clip_ratio_low}",
        (
            "actor_rollout_ref.actor.clip_ratio_high="
            f"{optimization.clip_ratio_high}"
        ),
        (
            "actor_rollout_ref.actor.loss_agg_mode="
            f"{trainer.sequence_loss_reduction}"
        ),
        f"actor_rollout_ref.actor.entropy_coeff={trainer.entropy_coefficient}",
        (
            "actor_rollout_ref.actor.fsdp_config.fsdp_size="
            f"{trainer.actor_fsdp_size}"
        ),
        (
            "actor_rollout_ref.actor.fsdp_config.param_offload="
            f"{trainer.parameter_offload}"
        ),
        (
            "actor_rollout_ref.actor.fsdp_config.optimizer_offload="
            f"{trainer.optimizer_offload}"
        ),
        f"trainer.n_gpus_per_node={config.resources.trainer_devices}",
        f"trainer.save_freq={trainer.checkpoint_every_steps}",
        f"trainer.test_freq={trainer.validation_every_steps}",
        f"trainer.total_epochs={trainer.train_epochs}",
    )
    contract = {
        "execution_profile": config.execution_profile,
        "action_protocol_version": config.action_protocol_version,
        "planner_context_schema_version": config.planner_context_schema_version,
        "staged_rollout_then_train": True,
        "rollout_sample_schema": "rl_rollout_sample_batch_v0.1",
        "optimizer_bridge": "gen_retry.rl.optimizer.prepare_optimizer_batch",
        "require_persisted_old_log_probs": (
            trainer.require_persisted_old_log_probs
        ),
        "require_persisted_reference_log_probs": (
            trainer.require_persisted_reference_log_probs
        ),
        "train_action_tokens_only": optimization.train_action_tokens_only,
        "train_tool_responses": optimization.train_tool_responses,
        "train_environment_observations": (
            optimization.train_environment_observations
        ),
        "infrastructure_failure_policy": "retry_then_exclude",
        "policy_invalid_reward": -config.reward.invalid_action_penalty,
        "zero_variance_group_policy": "account_and_mask",
        "token_budgets": {
            "per_action": rollout.max_action_tokens,
            "episode_assistant_cumulative": rollout.max_total_assistant_tokens,
            "verl_full_response_length": rollout.max_total_assistant_tokens,
        },
        "stage_admission": {
            "minimum_valid_group_fraction": (
                config.admission.minimum_valid_group_fraction
            ),
            "maximum_zero_variance_group_fraction": (
                config.admission.maximum_zero_variance_group_fraction
            ),
            "maximum_policy_invalid_fraction": (
                config.admission.maximum_policy_invalid_fraction
            ),
        },
        "manifests": {
            "train": str(config.admission.train_manifest),
            "development": str(config.admission.development_manifest),
            "confirmation": str(config.admission.confirmation_manifest),
        },
    }
    blockers = (
        "implement Gen-Retry strict-JSON multi-turn workflow for rLLM",
        "preserve Qwen3-VL image token/grid inputs through cumulative retokenization",
        "feed admitted persisted old/reference log-probs into verl without recomputation",
        "release rollout services before the eight-device FSDP optimizer stage",
        "validate the vendor HCU runtime with a 32-group resume/replay smoke",
    )
    unsigned = {
        "adapter_id": "rllm_verl_adapter@0.1",
        "upstream_reference": (
            "Gen-Searcher@e5078d31859bafee6b6b610f0cd40095cc72e2a4:"
            "Gen-DeepResearch-RL/rllm"
        ),
        "hydra_overrides": overrides,
        "gen_retry_contract": contract,
        "stock_runtime_blockers": blockers,
    }
    digest = hashlib.sha256(canonical_json(unsigned).encode("utf-8")).hexdigest()
    return VerlAdapterPlan(**unsigned, plan_sha256=digest)
