from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from gen_retry.agent.instruction_quality import evaluate_instruction_quality
from gen_retry.agent.teacher_client import (
    TEACHER_SYSTEM_PROMPT_VERSION,
    teacher_system_prompt_sha256,
)
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.reducer import AttemptRecord, build_transition, reduce_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Export one trajectory as a readable action trace.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export_trace(args.run_dir, args.output)
    print(f"wrote {args.output}")


def export_trace(run_dir: Path, output_path: Path) -> None:
    events = load_events_jsonl(run_dir / "events.jsonl")
    state = reduce_events(events)
    task_spec = json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))
    actions = _load_jsonl(run_dir / "canonical_actions.jsonl")
    planner_requests = {
        item["request_id"]: item
        for item in _load_jsonl(run_dir / "planner_requests.jsonl")
    }
    raw_outputs = {
        item["request_id"]: item
        for item in _load_jsonl(run_dir / "raw_teacher_outputs.jsonl")
    }
    tool_observations = _load_jsonl(run_dir / "tool_observations.jsonl")
    geneval_results = {
        item["attempt_id"]: item
        for item in _load_jsonl(run_dir / "geneval2_results.jsonl")
    }
    attempt_contexts = _attempt_contexts(state)
    attempt_by_action_event = {
        context["attempt"].action_event_id: context
        for context in attempt_contexts.values()
    }
    lines: list[str] = []
    lines.extend(_header(run_dir, task_spec, state))
    for action_record in actions:
        action = action_record["action"]
        request_id = action_record["request_id"]
        planner_request = planner_requests[request_id]
        context_ref = planner_request.get("planner_context_ref") or planner_request["planner_view_ref"]
        planner_context = json.loads((run_dir / context_ref).read_text(encoding="utf-8"))
        raw = raw_outputs.get(request_id)
        lines.extend(
            _turn_header(
                action_record=action_record,
                planner_request=planner_request,
                planner_context=planner_context,
                task_spec=task_spec,
                raw=raw,
            )
        )
        if action["action"] == "query_skill":
            lines.extend(_query_skill_output(action_record, tool_observations, events))
        elif action["action"] in {"generate_image", "edit_image"}:
            context = attempt_by_action_event[action_record["action_event_id"]]
            known_attempt_ids = [
                attempt["attempt_id"]
                for attempt in _known_attempt_summaries(planner_context)
            ]
            quality = evaluate_instruction_quality(
                action,
                task_spec,
                known_attempt_ids=known_attempt_ids,
            )
            lines.extend(
                _image_action_output(
                    run_dir=run_dir,
                    action_record=action_record,
                    context=context,
                    tool_observations=tool_observations,
                    geneval_result=geneval_results[context["attempt"].attempt_id],
                    instruction_quality=quality.to_dict(),
                )
            )
        elif action["action"] == "submit_attempt":
            lines.extend(_submit_output(action_record, state))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _header(run_dir: Path, task_spec: dict[str, Any], state: Any) -> list[str]:
    lines = [
        f"# Conversation Trace: {task_spec['episode_id']}",
        "",
        "This report renders one completed trajectory as a readable GenSearcher-style conversation trace.",
        "",
        "## Task",
        "",
        f"- Run dir: `{run_dir}`",
        f"- Original prompt: {task_spec['original_prompt']}",
        f"- Max image attempts: {task_spec['max_image_attempts']}",
        f"- Submitted attempt: `{state.submitted_attempt_id}` (`{state.submitted_reason_code}`)",
        f"- Best attempt: `{state.best_attempt_id}`",
        f"- System prompt version: `{TEACHER_SYSTEM_PROMPT_VERSION}`",
        f"- System prompt SHA-256: `{teacher_system_prompt_sha256()}`",
        "",
        "## Atom Rubric",
        "",
        "| ID | Type | Requirement | Evaluator Question |",
        "| --- | --- | --- | --- |",
    ]
    for constraint in task_spec["constraints"]:
        lines.append(
            "| `{constraint_id}` | `{constraint_type}` | {requirement} | {question} |".format(
                constraint_id=constraint["constraint_id"],
                constraint_type=constraint["constraint_type"],
                requirement=_escape_table(constraint["requirement"]),
                question=_escape_table(constraint.get("evaluator_question") or ""),
            )
        )
    lines.extend(["", "## Turns", ""])
    return lines


def _turn_header(
    *,
    action_record: dict[str, Any],
    planner_request: dict[str, Any],
    planner_context: dict[str, Any],
    task_spec: dict[str, Any],
    raw: dict[str, Any] | None,
) -> list[str]:
    action = action_record["action"]
    latest = _latest_summary(planner_context)
    best = _best_summary(planner_context)
    visible_images = planner_request.get("visible_images") or _visible_images(planner_context)
    context_ref = planner_request.get("planner_context_ref") or planner_request.get("planner_view_ref")
    lines = [
        f"### {action_record['turn_id']} - assistant `{action['action']}`",
        "",
        "**User / PlannerContext**",
        "",
        f"- Request: `{action_record['request_id']}`",
        f"- PlannerContext: `{context_ref}`",
        f"- Remaining image budget: {_remaining_budget(planner_context)}",
        f"- Latest attempt: {_attempt_inline(latest)}",
        f"- Best attempt: {_attempt_inline(best)}",
        f"- Visible images: {_visible_images_inline(visible_images)}",
        f"- Extra observations: {_list_inline(planner_request.get('extra_observations') or [])}",
        f"- Retrieved skills in context: {_list_inline(planner_request.get('retrieved_skill_ids') or [])}",
        f"- Active capability skills: {_active_operators_inline(_active_operators(planner_context))}",
        f"- Latest equals best: {_latest_equals_best(planner_context)}",
        "",
        "**Teacher Input**",
        "",
        f"- System prompt version: `{planner_request.get('system_prompt_version', TEACHER_SYSTEM_PROMPT_VERSION)}`",
        f"- System prompt SHA-256: `{planner_request.get('system_prompt_sha256', teacher_system_prompt_sha256())}`",
        f"- Atomic constraints: {len(task_spec.get('constraints', []))}",
        f"- Completed round memory length: {_round_memory_length(planner_context)}",
        f"- Image labels/order: {_image_labels_inline(visible_images, planner_context)}",
        "",
        _teacher_text_block(planner_request, planner_context, task_spec),
        "",
        "**Assistant Output**",
        "",
    ]
    if raw is not None:
        lines.append(f"- Raw teacher output SHA-256: `{raw['response_metadata']['raw_text_sha256']}`")
        lines.extend(["- Raw redacted teacher output:", "", "```json", json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True), "```"])
    lines.extend(
        [
            "- Canonical action:",
            "",
            "```json",
            json.dumps(action, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    instruction = (
        action["arguments"].get("instruction")
        or action["arguments"].get("generation_instruction")
        or action["arguments"].get("edit_instruction")
    )
    if instruction:
        lines.extend(["- Action instruction:", "", f"> {instruction}", ""])
    return lines


def _query_skill_output(
    action_record: dict[str, Any],
    tool_observations: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[str]:
    event_id = action_record["action_event_id"]
    skill_event_ids = {
        event["event_id"]
        for event in events
        if event["event_type"] == "skill_returned"
        and event["payload"].get("query_action_event_id") == event_id
    }
    matching = [
        obs
        for obs in tool_observations
        if obs.get("observation_type") == "skill_returned"
        and obs.get("event_id") in skill_event_ids
    ]
    lines = ["**Tool Output**", ""]
    if not matching:
        lines.extend(["- No skill output found.", ""])
        return lines
    obs = matching[0]
    lines.append(f"- Skill return event: `{obs['event_id']}` for action `{event_id}`")
    for skill in obs["skills"]:
        lines.append(
            f"- `{skill['skill_id']}`: {skill['summary']} (`{skill['content_ref']}`)"
        )
    lines.append("")
    return lines


def _image_action_output(
    *,
    run_dir: Path,
    action_record: dict[str, Any],
    context: dict[str, Any],
    tool_observations: list[dict[str, Any]],
    geneval_result: dict[str, Any],
    instruction_quality: dict[str, Any],
) -> list[str]:
    attempt: AttemptRecord = context["attempt"]
    obs = _image_observation(tool_observations, attempt.attempt_id)
    image_path = run_dir / f"images/{attempt.image_artifact_id}.png"
    transition = context["transition"]
    lines = [
        "**Image Tool Output**",
        "",
        f"- Attempt: `{attempt.attempt_id}`",
        f"- Parent/source attempt: `{attempt.parent_attempt_id}`" if attempt.parent_attempt_id else "- Parent/source attempt: none",
        f"- Image artifact: `{image_path}`",
        f"- Operation: `{attempt.operation}`",
    ]
    if obs:
        metadata = obs.get("metadata") or {}
        lines.extend(
            [
                f"- Render params: steps={metadata.get('num_inference_steps')}, size={metadata.get('width')}x{metadata.get('height')}, true_cfg={metadata.get('true_cfg_scale')}, guidance={metadata.get('guidance_scale')}, seed={metadata.get('seed')}",
                f"- Runtime: `{metadata.get('local_runtime')}`",
            ]
        )
    instruction = (
        action_record["action"]["arguments"].get("instruction")
        or action_record["action"]["arguments"].get("generation_instruction")
        or action_record["action"]["arguments"].get("edit_instruction")
    )
    lines.extend(
        [
            "",
            "**Instruction Quality**",
            "",
            f"- Verdict: `{instruction_quality['verdict']}`",
            f"- Vague-language flags: {_list_inline(instruction_quality['vague_language_flags'])}",
            f"- Contradiction flags: {_list_inline(instruction_quality['contradiction_flags'])}",
            f"- Overbroad-edit flags: {_list_inline(instruction_quality['overbroad_edit_flags'])}",
            f"- Notes: {_list_inline(instruction_quality['notes'])}",
            "",
            "**Exact Qwen-Image-Edit Input**",
            "",
            f"- Operation: `{attempt.operation}`",
            f"- Source attempt: `{attempt.parent_attempt_id}`" if attempt.parent_attempt_id else "- Source attempt: none",
            "- Instruction:",
            "",
            f"> {instruction}",
        ]
    )
    lines.extend(
        [
            "",
            "**Verifier Output / Memory Reduction**",
            "",
            f"- Pass count: {attempt.pass_count}/{len(attempt.constraint_results)}",
            f"- Fixed vs source/latest: {_list_inline(transition['fixed'])}",
            f"- Regressed vs source/latest: {_list_inline(transition['regressed'])}",
            f"- Stable pass: {_list_inline(transition['stable_pass'])}",
            f"- Persistent failed: {_list_inline(transition['persistent_failed'])}",
            f"- Best after this turn: `{context['best_after']}`",
            "",
            "| Atom | Status | Observed | Expected |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in geneval_result["constraint_results"]:
        lines.append(
            "| `{constraint_id}` | `{status}` | {observed} | {expected} |".format(
                constraint_id=result["constraint_id"],
                status=result["status"],
                observed=_escape_table(str(result.get("observed", ""))),
                expected=_escape_table(str(result.get("expected", ""))),
            )
        )
    lines.append("")
    return lines


def _submit_output(action_record: dict[str, Any], state: Any) -> list[str]:
    args = action_record["action"]["arguments"]
    selected = args["selected_attempt_id"]
    selected_attempt = state.attempts[selected]
    lines = [
        "**Submission Output**",
        "",
        f"- Selected attempt: `{selected}`",
        f"- Reason code: `{args['reason_code']}`",
        f"- Selected pass count: {selected_attempt.pass_count}/{len(selected_attempt.constraint_results)}",
        f"- Latest at submission: `{state.latest_attempt_id}`",
        f"- Best at submission: `{state.best_attempt_id}`",
        "- Interpretation: submits historical best instead of latest."
        if selected != state.latest_attempt_id
        else "- Interpretation: submits current latest/best.",
        "",
    ]
    return lines


def _attempt_contexts(state: Any) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    latest_before = None
    best_before = None
    for attempt_id in state.attempt_order:
        attempt = state.attempts[attempt_id]
        if attempt.parent_attempt_id:
            previous = state.attempts[attempt.parent_attempt_id]
        elif latest_before:
            previous = state.attempts[latest_before]
        else:
            previous = None
        transition = build_transition(previous, attempt)
        if best_before is None:
            best_after = attempt_id
        elif attempt.pass_count > state.attempts[best_before].pass_count:
            best_after = attempt_id
        else:
            best_after = best_before
        contexts[attempt_id] = {
            "attempt": attempt,
            "transition": transition,
            "latest_before": latest_before,
            "best_before": best_before,
            "best_after": best_after,
        }
        latest_before = attempt_id
        best_before = best_after
    return contexts


def _image_observation(
    tool_observations: list[dict[str, Any]],
    attempt_id: str,
) -> dict[str, Any] | None:
    for obs in tool_observations:
        if (
            obs.get("observation_type") == "image_execution_completed"
            and obs.get("attempt_id") == attempt_id
        ):
            return obs
    return None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _latest_summary(planner_context: dict[str, Any]) -> dict[str, Any] | None:
    observation = planner_context.get("latest_attempt") or planner_context.get("latest_observation")
    if observation is not None:
        if "constraint_results" not in observation:
            return observation
        return {
            "attempt_id": observation["attempt_id"],
            "passed_constraint_ids": observation["constraint_results"]["passed_constraint_ids"],
            "failed_constraint_ids": observation["constraint_results"]["failed_constraint_ids"],
        }
    return None


def _best_summary(planner_context: dict[str, Any]) -> dict[str, Any] | None:
    best = planner_context.get("episode_memory", {}).get("best_attempt")
    if best is not None:
        constraint_results = best.get("constraint_results")
        if constraint_results is None and best.get("constraint_results_ref") == "latest_attempt":
            return _latest_summary(planner_context)
        return {
            "attempt_id": best["attempt_id"],
            "passed_constraint_ids": constraint_results["passed_constraint_ids"],
            "failed_constraint_ids": constraint_results["failed_constraint_ids"],
        }
    return planner_context.get("best_attempt")


def _visible_images(planner_context: dict[str, Any]) -> list[dict[str, Any]]:
    return []


def _remaining_budget(planner_context: dict[str, Any]) -> int | None:
    if "runtime_state" in planner_context:
        return planner_context.get("runtime_state", {}).get("remaining_image_budget")
    return planner_context.get("remaining_budget")


def _active_operators(planner_context: dict[str, Any]) -> list[dict[str, Any]]:
    return planner_context.get("skill_context", {}).get("active_skills", [])


def _round_memory_length(planner_context: dict[str, Any]) -> int:
    memory = planner_context.get("episode_memory", {})
    prior = memory.get("prior_image_rounds", memory.get("earlier_rounds", []))
    last = memory.get("last_completed_image_round", memory.get("recent_round"))
    return len(prior) + (1 if last else 0)


def _known_attempt_summaries(planner_context: dict[str, Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    memory = planner_context.get("episode_memory", {})
    for item in memory.get("prior_image_rounds", memory.get("earlier_rounds", [])):
        summaries.append({"attempt_id": item["result_attempt_id"]})
    last = memory.get("last_completed_image_round", memory.get("recent_round"))
    if last:
        summaries.append({"attempt_id": last["result_attempt_id"]})
    return summaries


def _attempt_inline(attempt: dict[str, Any] | None) -> str:
    if attempt is None:
        return "none"
    return (
        f"`{attempt['attempt_id']}` {attempt.get('action_type', 'attempt')} "
        f"pass={len(attempt['passed_constraint_ids'])} "
        f"fail={len(attempt['failed_constraint_ids'])}"
    )


def _visible_images_inline(images: list[dict[str, Any]]) -> str:
    if not images:
        return "none"
    return ", ".join(
        f"`{image['role']}:{image['attempt_id']}:{image['artifact_id']}`"
        for image in images
    )


def _active_operators_inline(active: list[dict[str, Any]]) -> str:
    if not active:
        return "none"
    return ", ".join(
        f"`{item.get('failure_signature') or item.get('skill_id')}`"
        for item in active
    )


def _latest_equals_best(planner_context: dict[str, Any]) -> str:
    latest = _latest_summary(planner_context)
    best = _best_summary(planner_context)
    if latest is None or best is None:
        return "n/a"
    return str(latest.get("attempt_id") == best.get("attempt_id")).lower()


def _image_labels_inline(images: list[dict[str, Any]], planner_context: dict[str, Any]) -> str:
    if not images:
        return "none"
    latest_equals_best = _latest_equals_best(planner_context) == "true"
    labels = []
    for image in images:
        if image["role"] == "latest":
            label = "LATEST_IMAGE"
        elif image["role"] == "best" and latest_equals_best:
            label = "BEST_IMAGE_SAME_AS_LATEST"
        else:
            label = image["role"].upper() + "_IMAGE"
        labels.append(f"`{label}:{image['attempt_id']}:{image['artifact_id']}`")
    return ", ".join(labels)


def _teacher_text_block(
    planner_request: dict[str, Any],
    planner_context: dict[str, Any],
    task_spec: dict[str, Any],
) -> str:
    if planner_request.get("teacher_text_input"):
        return "\n".join(
            [
                "<details>",
                "<summary>Exact sanitized teacher text input</summary>",
                "",
                "```text",
                planner_request["teacher_text_input"],
                "```",
                "",
                "</details>",
            ]
        )
    reconstructed = {
        "note": "Historical run did not persist exact teacher_text_input; this is a sanitized reconstruction from artifacts.",
        "original_prompt": task_spec.get("original_prompt"),
        "planner_context_ref": planner_request.get("planner_context_ref") or planner_request.get("planner_view_ref"),
        "remaining_image_budget": _remaining_budget(planner_context),
        "visible_images": planner_request.get("visible_images", []) or _visible_images(planner_context),
        "retrieved_skill_ids": planner_request.get("retrieved_skill_ids", []),
        "active_skills": _active_operators(planner_context),
        "extra_observations": planner_request.get("extra_observations", []),
    }
    return "\n".join(
        [
            "<details>",
            "<summary>Sanitized teacher input reconstruction</summary>",
            "",
            "```json",
            json.dumps(reconstructed, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "</details>",
        ]
    )


def _list_inline(items: list[Any]) -> str:
    if not items:
        return "none"
    return ", ".join(f"`{item}`" for item in items)


def _escape_table(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
