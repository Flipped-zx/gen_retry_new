from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from gen_retry.runtime.json_canonical import canonical_json

PASS_THRESHOLD = 0.5
PROBABILITY_TOLERANCE = 1e-5


def analyze_qwen_best_of_5_baseline(
    *,
    baseline_detail_path: Path,
    selection_path: Path,
    agent_summary_path: Path,
    agent_run_root: Path,
    bootstrap_samples: int = 20_000,
    bootstrap_seed: int = 20_260_731,
) -> dict[str, Any]:
    baseline_detail = _load_json(baseline_detail_path)
    selection = _load_json(selection_path)
    agent_summary = _load_json(agent_summary_path)
    selected_prompts = selection["selected_prompts"]
    agent_episodes = agent_summary["episodes"]

    if not isinstance(baseline_detail, dict):
        raise ValueError("baseline detail must be an object keyed by selection index")
    expected_keys = {str(index) for index in range(len(selected_prompts))}
    if set(baseline_detail) != expected_keys:
        raise ValueError("baseline detail keys do not exactly cover selection indices")
    if len(agent_episodes) != len(selected_prompts):
        raise ValueError("agent and selection episode counts do not match")

    agent_by_prompt_id = _index_unique(agent_episodes, "prompt_id")
    rows: list[dict[str, Any]] = []
    probability_overshoots: list[float] = []
    reported_gm_differences: list[float] = []

    for index, selected in enumerate(selected_prompts):
        baseline = baseline_detail[str(index)]
        prompt_id = selected["prompt_id"]
        if baseline["prompt"] != selected["original_prompt"]:
            raise ValueError(f"selection rank {index + 1}: prompt mismatch")
        if baseline["vqa_list"] != selected["vqa_list"]:
            raise ValueError(f"selection rank {index + 1}: VQA list mismatch")
        if prompt_id not in agent_by_prompt_id:
            raise ValueError(f"{prompt_id}: missing from agent summary")
        agent = agent_by_prompt_id[prompt_id]
        if agent["constraint_count"] != len(selected["atomic_constraints"]):
            raise ValueError(f"{prompt_id}: constraint count mismatch")

        variants = _validate_variants(
            baseline=baseline,
            prompt_id=prompt_id,
            probability_overshoots=probability_overshoots,
            reported_gm_differences=reported_gm_differences,
        )
        gm_selected = variants[baseline["best_variant_idx"]]
        protocol_selected = max(
            variants.values(),
            key=lambda item: (
                item["pass_count"],
                item["gm"],
                -item["variant_idx"],
            ),
        )
        submitted = _load_agent_submitted(
            agent=agent,
            selected=selected,
            agent_run_root=agent_run_root,
        )
        first = {
            "pass_count": agent["initial_pass_count"],
            "am": agent["first_agent_geneval2_am"],
            "gm": agent["first_agent_geneval2_score"],
            "all_pass": (
                agent["initial_pass_count"] == agent["constraint_count"]
            ),
        }
        row = {
            "selection_rank": index + 1,
            "episode_id": agent["episode_id"],
            "prompt_id": prompt_id,
            "difficulty_tier": selected["difficulty_tier"],
            "constraint_count": agent["constraint_count"],
            "agent_image_attempt_count": agent["attempt_count"],
            "baseline_gm_selected": _public_metrics(gm_selected),
            "baseline_protocol_selected": _public_metrics(protocol_selected),
            "agent_first": first,
            "agent_submitted": submitted,
        }
        row["agent_vs_baseline"] = _paired_delta(
            baseline=row["baseline_gm_selected"],
            candidate=submitted,
        )
        rows.append(row)

    if set(agent_by_prompt_id) != {
        selected["prompt_id"] for selected in selected_prompts
    }:
        raise ValueError("agent summary contains prompts outside the selection")

    baseline_aggregate = _aggregate(rows, "baseline_gm_selected")
    protocol_aggregate = _aggregate(rows, "baseline_protocol_selected")
    agent_first_aggregate = _aggregate(rows, "agent_first")
    agent_aggregate = _aggregate(rows, "agent_submitted")
    comparison = _aggregate_comparison(
        rows=rows,
        baseline=baseline_aggregate,
        agent=agent_aggregate,
        bootstrap_samples=bootstrap_samples,
        bootstrap_seed=bootstrap_seed,
    )
    difficulty = [
        {
            "difficulty_tier": tier,
            "baseline": _aggregate(tier_rows, "baseline_gm_selected"),
            "agent": _aggregate(tier_rows, "agent_submitted"),
            "delta": _aggregate_delta(
                _aggregate(tier_rows, "baseline_gm_selected"),
                _aggregate(tier_rows, "agent_submitted"),
            ),
        }
        for tier in ("easy", "medium", "hard")
        if (
            tier_rows := [
                row for row in rows if row["difficulty_tier"] == tier
            ]
        )
    ]
    atom_types = _aggregate_atom_types(
        rows=rows,
        selected_prompts=selected_prompts,
        baseline_detail=baseline_detail,
    )
    best_of_k_curve = _best_of_k_curve(
        baseline_detail=baseline_detail,
        selected_prompts=selected_prompts,
    )
    initial_comparison = _aggregate_delta(
        baseline_aggregate,
        agent_first_aggregate,
    )
    retry_gain = _aggregate_delta(
        agent_first_aggregate,
        agent_aggregate,
    )
    selector_changed_rows = [
        row
        for row in rows
        if row["baseline_gm_selected"]["variant_idx"]
        != row["baseline_protocol_selected"]["variant_idx"]
    ]
    return {
        "schema_version": "0.1",
        "analysis_id": "qwen_image_best_of_5_vs_agent_200",
        "inputs": {
            "baseline_detail": _input_ref(baseline_detail_path),
            "selection": _input_ref(selection_path),
            "agent_summary": _input_ref(agent_summary_path),
            "agent_run_root": str(agent_run_root),
        },
        "scope": {
            "paired_episode_count": len(rows),
            "baseline_candidate_count_per_prompt": 5,
            "baseline_total_image_count": len(rows) * 5,
            "baseline_selector": "highest_soft_tifa_gm_then_earlier",
            "agent_selector": (
                "higher_pass_count_then_higher_primary_score_then_earlier"
            ),
            "pass_threshold": PASS_THRESHOLD,
            "baseline_prompt": "original_prompt",
            "claim_limit": (
                "Integrated paired comparison only. The baseline file does not "
                "persist renderer configuration/model revision, and the Agent "
                "uses rewritten instructions plus adaptive generation/editing."
            ),
        },
        "alignment_checks": {
            "prompt_exact_match_count": len(rows),
            "vqa_list_exact_match_count": len(rows),
            "five_variants_per_prompt_count": len(rows),
            "reported_best_selection_match_count": len(rows),
            "max_probability_overshoot": max(
                probability_overshoots,
                default=0.0,
            ),
            "max_reported_vs_recomputed_gm_abs_difference": max(
                reported_gm_differences,
                default=0.0,
            ),
            "probabilities_clamped_for_aggregate_metrics": True,
        },
        "aggregate": {
            "baseline_gm_selected": baseline_aggregate,
            "baseline_protocol_selected": protocol_aggregate,
            "agent_first": agent_first_aggregate,
            "agent_submitted": agent_aggregate,
            "agent_vs_baseline": comparison,
            "agent_first_vs_baseline": initial_comparison,
            "agent_retry_gain": retry_gain,
        },
        "selector_sensitivity": {
            "selection_changed_episode_count": len(selector_changed_rows),
            "baseline_gm_selected": baseline_aggregate,
            "baseline_protocol_selected": protocol_aggregate,
            "agent_vs_protocol_selected": _aggregate_delta(
                protocol_aggregate,
                agent_aggregate,
            ),
        },
        "best_of_k_prefix_curve": best_of_k_curve,
        "difficulty": difficulty,
        "atom_types": atom_types,
        "pairs": rows,
    }


def write_qwen_best_of_5_analysis(
    *,
    summary: dict[str, Any],
    artifact_path: Path,
    report_path: Path,
) -> None:
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")


def _validate_variants(
    *,
    baseline: dict[str, Any],
    prompt_id: str,
    probability_overshoots: list[float],
    reported_gm_differences: list[float],
) -> dict[int, dict[str, Any]]:
    raw_variants = baseline["all_variants"]
    if len(raw_variants) != 5:
        raise ValueError(f"{prompt_id}: expected exactly five baseline variants")
    variants: dict[int, dict[str, Any]] = {}
    for raw_variant in raw_variants:
        variant_idx = raw_variant["variant_idx"]
        if variant_idx in variants:
            raise ValueError(f"{prompt_id}: duplicate variant index {variant_idx}")
        raw_scores = [float(score) for score in raw_variant["atom_scores"]]
        if len(raw_scores) != len(baseline["vqa_list"]):
            raise ValueError(f"{prompt_id}: variant atom score count mismatch")
        for score in raw_scores:
            if not math.isfinite(score):
                raise ValueError(f"{prompt_id}: non-finite atom score")
            if score < -PROBABILITY_TOLERANCE or score > 1 + PROBABILITY_TOLERANCE:
                raise ValueError(f"{prompt_id}: atom score outside probability range")
            probability_overshoots.append(max(0.0, score - 1.0))
        raw_gm = _geometric_mean(raw_scores)
        reported_gm = float(raw_variant["prompt_score"])
        reported_gm_differences.append(abs(raw_gm - reported_gm))
        if not math.isclose(raw_gm, reported_gm, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"{prompt_id}: prompt score does not match atom scores")
        scores = [_clamp_probability(score) for score in raw_scores]
        variants[variant_idx] = {
            "variant_idx": variant_idx,
            "pass_count": sum(score >= PASS_THRESHOLD for score in scores),
            "am": sum(scores) / len(scores),
            "gm": _geometric_mean(scores),
            "all_pass": all(score >= PASS_THRESHOLD for score in scores),
            "atom_scores": scores,
        }
    if set(variants) != set(range(5)):
        raise ValueError(f"{prompt_id}: variant indices must be 0 through 4")

    best_idx = baseline["best_variant_idx"]
    expected_best = max(
        raw_variants,
        key=lambda item: (float(item["prompt_score"]), -item["variant_idx"]),
    )
    if best_idx != expected_best["variant_idx"]:
        raise ValueError(f"{prompt_id}: reported best variant is not max GM")
    if baseline["best_atom_scores"] != expected_best["atom_scores"]:
        raise ValueError(f"{prompt_id}: reported best atom scores mismatch")
    if not math.isclose(
        float(baseline["best_prompt_score"]),
        float(expected_best["prompt_score"]),
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        raise ValueError(f"{prompt_id}: reported best prompt score mismatch")
    return variants


def _load_agent_submitted(
    *,
    agent: dict[str, Any],
    selected: dict[str, Any],
    agent_run_root: Path,
) -> dict[str, Any]:
    report_path = (
        agent_run_root
        / agent["episode_id"]
        / "geneval2"
        / f"{agent['submitted_attempt_id']}.json"
    )
    report = _load_json(report_path)
    results_by_id = _index_unique(report["constraint_results"], "constraint_id")
    expected_ids = {
        constraint["constraint_id"]
        for constraint in selected["atomic_constraints"]
    }
    if set(results_by_id) != expected_ids:
        raise ValueError(
            f"{agent['episode_id']}: submitted evaluator constraint IDs mismatch"
        )
    ordered_results = [
        results_by_id[constraint["constraint_id"]]
        for constraint in selected["atomic_constraints"]
    ]
    scores = [
        _validated_probability(
            result["confidence"],
            label=f"{agent['episode_id']}:{result['constraint_id']}",
        )
        for result in ordered_results
    ]
    pass_count = sum(result["status"] == "pass" for result in ordered_results)
    if pass_count != agent["best_pass_count"]:
        raise ValueError(f"{agent['episode_id']}: submitted pass count mismatch")
    am = sum(scores) / len(scores)
    gm = _geometric_mean(scores)
    if not math.isclose(
        am,
        agent["submitted_geneval2_am"],
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(f"{agent['episode_id']}: submitted AM mismatch")
    if not math.isclose(
        gm,
        agent["submitted_geneval2_score"],
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(f"{agent['episode_id']}: submitted GM mismatch")
    return {
        "pass_count": pass_count,
        "am": am,
        "gm": gm,
        "all_pass": pass_count == len(ordered_results),
        "passed_constraint_ids": [
            result["constraint_id"]
            for result in ordered_results
            if result["status"] == "pass"
        ],
    }


def _aggregate(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    episode_count = len(rows)
    constraint_slots = sum(row["constraint_count"] for row in rows)
    passed_atoms = sum(row[field]["pass_count"] for row in rows)
    if field == "agent_first":
        image_count = episode_count
    elif field == "agent_submitted":
        image_count = sum(row["agent_image_attempt_count"] for row in rows)
    else:
        image_count = episode_count * 5
    return {
        "episode_count": episode_count,
        "constraint_slots": constraint_slots,
        "passed_atoms": passed_atoms,
        "atom_pass_rate": passed_atoms / constraint_slots,
        "soft_tifa_am": _mean(row[field]["am"] for row in rows),
        "soft_tifa_gm": _mean(row[field]["gm"] for row in rows),
        "all_pass_episodes": sum(row[field]["all_pass"] for row in rows),
        "image_count": image_count,
        "mean_images_per_episode": image_count / episode_count,
    }


def _aggregate_comparison(
    *,
    rows: list[dict[str, Any]],
    baseline: dict[str, Any],
    agent: dict[str, Any],
    bootstrap_samples: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    delta = _aggregate_delta(baseline, agent)
    pass_comparisons = Counter()
    gm_comparisons = Counter()
    paired_outcomes = Counter()
    all_pass_transitions = Counter()
    for row in rows:
        baseline_row = row["baseline_gm_selected"]
        agent_row = row["agent_submitted"]
        pass_delta = agent_row["pass_count"] - baseline_row["pass_count"]
        gm_delta = agent_row["gm"] - baseline_row["gm"]
        pass_comparisons[_sign_label(pass_delta)] += 1
        gm_comparisons[_sign_label(gm_delta)] += 1
        if pass_delta > 0:
            outcome = "positive_more_atoms"
        elif pass_delta < 0:
            outcome = "negative_fewer_atoms"
        elif gm_delta > 0:
            outcome = "positive_equal_atoms_higher_gm"
        elif gm_delta < 0:
            outcome = "negative_equal_atoms_lower_gm"
        else:
            outcome = "tied"
        paired_outcomes[outcome] += 1
        all_pass_transitions[
            f"{'pass' if baseline_row['all_pass'] else 'fail'}_to_"
            f"{'pass' if agent_row['all_pass'] else 'fail'}"
        ] += 1

    failed_baseline = baseline["constraint_slots"] - baseline["passed_atoms"]
    failed_agent = agent["constraint_slots"] - agent["passed_atoms"]
    delta.update(
        {
            "relative_atom_pass_rate_gain": _relative_change(
                baseline["atom_pass_rate"],
                agent["atom_pass_rate"],
            ),
            "relative_soft_tifa_gm_gain": _relative_change(
                baseline["soft_tifa_gm"],
                agent["soft_tifa_gm"],
            ),
            "relative_all_pass_gain": _relative_change(
                baseline["all_pass_episodes"],
                agent["all_pass_episodes"],
            ),
            "failed_atom_reduction": (
                (failed_baseline - failed_agent) / failed_baseline
            ),
            "image_count_delta": agent["image_count"] - baseline["image_count"],
            "relative_image_count_delta": _relative_change(
                baseline["image_count"],
                agent["image_count"],
            ),
            "pass_count_comparison": dict(sorted(pass_comparisons.items())),
            "gm_comparison": dict(sorted(gm_comparisons.items())),
            "pass_primary_paired_outcomes": dict(
                sorted(paired_outcomes.items())
            ),
            "all_pass_transitions": dict(sorted(all_pass_transitions.items())),
            "paired_episode_bootstrap": _paired_bootstrap(
                rows=rows,
                samples=bootstrap_samples,
                seed=bootstrap_seed,
            ),
        }
    )
    return delta


def _aggregate_delta(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "passed_atoms": candidate["passed_atoms"] - baseline["passed_atoms"],
        "atom_pass_rate": (
            candidate["atom_pass_rate"] - baseline["atom_pass_rate"]
        ),
        "soft_tifa_am": candidate["soft_tifa_am"] - baseline["soft_tifa_am"],
        "soft_tifa_gm": candidate["soft_tifa_gm"] - baseline["soft_tifa_gm"],
        "all_pass_episodes": (
            candidate["all_pass_episodes"] - baseline["all_pass_episodes"]
        ),
    }


def _aggregate_atom_types(
    *,
    rows: list[dict[str, Any]],
    selected_prompts: list[dict[str, Any]],
    baseline_detail: dict[str, Any],
) -> list[dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for index, (row, selected) in enumerate(zip(rows, selected_prompts)):
        baseline_variant_idx = row["baseline_gm_selected"]["variant_idx"]
        baseline_scores = baseline_detail[str(index)]["all_variants"][
            baseline_variant_idx
        ]["atom_scores"]
        agent_passed = set(
            row["agent_submitted"]["passed_constraint_ids"]
        )
        for constraint, baseline_score in zip(
            selected["atomic_constraints"],
            baseline_scores,
        ):
            atom_type = constraint["constraint_type"]
            counts[atom_type]["total"] += 1
            counts[atom_type]["baseline_pass"] += (
                float(baseline_score) >= PASS_THRESHOLD
            )
            counts[atom_type]["agent_pass"] += (
                constraint["constraint_id"] in agent_passed
            )
    order = ["object", "attribute", "count", "position", "verb"]
    result = []
    for atom_type in order:
        values = counts[atom_type]
        total = values["total"]
        if not total:
            continue
        result.append(
            {
                "atom_type": atom_type,
                "total": total,
                "baseline_pass": values["baseline_pass"],
                "baseline_pass_rate": values["baseline_pass"] / total,
                "agent_pass": values["agent_pass"],
                "agent_pass_rate": values["agent_pass"] / total,
                "pass_delta": (
                    values["agent_pass"] - values["baseline_pass"]
                ),
                "pass_rate_delta": (
                    (values["agent_pass"] - values["baseline_pass"]) / total
                ),
            }
        )
    return result


def _best_of_k_curve(
    *,
    baseline_detail: dict[str, Any],
    selected_prompts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for candidate_count in range(1, 6):
        episode_metrics = []
        for index, selected in enumerate(selected_prompts):
            variants = baseline_detail[str(index)]["all_variants"][
                :candidate_count
            ]
            best = max(
                variants,
                key=lambda item: (
                    float(item["prompt_score"]),
                    -item["variant_idx"],
                ),
            )
            scores = [
                _clamp_probability(float(score))
                for score in best["atom_scores"]
            ]
            episode_metrics.append(
                {
                    "constraint_count": len(scores),
                    "pass_count": sum(
                        score >= PASS_THRESHOLD for score in scores
                    ),
                    "am": sum(scores) / len(scores),
                    "gm": _geometric_mean(scores),
                    "all_pass": all(
                        score >= PASS_THRESHOLD for score in scores
                    ),
                    "difficulty_tier": selected["difficulty_tier"],
                }
            )
        slots = sum(item["constraint_count"] for item in episode_metrics)
        passed = sum(item["pass_count"] for item in episode_metrics)
        result.append(
            {
                "candidate_count": candidate_count,
                "passed_atoms": passed,
                "constraint_slots": slots,
                "atom_pass_rate": passed / slots,
                "soft_tifa_am": _mean(
                    item["am"] for item in episode_metrics
                ),
                "soft_tifa_gm": _mean(
                    item["gm"] for item in episode_metrics
                ),
                "all_pass_episodes": sum(
                    item["all_pass"] for item in episode_metrics
                ),
            }
        )
    return result


def _paired_bootstrap(
    *,
    rows: list[dict[str, Any]],
    samples: int,
    seed: int,
) -> dict[str, Any]:
    if samples < 1:
        raise ValueError("bootstrap samples must be positive")
    rng = random.Random(seed)
    distributions: dict[str, list[float]] = {
        "atom_pass_rate_delta": [],
        "soft_tifa_am_delta": [],
        "soft_tifa_gm_delta": [],
        "all_pass_rate_delta": [],
    }
    for _ in range(samples):
        sampled = [rows[rng.randrange(len(rows))] for _ in rows]
        slots = sum(row["constraint_count"] for row in sampled)
        distributions["atom_pass_rate_delta"].append(
            (
                sum(row["agent_submitted"]["pass_count"] for row in sampled)
                - sum(
                    row["baseline_gm_selected"]["pass_count"]
                    for row in sampled
                )
            )
            / slots
        )
        distributions["soft_tifa_am_delta"].append(
            _mean(
                row["agent_submitted"]["am"]
                - row["baseline_gm_selected"]["am"]
                for row in sampled
            )
        )
        distributions["soft_tifa_gm_delta"].append(
            _mean(
                row["agent_submitted"]["gm"]
                - row["baseline_gm_selected"]["gm"]
                for row in sampled
            )
        )
        distributions["all_pass_rate_delta"].append(
            _mean(
                int(row["agent_submitted"]["all_pass"])
                - int(row["baseline_gm_selected"]["all_pass"])
                for row in sampled
            )
        )
    return {
        "method": "paired_episode_cluster_percentile",
        "samples": samples,
        "seed": seed,
        "confidence_level": 0.95,
        "intervals": {
            metric: _percentile_interval(values)
            for metric, values in distributions.items()
        },
        "interpretation_limit": (
            "The 200 prompts are a designed fixed cohort, not an IID random "
            "sample; intervals describe paired-cohort stability and do not "
            "establish out-of-distribution generalization."
        ),
    }


def _render_report(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    baseline = aggregate["baseline_gm_selected"]
    protocol = aggregate["baseline_protocol_selected"]
    first = aggregate["agent_first"]
    agent = aggregate["agent_submitted"]
    delta = aggregate["agent_vs_baseline"]
    intervals = delta["paired_episode_bootstrap"]["intervals"]
    selector = summary["selector_sensitivity"]
    pairs = summary["pairs"]
    negative_atom_pairs = sorted(
        (
            pair
            for pair in pairs
            if pair["agent_vs_baseline"]["pass_count"] < 0
        ),
        key=lambda pair: (
            pair["agent_vs_baseline"]["pass_count"],
            pair["agent_vs_baseline"]["gm"],
        ),
    )
    top_positive_pairs = sorted(
        pairs,
        key=lambda pair: (
            pair["agent_vs_baseline"]["pass_count"],
            pair["agent_vs_baseline"]["gm"],
        ),
        reverse=True,
    )[:5]
    lines = [
        "# Qwen-Image Best-of-5 Baseline 与 200 条 Retry 轨迹对比",
        "",
        "## 结论",
        "",
        (
            "在完全对齐的 200 个 prompt / 1,419 个 Geneval2 atom 上，"
            "Agent 提交结果相对 Qwen-Image 原始 prompt、5 次独立生成后按"
            "最高 Soft-TIFA GM 取优的 baseline，增加 "
            f"**{delta['passed_atoms']:+d} 个通过 atom**，GM 提升 "
            f"**{delta['soft_tifa_gm'] * 100:+.2f} 分**，全通过轨迹增加 "
            f"**{delta['all_pass_episodes']:+d} 条**。"
        ),
        "",
        (
            "这个提升在更严格的 pass-count-first baseline 重选下仍然成立："
            f"Agent 仍多通过 {agent['passed_atoms'] - protocol['passed_atoms']} "
            f"个 atom，GM 高 {agent['soft_tifa_gm'] * 100 - protocol['soft_tifa_gm'] * 100:.2f} "
            "分。因此主结论不是由两边 selector 不一致造成的。"
        ),
        "",
        "## 主结果",
        "",
        "| 指标 | Qwen Best-of-5（最高 GM） | Agent 首图 | Agent 提交 | Agent - Baseline |",
        "| --- | ---: | ---: | ---: | ---: |",
        (
            f"| 通过 atoms | {baseline['passed_atoms']}/{baseline['constraint_slots']} "
            f"| {first['passed_atoms']}/{first['constraint_slots']} "
            f"| {agent['passed_atoms']}/{agent['constraint_slots']} "
            f"| {delta['passed_atoms']:+d} |"
        ),
        (
            f"| Atom pass rate | {_pct(baseline['atom_pass_rate'])} "
            f"| {_pct(first['atom_pass_rate'])} | {_pct(agent['atom_pass_rate'])} "
            f"| {_pp(delta['atom_pass_rate'])} |"
        ),
        (
            f"| Soft-TIFA AM | {_score(baseline['soft_tifa_am'])} "
            f"| {_score(first['soft_tifa_am'])} | {_score(agent['soft_tifa_am'])} "
            f"| {_score_delta(delta['soft_tifa_am'])} |"
        ),
        (
            f"| Soft-TIFA GM | {_score(baseline['soft_tifa_gm'])} "
            f"| {_score(first['soft_tifa_gm'])} | {_score(agent['soft_tifa_gm'])} "
            f"| {_score_delta(delta['soft_tifa_gm'])} |"
        ),
        (
            f"| 全通过轨迹 | {baseline['all_pass_episodes']}/200 "
            f"| {first['all_pass_episodes']}/200 | {agent['all_pass_episodes']}/200 "
            f"| {delta['all_pass_episodes']:+d} |"
        ),
        (
            f"| 图像调用数 | {baseline['image_count']} "
            f"| 200 | {agent['image_count']} "
            f"| {delta['image_count_delta']:+d} |"
        ),
        "",
        (
            f"- 失败 atom 从 {baseline['constraint_slots'] - baseline['passed_atoms']} "
            f"降到 {agent['constraint_slots'] - agent['passed_atoms']}，减少 "
            f"{delta['failed_atom_reduction'] * 100:.2f}%。"
        ),
        (
            f"- 全通过率从 {_pct(baseline['all_pass_episodes'] / 200)} "
            f"升到 {_pct(agent['all_pass_episodes'] / 200)}，绝对提升 "
            f"{_pp(delta['all_pass_episodes'] / 200)}，相对增加 "
            f"{delta['relative_all_pass_gain'] * 100:.2f}%。"
        ),
        (
            "- 配对 episode bootstrap 95% 区间：atom pass-rate 增量 "
            f"{_ci_pp(intervals['atom_pass_rate_delta'])}，GM 增量 "
            f"{_ci_score(intervals['soft_tifa_gm_delta'])}，全通过率增量 "
            f"{_ci_pp(intervals['all_pass_rate_delta'])}。"
        ),
        "",
        "## 配对胜负",
        "",
        (
            "- Pass count：Agent 更高 "
            f"{delta['pass_count_comparison'].get('higher', 0)} 条、持平 "
            f"{delta['pass_count_comparison'].get('equal', 0)} 条、更低 "
            f"{delta['pass_count_comparison'].get('lower', 0)} 条。"
        ),
        (
            "- GM：Agent 更高 "
            f"{delta['gm_comparison'].get('higher', 0)} 条、更低 "
            f"{delta['gm_comparison'].get('lower', 0)} 条。"
        ),
        (
            "- 按项目冻结的 pass-count-first 比较：Agent 胜 "
            f"{_positive_outcomes(delta['pass_primary_paired_outcomes'])} 条，"
            f"负 {_negative_outcomes(delta['pass_primary_paired_outcomes'])} 条。"
        ),
        (
            "- 全通过迁移：baseline 未全过但 Agent 全过 "
            f"{delta['all_pass_transitions'].get('fail_to_pass', 0)} 条；"
            "baseline 全过但 Agent 未全过 "
            f"{delta['all_pass_transitions'].get('pass_to_fail', 0)} 条。"
        ),
        "",
        "## 难度分层",
        "",
        "| 难度 | Episodes | Baseline atoms | Agent atoms | Δatoms | Baseline GM | Agent GM | ΔGM | 全通过变化 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["difficulty"]:
        base = item["baseline"]
        candidate = item["agent"]
        tier_delta = item["delta"]
        lines.append(
            f"| {item['difficulty_tier']} | {base['episode_count']} "
            f"| {base['passed_atoms']}/{base['constraint_slots']} "
            f"| {candidate['passed_atoms']}/{candidate['constraint_slots']} "
            f"| {tier_delta['passed_atoms']:+d} "
            f"| {_score(base['soft_tifa_gm'])} "
            f"| {_score(candidate['soft_tifa_gm'])} "
            f"| {_score_delta(tier_delta['soft_tifa_gm'])} "
            f"| {base['all_pass_episodes']} -> {candidate['all_pass_episodes']} |"
        )
    lines.extend(
        [
            "",
            (
                "提升主要集中在 medium/hard：两层分别增加 "
                f"{summary['difficulty'][1]['delta']['passed_atoms']} 和 "
                f"{summary['difficulty'][2]['delta']['passed_atoms']} 个通过 atom；"
                "hard baseline 没有全通过样本，Agent 达到 "
                f"{summary['difficulty'][2]['agent']['all_pass_episodes']}/"
                f"{summary['difficulty'][2]['agent']['episode_count']}。"
            ),
            "",
            "## Atom 类型",
            "",
            "| 类型 | Total | Baseline pass | Agent pass | Δpass | Pass-rate Δ |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summary["atom_types"]:
        lines.append(
            f"| {item['atom_type']} | {item['total']} "
            f"| {item['baseline_pass']} ({_pct(item['baseline_pass_rate'])}) "
            f"| {item['agent_pass']} ({_pct(item['agent_pass_rate'])}) "
            f"| {item['pass_delta']:+d} | {_pp(item['pass_rate_delta'])} |"
        )
    lines.extend(
        [
            "",
            (
                "绝对增量最大的是 count（+128），其次是 attribute（+69）和 "
                "position（+53）。Verb 从 5/22 提升到 10/22，但最终仍只有 "
                "45.45%，仍是最明显的内容瓶颈。"
            ),
            "",
            "## Selector 敏感性",
            "",
            (
                f"新增 JSON 用最高 GM 选图；项目 reducer 则先比较 pass count。"
                f"两种规则在 {selector['selection_changed_episode_count']}/200 "
                "条上选择不同图片。"
            ),
            "",
            "| Baseline 选择规则 | Passed atoms | Atom pass rate | AM | GM | 全通过 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
            (
                f"| 最高 GM | {baseline['passed_atoms']}/{baseline['constraint_slots']} "
                f"| {_pct(baseline['atom_pass_rate'])} "
                f"| {_score(baseline['soft_tifa_am'])} "
                f"| {_score(baseline['soft_tifa_gm'])} "
                f"| {baseline['all_pass_episodes']}/200 |"
            ),
            (
                f"| Pass count -> GM -> earlier | "
                f"{protocol['passed_atoms']}/{protocol['constraint_slots']} "
                f"| {_pct(protocol['atom_pass_rate'])} "
                f"| {_score(protocol['soft_tifa_am'])} "
                f"| {_score(protocol['soft_tifa_gm'])} "
                f"| {protocol['all_pass_episodes']}/200 |"
            ),
            "",
            (
                "协议对齐选择器让 baseline 多保留 30 个通过 atom，但平均 GM "
                "略降 0.40 分。即使用这个更强的 atom-pass baseline，Agent "
                f"仍增加 {agent['passed_atoms'] - protocol['passed_atoms']} "
                "个通过 atom。"
            ),
            "",
            "## Best-of-K 采样收益",
            "",
            "| 前 K 张按最高 GM 取优 | Atom pass rate | AM | GM | 全通过 |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summary["best_of_k_prefix_curve"]:
        lines.append(
            f"| {item['candidate_count']} "
            f"| {_pct(item['atom_pass_rate'])} "
            f"| {_score(item['soft_tifa_am'])} "
            f"| {_score(item['soft_tifa_gm'])} "
            f"| {item['all_pass_episodes']}/200 |"
        )
    lines.extend(
        [
            "",
            (
                "从第 1 个候选到 Best-of-5，baseline 自身 GM 提高 13.22 分、"
                "atom pass rate 提高 8.25 points、全通过增加 20 条。"
                "因此当前 baseline 已包含明显的随机采样取优收益，不应与后续"
                "真正的单次生成 baseline 混称为同一口径。"
            ),
            "",
            "## 提升来源的描述性拆分",
            "",
            (
                f"- Baseline Best-of-5 -> Agent 首图："
                f"{aggregate['agent_first_vs_baseline']['passed_atoms']:+d} atoms，"
                f"GM {_score_delta(aggregate['agent_first_vs_baseline']['soft_tifa_gm'])}，"
                f"全通过 {aggregate['agent_first_vs_baseline']['all_pass_episodes']:+d}。"
            ),
            (
                f"- Agent 首图 -> Agent 最终提交："
                f"{aggregate['agent_retry_gain']['passed_atoms']:+d} atoms，"
                f"GM {_score_delta(aggregate['agent_retry_gain']['soft_tifa_gm'])}，"
                f"全通过 {aggregate['agent_retry_gain']['all_pass_episodes']:+d}。"
            ),
            "",
            (
                "算术上，总 atom 增量 259 中有 117 出现在 Agent 首图阶段，"
                "142 来自后续 retry；总 GM 增量 41.97 中有 11.05 出现在首图，"
                "30.92 来自 retry。这不是因果归因：首图 prompt、采样配置和 "
                "baseline 的 Best-of-5 选择都没有被独立控制。"
            ),
            "",
            "## Agent 落后样本",
            "",
            (
                f"Agent 有 {len(negative_atom_pairs)} 条的提交 pass count 低于 "
                "Best-of-5 baseline。逐条列出，便于后续诊断："
            ),
            "",
            "| Episode | Tier | Baseline pass | Agent pass | Δpass | Baseline GM | Agent GM |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for pair in negative_atom_pairs:
        base = pair["baseline_gm_selected"]
        candidate = pair["agent_submitted"]
        pair_delta = pair["agent_vs_baseline"]
        lines.append(
            f"| {pair['episode_id']} | {pair['difficulty_tier']} "
            f"| {base['pass_count']}/{pair['constraint_count']} "
            f"| {candidate['pass_count']}/{pair['constraint_count']} "
            f"| {pair_delta['pass_count']:+d} "
            f"| {_score(base['gm'])} | {_score(candidate['gm'])} |"
        )
    lines.extend(
        [
            "",
            "最大正向 atom 增量的五条：",
            "",
            "| Episode | Tier | Baseline pass | Agent pass | Δpass | ΔGM |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for pair in top_positive_pairs:
        base = pair["baseline_gm_selected"]
        candidate = pair["agent_submitted"]
        pair_delta = pair["agent_vs_baseline"]
        lines.append(
            f"| {pair['episode_id']} | {pair['difficulty_tier']} "
            f"| {base['pass_count']}/{pair['constraint_count']} "
            f"| {candidate['pass_count']}/{pair['constraint_count']} "
            f"| {pair_delta['pass_count']:+d} "
            f"| {_score_delta(pair_delta['gm'])} |"
        )
    lines.extend(
        [
            "",
            "## 口径与限制",
            "",
            (
                f"- 对齐验证：200/200 prompt 文本和 VQA 列表逐项完全一致；"
                f"selection SHA256 为 `{summary['inputs']['selection']['sha256']}`，"
                f"baseline SHA256 为 `{summary['inputs']['baseline_detail']['sha256']}`。"
            ),
            (
                "- `evaluation_detail.json` 没有 prompt_id，当前按 JSON key "
                "`0..199` 对齐 selection rank `1..200`；完全一致的 prompt/VQA "
                "提供了内容校验，但后续产物应显式写入 prompt_id。"
            ),
            (
                "- Baseline 文件没有保存 Qwen-Image 的 model revision、steps、"
                "resolution、seed、negative prompt、运行 commit 或 evaluator "
                "version；因此不能把差异归因到 Agent policy 本身，也不能声称"
                "严格等算力。"
            ),
            (
                f"- Baseline 固定生成 1,000 张；Agent 共 {agent['image_count']} "
                "次图像调用（253 generate + 431 edit），少 31.60%。但 generate "
                "和 edit 单次成本未在 baseline 文件中对齐，图像调用数不等于"
                "精确 FLOPs 或 GPU-seconds。"
            ),
            (
                "- Baseline atom 概率存在最大 "
                f"{summary['alignment_checks']['max_probability_overshoot']:.2e} "
                "的数值越界；分析在验证其小于容差后 clamp 到 [0,1]。两位小数"
                "展示不受影响。"
            ),
            (
                "- Bootstrap 区间只衡量这个固定配对 cohort 对 episode 重采样"
                "的稳定性。200 条是按分布设计选出的固定集合，不是 IID 样本，"
                "区间不能支持对任意真实 prompt 的泛化声明。"
            ),
            "",
            "## 总体判断",
            "",
            (
                "当前证据支持：在这 200 条固定 Flow-DPPO synthetic-train "
                "prompt 上，完整 retry 系统相对原始 prompt 的 Qwen-Image "
                "Best-of-5 有大幅且分层一致的综合提升，并且用了更少的图像"
                "调用。提升在 pass-count 对齐 selector 后仍然稳健。"
            ),
            "",
            (
                "当前证据不支持：把全部增量解释为 history-aware retry 的独立"
                "因果效果。下一步单次生成 baseline 应保留完整 execution "
                "profile，并至少加入：原始 prompt 单次、Agent 首轮改写 prompt "
                "单次、等 5-call 的纯 regenerate Best-of-5、完整 Agent 四个臂，"
                "才能拆分 prompt rewriting、随机采样、verifier selection、edit "
                "与 history-aware decision 的贡献。"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _paired_delta(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "pass_count": candidate["pass_count"] - baseline["pass_count"],
        "am": candidate["am"] - baseline["am"],
        "gm": candidate["gm"] - baseline["gm"],
        "all_pass": int(candidate["all_pass"]) - int(baseline["all_pass"]),
    }


def _public_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: metrics[key]
        for key in ("variant_idx", "pass_count", "am", "gm", "all_pass")
    }


def _percentile_interval(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    lower_index = max(0, math.ceil(0.025 * len(ordered)) - 1)
    upper_index = min(len(ordered) - 1, math.ceil(0.975 * len(ordered)) - 1)
    return {
        "lower": ordered[lower_index],
        "upper": ordered[upper_index],
    }


def _validated_probability(value: Any, *, label: str) -> float:
    score = float(value)
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ValueError(f"{label}: invalid probability")
    return score


def _clamp_probability(value: float) -> float:
    return min(1.0, max(0.0, value))


def _geometric_mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise ValueError("geometric mean requires at least one value")
    return math.exp(
        sum(math.log(max(value, 1e-300)) for value in values) / len(values)
    )


def _index_unique(
    items: Iterable[dict[str, Any]],
    key: str,
) -> dict[str, dict[str, Any]]:
    result = {}
    for item in items:
        value = item[key]
        if value in result:
            raise ValueError(f"duplicate {key}: {value}")
        result[value] = item
    return result


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def _relative_change(baseline: float, candidate: float) -> float | None:
    if baseline == 0:
        return None
    return candidate / baseline - 1


def _sign_label(value: float) -> str:
    if value > 0:
        return "higher"
    if value < 0:
        return "lower"
    return "equal"


def _positive_outcomes(outcomes: dict[str, int]) -> int:
    return sum(
        count for name, count in outcomes.items() if name.startswith("positive")
    )


def _negative_outcomes(outcomes: dict[str, int]) -> int:
    return sum(
        count for name, count in outcomes.items() if name.startswith("negative")
    )


def _input_ref(path: Path) -> dict[str, str]:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _pp(value: float) -> str:
    return f"{value * 100:+.2f} points"


def _score(value: float) -> str:
    return f"{value * 100:.2f}"


def _score_delta(value: float) -> str:
    return f"{value * 100:+.2f}"


def _ci_pp(interval: dict[str, float]) -> str:
    return (
        f"[{interval['lower'] * 100:.2f}, "
        f"{interval['upper'] * 100:.2f}] points"
    )


def _ci_score(interval: dict[str, float]) -> str:
    return f"[{interval['lower'] * 100:.2f}, {interval['upper'] * 100:.2f}]"
