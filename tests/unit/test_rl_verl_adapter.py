from pathlib import Path

from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.verl_adapter import build_verl_adapter_plan


ROOT = Path(__file__).resolve().parents[2]


def test_verl_adapter_plan_maps_naive_grpo_with_active_kl() -> None:
    config = load_experiment_config(
        ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    )
    plan = build_verl_adapter_plan(config)
    overrides = set(plan.hydra_overrides)
    assert "actor_rollout_ref.rollout.n=4" in overrides
    assert "actor_rollout_ref.rollout.temperature=0.7" in overrides
    assert "actor_rollout_ref.actor.optim.lr=1e-06" in overrides
    assert "actor_rollout_ref.actor.use_kl_loss=True" in overrides
    assert "actor_rollout_ref.actor.kl_loss_coef=0.02" in overrides
    assert "algorithm.use_kl_in_reward=False" in overrides
    assert "actor_rollout_ref.actor.fsdp_config.fsdp_size=8" in overrides
    assert plan.gen_retry_contract["execution_profile"] == "qwen_dual_backend@1"
    assert plan.gen_retry_contract["train_action_tokens_only"] is True
    assert len(plan.plan_sha256) == 64


def test_verl_adapter_plan_does_not_claim_stock_runtime_is_executable() -> None:
    config = load_experiment_config(
        ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    )
    plan = build_verl_adapter_plan(config)
    assert plan.stock_runtime_blockers
    assert any("persisted old/reference" in item for item in plan.stock_runtime_blockers)
