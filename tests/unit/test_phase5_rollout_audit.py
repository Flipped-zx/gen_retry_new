from pathlib import Path

import pytest

from gen_retry.cli.audit_phase5_rollouts import _resolve_episode_ids
from gen_retry.phase5.rollout_audit import (
    _select_run_dirs,
    soft_tifa_arithmetic_mean,
    soft_tifa_geometric_mean,
)


def test_soft_tifa_arithmetic_mean_matches_geneval2_formula() -> None:
    assert soft_tifa_arithmetic_mean([1.0, 0.25]) == pytest.approx(0.625)


def test_soft_tifa_geometric_mean_matches_flow_dppo_formula() -> None:
    assert soft_tifa_geometric_mean([1.0, 0.25]) == pytest.approx(0.5)


def test_soft_tifa_geometric_mean_uses_flow_dppo_zero_floor() -> None:
    assert soft_tifa_geometric_mean([1.0, 0.0]) == pytest.approx(1e-150)


@pytest.mark.parametrize(
    "probabilities",
    [[], [-0.1], [1.1], [float("nan")]],
)
def test_soft_tifa_geometric_mean_rejects_invalid_inputs(
    probabilities: list[float],
) -> None:
    with pytest.raises(ValueError):
        soft_tifa_geometric_mean(probabilities)


@pytest.mark.parametrize(
    "probabilities",
    [[], [-0.1], [1.1], [float("nan")]],
)
def test_soft_tifa_arithmetic_mean_rejects_invalid_inputs(
    probabilities: list[float],
) -> None:
    with pytest.raises(ValueError):
        soft_tifa_arithmetic_mean(probabilities)


def test_select_run_dirs_limits_and_sorts_checkpoint_subset(tmp_path: Path) -> None:
    for episode_id in ("phase3_ep_001", "phase3_ep_002", "phase3_ep_003"):
        (tmp_path / episode_id).mkdir()

    assert _select_run_dirs(
        tmp_path,
        ["phase3_ep_003", "phase3_ep_001"],
    ) == [
        tmp_path / "phase3_ep_001",
        tmp_path / "phase3_ep_003",
    ]


def test_select_run_dirs_rejects_duplicate_or_missing_ids(tmp_path: Path) -> None:
    (tmp_path / "phase3_ep_001").mkdir()

    with pytest.raises(ValueError, match="must be unique"):
        _select_run_dirs(
            tmp_path,
            ["phase3_ep_001", "phase3_ep_001"],
        )
    with pytest.raises(ValueError, match="phase3_ep_002"):
        _select_run_dirs(tmp_path, ["phase3_ep_002"])


def test_resolve_episode_ids_builds_inclusive_checkpoint_range() -> None:
    assert _resolve_episode_ids(
        episode_ids=None,
        episode_start=41,
        episode_end=50,
    ) == [f"phase3_ep_{index:03d}" for index in range(41, 51)]


def test_resolve_episode_ids_rejects_ambiguous_range() -> None:
    with pytest.raises(SystemExit, match="cannot be combined"):
        _resolve_episode_ids(
            episode_ids=["phase3_ep_001"],
            episode_start=1,
            episode_end=20,
        )
