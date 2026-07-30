from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from gen_retry.runtime.json_canonical import canonical_json


def compare_paired_rollout_summaries(
    *,
    baseline_summary_path: Path,
    candidate_summary_path: Path,
    artifact_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    baseline = _load_json(baseline_summary_path)
    candidate = _load_json(candidate_summary_path)
    baseline_by_id = {
        episode["episode_id"]: episode for episode in baseline["episodes"]
    }
    candidate_by_id = {
        episode["episode_id"]: episode for episode in candidate["episodes"]
    }
    missing = sorted(set(candidate_by_id) - set(baseline_by_id))
    if missing:
        raise ValueError(
            "candidate episodes missing from baseline: " + ", ".join(missing)
        )
    pairs = [
        _compare_episode(
            baseline=baseline_by_id[episode_id],
            candidate=candidate_by_id[episode_id],
        )
        for episode_id in sorted(candidate_by_id)
    ]
    outcome_counts = Counter(pair["paired_outcome"] for pair in pairs)
    baseline_constraint_slots = sum(
        pair["constraint_count"] for pair in pairs
    )
    baseline_submitted_pass = sum(
        pair["baseline"]["submitted_pass_count"] for pair in pairs
    )
    candidate_submitted_pass = sum(
        pair["candidate"]["submitted_pass_count"] for pair in pairs
    )
    baseline_initial_pass = sum(
        pair["baseline"]["initial_pass_count"] for pair in pairs
    )
    candidate_initial_pass = sum(
        pair["candidate"]["initial_pass_count"] for pair in pairs
    )
    aggregate = {
        "constraint_slots": baseline_constraint_slots,
        "baseline_initial_pass_count": baseline_initial_pass,
        "candidate_initial_pass_count": candidate_initial_pass,
        "initial_pass_count_delta": candidate_initial_pass - baseline_initial_pass,
        "baseline_submitted_pass_count": baseline_submitted_pass,
        "candidate_submitted_pass_count": candidate_submitted_pass,
        "submitted_pass_count_delta": (
            candidate_submitted_pass - baseline_submitted_pass
        ),
        "baseline_submitted_gm": _mean(
            pair["baseline"]["submitted_gm"] for pair in pairs
        ),
        "candidate_submitted_gm": _mean(
            pair["candidate"]["submitted_gm"] for pair in pairs
        ),
        "baseline_submitted_am": _mean(
            pair["baseline"]["submitted_am"] for pair in pairs
        ),
        "candidate_submitted_am": _mean(
            pair["candidate"]["submitted_am"] for pair in pairs
        ),
        "baseline_initial_gm": _mean(
            pair["baseline"]["initial_gm"] for pair in pairs
        ),
        "candidate_initial_gm": _mean(
            pair["candidate"]["initial_gm"] for pair in pairs
        ),
        "baseline_attempt_count": sum(
            pair["baseline"]["attempt_count"] for pair in pairs
        ),
        "candidate_attempt_count": sum(
            pair["candidate"]["attempt_count"] for pair in pairs
        ),
        "paired_outcome_counts": dict(sorted(outcome_counts.items())),
        "candidate_all_pass_count": sum(
            pair["candidate"]["submitted_pass_count"]
            == pair["constraint_count"]
            for pair in pairs
        ),
        "baseline_all_pass_count": sum(
            pair["baseline"]["submitted_pass_count"]
            == pair["constraint_count"]
            for pair in pairs
        ),
        "gm_tiebreak_changed_best_count": sum(
            pair["candidate_policy_behavior"]["gm_tiebreak_changed_best"]
            for pair in pairs
        ),
        "gm_tiebreak_best_update_count": sum(
            pair["candidate_policy_behavior"][
                "gm_tiebreak_best_update_count"
            ]
            for pair in pairs
        ),
        "higher_gm_lower_pass_rejection_count": sum(
            pair["candidate_policy_behavior"][
                "higher_gm_lower_pass_rejection_count"
            ]
            for pair in pairs
        ),
        "rollback_to_historical_source_count": sum(
            pair["candidate_policy_behavior"][
                "rollback_to_historical_source_count"
            ]
            for pair in pairs
        ),
        "regenerate_after_initial_count": sum(
            pair["candidate_policy_behavior"][
                "regenerate_after_initial_count"
            ]
            for pair in pairs
        ),
    }
    aggregate["baseline_retry_pass_gain"] = (
        aggregate["baseline_submitted_pass_count"]
        - aggregate["baseline_initial_pass_count"]
    )
    aggregate["candidate_retry_pass_gain"] = (
        aggregate["candidate_submitted_pass_count"]
        - aggregate["candidate_initial_pass_count"]
    )
    aggregate["submitted_gm_delta"] = (
        aggregate["candidate_submitted_gm"]
        - aggregate["baseline_submitted_gm"]
    )
    aggregate["submitted_am_delta"] = (
        aggregate["candidate_submitted_am"]
        - aggregate["baseline_submitted_am"]
    )
    aggregate["initial_gm_delta"] = (
        aggregate["candidate_initial_gm"]
        - aggregate["baseline_initial_gm"]
    )
    aggregate["baseline_retry_gm_gain"] = (
        aggregate["baseline_submitted_gm"]
        - aggregate["baseline_initial_gm"]
    )
    aggregate["candidate_retry_gm_gain"] = (
        aggregate["candidate_submitted_gm"]
        - aggregate["candidate_initial_gm"]
    )
    summary = {
        "schema_version": "0.1",
        "comparison_id": "v07_dual_backend_score_v06_vs_flow_dppo20_baseline",
        "paired_episode_count": len(pairs),
        "baseline_summary_ref": str(baseline_summary_path),
        "candidate_summary_ref": str(candidate_summary_path),
        "comparison_scope": {
            "baseline": (
                "historical PlannerContext v0.5, edit-only image backend, "
                "pass-count/earlier-attempt best selection"
            ),
            "candidate": (
                "PlannerContext v0.6, qwen_dual_backend@1, "
                "pass-count/GM/earlier-attempt best selection"
            ),
            "causal_limit": (
                "The paired result measures the integrated system change. It "
                "does not isolate renderer routing, score feedback, Teacher "
                "prompt version, or stochastic generation."
            ),
        },
        "aggregate": aggregate,
        "pairs": pairs,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    return summary


def _compare_episode(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    if baseline["prompt_id"] != candidate["prompt_id"]:
        raise ValueError(
            f"{candidate['episode_id']}: paired prompt IDs do not match"
        )
    baseline_result = {
        "attempt_count": baseline["attempt_count"],
        "initial_pass_count": baseline["initial_pass_count"],
        "submitted_pass_count": baseline["best_pass_count"],
        "initial_gm": baseline["first_agent_geneval2_score"],
        "submitted_gm": baseline["submitted_geneval2_score"],
        "submitted_am": baseline["submitted_geneval2_am"],
        "submitted_attempt_id": baseline["submitted_attempt_id"],
        "image_action_sequence": [
            attempt["action"] for attempt in baseline["attempts"]
        ],
    }
    candidate_result = {
        "attempt_count": candidate["attempt_count"],
        "initial_pass_count": candidate["initial_pass_count"],
        "submitted_pass_count": candidate["best_pass_count"],
        "initial_gm": candidate["first_agent_geneval2_score"],
        "submitted_gm": candidate["submitted_geneval2_score"],
        "submitted_am": candidate["submitted_geneval2_am"],
        "submitted_attempt_id": candidate["submitted_attempt_id"],
        "image_action_sequence": [
            attempt["action"] for attempt in candidate["attempts"]
        ],
        "canonical_action_sequence": candidate.get(
            "canonical_action_sequence",
            [],
        ),
        "attempts": candidate["attempts"],
    }
    pass_delta = (
        candidate_result["submitted_pass_count"]
        - baseline_result["submitted_pass_count"]
    )
    gm_delta = (
        candidate_result["submitted_gm"]
        - baseline_result["submitted_gm"]
    )
    if pass_delta > 0:
        paired_outcome = "positive_more_atoms"
    elif pass_delta < 0:
        paired_outcome = "negative_fewer_atoms"
    elif gm_delta > 0:
        paired_outcome = "positive_equal_atoms_higher_gm"
    elif gm_delta < 0:
        paired_outcome = "negative_equal_atoms_lower_gm"
    else:
        paired_outcome = "tied"
    return {
        "episode_id": candidate["episode_id"],
        "prompt_id": candidate["prompt_id"],
        "difficulty_tier": candidate["difficulty_tier"],
        "constraint_count": candidate["constraint_count"],
        "baseline": baseline_result,
        "candidate": candidate_result,
        "submitted_pass_count_delta": pass_delta,
        "submitted_gm_delta": gm_delta,
        "submitted_am_delta": (
            candidate_result["submitted_am"]
            - baseline_result["submitted_am"]
        ),
        "initial_pass_count_delta": (
            candidate_result["initial_pass_count"]
            - baseline_result["initial_pass_count"]
        ),
        "initial_gm_delta": (
            candidate_result["initial_gm"]
            - baseline_result["initial_gm"]
        ),
        "paired_outcome": paired_outcome,
        "candidate_policy_behavior": _policy_behavior(candidate),
    }


def _policy_behavior(episode: dict[str, Any]) -> dict[str, Any]:
    attempts = episode["attempts"]
    if not attempts:
        return {
            "gm_tiebreak_changed_best": False,
            "gm_tiebreak_best_update_count": 0,
            "higher_gm_lower_pass_rejection_count": 0,
            "rollback_to_historical_source_count": 0,
            "regenerate_after_initial_count": 0,
        }
    earliest_max_pass = max(
        attempts,
        key=lambda attempt: attempt["pass_count"],
    )
    best_attempt_id = episode["best_attempt_id"]
    gm_tiebreak_changed_best = (
        earliest_max_pass["attempt_id"] != best_attempt_id
        and earliest_max_pass["pass_count"]
        == next(
            attempt["pass_count"]
            for attempt in attempts
            if attempt["attempt_id"] == best_attempt_id
        )
    )
    current_best = attempts[0]
    higher_gm_lower_pass_rejections = 0
    gm_tiebreak_best_updates = 0
    rollback_count = 0
    regenerate_count = 0
    previous_attempt_id = attempts[0]["attempt_id"]
    for attempt in attempts[1:]:
        if (
            attempt["pass_count"] < current_best["pass_count"]
            and attempt["geneval2_score"] > current_best["geneval2_score"]
        ):
            higher_gm_lower_pass_rejections += 1
        if (
            attempt["pass_count"] == current_best["pass_count"]
            and attempt["geneval2_score"] > current_best["geneval2_score"]
        ):
            gm_tiebreak_best_updates += 1
        if (
            attempt["action"] == "edit_image"
            and attempt["source_attempt_id"] != previous_attempt_id
        ):
            rollback_count += 1
        if attempt["action"] == "generate_image":
            regenerate_count += 1
        if (
            attempt["pass_count"] > current_best["pass_count"]
            or (
                attempt["pass_count"] == current_best["pass_count"]
                and attempt["geneval2_score"] > current_best["geneval2_score"]
            )
        ):
            current_best = attempt
        previous_attempt_id = attempt["attempt_id"]
    return {
        "gm_tiebreak_changed_best": gm_tiebreak_changed_best,
        "gm_tiebreak_best_update_count": gm_tiebreak_best_updates,
        "higher_gm_lower_pass_rejection_count": (
            higher_gm_lower_pass_rejections
        ),
        "rollback_to_historical_source_count": rollback_count,
        "regenerate_after_initial_count": regenerate_count,
    }


def _render_report(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    lines = [
        "# v0.7 / PlannerContext v0.6 五条配对轨迹分析",
        "",
        "## 汇总",
        "",
        f"- 配对轨迹：{summary['paired_episode_count']}",
        (
            "- 首次生成 atom pass："
            f"{aggregate['baseline_initial_pass_count']} -> "
            f"{aggregate['candidate_initial_pass_count']} "
            f"({aggregate['initial_pass_count_delta']:+d})"
        ),
        (
            "- 最终提交 atom pass："
            f"{aggregate['baseline_submitted_pass_count']} -> "
            f"{aggregate['candidate_submitted_pass_count']} "
            f"({aggregate['submitted_pass_count_delta']:+d})"
        ),
        (
            "- 首次生成平均 GM："
            f"{aggregate['baseline_initial_gm'] * 100:.2f} -> "
            f"{aggregate['candidate_initial_gm'] * 100:.2f} "
            f"({aggregate['initial_gm_delta'] * 100:+.2f})"
        ),
        (
            "- 最终提交平均 GM："
            f"{aggregate['baseline_submitted_gm'] * 100:.2f} -> "
            f"{aggregate['candidate_submitted_gm'] * 100:.2f} "
            f"({aggregate['submitted_gm_delta'] * 100:+.2f})"
        ),
        (
            "- 最终提交平均 AM："
            f"{aggregate['baseline_submitted_am'] * 100:.2f} -> "
            f"{aggregate['candidate_submitted_am'] * 100:.2f} "
            f"({aggregate['submitted_am_delta'] * 100:+.2f})"
        ),
        (
            "- 旧方案自身 retry atom gain："
            f"{aggregate['baseline_retry_pass_gain']:+d}"
        ),
        (
            "- 新方案自身 retry atom gain："
            f"{aggregate['candidate_retry_pass_gain']:+d}"
        ),
        (
            "- 旧方案自身 retry GM gain："
            f"{aggregate['baseline_retry_gm_gain'] * 100:+.2f}"
        ),
        (
            "- 新方案自身 retry GM gain："
            f"{aggregate['candidate_retry_gm_gain'] * 100:+.2f}"
        ),
        f"- 配对结果：{aggregate['paired_outcome_counts']}",
        (
            "- GM tie-break 实际更新 best："
            f"{aggregate['gm_tiebreak_best_update_count']} 次"
        ),
        (
            "- GM 更高但 pass 更少、被策略正确拒绝："
            f"{aggregate['higher_gm_lower_pass_rejection_count']} 次"
        ),
        (
            "- 回到历史 source 再编辑："
            f"{aggregate['rollback_to_historical_source_count']} 次"
        ),
        (
            "- 首次生成后主动重新 generate："
            f"{aggregate['regenerate_after_initial_count']} 次"
        ),
        "",
        "## 逐条",
        "",
        "| Episode | 旧提交 pass | 新提交 pass | Δpass | 旧 GM | 新 GM | ΔGM | 结论 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for pair in summary["pairs"]:
        lines.append(
            "| {episode_id} | {old_pass} | {new_pass} | {pass_delta:+d} | "
            "{old_gm:.2f} | {new_gm:.2f} | {gm_delta:+.2f} | {outcome} |".format(
                episode_id=pair["episode_id"],
                old_pass=pair["baseline"]["submitted_pass_count"],
                new_pass=pair["candidate"]["submitted_pass_count"],
                pass_delta=pair["submitted_pass_count_delta"],
                old_gm=pair["baseline"]["submitted_gm"] * 100,
                new_gm=pair["candidate"]["submitted_gm"] * 100,
                gm_delta=pair["submitted_gm_delta"] * 100,
                outcome=pair["paired_outcome"],
            )
        )
    lines.extend(["", "## 新轨迹逐 Attempt 行为", ""])
    for pair in summary["pairs"]:
        lines.extend(
            [
                f"### `{pair['episode_id']}`",
                "",
                "| Attempt | Action | Source | Backend | Pass | GM | Fixed | "
                "Regressed | Best |",
                "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |",
            ]
        )
        for attempt in pair["candidate"]["attempts"]:
            lines.append(
                "| {attempt_id} | {action} | {source} | {backend} | "
                "{pass_count} | {gm:.2f} | {fixed} | {regressed} | "
                "{best} |".format(
                    attempt_id=attempt["attempt_id"],
                    action=attempt["action"],
                    source=attempt["source_attempt_id"] or "-",
                    backend=attempt["backend"],
                    pass_count=attempt["pass_count"],
                    gm=attempt["geneval2_score"] * 100,
                    fixed=_list_cell(attempt["fixed_constraint_ids"]),
                    regressed=_list_cell(
                        attempt["regressed_constraint_ids"]
                    ),
                    best="yes" if attempt["became_best"] else "no",
                )
            )
        lines.append("")
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            summary["comparison_scope"]["causal_limit"],
            "",
            "因此本报告可以判断整套新方案是否方向正向，但不能单独把收益归因于 "
            "Qwen-Image、GM feedback、PlannerContext v0.6 或 Teacher prompt。"
            "要拆分因果贡献，仍需运行已准备的 edit-only v0.6 对照或固定 Action replay。",
            "",
        ]
    )
    return "\n".join(lines)


def _mean(values: Any) -> float:
    materialized = list(values)
    if not materialized:
        raise ValueError("cannot average an empty sequence")
    return sum(materialized) / len(materialized)


def _list_cell(values: list[str]) -> str:
    return ", ".join(values) if values else "-"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
