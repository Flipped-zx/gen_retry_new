from __future__ import annotations

import json
from pathlib import Path

from gen_retry.phase5.flow_dppo_selection import (
    select_flow_dppo_official_mix_prompts,
    select_flow_dppo_prompts,
)


def _row(prompt: str, atom_count: int, skill_tail: list[str]) -> dict:
    vqa_list = [
        ["How many cats are in the image?", "four"],
        ["Are there any cats in the image?", "Yes"],
    ]
    skills = ["count", "object"]
    for index, skill in enumerate(skill_tail):
        if skill == "verb":
            question = "Are the cats chasing the dogs?"
        elif skill == "position":
            question = "Are the cats behind the dogs?"
        else:
            question = f"Are the cats feature {index}?"
        vqa_list.append([question, "Yes"])
        skills.append(skill)
    return {
        "prompt": prompt,
        "atom_count": atom_count,
        "vqa_list": vqa_list,
        "skills": skills,
    }


def _write_dataset(path: Path) -> None:
    rows = []
    for index in range(4):
        rows.append(
            _row(
                f"four cats chasing dogs behind object {index}",
                10,
                ["attribute"] * 6 + ["verb", "position"],
            )
        )
    for index in range(3):
        rows.append(
            _row(
                f"four cats playing with dogs under object {index}",
                8,
                ["attribute"] * 4 + ["verb", "position"],
            )
        )
    for index in range(3):
        rows.append(
            _row(
                f"four cats jumping over object {index}",
                5,
                ["verb"],
            )
        )
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_flow_dppo_selection_is_deterministic_and_preserves_vqa(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    _write_dataset(dataset)
    heldout = tmp_path / "test.jsonl"
    heldout.write_text(
        json.dumps(_row("heldout cats chasing dogs", 10, ["verb"] * 8)) + "\n",
        encoding="utf-8",
    )
    counts = {"hard": 2, "medium": 2, "easy": 2}

    first = select_flow_dppo_prompts(
        dataset,
        heldout_dataset_path=heldout,
        tier_counts=counts,
    )
    second = select_flow_dppo_prompts(
        dataset,
        heldout_dataset_path=heldout,
        tier_counts=counts,
    )

    assert first == second
    assert first["selected_count"] == 6
    assert first["coverage"]["tier_histogram"] == counts
    assert first["source"]["official_800_held_out"] is True
    assert len({row["source_line"] for row in first["selected_prompts"]}) == 6
    for candidate in first["selected_prompts"]:
        assert candidate["vqa_list"]
        assert len(candidate["vqa_list"]) == len(candidate["atomic_constraints"])
        assert candidate["provenance"]["source_row_sha256"]
        assert candidate["provenance"]["official_test_set_held_out"] is True
        assert candidate["semantic_family_id"]


def test_flow_dppo_selection_rejects_insufficient_tier(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    _write_dataset(dataset)

    try:
        select_flow_dppo_prompts(
            dataset,
            tier_counts={"hard": 99, "medium": 1, "easy": 1},
        )
    except ValueError as exc:
        assert "hard rows" in str(exc)
    else:
        raise AssertionError("expected insufficient hard tier to fail")


def test_official_mix_matches_atom_distribution_and_excludes_prior_rows(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "train.jsonl"
    rows = []
    for atom_count in range(3, 11):
        for index in range(3):
            rows.append(
                {
                    "prompt": f"{atom_count} atom sample {index}",
                    "atom_count": atom_count,
                    "vqa_list": [
                        [f"Is atom {item} visible?", "Yes"]
                        for item in range(atom_count)
                    ],
                    "skills": ["object"] * atom_count,
                }
            )
    dataset.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    heldout = tmp_path / "heldout.jsonl"
    heldout_rows = []
    for atom_count in range(3, 11):
        for index in range(100):
            heldout_rows.append(
                {
                    "prompt": f"heldout {atom_count} sample {index}",
                    "atom_count": atom_count,
                    "vqa_list": [
                        [f"Is heldout attribute {item} visible?", "Yes"]
                        for item in range(atom_count)
                    ],
                    "skills": ["attribute"] * atom_count,
                }
            )
    heldout.write_text(
        "".join(json.dumps(row) + "\n" for row in heldout_rows),
        encoding="utf-8",
    )

    first = select_flow_dppo_official_mix_prompts(
        dataset,
        heldout_dataset_path=heldout,
        total_count=8,
    )
    first_again = select_flow_dppo_official_mix_prompts(
        dataset,
        heldout_dataset_path=heldout,
        total_count=8,
    )
    prior = tmp_path / "prior.json"
    prior.write_text(json.dumps(first), encoding="utf-8")
    second = select_flow_dppo_official_mix_prompts(
        dataset,
        heldout_dataset_path=heldout,
        total_count=8,
        excluded_selection_paths=[prior],
    )

    assert first["atom_count_counts"] == {
        str(atom_count): 1 for atom_count in range(3, 11)
    }
    assert first == first_again
    assert first["tier_counts"] == {"easy": 3, "hard": 2, "medium": 3}
    assert all(
        "official_skill_distribution_error" in item["selection_reason"]
        for item in first["selected_prompts"]
    )
    assert not (
        {item["source_row_sha256"] for item in first["selected_prompts"]}
        & {item["source_row_sha256"] for item in second["selected_prompts"]}
    )
    assert second["source"]["prior_selected_source_rows_excluded"] == 8
    assert sum(first["coverage"]["vqa_count_histogram"].values()) == 8


def test_official_mix_requires_exact_eight_bucket_multiple(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text("", encoding="utf-8")
    heldout = tmp_path / "heldout.jsonl"
    heldout.write_text("", encoding="utf-8")

    try:
        select_flow_dppo_official_mix_prompts(
            dataset,
            heldout_dataset_path=heldout,
            total_count=10,
        )
    except ValueError as exc:
        assert "multiple of 8" in str(exc)
    else:
        raise AssertionError("expected non-divisible official mix to fail")
