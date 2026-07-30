from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.reducer import AttemptRecord, build_transition, reduce_events


SCHEMA_VERSION = "0.2"

LABEL_TRAINABLE = "trainable_positive"
LABEL_RECOVERY = "recovery_positive"
LABEL_HARMFUL = "history_only_harmful"
LABEL_INEFFECTIVE = "history_only_ineffective"
LABEL_AMBIGUOUS = "excluded_ambiguous"
LABEL_INVALID = "excluded_invalid"

ALL_BEHAVIOR_LABELS = [
    "direct_success",
    "regeneration_used",
    "local_edit_used",
    "target_constraint_fixed",
    "constraint_regression",
    "persistent_failure",
    "repeated_ineffective_strategy",
    "historical_branch",
    "best_so_far_recovery",
    "historical_best_submission",
    "all_constraints_passed",
    "budget_exhausted",
    "invalid_infrastructure_run",
]

TRAINING_LABELS = {LABEL_TRAINABLE, LABEL_RECOVERY}
TARGETABLE_ACTIONS = {"generate_image", "edit_image", "submit_attempt"}
TARGET_PROTOCOL_VERSION = "0.5"


@dataclass(frozen=True)
class AttemptContext:
    attempt: AttemptRecord
    attempt_index: int
    latest_before: str | None
    best_before: str | None
    best_before_pass_count: int
    previous_for_transition: AttemptRecord | None
    transition: dict[str, Any]
    best_after: str


def analyze_phase3_rollouts(
    *,
    run_root: Path = Path("runs/phase3"),
    invalid_run_root: Path = Path("runs/phase3_invalid"),
    artifact_root: Path = Path("artifacts/phase3"),
    docs_root: Path = Path("docs/phase3"),
    expected_count: int = 10,
    episode_ids: list[str] | None = None,
) -> dict[str, Any]:
    run_dirs = _select_analysis_run_dirs(run_root, episode_ids)
    episodes = [_analyze_episode(path) for path in run_dirs]
    if len(episodes) != expected_count:
        raise ValueError(f"expected {expected_count} episodes, found {len(episodes)}")
    incomplete = [episode["episode_id"] for episode in episodes if not episode["submitted_attempt_id"]]
    if incomplete:
        raise ValueError(f"incomplete episodes: {', '.join(incomplete)}")

    invalid_runs = _collect_invalid_runs(invalid_run_root)
    index = _build_trajectory_index(episodes, invalid_runs)
    action_labels = [
        label
        for episode in episodes
        for label in episode["action_labels"]
    ]
    artifact_root.mkdir(parents=True, exist_ok=True)
    docs_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "trajectory_index.json").write_text(
        canonical_json(index) + "\n",
        encoding="utf-8",
    )
    _write_jsonl(artifact_root / "action_supervision_labels.jsonl", action_labels)

    for episode in episodes:
        _write_episode_report(episode)

    comparison_filename = (
        "ten_trajectory_comparison.md"
        if len(episodes) == 10
        else "trajectory_comparison.md"
    )
    (docs_root / comparison_filename).write_text(
        _render_comparison_report(episodes, invalid_runs),
        encoding="utf-8",
    )
    (docs_root / "behavior_coverage_report.md").write_text(
        _render_behavior_report(episodes, invalid_runs),
        encoding="utf-8",
    )
    (docs_root / "legacy_vs_fresh_strategy_analysis.md").write_text(
        _render_legacy_vs_fresh_report(episodes, invalid_runs),
        encoding="utf-8",
    )
    (docs_root / "sft_candidate_action_report.md").write_text(
        _render_sft_report(episodes, action_labels),
        encoding="utf-8",
    )
    return {
        "trajectory_index": index,
        "action_label_count": len(action_labels),
        "episode_count": len(episodes),
        "invalid_run_count": len(invalid_runs),
    }


def _select_analysis_run_dirs(
    run_root: Path,
    episode_ids: list[str] | None,
) -> list[Path]:
    if episode_ids is None:
        return sorted(path for path in run_root.glob("phase3_ep_*") if path.is_dir())
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("episode_ids must be unique")
    run_dirs = sorted(run_root / episode_id for episode_id in episode_ids)
    missing = [path.name for path in run_dirs if not path.is_dir()]
    if missing:
        raise ValueError("missing rollout directories: " + ", ".join(missing))
    return run_dirs


def _analyze_episode(run_dir: Path) -> dict[str, Any]:
    events = load_events_jsonl(run_dir / "events.jsonl")
    state = reduce_events(events)
    task_spec = state.task_spec
    actions = _load_jsonl(run_dir / "canonical_actions.jsonl")
    raw_outputs = _load_jsonl(run_dir / "raw_teacher_outputs.jsonl")
    format_errors = [
        event
        for event in events
        if event["event_type"] == "format_error"
    ]
    attempt_contexts = _attempt_contexts(state)
    attempt_by_action_event_id = {
        ctx.attempt.action_event_id: ctx
        for ctx in attempt_contexts.values()
    }
    skill_returned_ids = {
        ref
        for event in events
        if event["event_type"] == "skill_returned"
        for ref in event["input_refs"]
    }

    action_labels: list[dict[str, Any]] = []
    for action_record in actions:
        action = action_record["action"]
        action_event_id = action_record["action_event_id"]
        if action["action"] in {"generate_image", "edit_image"}:
            label = _label_image_action(
                episode_id=state.episode_id,
                action_record=action_record,
                context=attempt_by_action_event_id[action_event_id],
                task_constraint_count=len(task_spec["constraints"]),
            )
        elif action["action"] == "submit_attempt":
            label = _label_submit_action(
                state=state,
                action_record=action_record,
            )
        elif action["action"] == "query_skill":
            label = _label_query_skill_action(
                state.episode_id,
                action_record,
                has_skill_return=action_event_id in skill_returned_ids,
            )
        else:
            label = _base_label(
                state.episode_id,
                action_record,
                LABEL_AMBIGUOUS,
                "unknown canonical action type",
            )
        action_labels.append(label)

    valid_request_ids = {record["request_id"] for record in actions}
    error_by_request_id = {
        _request_id_from_raw_ref(event["payload"].get("raw_output_ref", "")): event
        for event in format_errors
    }
    for raw in raw_outputs:
        request_id = raw["request_id"]
        if request_id in valid_request_ids:
            continue
        error = error_by_request_id.get(request_id)
        action_labels.append(_invalid_raw_label(state.episode_id, raw, error))

    behavior_labels = _episode_behavior_labels(state, attempt_contexts, action_labels)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": state.episode_id,
        "run_dir": str(run_dir),
        "original_prompt": task_spec["original_prompt"],
        "constraint_count": len(task_spec["constraints"]),
        "max_image_attempts": task_spec["max_image_attempts"],
        "attempt_count": len(state.attempt_order),
        "submitted_attempt_id": state.submitted_attempt_id,
        "submitted_reason_code": state.submitted_reason_code,
        "best_attempt_id": state.best_attempt_id,
        "best_pass_count": state.attempts[state.best_attempt_id].pass_count
        if state.best_attempt_id
        else 0,
        "latest_attempt_id": state.latest_attempt_id,
        "remaining_budget": state.remaining_budget,
        "raw_output_count": len(raw_outputs),
        "validated_action_count": len(actions),
        "format_error_count": len(format_errors),
        "skill_return_count": len(skill_returned_ids),
        "behavior_labels": behavior_labels,
        "attempts": [
            _attempt_summary(attempt_contexts[attempt_id])
            for attempt_id in state.attempt_order
        ],
        "canonical_actions": action_labels,
    }
    summary["action_labels"] = action_labels
    return summary


def _attempt_contexts(state: Any) -> dict[str, AttemptContext]:
    contexts: dict[str, AttemptContext] = {}
    best_before: str | None = None
    latest_before: str | None = None
    for index, attempt_id in enumerate(state.attempt_order):
        attempt = state.attempts[attempt_id]
        if attempt.parent_attempt_id:
            previous = state.attempts[attempt.parent_attempt_id]
        elif latest_before:
            previous = state.attempts[latest_before]
        else:
            previous = None
        transition = build_transition(previous, attempt)
        best_after = _choose_best_after(state, best_before, attempt)
        contexts[attempt_id] = AttemptContext(
            attempt=attempt,
            attempt_index=index,
            latest_before=latest_before,
            best_before=best_before,
            best_before_pass_count=state.attempts[best_before].pass_count
            if best_before
            else -1,
            previous_for_transition=previous,
            transition=transition,
            best_after=best_after,
        )
        latest_before = attempt_id
        best_before = best_after
    return contexts


def _choose_best_after(state: Any, best_before: str | None, attempt: AttemptRecord) -> str:
    if best_before is None:
        return attempt.attempt_id
    current_best = state.attempts[best_before]
    if attempt.pass_count > current_best.pass_count:
        return attempt.attempt_id
    return best_before


def _label_query_skill_action(
    episode_id: str,
    action_record: dict[str, Any],
    *,
    has_skill_return: bool,
) -> dict[str, Any]:
    if has_skill_return:
        label = LABEL_TRAINABLE
        rationale = (
            "canonical query_skill was followed by a skill_returned event; "
            "it remains loss-0 context until Skill utility is validated"
        )
    else:
        label = LABEL_AMBIGUOUS
        rationale = "canonical query_skill has no matching skill_returned event"
    record = _base_label(episode_id, action_record, label, rationale)
    record["behavior_tags"] = ["skill_grounding"] if has_skill_return else []
    return record


def _label_image_action(
    *,
    episode_id: str,
    action_record: dict[str, Any],
    context: AttemptContext,
    task_constraint_count: int,
) -> dict[str, Any]:
    attempt = context.attempt
    action = action_record["action"]
    action_name = action["action"]
    source_attempt_id = action["arguments"].get("source_attempt_id")
    source = context.previous_for_transition
    source_pass = source.pass_count if source is not None else 0
    fixed = context.transition["fixed"]
    regressed = context.transition["regressed"]
    behavior_tags: list[str] = []
    if fixed:
        behavior_tags.append("target_constraint_fixed")
    if regressed:
        behavior_tags.append("constraint_regression")
    if action_name == "generate_image" and context.attempt_index > 0:
        behavior_tags.append("regeneration_used")
    if action_name == "edit_image":
        behavior_tags.append("local_edit_used")
    if (
        source_attempt_id
        and context.latest_before
        and source_attempt_id != context.latest_before
    ):
        behavior_tags.append("historical_branch")

    previous_best_pass = context.best_before_pass_count
    improved_over_source = attempt.pass_count > source_pass
    improved_over_best = attempt.pass_count > previous_best_pass
    all_passed = attempt.pass_count == task_constraint_count
    if all_passed:
        behavior_tags.append("all_constraints_passed")

    if context.attempt_index == 0 and action_name == "generate_image":
        label = LABEL_TRAINABLE
        rationale = "first image action creates the required fresh-start attempt"
    elif all_passed or improved_over_best:
        if "historical_branch" in behavior_tags:
            label = LABEL_RECOVERY
            rationale = "historical branch produced a new best attempt"
            behavior_tags.append("best_so_far_recovery")
        else:
            label = LABEL_TRAINABLE
            rationale = "image action improved the best-so-far score"
    elif action_name == "edit_image" and improved_over_source and not regressed:
        label = LABEL_TRAINABLE
        rationale = "edit improved its source without regressing passed constraints"
    elif regressed and attempt.pass_count < source_pass:
        label = LABEL_HARMFUL
        rationale = "image action regressed previously passing constraints"
    elif fixed and regressed:
        label = LABEL_HARMFUL
        rationale = "image action fixed some constraints but introduced regressions"
    elif action_name == "edit_image" and not improved_over_source:
        label = LABEL_INEFFECTIVE
        rationale = "edit did not improve over its source attempt"
    else:
        label = LABEL_INEFFECTIVE
        rationale = "image action did not improve the best-so-far attempt"

    record = _base_label(episode_id, action_record, label, rationale)
    record.update(
        {
            "attempt_id": attempt.attempt_id,
            "attempt_index": context.attempt_index,
            "source_attempt_id": source_attempt_id,
            "latest_before": context.latest_before,
            "best_before": context.best_before,
            "pass_count": attempt.pass_count,
            "source_pass_count": source_pass if source is not None else None,
            "best_before_pass_count": previous_best_pass,
            "fixed_constraint_ids": fixed,
            "regressed_constraint_ids": regressed,
            "behavior_tags": sorted(set(behavior_tags)),
        }
    )
    return record


def _label_submit_action(
    *,
    state: Any,
    action_record: dict[str, Any],
) -> dict[str, Any]:
    action = action_record["action"]
    selected = action["arguments"]["selected_attempt_id"]
    reason_code = action["arguments"]["reason_code"]
    latest = state.latest_attempt_id
    best = state.best_attempt_id
    behavior_tags: list[str] = []
    if reason_code == "all_constraints_passed":
        behavior_tags.append("all_constraints_passed")
    if reason_code == "best_available_under_budget":
        behavior_tags.append("budget_exhausted")
    if selected != latest:
        behavior_tags.append("historical_best_submission")
    if selected == best:
        if selected != latest:
            label = LABEL_RECOVERY
            rationale = "submitted the historical best instead of the latest attempt"
            behavior_tags.append("best_so_far_recovery")
        else:
            label = LABEL_TRAINABLE
            rationale = "submitted the current best attempt with a valid reason code"
    else:
        label = LABEL_HARMFUL
        rationale = "submitted an attempt that was not best-so-far"
    record = _base_label(state.episode_id, action_record, label, rationale)
    record.update(
        {
            "selected_attempt_id": selected,
            "best_attempt_id": best,
            "latest_attempt_id": latest,
            "reason_code": reason_code,
            "behavior_tags": sorted(set(behavior_tags)),
        }
    )
    return record


def _base_label(
    episode_id: str,
    action_record: dict[str, Any],
    label: str,
    rationale: str,
) -> dict[str, Any]:
    action = action_record["action"]
    return {
        "schema_version": SCHEMA_VERSION,
        "episode_id": episode_id,
        "request_id": action_record["request_id"],
        "turn_id": action_record["turn_id"],
        "action_event_id": action_record["action_event_id"],
        "action": action["action"],
        "label": label,
        "sft_candidate": (
            label in TRAINING_LABELS
            and action["action"] in TARGETABLE_ACTIONS
            and action.get("schema_version") == TARGET_PROTOCOL_VERSION
        ),
        "label_rationale": rationale,
        "canonical_action": action,
        "behavior_tags": [],
    }


def _invalid_raw_label(
    episode_id: str,
    raw: dict[str, Any],
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "episode_id": episode_id,
        "request_id": raw["request_id"],
        "turn_id": _turn_id_from_request_id(raw["request_id"]),
        "action_event_id": None,
        "action": "invalid_raw_output",
        "label": LABEL_INVALID,
        "sft_candidate": False,
        "label_rationale": (
            error["payload"]["error_code"] if error else "raw output had no canonical action"
        ),
        "raw_output_ref": f"raw_teacher_outputs/{raw['request_id']}.json",
        "format_error_event_id": error["event_id"] if error else None,
        "behavior_tags": ["invalid_infrastructure_run"]
        if error and not error["payload"].get("retryable", True)
        else [],
    }


def _episode_behavior_labels(
    state: Any,
    attempt_contexts: dict[str, AttemptContext],
    action_labels: list[dict[str, Any]],
) -> list[str]:
    behaviors: set[str] = set()
    constraint_count = len(state.task_spec["constraints"])
    first_attempt = state.attempts[state.attempt_order[0]] if state.attempt_order else None
    if first_attempt and first_attempt.pass_count == constraint_count:
        behaviors.add("direct_success")
    if any(
        ctx.attempt.action["action"] == "generate_image" and ctx.attempt_index > 0
        for ctx in attempt_contexts.values()
    ):
        behaviors.add("regeneration_used")
    if any(ctx.attempt.action["action"] == "edit_image" for ctx in attempt_contexts.values()):
        behaviors.add("local_edit_used")
    if any(ctx.transition["fixed"] for ctx in attempt_contexts.values()):
        behaviors.add("target_constraint_fixed")
    if any(ctx.transition["regressed"] for ctx in attempt_contexts.values()):
        behaviors.add("constraint_regression")
    if state.best_attempt_id and state.attempts[state.best_attempt_id].pass_count < constraint_count:
        behaviors.add("persistent_failure")
    ineffective_count = sum(
        1
        for record in action_labels
        if record["label"] in {LABEL_INEFFECTIVE, LABEL_HARMFUL}
        and record["action"] in {"generate_image", "edit_image"}
    )
    if ineffective_count >= 2:
        behaviors.add("repeated_ineffective_strategy")
    if any("historical_branch" in record.get("behavior_tags", []) for record in action_labels):
        behaviors.add("historical_branch")
    if any("best_so_far_recovery" in record.get("behavior_tags", []) for record in action_labels):
        behaviors.add("best_so_far_recovery")
    if state.submitted_attempt_id and state.submitted_attempt_id != state.latest_attempt_id:
        behaviors.add("historical_best_submission")
    if any(
        state.attempts[attempt_id].pass_count == constraint_count
        for attempt_id in state.attempt_order
    ):
        behaviors.add("all_constraints_passed")
    if state.remaining_budget == 0 and state.submitted_reason_code == "best_available_under_budget":
        behaviors.add("budget_exhausted")
    return sorted(behaviors)


def _attempt_summary(context: AttemptContext) -> dict[str, Any]:
    attempt = context.attempt
    return {
        "attempt_id": attempt.attempt_id,
        "operation": attempt.operation,
        "action": attempt.action["action"],
        "parent_attempt_id": attempt.parent_attempt_id,
        "image_artifact_id": attempt.image_artifact_id,
        "pass_count": attempt.pass_count,
        "passed_constraint_ids": attempt.passed_constraint_ids,
        "failed_constraint_ids": attempt.failed_constraint_ids,
        "fixed_constraint_ids": context.transition["fixed"],
        "regressed_constraint_ids": context.transition["regressed"],
        "latest_before": context.latest_before,
        "best_before": context.best_before,
        "best_after": context.best_after,
    }


def _build_trajectory_index(
    episodes: list[dict[str, Any]],
    invalid_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "phase": "3",
        "episode_count": len(episodes),
        "valid_episode_count": len(episodes),
        "invalid_run_count": len(invalid_runs),
        "fresh_start_policy": {
            "initial_attempt_history": "empty",
            "legacy_images_reused": False,
            "max_image_attempts": 5,
            "smoke_tests_counted_as_phase3": False,
        },
        "episodes": [
            {
                key: episode[key]
                for key in (
                    "episode_id",
                    "run_dir",
                    "constraint_count",
                    "attempt_count",
                    "submitted_attempt_id",
                    "submitted_reason_code",
                    "best_attempt_id",
                    "best_pass_count",
                    "remaining_budget",
                    "raw_output_count",
                    "validated_action_count",
                    "format_error_count",
                    "skill_return_count",
                    "behavior_labels",
                )
            }
            for episode in episodes
        ],
        "invalid_runs": invalid_runs,
    }


def _collect_invalid_runs(invalid_run_root: Path) -> list[dict[str, Any]]:
    if not invalid_run_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for path in sorted(invalid_run_root.iterdir()):
        if not path.is_dir():
            continue
        events_path = path / "events.jsonl"
        latest_event = None
        event_count = 0
        if events_path.exists():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    event_count += 1
                    latest_event = json.loads(line)
        runs.append(
            {
                "run_dir": str(path),
                "behavior_label": "invalid_infrastructure_run",
                "event_count": event_count,
                "latest_event_type": latest_event["event_type"] if latest_event else None,
                "phase3_episode_counted": False,
                "sft_candidate_actions": 0,
            }
        )
    return runs


def _write_episode_report(episode: dict[str, Any]) -> None:
    run_dir = Path(episode["run_dir"])
    (run_dir / "trajectory_analysis.md").write_text(
        _render_episode_report(episode),
        encoding="utf-8",
    )


def _render_episode_report(episode: dict[str, Any]) -> str:
    lines = [
        f"# Trajectory Analysis: {episode['episode_id']}",
        "",
        f"- Submitted: `{episode['submitted_attempt_id']}` (`{episode['submitted_reason_code']}`)",
        f"- Best: `{episode['best_attempt_id']}` with {episode['best_pass_count']}/{episode['constraint_count']} passing atoms",
        f"- Attempts: {episode['attempt_count']} of {episode['max_image_attempts']}",
        f"- Behavior labels: {', '.join(f'`{label}`' for label in episode['behavior_labels']) or '`none`'}",
        f"- Rejected raw turns: {episode['format_error_count']}",
        "",
        "## Attempts",
        "",
        "| Attempt | Action | Parent | Pass | Fixed | Regressed | Best After |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for attempt in episode["attempts"]:
        lines.append(
            "| {attempt_id} | {action} | {parent} | {pass_count} | {fixed} | {regressed} | {best_after} |".format(
                attempt_id=f"`{attempt['attempt_id']}`",
                action=f"`{attempt['action']}`",
                parent=f"`{attempt['parent_attempt_id']}`" if attempt["parent_attempt_id"] else "-",
                pass_count=attempt["pass_count"],
                fixed=_fmt_ids(attempt["fixed_constraint_ids"]),
                regressed=_fmt_ids(attempt["regressed_constraint_ids"]),
                best_after=f"`{attempt['best_after']}`",
            )
        )
    lines.extend(
        [
            "",
            "## Action Labels",
            "",
            "| Turn | Action | Label | Candidate | Rationale |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for record in episode["canonical_actions"]:
        lines.append(
            "| {turn} | {action} | `{label}` | {candidate} | {rationale} |".format(
                turn=f"`{record['turn_id']}`",
                action=f"`{record['action']}`",
                label=record["label"],
                candidate="yes" if record["sft_candidate"] else "no",
                rationale=record["label_rationale"].replace("|", "\\|"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _render_comparison_report(
    episodes: list[dict[str, Any]],
    invalid_runs: list[dict[str, Any]],
) -> str:
    lines = [
        f"# Phase 3 {len(episodes)}-Trajectory Comparison",
        "",
        (
            f"All {len(episodes)} rows below are fresh-start live trajectories. "
            "Smoke outputs and archived invalid infrastructure runs are not counted."
        ),
        "",
        "| Episode | Attempts | Best | Submitted | Reason | Best Pass | Raw Errors | Behaviors |",
        "| --- | ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for episode in episodes:
        lines.append(
            "| {ep} | {attempts} | {best} | {submitted} | {reason} | {best_pass}/{constraints} | {errors} | {behaviors} |".format(
                ep=f"`{episode['episode_id']}`",
                attempts=episode["attempt_count"],
                best=f"`{episode['best_attempt_id']}`",
                submitted=f"`{episode['submitted_attempt_id']}`",
                reason=f"`{episode['submitted_reason_code']}`",
                best_pass=episode["best_pass_count"],
                constraints=episode["constraint_count"],
                errors=episode["format_error_count"],
                behaviors=", ".join(f"`{label}`" for label in episode["behavior_labels"]),
            )
        )
    if invalid_runs:
        lines.extend(
            [
                "",
                "## Excluded Invalid Runs",
                "",
                "| Run | Latest Event | Counted |",
                "| --- | --- | --- |",
            ]
        )
        for run in invalid_runs:
            lines.append(
                f"| `{run['run_dir']}` | `{run['latest_event_type']}` | no |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_behavior_report(
    episodes: list[dict[str, Any]],
    invalid_runs: list[dict[str, Any]],
) -> str:
    counter: Counter[str] = Counter()
    by_label: dict[str, list[str]] = defaultdict(list)
    for episode in episodes:
        for label in episode["behavior_labels"]:
            counter[label] += 1
            by_label[label].append(episode["episode_id"])
    if invalid_runs:
        counter["invalid_infrastructure_run"] += len(invalid_runs)
        by_label["invalid_infrastructure_run"].extend(run["run_dir"] for run in invalid_runs)
    lines = [
        "# Phase 3 Behavior Coverage",
        "",
        "| Behavior | Count | Evidence |",
        "| --- | ---: | --- |",
    ]
    for label in ALL_BEHAVIOR_LABELS:
        evidence = ", ".join(f"`{item}`" for item in by_label.get(label, [])) or "-"
        lines.append(f"| `{label}` | {counter[label]} | {evidence} |")
    all_pass_count = counter["all_constraints_passed"]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The fresh rollouts exercise both productive and non-productive history use. "
                "Historical-best submission appears when the policy submits an earlier best "
                "attempt after later edits or regenerations regress. Constraint regression and "
                "repeated ineffective strategy supply negative history-only examples. "
                f"{all_pass_count} trajectories reached all atom constraints."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _render_legacy_vs_fresh_report(
    episodes: list[dict[str, Any]],
    invalid_runs: list[dict[str, Any]],
) -> str:
    total_attempts = sum(episode["attempt_count"] for episode in episodes)
    edit_count = sum(
        1
        for episode in episodes
        for attempt in episode["attempts"]
        if attempt["action"] == "edit_image"
    )
    generate_count = total_attempts - edit_count
    historical_submits = sum(
        1 for episode in episodes if "historical_best_submission" in episode["behavior_labels"]
    )
    lines = [
        "# Legacy vs Fresh Strategy Analysis",
        "",
        (
            f"The {len(episodes)} completed trajectories used the selected fresh prompts and "
            "did not import legacy images, legacy attempts, or legacy parentage. Legacy evidence "
            "remains limited to the earlier read-only diagnostic reports under `docs/phase3/` "
            "and `artifacts/phase3/`."
        ),
        "",
        f"- Fresh image attempts: {total_attempts} total; {generate_count} generation/regeneration actions and {edit_count} edit actions.",
        f"- Historical-best submissions: {historical_submits}/{len(episodes)} trajectories.",
        f"- Archived invalid infrastructure runs counted as Phase 3 episodes: 0 (archived count: {len(invalid_runs)}).",
        "",
        "The fresh rollouts differ from legacy-derived traces in the evidence available to the policy: every branch, regression, best-so-far update, and submission here is grounded in v0.2 canonical events and local Geneval2 atom normalization. This makes the traces suitable for Phase 4 supervision design without treating legacy behavior as a positive target.",
        "",
    ]
    return "\n".join(lines)


def _render_sft_report(
    episodes: list[dict[str, Any]],
    action_labels: list[dict[str, Any]],
) -> str:
    label_counts = Counter(record["label"] for record in action_labels)
    action_counts = Counter(record["action"] for record in action_labels)
    candidate_count = sum(1 for record in action_labels if record["sft_candidate"])
    masked_query_count = sum(
        1 for record in action_labels if record["action"] == "query_skill"
    )
    canonical_count = sum(1 for record in action_labels if record["action"] != "invalid_raw_output")
    lines = [
        "# Phase 3 SFT Candidate Action Report",
        "",
        f"- Episodes analyzed: {len(episodes)}",
        f"- Canonical actions labeled: {canonical_count}",
        f"- Raw rejected turns labeled excluded: {action_counts['invalid_raw_output']}",
        f"- SFT candidate actions: {candidate_count}",
        f"- Valid query_skill actions retained with loss 0: {masked_query_count}",
        "",
        "## Label Counts",
        "",
        "| Label | Count |",
        "| --- | ---: |",
    ]
    for label in [
        LABEL_TRAINABLE,
        LABEL_RECOVERY,
        LABEL_HARMFUL,
        LABEL_INEFFECTIVE,
        LABEL_AMBIGUOUS,
        LABEL_INVALID,
    ]:
        lines.append(f"| `{label}` | {label_counts[label]} |")
    lines.extend(
        [
            "",
            "## Action Counts",
            "",
            "| Action | Count |",
            "| --- | ---: |",
        ]
    )
    for action, count in sorted(action_counts.items()):
        lines.append(f"| `{action}` | {count} |")
    lines.extend(
        [
            "",
            "## SFT Policy",
            "",
            (
                "Use only native v0.5 `generate_image`, `edit_image`, and `submit_attempt` "
                "actions labeled `trainable_positive` or `recovery_positive` as candidate "
                "targets. Keep `query_skill` actions and linked tool responses at loss 0 until "
                "Skill utility validation is accepted. Harmful, ineffective, ambiguous, invalid, "
                "Geneval2, and raw teacher records remain context or audit evidence only."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
    )


def _fmt_ids(ids: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in ids) if ids else "-"


def _turn_id_from_request_id(request_id: str) -> str | None:
    if "_turn_" not in request_id:
        return None
    return "turn_" + request_id.rsplit("_turn_", 1)[1]


def _request_id_from_raw_ref(raw_ref: str) -> str:
    name = Path(raw_ref).name
    if name.endswith(".json"):
        return name[:-5]
    return name
