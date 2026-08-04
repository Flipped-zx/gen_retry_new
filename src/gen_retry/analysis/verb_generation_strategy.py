from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.phase3.model_config import load_model_config
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.tools.geneval2_adapter import LocalGeneval2Adapter
from gen_retry.tools.qwen_image_adapter import QwenImageAdapter


STRATEGY_VERSION_V1 = "verb_generation_techniques_v1"
STRATEGY_VERSION_V2 = "verb_generation_techniques_v2"
STRATEGY_VERSION_V3 = "verb_generation_techniques_v3"
STRATEGY_LATERAL = "lateral_kinematic_chain"
STRATEGY_FOCAL = "focal_action_anchor"
STRATEGY_IMMINENT = "imminent_capture_frontload"
STRATEGY_GRAPHIC = "graphic_action_strip"
STRATEGY_COMPACT_GAP = "compact_capture_gap"
STRATEGY_COMPACT_INTENT = "compact_intent_asymmetry"
STRATEGY_IDS = (
    STRATEGY_LATERAL,
    STRATEGY_FOCAL,
    STRATEGY_IMMINENT,
    STRATEGY_GRAPHIC,
    STRATEGY_COMPACT_GAP,
    STRATEGY_COMPACT_INTENT,
)
STRATEGY_VERSIONS = {
    STRATEGY_LATERAL: STRATEGY_VERSION_V1,
    STRATEGY_FOCAL: STRATEGY_VERSION_V1,
    STRATEGY_IMMINENT: STRATEGY_VERSION_V2,
    STRATEGY_GRAPHIC: STRATEGY_VERSION_V2,
    STRATEGY_COMPACT_GAP: STRATEGY_VERSION_V3,
    STRATEGY_COMPACT_INTENT: STRATEGY_VERSION_V3,
}


@dataclass(frozen=True)
class VerbRelation:
    constraint_id: str
    verb: str
    subject: str
    object: str
    evaluator_question: str


def verb_relation(task_spec: dict[str, Any]) -> VerbRelation:
    constraints = [
        constraint
        for constraint in task_spec["constraints"]
        if constraint["constraint_type"] == "verb"
    ]
    if len(constraints) != 1:
        raise ValueError(
            "verb strategy experiment requires exactly one verb constraint; "
            f"found {len(constraints)}"
        )
    constraint = constraints[0]
    question = str(constraint["evaluator_question"]).strip()
    match = re.fullmatch(
        r"(?:Is|Are)\s+(?:the\s+)?(.+?)\s+"
        r"(chasing|playing with|jumping over)\s+"
        r"(?:the\s+)?(.+?)\?",
        question,
        flags=re.IGNORECASE,
    )
    if match is None:
        raise ValueError(f"unsupported verb evaluator question: {question}")
    return VerbRelation(
        constraint_id=str(constraint["constraint_id"]),
        verb=match.group(2).lower(),
        subject=match.group(1).strip(),
        object=match.group(3).strip(),
        evaluator_question=question,
    )


def compose_strategy_instruction(
    *,
    baseline_instruction: str,
    task_spec: dict[str, Any],
    strategy_id: str,
) -> str:
    relation = verb_relation(task_spec)
    if strategy_id == STRATEGY_LATERAL:
        operator = _lateral_operator(relation)
    elif strategy_id == STRATEGY_FOCAL:
        operator = _focal_operator(relation)
    elif strategy_id == STRATEGY_IMMINENT:
        return _frontloaded_instruction(
            baseline_instruction=baseline_instruction,
            strategy_id=strategy_id,
            operator=_imminent_operator(relation),
        )
    elif strategy_id == STRATEGY_GRAPHIC:
        return _frontloaded_instruction(
            baseline_instruction=baseline_instruction,
            strategy_id=strategy_id,
            operator=_graphic_operator(relation),
        )
    elif strategy_id == STRATEGY_COMPACT_GAP:
        return _insert_compact_operator(
            baseline_instruction=baseline_instruction,
            strategy_id=strategy_id,
            operator=_compact_gap_operator(relation),
        )
    elif strategy_id == STRATEGY_COMPACT_INTENT:
        return _insert_compact_operator(
            baseline_instruction=baseline_instruction,
            strategy_id=strategy_id,
            operator=_compact_intent_operator(relation),
        )
    else:
        raise ValueError(f"unknown verb strategy: {strategy_id}")
    return (
        f"{baseline_instruction.rstrip()}\n\n"
        f"Verb-specific composition technique "
        f"({strategy_version(strategy_id)}, {strategy_id}): "
        f"{operator} Preserve every requested exact count, object identity, attribute, "
        "and static spatial relation from the scene specification. Supporting objects "
        "must remain visible in their assigned regions, but must not occlude or split "
        "the action endpoints. Do not add labels, arrows, captions, panels, or text."
    )


def run_strategy_episode(
    *,
    baseline_episode_dir: Path,
    output_episode_dir: Path,
    strategy_id: str,
    seed: int = 0,
    num_inference_steps: int | None = None,
    height: int = 1024,
    width: int = 1024,
) -> dict[str, Any]:
    task_spec = _read_json(baseline_episode_dir / "task_spec.json")
    baseline_state = _read_json(baseline_episode_dir / "episode_state.json")
    relation = verb_relation(task_spec)
    baseline_attempt = baseline_state["attempts"]["a_000"]
    if baseline_attempt["operation"] != "generate":
        raise ValueError(f"baseline a_000 is not a generation: {baseline_episode_dir}")
    baseline_instruction = baseline_attempt["action"]["arguments"]["instruction"]
    instruction = compose_strategy_instruction(
        baseline_instruction=baseline_instruction,
        task_spec=task_spec,
        strategy_id=strategy_id,
    )

    config = load_model_config()
    execution = config.resolved_image_execution
    backend = execution.generate_backend
    resolved_steps = num_inference_steps or backend.num_inference_steps or 50
    output_episode_dir.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_episode_dir / "task_spec.json", task_spec)
    input_payload = {
        "schema_version": "0.1",
        "experiment_version": strategy_version(strategy_id),
        "strategy_id": strategy_id,
        "episode_id": task_spec["episode_id"],
        "baseline_episode_dir": str(baseline_episode_dir),
        "baseline_attempt_id": "a_000",
        "baseline_submitted_attempt_id": baseline_state["submitted_attempt_id"],
        "verb_relation": {
            "constraint_id": relation.constraint_id,
            "verb": relation.verb,
            "subject": relation.subject,
            "object": relation.object,
            "evaluator_question": relation.evaluator_question,
        },
        "baseline_instruction": baseline_instruction,
        "candidate_instruction": instruction,
        "candidate_instruction_sha256": sha256_bytes(instruction.encode("utf-8")),
        "execution_profile": {
            "profile_id": execution.profile_id,
            "profile_version": execution.profile_version,
            "backend_id": backend.backend_id,
            "model_id": backend.model_id,
            "seed": seed,
            "num_inference_steps": resolved_steps,
            "height": height,
            "width": width,
            "true_cfg_scale": backend.true_cfg_scale,
        },
    }
    _write_json_atomic(output_episode_dir / "experiment_input.json", input_payload)

    generator = QwenImageAdapter(
        provider=backend.provider,
        model_id=backend.model_id,
        model_path=backend.model_path,
        artifact_root=output_episode_dir,
        height=height,
        width=width,
        num_inference_steps=resolved_steps,
        true_cfg_scale=backend.true_cfg_scale,
        seed=seed,
    )
    generation = generator.generate(
        request_id=(
            f"{strategy_version(strategy_id)}_{strategy_id}_{task_spec['episode_id']}"
        ),
        attempt_id="a_000",
        image_artifact_id="img_000",
        instruction=instruction,
    )

    evaluator = LocalGeneval2Adapter(
        evaluator_root=config.evaluator.config_path,
        artifact_root=output_episode_dir,
    )
    report = evaluator.evaluate_to_report(
        task_spec=task_spec,
        attempt_id="a_000",
        image_path=output_episode_dir / generation.artifact_uri,
    )
    manifest = {
        "schema_version": "0.2",
        "episode_id": task_spec["episode_id"],
        "artifacts": [generation.manifest_entry, report.manifest_entry],
    }
    _write_json_atomic(output_episode_dir / "manifest.json", manifest)

    baseline_submitted = baseline_state["attempts"][
        baseline_state["submitted_attempt_id"]
    ]
    candidate_results = {
        result["constraint_id"]: result for result in report.constraint_results
    }
    result_payload = {
        "schema_version": "0.1",
        "experiment_version": strategy_version(strategy_id),
        "strategy_id": strategy_id,
        "episode_id": task_spec["episode_id"],
        "verb": relation.verb,
        "verb_constraint_id": relation.constraint_id,
        "image_ref": generation.artifact_uri,
        "image_sha256": generation.artifact_sha256,
        "candidate": {
            "verb_status": candidate_results[relation.constraint_id]["status"],
            "verb_confidence": candidate_results[relation.constraint_id]["confidence"],
            "passed_constraint_ids": sorted(
                constraint_id
                for constraint_id, result in candidate_results.items()
                if result["status"] == "pass"
            ),
            "primary_score": report.primary_score,
        },
        "baseline_first": _baseline_outcome(
            baseline_attempt, relation.constraint_id
        ),
        "baseline_submitted": _baseline_outcome(
            baseline_submitted, relation.constraint_id
        ),
        "comparison_to_first": _compare_results(
            baseline_attempt["constraint_results"], candidate_results
        ),
        "comparison_to_submitted": _compare_results(
            baseline_submitted["constraint_results"], candidate_results
        ),
    }
    _write_json_atomic(output_episode_dir / "result.json", result_payload)
    return result_payload


def summarize_strategy_root(run_root: Path) -> dict[str, Any]:
    results = [
        _read_json(path)
        for path in sorted(run_root.glob("phase3_ep_*/result.json"))
    ]
    if not results:
        return {
            "schema_version": "0.1",
            "experiment_version": None,
            "strategy_id": run_root.name,
            "completed": 0,
        }
    strategy_ids = {result["strategy_id"] for result in results}
    if len(strategy_ids) != 1:
        raise ValueError(f"mixed strategies under {run_root}: {sorted(strategy_ids)}")
    verb_breakdown: dict[str, dict[str, int]] = {}
    for result in results:
        verb = result["verb"]
        counts = verb_breakdown.setdefault(
            verb,
            {
                "episodes": 0,
                "candidate_pass": 0,
                "baseline_first_pass": 0,
                "baseline_submitted_pass": 0,
            },
        )
        counts["episodes"] += 1
        counts["candidate_pass"] += result["candidate"]["verb_status"] == "pass"
        counts["baseline_first_pass"] += (
            result["baseline_first"]["verb_status"] == "pass"
        )
        counts["baseline_submitted_pass"] += (
            result["baseline_submitted"]["verb_status"] == "pass"
        )
    summary = {
        "schema_version": "0.1",
        "experiment_version": results[0]["experiment_version"],
        "strategy_id": next(iter(strategy_ids)),
        "completed": len(results),
        "verb_pass": {
            "candidate": sum(
                result["candidate"]["verb_status"] == "pass" for result in results
            ),
            "baseline_first": sum(
                result["baseline_first"]["verb_status"] == "pass"
                for result in results
            ),
            "baseline_submitted": sum(
                result["baseline_submitted"]["verb_status"] == "pass"
                for result in results
            ),
        },
        "nonverb_pass": {
            "candidate": sum(
                len(result["candidate"]["passed_constraint_ids"])
                - (result["candidate"]["verb_status"] == "pass")
                for result in results
            ),
            "baseline_first": sum(
                result["baseline_first"]["pass_count"]
                - (result["baseline_first"]["verb_status"] == "pass")
                for result in results
            ),
            "baseline_submitted": sum(
                result["baseline_submitted"]["pass_count"]
                - (result["baseline_submitted"]["verb_status"] == "pass")
                for result in results
            ),
        },
        "comparison_to_first": {
            "fixed_atoms": sum(
                len(result["comparison_to_first"]["fixed_constraint_ids"])
                for result in results
            ),
            "regressed_atoms": sum(
                len(result["comparison_to_first"]["regressed_constraint_ids"])
                for result in results
            ),
        },
        "verb_breakdown": dict(sorted(verb_breakdown.items())),
        "episode_ids": [result["episode_id"] for result in results],
    }
    _write_json_atomic(run_root / "summary.json", summary)
    return summary


def strategy_version(strategy_id: str) -> str:
    try:
        return STRATEGY_VERSIONS[strategy_id]
    except KeyError as exc:
        raise ValueError(f"unknown verb strategy: {strategy_id}") from exc


def _lateral_operator(relation: VerbRelation) -> str:
    if relation.verb == "chasing":
        return (
            f"Use a strict lateral side-view, readable as one frozen action frame. "
            f"Stage every {relation.subject} in a compact pursuit lane on the viewer-left "
            f"and every {relation.object} in a separate escape lane on the viewer-right. "
            f"All heads, noses, torsos, and running strides point left-to-right; no action "
            f"animal faces the camera. The {relation.subject} look directly at and lean "
            f"toward the {relation.object}; the {relation.object} lean away and flee. "
            "Keep a short, empty chase gap between the two role-separated groups. Never "
            "intermix the groups, place them side-by-side, make them run toward one "
            "another, or reverse chaser and target order. Use clear full-body silhouettes "
            "against an uncluttered background."
        )
    if relation.verb == "jumping over":
        return (
            f"Use a strict lateral side-view at the decisive airborne instant. Place the "
            f"{relation.subject} visibly above and crossing over the {relation.object}, "
            "with bent legs, a clean band of empty air under every jumper, and a separate "
            "ground shadow below. Keep jumper and obstacle silhouettes fully visible; "
            "never place them merely beside, behind, touching, or standing on one another. "
            "Use an uncluttered background and one consistent left-to-right trajectory."
        )
    return (
        f"Use a clean three-quarter side-view centered on one shared play zone. Arrange "
        f"the {relation.subject} and {relation.object} facing inward toward one another "
        "around the same visible toy or ball. Show reciprocal play through reaching paws, "
        "mutual gaze, and contact with that single shared prop. Keep the two roles "
        "separated and full-bodied, but close enough to form one interaction cluster; "
        "never show unrelated standing, parallel posing, fighting, or separate activities."
    )


def _focal_operator(relation: VerbRelation) -> str:
    if relation.verb == "chasing":
        return (
            f"Build the whole composition around one unmistakable focal pursuit pair at "
            f"image center: one lead {relation.subject} is a short distance directly "
            f"behind one lead {relation.object}, gaze locked on the target, body stretched "
            f"forward in a running stride, while the target runs away and looks back over "
            "its shoulder. Continue all remaining required instances in two distinct "
            "role-specific trails behind the corresponding lead animal, moving in the "
            "same direction. A continuous dust trail or motion streak may connect the "
            "pursuit, but the bodies must stay sharp, full, separate, and countable. Keep "
            "the target ahead, the chaser behind, and never mix or reverse their roles."
        )
    if relation.verb == "jumping over":
        return (
            f"Build the scene around one unmistakable focal crossing: a lead "
            f"{relation.subject} is frozen at the apex directly above a clearly visible "
            f"{relation.object}, with tucked legs, open air between them, and the jumper's "
            "shadow on the far side to prove forward travel. Arrange additional required "
            "instances as repetitions of the same crossing without overlap. Do not show "
            "standing beside, resting on, or merely appearing behind the target."
        )
    return (
        f"Build the scene around one unmistakable focal play interaction between a lead "
        f"{relation.subject} and a lead {relation.object}: both look at the same single "
        "toy or ball, both reach toward it, and at least one from each role visibly "
        "touches it. Arrange all remaining required instances as participants around this "
        "same focal game, facing inward rather than posing independently. Keep every body "
        "recognizable, separate, and countable; do not turn play into fighting or unrelated "
        "parallel activity."
    )


def _frontloaded_instruction(
    *,
    baseline_instruction: str,
    strategy_id: str,
    operator: str,
) -> str:
    return (
        f"Primary verb composition technique "
        f"({strategy_version(strategy_id)}, {strategy_id}): {operator} "
        "This action topology is the foreground focal point. Preserve every exact count, "
        "object identity, attribute, and static spatial relation specified below. Place "
        "supporting objects outside the clear gap between actor and target. Do not add "
        "labels, arrows, captions, panels, or text.\n\n"
        f"Scene requirements: {baseline_instruction.rstrip()}"
    )


def _imminent_operator(relation: VerbRelation) -> str:
    if relation.verb == "chasing":
        return (
            f"Freeze the instant just before capture in a strict side view. The "
            f"{relation.subject} are the pursuers and must be directly behind the "
            f"{relation.object}, never ahead of them; the {relation.object} are the "
            "fleeing targets, never the pursuers. At image center, one lead pursuer's "
            "outstretched paw, hoof, beak, or nose is almost touching the lead target's "
            "tail or rear leg. The pursuer stares at and reaches for the target; the "
            "target looks back in alarm while sprinting away. Repeat the same role order "
            "for all remaining instances in two separated trails. Make the short capture "
            "gap, asymmetric intent, and full-body running poses more visually dominant "
            "than generic dust or motion blur."
        )
    if relation.verb == "jumping over":
        return (
            f"Freeze the decisive apex: the {relation.subject} are fully airborne "
            f"directly above the {relation.object}, with tucked legs and a clean visible "
            "air gap. Put the takeoff point on one side and the landing shadow on the "
            "other, so the crossing cannot read as standing beside or resting on."
        )
    return (
        f"Freeze a decisive shared-play instant: the {relation.subject} and "
        f"{relation.object} face each other at close range, both look at and reach for "
        "the same single ball or toy, and one member of each role visibly touches it. "
        "All remaining instances join this same game instead of posing independently."
    )


def _graphic_operator(relation: VerbRelation) -> str:
    style = (
        "Use a clean editorial action illustration on a plain light background, with "
        "sharp full-body silhouettes, restrained detail, strong pose readability, and "
        "one horizontal left-to-right action line. "
    )
    if relation.verb == "chasing":
        return (
            f"{style}The {relation.subject} are unmistakably the pursuers on the left and "
            f"the {relation.object} are unmistakably the fleeing targets on the right. "
            "Show a pursuer very close behind a target, reaching toward its tail, while "
            "the target looks backward in alarm. Every body faces and runs to the right. "
            "Keep the two roles in separate trails; never reverse them, interleave them, "
            "or make them face the viewer. Exaggerate the chase poses enough to read at "
            "thumbnail size without symbols or text."
        )
    if relation.verb == "jumping over":
        return (
            f"{style}Show the {relation.subject} at the apex of a left-to-right leap "
            f"directly above the {relation.object}, with a clean air gap and a separate "
            "shadow below. Exaggerate the arc and tucked legs so the crossing reads at "
            "thumbnail size."
        )
    return (
        f"{style}Place the {relation.subject} and {relation.object} in one centered "
        "interaction cluster around a single bright ball or toy. Use mutual gaze, inward "
        "body orientation, reaching limbs, and shared contact so play reads at thumbnail "
        "size without symbols or text."
    )


def _insert_compact_operator(
    *,
    baseline_instruction: str,
    strategy_id: str,
    operator: str,
) -> str:
    stripped = baseline_instruction.strip()
    sentence_end = stripped.find(".")
    compact = (
        f" Verb technique ({strategy_version(strategy_id)}): {operator}"
    )
    if sentence_end < 0:
        return f"{stripped}.{compact}"
    return f"{stripped[: sentence_end + 1]}{compact}{stripped[sentence_end + 1:]}"


def _compact_gap_operator(relation: VerbRelation) -> str:
    if relation.verb == "chasing":
        return (
            f"Make {relation.subject} the only pursuers and {relation.object} the only "
            f"fleeing targets. Put one lead {relation.subject} immediately behind one "
            f"{relation.object}, staring at it and reaching to within a small gap of its "
            "tail, while the target looks back in alarm and escapes; never reverse or "
            "intermix the roles. "
        )
    if relation.verb == "jumping over":
        return (
            f"Freeze the {relation.subject} fully airborne directly above the "
            f"{relation.object}, with tucked legs, a clean air gap, and a separate landing "
            "shadow; never show them merely beside or standing on the target. "
        )
    return (
        f"Make the {relation.subject} and {relation.object} face one another and both "
        "reach for and touch the same single toy, so their shared play is visually "
        "decisive rather than parallel posing. "
    )


def _compact_intent_operator(relation: VerbRelation) -> str:
    if relation.verb == "chasing":
        return (
            f"Show {relation.subject} actively trying to catch {relation.object}: the "
            "pursuers focus on the targets with forward-reaching limbs or open mouths, "
            "and the targets recoil, look back fearfully, and sprint away. Make this "
            "asymmetric capture intent unmistakable, not generic running together. "
        )
    if relation.verb == "jumping over":
        return (
            f"Show takeoff-to-landing intent: the {relation.subject} are at the apex above "
            f"the {relation.object}, legs tucked and body stretched forward, with open air "
            "below and the landing zone ahead. "
        )
    return (
        f"Show reciprocal playful intent between {relation.subject} and "
        f"{relation.object}: mutual gaze, relaxed playful poses, and both roles reaching "
        "for the same toy; avoid fighting or unrelated motion. "
    )


def _baseline_outcome(
    attempt: dict[str, Any],
    verb_constraint_id: str,
) -> dict[str, Any]:
    return {
        "attempt_id": attempt["attempt_id"],
        "verb_status": attempt["constraint_results"][verb_constraint_id]["status"],
        "verb_confidence": attempt["constraint_results"][verb_constraint_id][
            "confidence"
        ],
        "pass_count": len(attempt["passed_constraint_ids"]),
        "passed_constraint_ids": sorted(attempt["passed_constraint_ids"]),
        "primary_score": attempt["primary_score"],
    }


def _compare_results(
    baseline_results: dict[str, dict[str, Any]],
    candidate_results: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    baseline_pass = {
        constraint_id
        for constraint_id, result in baseline_results.items()
        if result["status"] == "pass"
    }
    candidate_pass = {
        constraint_id
        for constraint_id, result in candidate_results.items()
        if result["status"] == "pass"
    }
    return {
        "fixed_constraint_ids": sorted(candidate_pass - baseline_pass),
        "regressed_constraint_ids": sorted(baseline_pass - candidate_pass),
        "stable_pass_constraint_ids": sorted(baseline_pass & candidate_pass),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    os.replace(temporary, path)
