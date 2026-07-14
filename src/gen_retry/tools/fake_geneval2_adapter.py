from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import artifact_manifest_entry, sha256_bytes, write_artifact_bytes
from gen_retry.runtime.json_canonical import canonical_json


@dataclass(frozen=True)
class FakeGeneval2Report:
    attempt_id: str
    constraint_results: list[dict[str, Any]]
    report_ref: str
    report_sha256: str
    manifest_entry: dict[str, Any]


class FakeGeneval2Adapter:
    def __init__(
        self,
        results_by_attempt_id: dict[str, list[dict[str, Any]]],
        *,
        artifact_root: Path | None = None,
    ):
        self.results_by_attempt_id = results_by_attempt_id
        self.artifact_root = artifact_root

    def evaluate(self, *, task_spec: dict[str, Any], attempt_id: str) -> list[dict[str, Any]]:
        results = self.results_by_attempt_id[attempt_id]
        expected = {constraint["constraint_id"] for constraint in task_spec["constraints"]}
        observed = {result["constraint_id"] for result in results}
        if observed != expected:
            missing = sorted(expected - observed)
            extra = sorted(observed - expected)
            raise ValueError(f"constraint coverage mismatch missing={missing} extra={extra}")
        return sorted(results, key=lambda result: result["constraint_id"])

    def evaluate_to_report(
        self,
        *,
        task_spec: dict[str, Any],
        attempt_id: str,
        report_ref: str | None = None,
    ) -> FakeGeneval2Report:
        constraint_results = self.evaluate(task_spec=task_spec, attempt_id=attempt_id)
        report_ref = report_ref or f"artifacts/geneval2/{attempt_id}.json"
        report_payload = {
            "schema_version": "0.2",
            "attempt_id": attempt_id,
            "constraint_results": constraint_results,
        }
        report_bytes = canonical_json(report_payload).encode("utf-8")
        report_sha256 = (
            write_artifact_bytes(self.artifact_root, report_ref, report_bytes)
            if self.artifact_root is not None
            else sha256_bytes(report_bytes)
        )
        manifest_entry = artifact_manifest_entry(
            artifact_id=_report_artifact_id(attempt_id),
            attempt_id=attempt_id,
            artifact_type="geneval2_report",
            uri=report_ref,
            sha256=report_sha256,
            media_type="application/json",
            producer="fake_geneval2_adapter",
        )
        return FakeGeneval2Report(
            attempt_id=attempt_id,
            constraint_results=constraint_results,
            report_ref=report_ref,
            report_sha256=report_sha256,
            manifest_entry=manifest_entry,
        )


def _report_artifact_id(attempt_id: str) -> str:
    if not attempt_id.startswith("a_") or not attempt_id[2:].isdigit():
        raise ValueError(f"cannot derive Geneval2 report artifact ID from {attempt_id}")
    return f"geneval2_report_{attempt_id[2:]}"
