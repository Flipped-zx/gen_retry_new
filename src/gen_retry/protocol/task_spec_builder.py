from __future__ import annotations

from typing import Any

from gen_retry.protocol.schema_loader import validate_instance


GENEVAL_TAGS = {
    "single_object",
    "two_object",
    "counting",
    "colors",
    "position",
    "color_attr",
}


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


def task_spec_from_geneval_row(
    row: dict[str, Any],
    *,
    episode_id: str,
    max_image_attempts: int = 5,
) -> dict[str, Any]:
    """Build a TaskSpec from one original GenEval metadata row."""

    prompt = _required_nonempty_string(row.get("prompt"), "prompt")
    tag = _required_nonempty_string(row.get("tag"), "tag")
    if tag not in GENEVAL_TAGS:
        raise ValueError(f"unsupported original GenEval tag: {tag}")
    unexpected = set(row) - {"tag", "prompt", "include", "exclude"}
    if unexpected:
        raise ValueError(f"unsupported original GenEval fields: {sorted(unexpected)}")

    include = _clauses(row.get("include"), field="include", allow_position=True)
    exclude = _clauses(row.get("exclude", []), field="exclude", allow_position=False)
    constraints: list[dict[str, Any]] = []
    exact_upper_bounds = {
        clause["class"]: clause["count"]
        for clause in exclude
    }

    def add(constraint_type: str, requirement: str, question: str) -> None:
        constraints.append(
            {
                "constraint_id": f"c_{len(constraints) + 1:03d}",
                "constraint_type": constraint_type,
                "requirement": requirement,
                "evaluator_question": question,
                "priority": 3,
            }
        )

    for index, clause in enumerate(include):
        classname = clause["class"]
        count = clause["count"]
        upper = exact_upper_bounds.get(classname)
        if upper == count + 1:
            add(
                "count",
                f"Expected answer: {_number_word(count)}",
                f"How many {classname} objects are in the image?",
            )
        else:
            add(
                "object" if count == 1 else "count",
                "Expected answer: Yes",
                f"Are there at least {count} {classname} objects in the image?",
            )
        if "color" in clause:
            color = clause["color"]
            add(
                "attribute",
                "Expected answer: Yes",
                f"Are the required {classname} objects {color}?",
            )
        if "position" in clause:
            relation, target_index = clause["position"]
            if target_index >= index:
                raise ValueError(
                    f"include[{index}].position target must reference an earlier include clause"
                )
            target = include[target_index]["class"]
            add(
                "position",
                "Expected answer: Yes",
                f"Is the {classname} {relation} the {target}?",
            )

    for clause in exclude:
        classname = clause["class"]
        upper = clause["count"]
        matching_lower = next(
            (item["count"] for item in include if item["class"] == classname),
            None,
        )
        if matching_lower is not None and upper == matching_lower + 1:
            continue
        add(
            "count",
            "Expected answer: No",
            f"Are there at least {upper} {classname} objects in the image?",
        )

    task_spec = {
        "schema_version": "0.2",
        "episode_id": episode_id,
        "original_prompt": prompt,
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


def _clauses(value: Any, *, field: str, allow_position: bool) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (field == "include" and not value):
        raise ValueError(f"{field} must be a {'non-empty ' if field == 'include' else ''}list")
    clauses: list[dict[str, Any]] = []
    allowed = {"class", "count", "color"} | ({"position"} if allow_position else set())
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) - allowed:
            raise ValueError(f"unsupported {field}[{index}] clause")
        classname = _required_nonempty_string(item.get("class"), f"{field}[{index}].class")
        count = item.get("count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError(f"{field}[{index}].count must be a positive integer")
        clause: dict[str, Any] = {"class": classname, "count": count}
        if "color" in item:
            clause["color"] = _required_nonempty_string(item["color"], f"{field}[{index}].color")
        if "position" in item:
            position = item["position"]
            if (
                not isinstance(position, list)
                or len(position) != 2
                or not isinstance(position[0], str)
                or not position[0].strip()
                or not isinstance(position[1], int)
                or isinstance(position[1], bool)
                or position[1] < 0
            ):
                raise ValueError(f"{field}[{index}].position is invalid")
            clause["position"] = [position[0].strip(), position[1]]
        clauses.append(clause)
    return clauses


def _required_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _number_word(value: int) -> str:
    return {
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
    }.get(value, str(value))
