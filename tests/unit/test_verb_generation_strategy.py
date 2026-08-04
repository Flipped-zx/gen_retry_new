from gen_retry.analysis.verb_generation_strategy import (
    STRATEGY_COMPACT_GAP,
    STRATEGY_COMPACT_INTENT,
    STRATEGY_FOCAL,
    STRATEGY_GRAPHIC,
    STRATEGY_IMMINENT,
    STRATEGY_LATERAL,
    compose_strategy_instruction,
    verb_relation,
)


def _task(question: str) -> dict:
    return {
        "constraints": [
            {
                "constraint_id": "c_003",
                "constraint_type": "verb",
                "evaluator_question": question,
            }
        ]
    }


def test_parses_supported_verb_relation_from_evaluator_question() -> None:
    relation = verb_relation(_task("Are the koalas chasing the raccoons?"))

    assert relation.constraint_id == "c_003"
    assert relation.verb == "chasing"
    assert relation.subject == "koalas"
    assert relation.object == "raccoons"


def test_lateral_chasing_operator_is_camera_and_role_explicit() -> None:
    instruction = compose_strategy_instruction(
        baseline_instruction="Show five koalas chasing seven raccoons.",
        task_spec=_task("Are the koalas chasing the raccoons?"),
        strategy_id=STRATEGY_LATERAL,
    )

    assert instruction.startswith("Show five koalas chasing seven raccoons.")
    assert "strict lateral side-view" in instruction
    assert "no action animal faces the camera" in instruction
    assert "Never intermix the groups" in instruction
    assert "Do not add labels, arrows, captions, panels, or text" in instruction


def test_focal_operator_supports_all_current_verb_types() -> None:
    cases = [
        ("Is the lion playing with the dogs?", "single toy or ball"),
        ("Are the cats jumping over the monkey?", "focal crossing"),
        ("Is the horse chasing the pigs?", "focal pursuit pair"),
    ]
    for question, expected in cases:
        instruction = compose_strategy_instruction(
            baseline_instruction="Baseline.",
            task_spec=_task(question),
            strategy_id=STRATEGY_FOCAL,
        )
        assert expected in instruction


def test_v2_imminent_strategy_frontloads_role_asymmetry() -> None:
    instruction = compose_strategy_instruction(
        baseline_instruction="Baseline scene requirements.",
        task_spec=_task("Is the kangaroo chasing the elephants?"),
        strategy_id=STRATEGY_IMMINENT,
    )

    assert instruction.startswith("Primary verb composition technique")
    assert "kangaroo are the pursuers" in instruction
    assert "elephants are the fleeing targets" in instruction
    assert "almost touching" in instruction
    assert instruction.endswith("Scene requirements: Baseline scene requirements.")


def test_v2_graphic_strategy_uses_text_free_action_strip() -> None:
    instruction = compose_strategy_instruction(
        baseline_instruction="Baseline scene requirements.",
        task_spec=_task("Are the flamingos chasing the cats?"),
        strategy_id=STRATEGY_GRAPHIC,
    )

    assert "clean editorial action illustration" in instruction
    assert "one horizontal left-to-right action line" in instruction
    assert "without symbols or text" in instruction


def test_v3_compact_gap_is_inserted_after_first_scene_sentence() -> None:
    instruction = compose_strategy_instruction(
        baseline_instruction="Create the scene. Keep exact counts. Preserve colors.",
        task_spec=_task("Are the giraffes chasing the monkeys?"),
        strategy_id=STRATEGY_COMPACT_GAP,
    )

    assert instruction.startswith(
        "Create the scene. Verb technique (verb_generation_techniques_v3):"
    )
    assert "reaching to within a small gap of its tail" in instruction
    assert instruction.endswith(" Keep exact counts. Preserve colors.")


def test_v3_compact_intent_does_not_change_baseline_requirements() -> None:
    baseline = "Create the scene. Keep exact counts. Preserve colors."
    instruction = compose_strategy_instruction(
        baseline_instruction=baseline,
        task_spec=_task("Are the koalas chasing the raccoons?"),
        strategy_id=STRATEGY_COMPACT_INTENT,
    )

    assert "asymmetric capture intent unmistakable" in instruction
    assert "Keep exact counts. Preserve colors." in instruction
