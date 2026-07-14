from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_retry.cli.select_phase3_prompts import select_phase3_prompts
from gen_retry.phase3.selection import select_candidates


def _candidate(
    index: int,
    *,
    types: dict[str, int],
    group: str,
    failed: int = 0,
    retries: int = 0,
    unresolved: bool = False,
    eligible: bool = True,
) -> dict[str, object]:
    return {
        "candidate_id": f"cand_{index:03d}",
        "prompt_id": f"prompt_{index:03d}",
        "original_prompt": f"Prompt {index}",
        "atomic_constraints": [
            {"constraint_type": key, "requirement": f"{key} requirement"}
            for key in types
        ],
        "constraint_count": sum(types.values()),
        "constraint_type_histogram": types,
        "constraint_type_combination": sorted(types),
        "baseline_difficulty_evidence": {
            "failed_atom_count": failed,
            "pass_ratio": 0.5,
        },
        "historical_difficulty_evidence": {"retry_depth": retries},
        "historical_unresolved_evidence": unresolved,
        "semantic_duplication_group": group,
        "provenance": {"source": "unit"},
        "selection_eligibility": eligible,
    }


def test_select_candidates_is_deterministic_and_balances_coverage() -> None:
    candidates = [
        _candidate(0, types={"count": 2, "spatial": 1}, group="apples", failed=3, retries=2),
        _candidate(1, types={"attribute": 2}, group="color", failed=1),
        _candidate(2, types={"object": 3}, group="objects", failed=2),
        _candidate(3, types={"count": 1, "attribute": 1}, group="mixed_a", failed=2),
        _candidate(4, types={"spatial": 2, "object": 1}, group="mixed_b", failed=3),
        _candidate(5, types={"relation": 1}, group="relations", failed=1),
        _candidate(6, types={"count": 1, "relation": 1}, group="mixed_c", retries=2),
        _candidate(7, types={"attribute": 1, "spatial": 1}, group="mixed_d", failed=1),
        _candidate(8, types={"object": 1, "attribute": 1}, group="mixed_e", unresolved=True),
        _candidate(9, types={"count": 1}, group="count_single", failed=1),
        _candidate(10, types={"spatial": 1}, group="spatial_single", failed=1),
        _candidate(11, types={"attribute": 1}, group="ineligible", eligible=False),
    ]

    first, first_matrix = select_candidates(candidates, limit=10)
    second, second_matrix = select_candidates(candidates, limit=10)

    assert first == second
    assert first_matrix == second_matrix
    assert len(first) == 10
    assert "cand_011" not in {candidate["candidate_id"] for candidate in first}
    assert all(candidate["selection_eligibility"] for candidate in first)
    assert set(first_matrix["constraint_types"]) == {
        "attribute",
        "count",
        "object",
        "relation",
        "spatial",
    }


def test_select_candidates_requires_enough_eligible_candidates() -> None:
    candidates = [
        _candidate(0, types={"count": 1}, group="a"),
        _candidate(1, types={"attribute": 1}, group="b", eligible=False),
    ]

    with pytest.raises(ValueError, match="need at least 2 eligible candidates"):
        select_candidates(candidates, limit=2)


def test_select_phase3_prompts_cli_helper_writes_required_artifacts(tmp_path: Path) -> None:
    candidate_pool = tmp_path / "candidate_pool.jsonl"
    candidates = [
        _candidate(index, types={"count": 1, "attribute": 1}, group=f"group_{index}", failed=index % 3)
        for index in range(10)
    ]
    candidate_pool.write_text(
        "".join(json.dumps(candidate, sort_keys=True) + "\n" for candidate in candidates),
        encoding="utf-8",
    )

    selected_output = tmp_path / "selected_ten_prompts.json"
    coverage_output = tmp_path / "constraint_coverage_matrix.json"
    prompt_selection_report = tmp_path / "prompt_selection_report.md"
    selection_provenance = tmp_path / "selection_provenance.md"
    selected, coverage = select_phase3_prompts(
        candidate_pool=candidate_pool,
        selected_output=selected_output,
        coverage_output=coverage_output,
        prompt_selection_report=prompt_selection_report,
        selection_provenance=selection_provenance,
    )

    assert selected_output.is_file()
    assert coverage_output.is_file()
    assert prompt_selection_report.is_file()
    assert selection_provenance.is_file()
    selected_payload = json.loads(selected_output.read_text(encoding="utf-8"))
    coverage_payload = json.loads(coverage_output.read_text(encoding="utf-8"))
    assert selected_payload["selected_prompts"] == selected
    assert coverage_payload == coverage
    assert "Phase 3 Prompt Selection Report" in prompt_selection_report.read_text(encoding="utf-8")
