from __future__ import annotations

import pytest

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.protocol.task_spec_builder import task_spec_from_geneval2_row


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


def test_task_spec_builder_requires_vqa_list() -> None:
    with pytest.raises(ValueError):
        task_spec_from_geneval2_row({"prompt": "missing atoms"}, episode_id="ep_builder_002")
