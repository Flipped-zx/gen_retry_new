from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from gen_retry.domain.score_policy import (
    planner_context_version_is_compatible,
    score_policy_from_task_payload,
)
from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.planner_context import (
    build_planner_context_from_events,
    load_skill_observations,
)


SCHEMA_VERSION = "0.5"
TRAINING_LABELS = {"trainable_positive", "recovery_positive"}
TARGETABLE_ACTIONS = {"generate_image", "edit_image", "submit_attempt"}
MASKED_CONTEXT_ROLES = {"system", "user"}

SYSTEM_PROMPT = (
    "You are the Gen-Retry v0.5 planner. Given the canonical "
    "PlannerContext, visible image references, active skill guidance, and "
    "environment-owned attempt history, emit exactly one strict JSON planner "
    "action matching action_protocol_v0.5. generate_image is a source-free root "
    "generation; edit_image modifies one declared historical source attempt. "
    "Passed-atom count is the primary objective; when it ties, use the "
    "environment-owned primary_score. Never output backend, mode, or score fields."
)


def default_supervision_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_id": "phase4_sft_supervision_freeze_v0.6",
        "principal_target": "canonical assistant action JSON",
        "accepted_action_labels": sorted(TRAINING_LABELS),
        "targetable_actions": sorted(TARGETABLE_ACTIONS),
        "context_only_labels": [
            "history_only_harmful",
            "history_only_ineffective",
            "excluded_ambiguous",
            "excluded_invalid",
        ],
        "query_skill_policy": {
            "decision": "context_only_until_utility_validated",
            "reason": (
                "PlannerContext v0.5 treats query_skill as a real Planner Action, "
                "but both the assistant query action and linked skill_returned response "
                "have loss mask 0 until Skill utility validation passes."
            ),
        },
        "message_format": {
            "system": "fixed planner contract",
            "user": "canonical PlannerContext and image references",
            "assistant": "canonical action JSON only when selected as a target",
        },
        "loss_mask_policy": {
            "system": 0,
            "user": 0,
            "assistant_target": 1,
            "tool_or_environment_observations": 0,
            "raw_teacher_outputs": 0,
        },
        "split_policy": {
            "method": "stable_sha256_prompt_group",
            "train_fraction": 0.8,
            "validation_fraction": 0.1,
            "test_fraction": 0.1,
            "invariant": "one original prompt group appears in exactly one split",
        },
        "execution_profile_policy": {
            "method": "homogeneous_export_only",
            "invariant": (
                "one export contains one execution profile; legacy white-canvas "
                "generation and native T2I generation are never silently mixed"
            ),
        },
        "planner_context_policy": {
            "method": "homogeneous_context_score_contract_only",
            "invariant": (
                "one export contains one PlannerContext version and score-policy "
                "tuple; every input is rebuilt from its exact temporal event prefix"
            ),
        },
        "context_budget": {
            "estimated_token_method": "ceil(characters/4)",
            "max_context_tokens": 24000,
            "max_target_tokens": 1400,
            "truncation_order": [
                "drop_oldest_nonvisible_history",
                "keep_task_spec",
                "keep_latest_attempt",
                "keep_best_attempt",
                "keep_visible_images",
            ],
        },
    }


def skill_supervision_policy() -> dict[str, Any]:
    """Return the frozen-candidate policy with utility-linked Skill targets.

    A Skill query is positive only when the immutable trajectory contains a
    matching ``skill_returned`` observation and the next relevant image action
    is itself a positive/recovery action on an overlapping constraint set.
    Queries without that evidence remain context-only.
    """

    policy = deepcopy(default_supervision_policy())
    policy["policy_id"] = "flow_dppo1000_v9_selective_skill_v1"
    policy["targetable_actions"] = sorted(TARGETABLE_ACTIONS | {"query_skill"})
    policy["query_skill_policy"] = {
        "decision": "utility_linked_positive",
        "reason": (
            "include query_skill only when skill_returned is present and the "
            "next positive/recovery image action targets an overlapping constraint"
        ),
        "utility_evidence": "immutable skill_returned -> next image action outcome",
    }
    return policy


def annotate_skill_utility_labels(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate query labels with deterministic next-action utility evidence."""

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        if label.get("action") != "invalid_raw_output":
            grouped[str(label["episode_id"])].append(label)

    for episode_labels in grouped.values():
        episode_labels.sort(key=_turn_sort_key)
        for index, label in enumerate(episode_labels):
            if label.get("action") != "query_skill":
                continue
            label["skill_utility_validated"] = False
            label.pop("skill_utility_linked_action_event_id", None)
            label.pop("skill_utility_overlap_constraint_ids", None)
            if "skill_grounding" not in (label.get("behavior_tags") or []):
                continue
            query_action = label.get("canonical_action") or {}
            query_targets = set(
                (query_action.get("arguments") or {}).get("target_constraint_ids")
                or []
            )
            for candidate in episode_labels[index + 1 :]:
                if candidate.get("action") not in {"generate_image", "edit_image"}:
                    continue
                if candidate.get("label") not in TRAINING_LABELS:
                    break
                candidate_action = candidate.get("canonical_action") or {}
                candidate_args = candidate_action.get("arguments") or {}
                candidate_constraints = set(
                    candidate_args.get("target_constraint_ids") or []
                ) | set(candidate_args.get("preserve_constraint_ids") or [])
                overlap = sorted(query_targets & candidate_constraints)
                if overlap:
                    label["skill_utility_validated"] = True
                    label["skill_utility_linked_action_event_id"] = candidate.get(
                        "action_event_id"
                    )
                    label["skill_utility_overlap_constraint_ids"] = overlap
                break
    return labels


def _turn_sort_key(label: dict[str, Any]) -> tuple[int, str]:
    turn = str(label.get("turn_id", ""))
    try:
        number = int(turn.rsplit("_", 1)[-1])
    except ValueError:
        number = 10**9
    return number, str(label.get("action_event_id", ""))


def run_phase4_sft_dry_run(
    *,
    run_root: Path = Path("runs/phase3"),
    labels_path: Path = Path("artifacts/phase3/action_supervision_labels.jsonl"),
    output_root: Path = Path("artifacts/phase4"),
    report_path: Path = Path("docs/phase4/sft_export_dry_run_report.md"),
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or default_supervision_policy()
    labels = _load_jsonl(labels_path)
    if policy.get("query_skill_policy", {}).get("decision") == "utility_linked_positive":
        annotate_skill_utility_labels(labels)
    run_index = _load_run_index(run_root)
    split_manifest = _assign_splits(run_index)

    decision_records: list[dict[str, Any]] = []
    target_records: list[dict[str, Any]] = []
    # A trajectory contributes multiple action labels. Keep immutable per-run
    # inputs in memory so export does not reread the same planner log for every
    # target record.
    request_index_cache: dict[Path, dict[str, dict[str, Any]]] = {}
    task_spec_cache: dict[Path, dict[str, Any]] = {}
    execution_profile_cache: dict[Path, dict[str, Any]] = {}
    events_cache: dict[Path, list[dict[str, Any]]] = {}
    skill_observations_cache: dict[Path, dict[str, Any]] = {}
    for label in labels:
        decision = decide_supervision(label, policy)
        decision["split"] = split_manifest["episode_splits"].get(label["episode_id"])
        decision_records.append(decision)
        if not decision["include_as_target"]:
            continue
        sample = build_supervised_sample(
            label=label,
            run_dir=run_index[label["episode_id"]]["run_dir"],
            split=decision["split"],
            policy=policy,
            request_index_cache=request_index_cache,
            task_spec_cache=task_spec_cache,
            execution_profile_cache=execution_profile_cache,
            events_cache=events_cache,
            skill_observations_cache=skill_observations_cache,
        )
        target_records.append(sample)

    audit = _build_audit(
        labels=labels,
        decisions=decision_records,
        targets=target_records,
        split_manifest=split_manifest,
        policy=policy,
    )
    output_root.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    (output_root / "sft_supervision_policy.json").write_text(
        canonical_json(policy) + "\n",
        encoding="utf-8",
    )
    _write_jsonl(output_root / "sft_dry_run_decisions.jsonl", decision_records)
    _write_jsonl(output_root / "sft_dry_run_records.jsonl", target_records)
    (output_root / "sft_split_manifest.json").write_text(
        canonical_json(split_manifest) + "\n",
        encoding="utf-8",
    )
    (output_root / "sft_dry_run_audit.json").write_text(
        canonical_json(audit) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_render_dry_run_report(audit, policy), encoding="utf-8")
    return audit


def decide_supervision(label: dict[str, Any], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or default_supervision_policy()
    action = label["action"]
    label_name = label["label"]
    include = False
    reason = "not_selected"
    if action == "invalid_raw_output":
        reason = "raw_teacher_output_excluded"
    elif action == "query_skill":
        if (
            "query_skill" in set(policy.get("targetable_actions") or [])
            and label_name in TRAINING_LABELS
            and label.get("skill_utility_validated") is True
        ):
            include = True
            reason = "query_skill_utility_validated"
        else:
            reason = "query_skill_context_only_until_utility_validated"
    elif label.get("canonical_action", {}).get("schema_version") != SCHEMA_VERSION:
        reason = "non_v0_5_action_context_only"
    elif label_name not in TRAINING_LABELS:
        reason = f"label_{label_name}_context_only"
    elif action not in TARGETABLE_ACTIONS:
        reason = "action_not_targetable"
    else:
        include = True
        reason = "positive_or_recovery_canonical_action"
    return {
        "schema_version": SCHEMA_VERSION,
        "episode_id": label["episode_id"],
        "request_id": label["request_id"],
        "turn_id": label["turn_id"],
        "action_event_id": label.get("action_event_id"),
        "action": action,
        "phase3_label": label_name,
        "include_as_target": include,
        "loss_weight": 1 if include else 0,
        "decision_reason": reason,
        "source_label_sha256": _sha256_text(canonical_json(label)),
        "policy_id": policy["policy_id"],
    }


def build_supervised_sample(
    *,
    label: dict[str, Any],
    run_dir: Path,
    split: str,
    policy: dict[str, Any] | None = None,
    request_index_cache: dict[Path, dict[str, dict[str, Any]]] | None = None,
    task_spec_cache: dict[Path, dict[str, Any]] | None = None,
    execution_profile_cache: dict[Path, dict[str, Any]] | None = None,
    events_cache: dict[Path, list[dict[str, Any]]] | None = None,
    skill_observations_cache: dict[Path, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    policy = policy or default_supervision_policy()
    if request_index_cache is not None and run_dir in request_index_cache:
        request_index = request_index_cache[run_dir]
    else:
        request_index = _index_identical_records(
            _load_jsonl(run_dir / "planner_requests.jsonl"),
            key="request_id",
            source=run_dir / "planner_requests.jsonl",
        )
        if request_index_cache is not None:
            request_index_cache[run_dir] = request_index
    request = request_index[label["request_id"]]
    context_ref = request.get("planner_context_ref") or request.get("planner_view_ref")
    planner_context = json.loads((run_dir / context_ref).read_text(encoding="utf-8"))
    if task_spec_cache is not None and run_dir in task_spec_cache:
        task_spec = task_spec_cache[run_dir]
    else:
        task_spec = json.loads((run_dir / "task_spec.json").read_text(encoding="utf-8"))
        if task_spec_cache is not None:
            task_spec_cache[run_dir] = task_spec
    if execution_profile_cache is not None and run_dir in execution_profile_cache:
        execution_profile = execution_profile_cache[run_dir]
    else:
        execution_profile = _execution_profile_for_run(run_dir)
        if execution_profile_cache is not None:
            execution_profile_cache[run_dir] = execution_profile
    context_contract = _validate_planner_context_prefix(
        run_dir=run_dir,
        context_ref=context_ref,
        planner_context=planner_context,
        target_action_event_id=label["action_event_id"],
        events_cache=events_cache,
        skill_observations_cache=skill_observations_cache,
    )
    messages = render_messages(
        task_spec=task_spec,
        planner_context=planner_context,
        visible_images=_resolve_visible_images(request, planner_context),
        target_action=label["canonical_action"],
        policy=policy,
    )
    context_chars = sum(len(message["content"]) for message in messages[:-1])
    target_chars = len(messages[-1]["content"])
    sample_id = "{episode_id}_{turn_id}_{action_event_id}".format(
        episode_id=label["episode_id"],
        turn_id=label["turn_id"],
        action_event_id=label["action_event_id"],
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "sample_id": sample_id,
        "episode_id": label["episode_id"],
        "request_id": label["request_id"],
        "turn_id": label["turn_id"],
        "split": split,
        "phase3_label": label["label"],
        "action": label["action"],
        "messages": messages,
        "loss_mask": [
            {
                "message_index": index,
                "role": message["role"],
                "loss_weight": message["loss_weight"],
                "token_source": message["token_source"],
            }
            for index, message in enumerate(messages)
        ],
        "target_text_sha256": _sha256_text(messages[-1]["content"]),
        "context_estimated_tokens": _estimate_tokens(context_chars),
        "target_estimated_tokens": _estimate_tokens(target_chars),
        "truncated": False,
        "policy_id": policy["policy_id"],
        "execution_profile": execution_profile,
        **context_contract,
    }


def render_messages(
    *,
    task_spec: dict[str, Any],
    planner_context: dict[str, Any],
    visible_images: list[dict[str, Any]],
    target_action: dict[str, Any] | None,
    policy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    policy = policy or default_supervision_policy()
    targetable_actions = set(policy.get("targetable_actions") or TARGETABLE_ACTIONS)
    if target_action is not None and target_action.get("action") not in targetable_actions:
        raise ValueError(
            f"action is context-only under v0.5 supervision: {target_action.get('action')}"
        )
    if target_action is not None:
        validate_instance(target_action, "action_protocol_v0_5.schema.json")
    user_payload = {
        "schema_version": SCHEMA_VERSION,
        "planner_context": planner_context,
        "visible_images": visible_images,
        "response_contract": {
            "schema": "action_protocol_v0_5",
            "exactly_one_action": True,
            "allowed_actions": [
                "query_skill",
                "generate_image",
                "edit_image",
                "submit_attempt",
            ],
        },
    }
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
            "loss_weight": 0,
            "token_source": "phase4_system_prompt",
        },
        {
            "role": "user",
            "content": canonical_json(user_payload),
            "loss_weight": 0,
            "token_source": "task_spec_and_planner_context",
            "image_refs": visible_images,
        },
    ]
    if target_action is not None:
        messages.append(
            {
                "role": "assistant",
                "content": canonical_json(target_action),
                "loss_weight": 1,
                "token_source": "canonical_action",
            }
        )
    return messages


def _load_run_index(run_root: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for run_dir in sorted(run_root.glob("phase3_ep_*")):
        task_spec_path = run_dir / "task_spec.json"
        if not task_spec_path.exists():
            continue
        task_spec = json.loads(task_spec_path.read_text(encoding="utf-8"))
        index[task_spec["episode_id"]] = {
            "run_dir": run_dir,
            "original_prompt": task_spec["original_prompt"],
            "prompt_group_sha256": _sha256_text(task_spec["original_prompt"]),
            "execution_profile": _execution_profile_for_run(run_dir),
        }
    return index


def _assign_splits(run_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    grouped_episodes: dict[str, list[str]] = defaultdict(list)
    for episode_id, info in run_index.items():
        grouped_episodes[info["prompt_group_sha256"]].append(episode_id)
    groups = [
        (prompt_hash, sorted(episode_ids))
        for prompt_hash, episode_ids in sorted(grouped_episodes.items())
    ]
    total = len(groups)
    train_cut = math.floor(total * 0.8)
    validation_cut = train_cut + max(1, math.floor(total * 0.1)) if total else 0
    if total >= 3:
        train_cut = max(1, min(train_cut, total - 2))
        validation_cut = min(max(train_cut + 1, validation_cut), total - 1)
    episode_splits: dict[str, str] = {}
    split_group_counts: Counter[str] = Counter()
    split_episode_counts: Counter[str] = Counter()
    prompt_groups: dict[str, dict[str, Any]] = {}
    for index, (prompt_hash, episode_ids) in enumerate(groups):
        if index < train_cut:
            split = "train"
        elif index < validation_cut:
            split = "validation"
        else:
            split = "test"
        for episode_id in episode_ids:
            episode_splits[episode_id] = split
            split_episode_counts[split] += 1
        split_group_counts[split] += 1
        prompt_groups[prompt_hash] = {
            "episode_ids": episode_ids,
            "split": split,
        }
    cross_split_violations = [
        prompt_hash
        for prompt_hash, episode_ids in prompt_groups.items()
        if len({episode_splits[item] for item in episode_ids["episode_ids"]}) > 1
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "format_version": "sft_split_manifest_v2",
        "method": "stable_sha256_prompt_group",
        "episode_splits": dict(sorted(episode_splits.items())),
        "split_counts": dict(sorted(split_group_counts.items())),
        "split_episode_counts": dict(sorted(split_episode_counts.items())),
        "prompt_groups": dict(sorted(prompt_groups.items())),
        "prompt_group_cross_split_violations": cross_split_violations,
    }


def _resolve_visible_images(
    request: dict[str, Any],
    planner_context: dict[str, Any],
) -> list[dict[str, Any]]:
    request_images = request.get("visible_images") or []
    resolved: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for image in request_images:
        artifact_id = image["artifact_id"]
        role = image["role"]
        key = (artifact_id, role)
        if key in seen:
            continue
        seen.add(key)
        resolved.append(
            {
                "artifact_id": artifact_id,
                "attempt_id": image["attempt_id"],
                "role": role,
                "uri": f"images/{artifact_id.replace('img_', 'img_')}.png",
            }
        )
    return resolved


def _build_audit(
    *,
    labels: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    split_manifest: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    label_counts = Counter(label["label"] for label in labels)
    action_counts = Counter(label["action"] for label in labels)
    decision_counts = Counter(decision["decision_reason"] for decision in decisions)
    target_actions = Counter(target["action"] for target in targets)
    execution_profiles = Counter(
        "{profile_id}@{profile_version}".format(**target["execution_profile"])
        for target in targets
    )
    mixed_execution_profile_violations = (
        sorted(execution_profiles) if len(execution_profiles) > 1 else []
    )
    context_score_contracts = Counter(
        canonical_json(
            {
                "planner_context_schema_version": target[
                    "planner_context_schema_version"
                ],
                "score_policy": target["score_policy"],
            }
        )
        for target in targets
    )
    mixed_context_score_contract_violations = (
        sorted(context_score_contracts) if len(context_score_contracts) > 1 else []
    )
    loss_violations = [
        target["sample_id"]
        for target in targets
        if any(
            mask["loss_weight"] != (1 if mask["role"] == "assistant" else 0)
            for mask in target["loss_mask"]
        )
    ]
    targetable_actions = set(policy.get("targetable_actions") or TARGETABLE_ACTIONS)
    noncanonical_targets = [
        target["sample_id"]
        for target in targets
        if target["action"] not in targetable_actions
        or target["phase3_label"] not in TRAINING_LABELS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_id": policy["policy_id"],
        "input_label_count": len(labels),
        "canonical_label_count": sum(1 for label in labels if label["action"] != "invalid_raw_output"),
        "raw_rejected_count": action_counts["invalid_raw_output"],
        "target_record_count": len(targets),
        "context_only_record_count": len(decisions) - len(targets),
        "label_counts": dict(sorted(label_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "target_action_counts": dict(sorted(target_actions.items())),
        "execution_profile_counts": dict(sorted(execution_profiles.items())),
        "mixed_execution_profile_violations": mixed_execution_profile_violations,
        "context_score_contract_counts": dict(
            sorted(context_score_contracts.items())
        ),
        "mixed_context_score_contract_violations": (
            mixed_context_score_contract_violations
        ),
        "split_counts": split_manifest["split_counts"],
        "prompt_group_cross_split_violations": split_manifest[
            "prompt_group_cross_split_violations"
        ],
        "loss_mask_violations": loss_violations,
        "noncanonical_target_violations": noncanonical_targets,
        "token_estimate_percentiles": _token_percentiles(targets),
        "gate2_validation_experiment_passed": (
            not loss_violations
            and not noncanonical_targets
            and not split_manifest["prompt_group_cross_split_violations"]
            and not mixed_execution_profile_violations
            and not mixed_context_score_contract_violations
        ),
    }


def _execution_profile_for_run(run_dir: Path) -> dict[str, str]:
    plan_path = run_dir / "rollout_plan.json"
    if not plan_path.exists():
        return {
            "profile_id": "qwen_image_edit_only",
            "profile_version": "1",
        }
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    profile = plan.get("execution_profile") or {}
    return {
        "profile_id": str(profile.get("profile_id", "qwen_image_edit_only")),
        "profile_version": str(profile.get("profile_version", "1")),
    }


def _validate_planner_context_prefix(
    *,
    run_dir: Path,
    context_ref: str,
    planner_context: dict[str, Any],
    target_action_event_id: str,
    events_cache: dict[Path, list[dict[str, Any]]] | None = None,
    skill_observations_cache: dict[Path, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if events_cache is not None and run_dir in events_cache:
        events = events_cache[run_dir]
    else:
        events = load_events_jsonl(run_dir / "events.jsonl")
        if events_cache is not None:
            events_cache[run_dir] = events
    matches = [
        (index, event)
        for index, event in enumerate(events)
        if event["event_type"] == "planner_context_built"
        and (
            event["payload"].get("planner_context_ref")
            or event["payload"].get("planner_view_ref")
        )
        == context_ref
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one planner_context_built event for {context_ref}, "
            f"found {len(matches)}"
        )
    context_index, context_event = matches[0]
    target_indices = [
        index
        for index, event in enumerate(events)
        if event["event_id"] == target_action_event_id
    ]
    if len(target_indices) != 1 or target_indices[0] <= context_index:
        raise ValueError(
            "SFT target action must occur after its planner context event"
        )
    score_policy = score_policy_from_task_payload(events[0]["payload"])
    context_version = str(
        context_event["payload"].get(
            "planner_context_schema_version",
            planner_context.get("planner_context_schema_version", "0.5"),
        )
    )
    if not planner_context_version_is_compatible(score_policy, context_version):
        raise ValueError(
            "planner context and score policy are incompatible: "
            f"context={context_version}, policy={score_policy['policy_id']}"
        )
    if skill_observations_cache is not None and run_dir in skill_observations_cache:
        skill_observations = skill_observations_cache[run_dir]
    else:
        skill_observations = load_skill_observations(run_dir)
        if skill_observations_cache is not None:
            skill_observations_cache[run_dir] = skill_observations
    rebuilt = build_planner_context_from_events(
        events[: context_index + 1],
        task_spec_ref="task_spec.json",
        schema_version=context_version,
        skill_observations=skill_observations,
    )
    if canonical_json(rebuilt) != canonical_json(planner_context):
        raise ValueError(
            f"persisted PlannerContext is not reproducible from its event prefix: "
            f"{context_ref}"
        )
    return {
        "planner_context_schema_version": context_version,
        "score_policy": score_policy,
    }


def _token_percentiles(targets: list[dict[str, Any]]) -> dict[str, Any]:
    if not targets:
        return {}
    context = sorted(target["context_estimated_tokens"] for target in targets)
    target = sorted(target["target_estimated_tokens"] for target in targets)
    return {
        "context": _percentiles(context),
        "target": _percentiles(target),
    }


def _percentiles(values: list[int]) -> dict[str, int]:
    return {
        "p50": _percentile(values, 0.50),
        "p90": _percentile(values, 0.90),
        "p95": _percentile(values, 0.95),
        "max": values[-1],
    }


def _percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    index = min(len(values) - 1, math.ceil(q * len(values)) - 1)
    return values[index]


def _render_dry_run_report(audit: dict[str, Any], policy: dict[str, Any]) -> str:
    lines = [
        "# Phase 4 SFT Export Dry Run",
        "",
        f"- Policy: `{policy['policy_id']}`",
        f"- Input labeled records: {audit['input_label_count']}",
        f"- Canonical labeled actions: {audit['canonical_label_count']}",
        f"- Raw rejected turns kept context-only: {audit['raw_rejected_count']}",
        f"- Target records emitted: {audit['target_record_count']}",
        f"- Context-only records: {audit['context_only_record_count']}",
        f"- Gate 2 validation experiment: {'PASS' if audit['gate2_validation_experiment_passed'] else 'FAIL'}",
        "",
        "## Target Action Counts",
        "",
        "| Action | Count |",
        "| --- | ---: |",
    ]
    for action, count in audit["target_action_counts"].items():
        lines.append(f"| `{action}` | {count} |")
    lines.extend(
        [
            "",
            "## Exclusion Reasons",
            "",
            "| Reason | Count |",
            "| --- | ---: |",
        ]
    )
    for reason, count in audit["decision_counts"].items():
        lines.append(f"| `{reason}` | {count} |")
    lines.extend(
        [
            "",
            "## Split Counts",
            "",
            "| Split | Prompt Groups |",
            "| --- | ---: |",
        ]
    )
    for split, count in audit["split_counts"].items():
        lines.append(f"| `{split}` | {count} |")
    token = audit["token_estimate_percentiles"]
    if token:
        lines.extend(
            [
                "",
                "## Token Estimate Percentiles",
                "",
                "| Segment | p50 | p90 | p95 | max |",
                "| --- | ---: | ---: | ---: | ---: |",
                "| context | {p50} | {p90} | {p95} | {max} |".format(**token["context"]),
                "| target | {p50} | {p90} | {p95} | {max} |".format(**token["target"]),
            ]
        )
    lines.extend(
        [
            "",
            "## Mask Invariants",
            "",
            "- System and user messages have loss weight 0.",
            "- Assistant messages have loss weight 1 only for selected canonical action targets.",
            "- `query_skill` assistant actions and linked tool responses have loss weight 0 until Skill utility is validated.",
            "- Raw teacher output, format errors, Geneval2 observations, harmful actions, and ineffective actions are context-only.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records


def _index_identical_records(
    records: list[dict[str, Any]],
    *,
    key: str,
    source: Path,
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record[key]
        existing = index.get(record_id)
        if existing is not None and existing != record:
            raise ValueError(
                f"conflicting duplicate {key}={record_id} in {source}"
            )
        index[record_id] = record
    return index


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
    )


def _estimate_tokens(char_count: int) -> int:
    return math.ceil(char_count / 4)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
