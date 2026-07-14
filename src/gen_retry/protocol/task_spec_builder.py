from __future__ import annotations

from typing import Any

from gen_retry.protocol.schema_loader import validate_instance


def task_spec_from_geneval2_row(
    row: dict[str, Any],
    *,
    episode_id: str,
    max_image_attempts: int = 3,
) -> dict[str, Any]:
    """Build a v0.2 TaskSpec from a Geneval2-style benchmark row."""

    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Geneval2 row must include a non-empty prompt.")

    vqa_list = row.get("vqa_list")
    if not isinstance(vqa_list, list) or not vqa_list:
        raise ValueError("Geneval2 row must include a non-empty vqa_list.")

    constraints: list[dict[str, Any]] = []
    for index, item in enumerate(vqa_list, start=1):
        constraint_id = f"c_{index:03d}"
        aligned_skill = _aligned_skill(row, index)
        if isinstance(item, dict):
            question = item.get("question") or item.get("vqa_question")
            expected = item.get("answer") or item.get("expected") or item.get("target")
            constraint_type = item.get("type") or item.get("skill") or aligned_skill or "geneval2_atom"
            requirement = item.get("requirement") or expected or question
        elif _is_vqa_pair(item):
            question = str(item[0])
            expected = str(item[1])
            requirement = f"Expected answer: {expected}"
            constraint_type = aligned_skill or "geneval2_atom"
        else:
            question = str(item)
            requirement = str(item)
            constraint_type = aligned_skill or "geneval2_atom"

        if not isinstance(requirement, str) or not requirement.strip():
            raise ValueError(f"Geneval2 atom {index} does not expose a requirement.")

        constraints.append(
            {
                "constraint_id": constraint_id,
                "constraint_type": str(constraint_type),
                "requirement": requirement.strip(),
                "evaluator_question": question if isinstance(question, str) else None,
                "priority": 3,
            }
        )

    task_spec = {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "original_prompt": prompt.strip(),
        "constraints": constraints,
        "max_image_attempts": max_image_attempts,
    }
    validate_instance(task_spec, "task_spec_v0_2.schema.json")
    return task_spec


def _is_vqa_pair(item: Any) -> bool:
    return (
        isinstance(item, (list, tuple))
        and len(item) == 2
        and all(isinstance(value, str) and value.strip() for value in item)
    )


def _aligned_skill(row: dict[str, Any], one_based_index: int) -> str | None:
    skills = row.get("skills")
    if not isinstance(skills, list):
        return None
    zero_based_index = one_based_index - 1
    if zero_based_index >= len(skills):
        return None
    skill = skills[zero_based_index]
    return skill if isinstance(skill, str) and skill.strip() else None
