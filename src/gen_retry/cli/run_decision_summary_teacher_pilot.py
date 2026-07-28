from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from gen_retry.domain.artifacts import sha256_bytes
from gen_retry.phase3.model_config import load_model_config
from gen_retry.protocol.action_parser import ActionParseError, parse_action
from gen_retry.protocol.reference_validator import ActionReferenceError, validate_action_references
from gen_retry.runtime.json_canonical import canonical_json


DEFAULT_OUTPUT_ROOT = Path("artifacts/phase4/decision_summary_teacher_pilot")
CAUSAL_CONNECTORS = re.compile(r"\b(because|since|given|while|after|as)\b", re.IGNORECASE)
FUTURE_LEAKAGE = re.compile(
    r"\b(will pass|will fix|will improve|geneval2 will|evaluator will|result will)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PilotCase:
    case_id: str
    planner_context: dict[str, Any]
    expected_action: str
    expected_attempt_id: str | None = None


def _atom_constraints() -> list[dict[str, Any]]:
    rows = [
        ("c_001", "count", "Expected answer: six", "How many lions are in the image?"),
        ("c_002", "attribute", "Expected answer: Yes", "Are the lions made of glass?"),
        ("c_003", "object", "Expected answer: Yes", "Are there any lions in the image?"),
        ("c_004", "verb", "Expected answer: Yes", "Are the lions chasing the cats?"),
        ("c_005", "count", "Expected answer: three", "How many cats are in the image?"),
        ("c_006", "attribute", "Expected answer: Yes", "Are the cats red?"),
        ("c_007", "object", "Expected answer: Yes", "Are there any cats in the image?"),
        ("c_008", "position", "Expected answer: Yes", "Are the cats behind the donut?"),
        ("c_009", "count", "Expected answer: one", "How many donuts are in the image?"),
        ("c_010", "attribute", "Expected answer: Yes", "Is the donut brown?"),
        ("c_011", "object", "Expected answer: Yes", "Are there any donuts in the image?"),
    ]
    return [
        {
            "constraint_id": constraint_id,
            "constraint_type": constraint_type,
            "requirement": requirement,
            "evaluator_question": question,
        }
        for constraint_id, constraint_type, requirement, question in rows
    ]


def _task_spec() -> dict[str, Any]:
    return {
        "schema_version": "0.2",
        "episode_id": "decision_summary_pilot",
        "original_prompt": "six glass lions chasing three red cats behind a brown donut",
        "max_image_attempts": 5,
        "constraints": _atom_constraints(),
    }


def _constraint_results(
    passed: list[str],
    failed: list[str],
    uncertain: list[str] | None = None,
) -> dict[str, Any]:
    uncertain = uncertain or []
    statuses = {constraint_id: "pass" for constraint_id in passed}
    statuses.update({constraint_id: "fail" for constraint_id in failed})
    statuses.update({constraint_id: "uncertain" for constraint_id in uncertain})
    return {
        "passed_constraint_ids": passed,
        "failed_constraint_ids": failed,
        "uncertain_constraint_ids": uncertain,
        "observations": [
            {
                "constraint_id": atom["constraint_id"],
                "status": statuses[atom["constraint_id"]],
                "observed_value": statuses[atom["constraint_id"]],
            }
            for atom in _atom_constraints()
        ],
    }


def _round_action(
    action: str,
    source_attempt_id: str | None,
    target: list[str],
    preserve: list[str],
    instruction: str,
) -> dict[str, Any]:
    return {
        "action": action,
        "source_attempt_id": source_attempt_id,
        "target_constraint_ids": target,
        "preserve_constraint_ids": preserve,
        "instruction": instruction,
    }


def _initial_round(result_attempt_id: str, results: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_queries": [],
        "image_action": _round_action(
            "generate_image",
            None,
            [atom["constraint_id"] for atom in _atom_constraints()],
            [],
            "Create the complete requested scene with exact counts and relations.",
        ),
        "result_attempt_id": result_attempt_id,
        "observed_outcome": {
            "baseline_attempt_id": None,
            "initial_failed_constraint_ids": results["failed_constraint_ids"],
            "initial_uncertain_constraint_ids": results["uncertain_constraint_ids"],
            "became_best": True,
        },
    }


def _transition_round(
    source: str,
    result: str,
    target: list[str],
    preserve: list[str],
    *,
    fixed: list[str],
    regressed: list[str],
    persistent: list[str],
) -> dict[str, Any]:
    return {
        "skill_queries": [],
        "image_action": _round_action(
            "edit_image",
            source,
            target,
            preserve,
            "Apply a localized repair while preserving all listed passed constraints.",
        ),
        "result_attempt_id": result,
        "observed_outcome": {
            "baseline_attempt_id": source,
            "fixed_constraint_ids": fixed,
            "regressed_constraint_ids": regressed,
            "persistent_failed_constraint_ids": persistent,
            "preserved_constraint_ids": preserve,
            "new_uncertain_constraint_ids": [],
            "became_best": False,
        },
    }


def _base_context() -> dict[str, Any]:
    return {
        "task_context": {
            "original_prompt": "six glass lions chasing three red cats behind a brown donut",
            "max_image_attempts": 5,
            "atom_constraints": _atom_constraints(),
        },
        "latest_attempt": None,
        "skill_context": {
            "active_skills": [
                {
                    "skill_id": "counting_and_instance_layout",
                    "target_constraint_ids": ["c_001", "c_005", "c_009"],
                    "guidance": "Use exact totals, visible separation, and anti-duplication clauses.",
                    "guidance_level": "summary",
                },
                {
                    "skill_id": "action_pose_relation",
                    "target_constraint_ids": ["c_004"],
                    "guidance": "Use unambiguous pursuit orientation, gaze, stride, and spacing.",
                    "guidance_level": "summary",
                },
            ]
        },
        "episode_memory": {
            "last_completed_image_round": None,
            "prior_image_rounds": [],
            "best_attempt": None,
        },
        "runtime_state": {
            "remaining_image_budget": 5,
            "available_actions": ["generate_image"],
        },
    }


def _pilot_cases() -> list[PilotCase]:
    all_ids = [atom["constraint_id"] for atom in _atom_constraints()]
    first = _base_context()

    broad_results = _constraint_results(
        ["c_003", "c_006", "c_007", "c_009", "c_010", "c_011"],
        ["c_001", "c_004", "c_005", "c_008"],
        ["c_002"],
    )
    broad = _base_context()
    broad["latest_attempt"] = {"attempt_id": "a_000", "constraint_results": broad_results}
    broad["episode_memory"] = {
        "last_completed_image_round": _initial_round("a_000", broad_results),
        "prior_image_rounds": [],
        "best_attempt": {"attempt_id": "a_000", "constraint_results_ref": "latest_attempt"},
    }
    broad["runtime_state"] = {
        "remaining_image_budget": 4,
        "available_actions": ["generate_image"],
    }

    local_results = _constraint_results(
        ["c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
        ["c_001", "c_004", "c_008"],
    )
    local_edit = _base_context()
    local_edit["latest_attempt"] = {"attempt_id": "a_001", "constraint_results": local_results}
    local_edit["episode_memory"] = {
        "last_completed_image_round": _initial_round("a_001", local_results),
        "prior_image_rounds": [],
        "best_attempt": {"attempt_id": "a_001", "constraint_results_ref": "latest_attempt"},
    }
    local_edit["runtime_state"] = {
        "remaining_image_budget": 3,
        "available_actions": ["edit_image"],
    }

    best_results = _constraint_results(
        ["c_001", "c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
        ["c_004", "c_008"],
    )
    latest_regressed_results = _constraint_results(
        ["c_001", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
        ["c_002", "c_004", "c_008"],
    )
    rollback = _base_context()
    rollback["latest_attempt"] = {
        "attempt_id": "a_003",
        "constraint_results": latest_regressed_results,
    }
    rollback["episode_memory"] = {
        "last_completed_image_round": _transition_round(
            "a_002",
            "a_003",
            ["c_004", "c_008"],
            ["c_001", "c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
            fixed=[],
            regressed=["c_002"],
            persistent=["c_004", "c_008"],
        ),
        "prior_image_rounds": [
            {
                "action": "edit_image",
                "source_attempt_id": "a_001",
                "result_attempt_id": "a_002",
                "target_constraint_ids": ["c_001", "c_004", "c_008"],
                "preserve_constraint_ids": ["c_002", "c_003", "c_005", "c_006", "c_007", "c_009", "c_010", "c_011"],
                "outcome_summary": {
                    "result_failed_constraint_ids": ["c_004", "c_008"],
                    "result_uncertain_constraint_ids": [],
                    "fixed_constraint_ids": ["c_001"],
                    "regressed_constraint_ids": [],
                    "became_best": True,
                },
            }
        ],
        "best_attempt": {"attempt_id": "a_002", "constraint_results": best_results},
    }
    rollback["runtime_state"] = {
        "remaining_image_budget": 1,
        "available_actions": ["edit_image", "submit_attempt"],
    }

    submit = json.loads(json.dumps(rollback))
    submit["latest_attempt"] = {
        "attempt_id": "a_004",
        "constraint_results": latest_regressed_results,
    }
    submit["runtime_state"] = {
        "remaining_image_budget": 0,
        "available_actions": ["submit_attempt"],
    }

    return [
        PilotCase("first_generation", first, "generate_image"),
        PilotCase("broad_failure_regenerate", broad, "generate_image"),
        PilotCase("localized_edit", local_edit, "edit_image", "a_001"),
        PilotCase("rollback_best", rollback, "edit_image", "a_002"),
        PilotCase("budget_exhausted_submit", submit, "submit_attempt", "a_002"),
    ]


def _known_attempt_ids(context: dict[str, Any]) -> list[str]:
    ids: set[str] = set()
    latest = context.get("latest_attempt")
    if latest:
        ids.add(latest["attempt_id"])
    memory = context["episode_memory"]
    best = memory.get("best_attempt")
    if best:
        ids.add(best["attempt_id"])
    recent = memory.get("last_completed_image_round")
    if recent:
        ids.add(recent["result_attempt_id"])
        source = recent["image_action"].get("source_attempt_id")
        if source:
            ids.add(source)
    for prior in memory.get("prior_image_rounds", []):
        ids.add(prior["result_attempt_id"])
        if prior.get("source_attempt_id"):
            ids.add(prior["source_attempt_id"])
    return sorted(ids)


def _messages(case: PilotCase, *, candidate: bool) -> list[dict[str, str]]:
    decision_contract = (
        "For generate_image, edit_image, and submit_attempt, arguments must also contain "
        "decision_summary: one sentence, 12-200 characters and at most 48 tokens. Explain "
        "only why this action is chosen from the visible state. For edit, explain the "
        "source choice. For submit, explain stopping and attempt selection. Do not repeat "
        "the instruction, expose chain-of-thought, or predict future evaluator results."
        if candidate
        else "Do not include decision_summary or any rationale field."
    )
    system = (
        "You are the Gen-Retry teacher planner. Return exactly one strict JSON action and "
        "no markdown, prose, or chain-of-thought. Use only information already present in "
        "PlannerContext. Never emit evaluator outcomes or future predictions."
    )
    user = "\n\n".join(
        [
            "Contract:",
            (
                "Top-level keys are exactly schema_version, action, arguments. "
                "schema_version is \"0.5\". Legal actions are exactly those listed in "
                "runtime_state.available_actions. generate_image arguments require "
                "target_constraint_ids, preserve_constraint_ids, instruction. edit_image "
                "also requires source_attempt_id. submit_attempt requires "
                "selected_attempt_id and reason_code. target and preserve must not overlap."
            ),
            decision_contract,
            (
                "Use best/latest history correctly. With zero remaining image budget, "
                "submit the historical best using reason_code best_available_under_budget. "
                "Instructions must remain executable and preserve passed non-target atoms."
            ),
            "PlannerContext:",
            canonical_json(case.planner_context),
        ]
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _strip_candidate_summary(action: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    base_action = json.loads(json.dumps(action))
    summary = base_action.get("arguments", {}).pop("decision_summary", None)
    return base_action, summary


def _validate_output(
    raw_text: str,
    case: PilotCase,
    *,
    candidate: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "json_valid": False,
        "schema_valid": False,
        "reference_valid": False,
        "decision_correct": False,
        "summary_contract_valid": not candidate,
        "summary_state_to_decision": not candidate,
        "summary_future_leakage": False,
        "errors": [],
    }
    try:
        action = json.loads(raw_text)
        if not isinstance(action, dict):
            raise ValueError("output is not a JSON object")
        result["json_valid"] = True
    except (json.JSONDecodeError, ValueError) as exc:
        result["errors"].append(str(exc))
        return result

    base_action, summary = _strip_candidate_summary(action)
    try:
        parse_action(canonical_json(base_action))
        result["schema_valid"] = True
    except ActionParseError as exc:
        result["errors"].append(f"{exc.error_code}: {exc.message}")

    try:
        validate_action_references(
            base_action,
            _task_spec(),
            known_attempt_ids=_known_attempt_ids(case.planner_context),
        )
        result["reference_valid"] = True
    except ActionReferenceError as exc:
        result["errors"].append(str(exc))

    selected_id = None
    arguments = base_action.get("arguments", {})
    if base_action.get("action") == "edit_image":
        selected_id = arguments.get("source_attempt_id")
    elif base_action.get("action") == "submit_attempt":
        selected_id = arguments.get("selected_attempt_id")
    result["decision_correct"] = (
        base_action.get("action") == case.expected_action
        and (case.expected_attempt_id is None or selected_id == case.expected_attempt_id)
    )

    if candidate:
        summary_text = summary if isinstance(summary, str) else ""
        summary_characters = len(summary_text)
        summary_words = len(summary_text.split())
        result["summary"] = summary_text
        result["summary_characters"] = summary_characters
        result["summary_words"] = summary_words
        result["summary_contract_valid"] = (
            isinstance(summary, str)
            and 12 <= summary_characters <= 200
            and "\n" not in summary_text
            and "\r" not in summary_text
            and summary_words <= 48
        )
        result["summary_state_to_decision"] = bool(CAUSAL_CONNECTORS.search(summary_text))
        result["summary_future_leakage"] = bool(FUTURE_LEAKAGE.search(summary_text))
    elif summary is not None:
        result["schema_valid"] = False
        result["errors"].append("control output unexpectedly included decision_summary")

    return result


def _call_one(
    *,
    case: PilotCase,
    candidate: bool,
    sample_index: int,
    output_root: Path,
    model_id: str,
    api_key: str,
    base_url: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    profile = "candidate" if candidate else "control"
    output_path = output_root / f"{profile}__{case.case_id}__sample_{sample_index}.json"
    if output_path.exists():
        return json.loads(output_path.read_text(encoding="utf-8"))

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout_seconds,
        max_retries=1,
    )
    response = client.chat.completions.create(
        model=model_id,
        messages=_messages(case, candidate=candidate),
        max_completion_tokens=900,
    )
    choice = response.choices[0]
    raw_text = choice.message.content or ""
    usage = getattr(response, "usage", None)
    record = {
        "profile": profile,
        "case_id": case.case_id,
        "sample_index": sample_index,
        "model_id": model_id,
        "raw_output": raw_text,
        "raw_output_sha256": sha256_bytes(raw_text.encode("utf-8")),
        "finish_reason": choice.finish_reason,
        "usage": usage.model_dump() if hasattr(usage, "model_dump") else None,
        "validation": _validate_output(raw_text, case, candidate=candidate),
    }
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_profile: dict[str, Any] = {}
    for profile in ("control", "candidate"):
        selected = [record for record in records if record["profile"] == profile]
        by_profile[profile] = {
            "sample_count": len(selected),
            "schema_valid": sum(record["validation"]["schema_valid"] for record in selected),
            "reference_valid": sum(record["validation"]["reference_valid"] for record in selected),
            "decision_correct": sum(record["validation"]["decision_correct"] for record in selected),
        }
        if profile == "candidate":
            by_profile[profile].update(
                {
                    "summary_contract_valid": sum(
                        record["validation"]["summary_contract_valid"] for record in selected
                    ),
                    "summary_state_to_decision": sum(
                        record["validation"]["summary_state_to_decision"] for record in selected
                    ),
                    "summary_future_leakage": sum(
                        record["validation"]["summary_future_leakage"] for record in selected
                    ),
                }
            )
    candidate = by_profile["candidate"]
    control = by_profile["control"]
    automatic_pass = (
        candidate["sample_count"] == 10
        and candidate["schema_valid"] == 10
        and candidate["reference_valid"] == 10
        and candidate["decision_correct"] == 10
        and candidate["summary_contract_valid"] == 10
        and candidate["summary_state_to_decision"] == 10
        and candidate["summary_future_leakage"] == 0
        and candidate["decision_correct"] >= control["decision_correct"]
    )
    return {
        "experiment": "decision_summary_teacher_only_ab",
        "model_id": records[0]["model_id"] if records else None,
        "credentials_persisted_in_artifacts": False,
        "profiles": by_profile,
        "automatic_pass": automatic_pass,
        "manual_sol_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--samples-per-case", type=int, default=2)
    parser.add_argument("--max-workers", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()

    config = load_model_config()
    api_key = os.environ.get(config.teacher.api_key_env)
    base_url = os.environ.get(config.teacher.base_url_env)
    if not api_key or not base_url:
        raise RuntimeError("Teacher environment is missing after local configuration load")

    args.output_root.mkdir(parents=True, exist_ok=True)
    jobs = [
        (case, candidate, sample_index)
        for candidate in (False, True)
        for case in _pilot_cases()
        for sample_index in range(1, args.samples_per_case + 1)
    ]
    records: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(
                _call_one,
                case=case,
                candidate=candidate,
                sample_index=sample_index,
                output_root=args.output_root,
                model_id=config.teacher.model_id,
                api_key=api_key,
                base_url=base_url,
                timeout_seconds=args.timeout_seconds,
            )
            for case, candidate, sample_index in jobs
        ]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())

    records.sort(key=lambda record: (record["profile"], record["case_id"], record["sample_index"]))
    summary = _summary(records)
    (args.output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(canonical_json(summary))
    return 0 if summary["automatic_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
