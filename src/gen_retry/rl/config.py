from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from gen_retry.rl.credit import RewardConfig
from gen_retry.rl.objective import ObjectiveConfig


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _strict_kwargs(cls: type, payload: Mapping[str, Any], name: str) -> dict[str, Any]:
    unknown = set(payload) - set(cls.__dataclass_fields__)
    if unknown:
        raise ValueError(f"unknown {name} fields: {sorted(unknown)}")
    return dict(payload)


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _non_negative_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class RolloutConfig:
    prompt_source: str
    full_rollouts_per_prompt: int
    pivot_groups_per_prompt: int
    max_image_attempts: int
    require_on_policy_candidates: bool
    allow_forced_action_candidates_for_training: bool
    prompt_batch_size: int
    temperature: float
    top_p: float
    top_k: int
    max_context_tokens: int
    max_action_tokens: int
    max_total_assistant_tokens: int
    seed: int
    pivot_candidates: int | None = None
    pivot_continuation: str | None = None

    def __post_init__(self) -> None:
        if not self.prompt_source:
            raise ValueError("rollout.prompt_source must be non-empty")
        for name in (
            "full_rollouts_per_prompt",
            "max_image_attempts",
            "prompt_batch_size",
            "max_context_tokens",
            "max_action_tokens",
            "max_total_assistant_tokens",
        ):
            _positive_int(getattr(self, name), f"rollout.{name}")
        if self.full_rollouts_per_prompt < 2:
            raise ValueError("GRPO requires at least two rollouts per prompt")
        if (
            isinstance(self.pivot_groups_per_prompt, bool)
            or not isinstance(self.pivot_groups_per_prompt, int)
            or self.pivot_groups_per_prompt < 0
        ):
            raise ValueError("rollout.pivot_groups_per_prompt must be non-negative")
        if self.pivot_candidates is not None:
            _positive_int(self.pivot_candidates, "rollout.pivot_candidates")
        if not 0.0 < float(self.temperature):
            raise ValueError("rollout.temperature must be positive")
        if not 0.0 < float(self.top_p) <= 1.0:
            raise ValueError("rollout.top_p must be in (0, 1]")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("rollout.seed must be a non-negative integer")
        if self.max_total_assistant_tokens < self.max_action_tokens:
            raise ValueError(
                "rollout.max_total_assistant_tokens must cover one complete action"
            )
        for name in (
            "require_on_policy_candidates",
            "allow_forced_action_candidates_for_training",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"rollout.{name} must be boolean")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "RolloutConfig":
        return cls(**_strict_kwargs(cls, payload, "rollout config"))


@dataclass(frozen=True)
class TrainerConfig:
    backend_target: str
    rollout_engine: str
    dtype: str
    actor_strategy: str
    actor_fsdp_size: int
    rollout_tensor_parallel_size: int
    rollout_gpu_memory_utilization: float
    learning_rate: float
    sequence_loss_reduction: str
    prompt_mini_batch_size: int
    ppo_micro_batch_per_device: int
    ppo_epochs: int
    train_epochs: int
    max_grad_norm: float
    weight_decay: float
    warmup_ratio: float
    entropy_coefficient: float
    dynamic_batching: bool
    parameter_offload: bool
    optimizer_offload: bool
    checkpoint_every_steps: int
    validation_every_steps: int
    require_persisted_old_log_probs: bool
    require_persisted_reference_log_probs: bool
    mask_zero_variance_groups: bool

    def __post_init__(self) -> None:
        if self.backend_target != "rllm_verl_adapter":
            raise ValueError("trainer.backend_target must be rllm_verl_adapter")
        if self.rollout_engine != "sglang":
            raise ValueError("trainer.rollout_engine must be sglang")
        if self.dtype != "bfloat16":
            raise ValueError("trainer.dtype must be bfloat16")
        if self.actor_strategy != "fsdp":
            raise ValueError("trainer.actor_strategy must be fsdp")
        for name in (
            "actor_fsdp_size",
            "rollout_tensor_parallel_size",
            "prompt_mini_batch_size",
            "ppo_micro_batch_per_device",
            "ppo_epochs",
            "train_epochs",
            "checkpoint_every_steps",
            "validation_every_steps",
        ):
            _positive_int(getattr(self, name), f"trainer.{name}")
        for name in (
            "rollout_gpu_memory_utilization",
            "learning_rate",
            "max_grad_norm",
            "weight_decay",
            "warmup_ratio",
            "entropy_coefficient",
        ):
            _non_negative_number(getattr(self, name), f"trainer.{name}")
        if not 0.0 < self.rollout_gpu_memory_utilization <= 1.0:
            raise ValueError(
                "trainer.rollout_gpu_memory_utilization must be in (0, 1]"
            )
        if self.learning_rate <= 0.0:
            raise ValueError("trainer.learning_rate must be positive")
        if not 0.0 <= self.warmup_ratio < 1.0:
            raise ValueError("trainer.warmup_ratio must be in [0, 1)")
        if self.sequence_loss_reduction != "seq-mean-token-sum":
            raise ValueError(
                "trainer.sequence_loss_reduction must be seq-mean-token-sum"
            )
        for name in (
            "dynamic_batching",
            "parameter_offload",
            "optimizer_offload",
            "require_persisted_old_log_probs",
            "require_persisted_reference_log_probs",
            "mask_zero_variance_groups",
        ):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"trainer.{name} must be boolean")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TrainerConfig":
        return cls(**_strict_kwargs(cls, payload, "trainer config"))


@dataclass(frozen=True)
class ResourceConfig:
    scheduling_mode: str
    accelerator_count: int
    policy_rollout_devices: int
    generate_replicas: int
    edit_replicas: int
    geneval2_replicas: int
    image_replica_tensor_parallel_size: int
    trainer_devices: int
    allow_generate_edit_rebalance: bool
    edit_share_rebalance_threshold: float

    def __post_init__(self) -> None:
        if self.scheduling_mode != "staged_rollout_then_train":
            raise ValueError(
                "resources.scheduling_mode must be staged_rollout_then_train"
            )
        for name in (
            "accelerator_count",
            "policy_rollout_devices",
            "generate_replicas",
            "edit_replicas",
            "geneval2_replicas",
            "image_replica_tensor_parallel_size",
            "trainer_devices",
        ):
            _positive_int(getattr(self, name), f"resources.{name}")
        rollout_devices = (
            self.policy_rollout_devices
            + self.generate_replicas * self.image_replica_tensor_parallel_size
            + self.edit_replicas * self.image_replica_tensor_parallel_size
            + self.geneval2_replicas
        )
        if rollout_devices > self.accelerator_count:
            raise ValueError(
                "resources rollout topology exceeds accelerator_count: "
                f"{rollout_devices} > {self.accelerator_count}"
            )
        if self.trainer_devices > self.accelerator_count:
            raise ValueError("resources.trainer_devices exceeds accelerator_count")
        if not isinstance(self.allow_generate_edit_rebalance, bool):
            raise ValueError(
                "resources.allow_generate_edit_rebalance must be boolean"
            )
        if not 0.0 <= float(self.edit_share_rebalance_threshold) <= 1.0:
            raise ValueError(
                "resources.edit_share_rebalance_threshold must be in [0, 1]"
            )

    @property
    def rollout_devices(self) -> int:
        return (
            self.policy_rollout_devices
            + self.generate_replicas * self.image_replica_tensor_parallel_size
            + self.edit_replicas * self.image_replica_tensor_parallel_size
            + self.geneval2_replicas
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ResourceConfig":
        return cls(**_strict_kwargs(cls, payload, "resource config"))


@dataclass(frozen=True)
class TrackingConfig:
    provider: str
    mode: str
    mode_env: str
    api_key_env: str
    entity_env: str
    project: str
    group: str
    job_type: str
    run_name_prefix: str
    tags: tuple[str, ...]
    directory: Path
    resume: str
    log_model: bool
    log_artifacts: bool

    def __post_init__(self) -> None:
        if self.provider != "wandb":
            raise ValueError("tracking.provider must be wandb")
        if self.mode not in {"online", "offline", "disabled"}:
            raise ValueError("tracking.mode must be online, offline, or disabled")
        if self.resume not in {"allow", "must", "never"}:
            raise ValueError("tracking.resume must be allow, must, or never")
        for name in (
            "api_key_env",
            "mode_env",
            "entity_env",
            "project",
            "group",
            "job_type",
            "run_name_prefix",
        ):
            if not getattr(self, name):
                raise ValueError(f"tracking.{name} must be non-empty")
        if not self.tags or any(not item for item in self.tags):
            raise ValueError("tracking.tags must contain non-empty strings")
        for name in ("log_model", "log_artifacts"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"tracking.{name} must be boolean")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TrackingConfig":
        values = _strict_kwargs(cls, payload, "tracking config")
        tags = values.get("tags")
        if not isinstance(tags, list) or not all(isinstance(item, str) for item in tags):
            raise ValueError("tracking.tags must be a list of strings")
        values["tags"] = tuple(tags)
        values["directory"] = Path(str(values["directory"]))
        return cls(**values)


@dataclass(frozen=True)
class AdmissionConfig:
    smoke_prompts: int
    pilot_prompts: int
    minimum_trainable_prompts: int
    first_efficacy_prompts: int
    expand_to_prompts: int
    expand_only_after_predeclared_review: bool
    minimum_valid_group_fraction: float
    maximum_zero_variance_group_fraction: float
    maximum_policy_invalid_fraction: float
    increase_rollouts_to: int
    train_manifest: Path
    development_manifest: Path
    confirmation_manifest: Path
    experiment_declaration: Path
    live_adapter_evidence: Path
    smoke_report: Path

    def __post_init__(self) -> None:
        counts = (
            self.smoke_prompts,
            self.pilot_prompts,
            self.minimum_trainable_prompts,
            self.first_efficacy_prompts,
            self.expand_to_prompts,
        )
        for name, value in zip(
            (
                "smoke_prompts",
                "pilot_prompts",
                "minimum_trainable_prompts",
                "first_efficacy_prompts",
                "expand_to_prompts",
            ),
            counts,
        ):
            _positive_int(value, f"admission.{name}")
        if tuple(sorted(counts)) != counts:
            raise ValueError("admission prompt counts must be non-decreasing")
        for name in (
            "minimum_valid_group_fraction",
            "maximum_zero_variance_group_fraction",
            "maximum_policy_invalid_fraction",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"admission.{name} must be in [0, 1]")
        _positive_int(self.increase_rollouts_to, "admission.increase_rollouts_to")
        if not isinstance(self.expand_only_after_predeclared_review, bool):
            raise ValueError(
                "admission.expand_only_after_predeclared_review must be boolean"
            )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "AdmissionConfig":
        values = _strict_kwargs(cls, payload, "admission config")
        for name in (
            "train_manifest",
            "development_manifest",
            "confirmation_manifest",
            "experiment_declaration",
            "live_adapter_evidence",
            "smoke_report",
        ):
            values[name] = Path(str(values[name]))
        return cls(**values)


@dataclass(frozen=True)
class RlExperimentConfig:
    method_id: str
    method_version: str
    base_checkpoint: Path
    base_checkpoint_fingerprint: str
    policy_revision: str
    planner_context_schema_version: str
    action_protocol_version: str
    execution_profile: str
    reward: RewardConfig
    rollout: RolloutConfig
    optimization: ObjectiveConfig
    trainer: TrainerConfig
    resources: ResourceConfig
    tracking: TrackingConfig
    admission: AdmissionConfig

    def __post_init__(self) -> None:
        if self.method_id != "naive_geneval2_grpo" or self.method_version != "0.1":
            raise ValueError("this live scaffold accepts naive_geneval2_grpo@0.1")
        if self.planner_context_schema_version != "0.7":
            raise ValueError("RL v0.1 requires PlannerContext v0.7")
        if self.action_protocol_version != "0.5":
            raise ValueError("RL v0.1 requires Action Protocol v0.5")
        if self.execution_profile != "qwen_dual_backend@1":
            raise ValueError("RL v0.1 requires qwen_dual_backend@1")
        fingerprint = self.base_checkpoint_fingerprint.removeprefix("sha256:")
        if len(fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in fingerprint):
            raise ValueError("base_checkpoint_fingerprint must be a SHA256 digest")
        if self.reward.reward_policy_id != "geneval2_terminal_outcome":
            raise ValueError("naive GRPO requires terminal-outcome reward")
        if self.rollout.pivot_groups_per_prompt != 0:
            raise ValueError("naive GRPO forbids pivot groups")
        if self.rollout.allow_forced_action_candidates_for_training:
            raise ValueError("naive GRPO forbids forced training candidates")
        if not self.rollout.require_on_policy_candidates:
            raise ValueError("naive GRPO requires on-policy candidates")
        if self.trainer.rollout_tensor_parallel_size != self.resources.policy_rollout_devices:
            raise ValueError(
                "rollout tensor parallel size must match policy rollout devices"
            )
        if self.trainer.actor_fsdp_size != self.resources.trainer_devices:
            raise ValueError("actor FSDP size must match trainer devices")
        if self.rollout.prompt_batch_size != self.trainer.prompt_mini_batch_size:
            raise ValueError("rollout and trainer prompt batch sizes must match")
        if self.admission.increase_rollouts_to <= self.rollout.full_rollouts_per_prompt:
            raise ValueError("increase_rollouts_to must exceed the initial group size")

    @property
    def checkpoint_sha256(self) -> str:
        return self.base_checkpoint_fingerprint.removeprefix("sha256:")


def load_experiment_config(path: Path) -> RlExperimentConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _mapping(payload, "RL experiment config")
    expected = set(RlExperimentConfig.__dataclass_fields__)
    unknown = set(root) - expected
    missing = expected - set(root)
    if unknown:
        raise ValueError(f"unknown RL experiment config fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing RL experiment config fields: {sorted(missing)}")
    return RlExperimentConfig(
        method_id=str(root["method_id"]),
        method_version=str(root["method_version"]),
        base_checkpoint=Path(str(root["base_checkpoint"])),
        base_checkpoint_fingerprint=str(root["base_checkpoint_fingerprint"]),
        policy_revision=str(root["policy_revision"]),
        planner_context_schema_version=str(root["planner_context_schema_version"]),
        action_protocol_version=str(root["action_protocol_version"]),
        execution_profile=str(root["execution_profile"]),
        reward=RewardConfig.from_mapping(_mapping(root["reward"], "reward")),
        rollout=RolloutConfig.from_mapping(_mapping(root["rollout"], "rollout")),
        optimization=ObjectiveConfig.from_mapping(
            _mapping(root["optimization"], "optimization")
        ),
        trainer=TrainerConfig.from_mapping(_mapping(root["trainer"], "trainer")),
        resources=ResourceConfig.from_mapping(
            _mapping(root["resources"], "resources")
        ),
        tracking=TrackingConfig.from_mapping(
            _mapping(root["tracking"], "tracking")
        ),
        admission=AdmissionConfig.from_mapping(
            _mapping(root["admission"], "admission")
        ),
    )
