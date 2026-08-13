from __future__ import annotations

import pytest

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.task_spec_builder import (
    task_spec_from_geneval2_row,
    task_spec_from_geneval_plus_plus_row,
    task_spec_from_geneval_row,
)


def test_task_spec_builder_from_geneval2_row() -> None:
    task_spec = task_spec_from_geneval2_row(
        {
            "prompt": "A red cube is left of a blue sphere.",
            "vqa_list": [
                {
                    "question": "Is there a red cube?",
                    "answer": "red cube present",
                    "skill": "attribute_binding",
                },
                {
                    "question": "Is the red cube left of the blue sphere?",
                    "answer": "cube left of sphere",
                    "skill": "spatial_relation",
                },
            ],
        },
        episode_id="ep_builder_001",
    )

    assert [constraint["constraint_id"] for constraint in task_spec["constraints"]] == [
        "c_001",
        "c_002",
    ]
    validate_instance(task_spec, "task_spec_v0_2.schema.json")


def test_task_spec_builder_preserves_geneval2_list_pair_skills() -> None:
    task_spec = task_spec_from_geneval2_row(
        {
            "prompt": "a green backpack and a pig",
            "atom_count": 3,
            "vqa_list": [
                ["How many backpacks are in the image?", "one"],
                ["Is the backpack green?", "Yes"],
                ["Are there any pigs in the image?", "Yes"],
            ],
            "skills": ["count", "attribute", "object"],
        },
        episode_id="ep_builder_003",
    )

    assert [
        constraint["constraint_type"] for constraint in task_spec["constraints"]
    ] == ["count", "attribute", "object"]
    assert task_spec["constraints"][0]["evaluator_question"] == "How many backpacks are in the image?"
    assert task_spec["constraints"][0]["requirement"] == "Expected answer: one"
    validate_instance(task_spec, "task_spec_v0_2.schema.json")


def test_task_spec_builder_requires_vqa_list() -> None:
    with pytest.raises(ValueError):
        task_spec_from_geneval2_row({"prompt": "missing atoms"}, episode_id="ep_builder_002")


@pytest.mark.parametrize(
    ("row", "types"),
    [
        (
            {
                "tag": "single_object",
                "include": [{"class": "bench", "count": 1}],
                "prompt": "a photo of a bench",
            },
            ["object"],
        ),
        (
            {
                "tag": "two_object",
                "include": [
                    {"class": "bench", "count": 1},
                    {"class": "dog", "count": 1},
                ],
                "prompt": "a bench and a dog",
            },
            ["object", "object"],
        ),
        (
            {
                "tag": "colors",
                "include": [{"class": "bench", "count": 1, "color": "red"}],
                "prompt": "a red bench",
            },
            ["object", "attribute"],
        ),
        (
            {
                "tag": "position",
                "include": [
                    {"class": "bench", "count": 1},
                    {
                        "class": "dog",
                        "count": 1,
                        "position": ["right of", 0],
                    },
                ],
                "prompt": "a dog right of a bench",
            },
            ["object", "object", "position"],
        ),
    ],
)
def test_task_spec_builder_from_original_geneval_families(row: dict, types: list[str]) -> None:
    task_spec = task_spec_from_geneval_row(row, episode_id="ep_geneval_001")
    assert [item["constraint_type"] for item in task_spec["constraints"]] == types
    validate_instance(task_spec, "task_spec_v0_2.schema.json")


def test_original_geneval_exact_count_preserves_include_exclude_bounds() -> None:
    task_spec = task_spec_from_geneval_row(
        {
            "tag": "counting",
            "include": [{"class": "clock", "count": 2}],
            "exclude": [{"class": "clock", "count": 3}],
            "prompt": "two clocks",
        },
        episode_id="ep_geneval_002",
    )
    assert task_spec["constraints"] == [
        {
            "constraint_id": "c_001",
            "constraint_type": "count",
            "requirement": "Expected answer: two",
            "evaluator_question": "How many clock objects are in the image?",
            "priority": 3,
        }
    ]


@pytest.mark.parametrize(
    "row",
    [
        {"tag": "unknown", "include": [{"class": "dog", "count": 1}], "prompt": "dog"},
        {
            "tag": "single_object",
            "include": [{"class": "dog", "count": 1, "answer": True}],
            "prompt": "dog",
        },
        {
            "tag": "position",
            "include": [
                {"class": "dog", "count": 1, "position": ["left of", 0]}
            ],
            "prompt": "dog",
        },
    ],
)
def test_original_geneval_builder_fails_closed(row: dict) -> None:
    with pytest.raises(ValueError):
        task_spec_from_geneval_row(row, episode_id="ep_geneval_bad")


def test_geneval_plus_plus_preserves_exact_count_color_and_region() -> None:
    task_spec = task_spec_from_geneval_plus_plus_row(
        {
            "tag": "color_spatial_attr",
            "include": [
                {"class": "spoon", "count": 1, "color": "blue", "region": "left"},
                {"class": "couch", "count": 1, "color": "red", "region": "right"},
            ],
            "prompt": "A blue spoon on the left and a red couch on the right",
        },
        episode_id="ep_geneval_plus_001",
    )
    assert [item["constraint_type"] for item in task_spec["constraints"]] == [
        "count",
        "attribute",
        "region",
        "count",
        "attribute",
        "region",
    ]
    assert task_spec["constraints"][0]["requirement"] == "Expected answer: one"
    assert "left part" in task_spec["constraints"][2]["evaluator_question"]


def test_geneval_plus_plus_merges_matching_count_upper_bound() -> None:
    task_spec = task_spec_from_geneval_plus_plus_row(
        {
            "tag": "counting",
            "include": [{"class": "clock", "count": 6}],
            "exclude": [{"class": "clock", "count": 7}],
            "prompt": "A photo of six clocks",
        },
        episode_id="ep_geneval_plus_002",
    )
    assert task_spec["constraints"] == [
        {
            "constraint_id": "c_001",
            "constraint_type": "count",
            "requirement": "Expected answer: six",
            "evaluator_question": "How many clock objects are in the image?",
            "priority": 3,
        }
    ]


def test_geneval_plus_plus_emits_one_relative_size_atom() -> None:
    task_spec = task_spec_from_geneval_plus_plus_row(
        {
            "tag": "size_spatial_attr",
            "include": [
                {"class": "bench", "count": 1, "size": "larger", "region": "above"},
                {"class": "spoon", "count": 1, "size": "smaller", "region": "below"},
            ],
            "prompt": "A larger bench above a smaller spoon",
        },
        episode_id="ep_geneval_plus_003",
    )
    size_atoms = [
        item
        for item in task_spec["constraints"]
        if item["constraint_type"] == "relative_size"
    ]
    assert len(size_atoms) == 1
    assert size_atoms[0]["evaluator_question"] == (
        "Is the bench larger than the spoon?"
    )


@pytest.mark.parametrize(
    "row",
    [
        {
            "tag": "unknown",
            "include": [{"class": "dog", "count": 1}],
            "prompt": "dog",
        },
        {
            "tag": "spatial_count_attr",
            "include": [{"class": "dog", "count": 1, "region": "center"}],
            "prompt": "dog",
        },
        {
            "tag": "size_spatial_attr",
            "include": [
                {"class": "dog", "count": 1, "size": "larger"},
                {"class": "cat", "count": 1, "size": "larger"},
            ],
            "prompt": "dogs and cats",
        },
    ],
)
def test_geneval_plus_plus_builder_fails_closed(row: dict) -> None:
    with pytest.raises(ValueError):
        task_spec_from_geneval_plus_plus_row(
            row, episode_id="ep_geneval_plus_bad"
        )
