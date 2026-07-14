from __future__ import annotations

from typing import Any


class FakeGeneval2Adapter:
    def __init__(self, results_by_attempt_id: dict[str, list[dict[str, Any]]]):
        self.results_by_attempt_id = results_by_attempt_id

    def evaluate(self, *, task_spec: dict[str, Any], attempt_id: str) -> list[dict[str, Any]]:
        results = self.results_by_attempt_id[attempt_id]
        expected = {constraint["constraint_id"] for constraint in task_spec["constraints"]}
        observed = {result["constraint_id"] for result in results}
        if observed != expected:
            missing = sorted(expected - observed)
            extra = sorted(observed - expected)
            raise ValueError(f"constraint coverage mismatch missing={missing} extra={extra}")
        return sorted(results, key=lambda result: result["constraint_id"])
