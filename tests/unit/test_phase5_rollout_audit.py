import pytest

from gen_retry.phase5.rollout_audit import (
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
