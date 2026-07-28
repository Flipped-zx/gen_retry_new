from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


FLOW_DPPO_COMMIT = "e1a814ff9de6de644b093c6ed0106869c1881e53"
FLOW_DPPO_DATASET_REF = "datasets/geneval2/synthetic/train.jsonl"
DEFAULT_TIER_COUNTS = {"hard": 12, "medium": 5, "easy": 3}

_RELATION_PHRASES = (
    "jumping over",
    "playing with",
    "chasing",
    "in front of",
    "to the right of",
    "to the left of",
    "on top of",
    "behind",
    "under",
)
_COUNT_VALUES = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
}


def select_flow_dppo_prompts(
    dataset_path: Path,
    *,
    heldout_dataset_path: Path | None = None,
    tier_counts: dict[str, int] | None = None,
    source_commit: str = FLOW_DPPO_COMMIT,
) -> dict[str, Any]:
    counts = dict(tier_counts or DEFAULT_TIER_COUNTS)
    if set(counts) != {"hard", "medium", "easy"}:
        raise ValueError("tier_counts must define hard, medium, and easy")
    if any(value <= 0 for value in counts.values()):
        raise ValueError("all tier counts must be positive")

    rows, source_sha256 = _load_rows(dataset_path)
    boundary = _heldout_boundary(rows, heldout_dataset_path)
    eligible_rows = [
        row
        for row in rows
        if row["prompt"].strip().lower() not in boundary["heldout_prompts"]
        and row["_semantic_family_id"] not in boundary["heldout_family_ids"]
    ]
    pools: dict[str, list[dict[str, Any]]] = {"hard": [], "medium": [], "easy": []}
    for row in eligible_rows:
        tier = _difficulty_tier(row)
        if tier is not None:
            pools[tier].append(row)

    selected_rows: list[dict[str, Any]] = []
    for tier in ("hard", "medium", "easy"):
        if len(pools[tier]) < counts[tier]:
            raise ValueError(
                f"need {counts[tier]} {tier} rows, found {len(pools[tier])}"
            )
        selected_rows.extend(
            _select_tier(
                pools[tier],
                count=counts[tier],
                already_selected=selected_rows,
            )
        )

    selected_prompts = [
        _candidate_from_row(
            row,
            selection_rank=index,
            source_commit=source_commit,
            source_file_sha256=source_sha256,
        )
        for index, row in enumerate(selected_rows, start=1)
    ]
    return {
        "schema_version": "0.2",
        "selection_method": "flow_dppo_geneval2_hard_heavy_deterministic_v1",
        "selected_count": len(selected_prompts),
        "tier_counts": counts,
        "source": {
            "repository": "Tencent-Hunyuan/UniRL",
            "commit": source_commit,
            "dataset_ref": FLOW_DPPO_DATASET_REF,
            "dataset_sha256": source_sha256,
            "dataset_row_count": len(rows),
            "atom_vqa_count_mismatch_rows": sum(
                int(row.get("atom_count", 0)) != len(row["vqa_list"])
                for row in rows
            ),
            "official_800_held_out": True,
            "heldout_dataset_ref": boundary["heldout_dataset_ref"],
            "heldout_dataset_sha256": boundary["heldout_dataset_sha256"],
            "heldout_row_count": boundary["heldout_row_count"],
            "exact_prompt_overlap_rows_excluded": boundary[
                "exact_prompt_overlap_rows"
            ],
            "semantic_family_overlap_rows_excluded": boundary[
                "semantic_family_overlap_rows"
            ],
            "eligible_training_rows": len(eligible_rows),
            "semantic_family_definition": (
                "ordered relation/action phrases + ordered skills + actual VQA count"
            ),
        },
        "selected_prompts": selected_prompts,
        "coverage": _coverage(selected_prompts),
    }


def selection_report(payload: dict[str, Any]) -> str:
    coverage = payload["coverage"]
    lines = [
        "# Flow-DPPO Geneval2 20-Prompt Selection",
        "",
        "## Policy",
        "",
        f"- Source: `Tencent-Hunyuan/UniRL@{payload['source']['commit']}`",
        f"- Dataset: `{payload['source']['dataset_ref']}`",
        f"- Source rows: {payload['source']['dataset_row_count']}",
        (
            "- Rows where `atom_count != len(vqa_list)`: "
            f"{payload['source']['atom_vqa_count_mismatch_rows']}"
        ),
        "- Official 800-row Geneval2 test set remains held out.",
        (
            "- Held-out boundary: exact prompt overlaps excluded="
            f"{payload['source']['exact_prompt_overlap_rows_excluded']}; "
            "semantic-family overlaps excluded="
            f"{payload['source']['semantic_family_overlap_rows_excluded']}."
        ),
        (
            "- Tier mix: "
            + ", ".join(
                f"{tier}={count}"
                for tier, count in payload["tier_counts"].items()
            )
        ),
        "- Selection is deterministic and uses metadata/semantic diversity only; no live image result is used.",
        "",
        "## Coverage",
        "",
        f"- Selected prompts: {payload['selected_count']}",
        f"- Distinct entities: {coverage['distinct_entity_count']}",
        f"- Relation/action phrases: {', '.join(coverage['relation_phrases'])}",
        (
            "- Constraint atoms: "
            + ", ".join(
                f"{key}={value}"
                for key, value in coverage["constraint_type_histogram"].items()
            )
        ),
        "",
        "## Selected Rows",
        "",
        "| Rank | Tier | Source line | Atoms/VQAs | Prompt |",
        "|---:|---|---:|---:|---|",
    ]
    for candidate in payload["selected_prompts"]:
        prompt = candidate["original_prompt"].replace("|", "\\|")
        lines.append(
            f"| {candidate['selection_rank']} | {candidate['difficulty_tier']} | "
            f"{candidate['source_line']} | {candidate['atom_count']}/"
            f"{candidate['constraint_count']} | {prompt} |"
        )
    lines.extend(
        [
            "",
            "Each selected record in the JSON artifact retains the original `vqa_list`, "
            "`skills`, normalized atomic constraints, score components, source line, "
            "row hash, and dataset hash.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_rows(dataset_path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = dataset_path.read_bytes()
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw.splitlines(), start=1):
        if not raw_line.strip():
            continue
        row = json.loads(raw_line)
        if not isinstance(row.get("prompt"), str):
            raise ValueError(f"row {line_number} has no prompt")
        if not isinstance(row.get("vqa_list"), list) or not row["vqa_list"]:
            raise ValueError(f"row {line_number} has no vqa_list")
        if len(row.get("skills", [])) != len(row["vqa_list"]):
            raise ValueError(f"row {line_number} has misaligned skills and vqa_list")
        rows.append(
            {
                **row,
                "_source_line": line_number,
                "_row_sha256": hashlib.sha256(raw_line).hexdigest(),
                "_features": _features(row),
            }
        )
        rows[-1]["_semantic_family_id"] = _semantic_family_id(rows[-1])
    return rows, hashlib.sha256(raw).hexdigest()


def _heldout_boundary(
    train_rows: list[dict[str, Any]],
    heldout_dataset_path: Path | None,
) -> dict[str, Any]:
    if heldout_dataset_path is None:
        return {
            "heldout_prompts": set(),
            "heldout_family_ids": set(),
            "heldout_dataset_ref": None,
            "heldout_dataset_sha256": None,
            "heldout_row_count": 0,
            "exact_prompt_overlap_rows": 0,
            "semantic_family_overlap_rows": 0,
        }
    heldout_rows, heldout_sha256 = _load_rows(heldout_dataset_path)
    heldout_prompts = {
        row["prompt"].strip().lower()
        for row in heldout_rows
    }
    heldout_family_ids = {
        row["_semantic_family_id"]
        for row in heldout_rows
    }
    exact_prompt_overlap_rows = sum(
        row["prompt"].strip().lower() in heldout_prompts
        for row in train_rows
    )
    semantic_family_overlap_rows = sum(
        row["_semantic_family_id"] in heldout_family_ids
        for row in train_rows
    )
    return {
        "heldout_prompts": heldout_prompts,
        "heldout_family_ids": heldout_family_ids,
        "heldout_dataset_ref": str(heldout_dataset_path),
        "heldout_dataset_sha256": heldout_sha256,
        "heldout_row_count": len(heldout_rows),
        "exact_prompt_overlap_rows": exact_prompt_overlap_rows,
        "semantic_family_overlap_rows": semantic_family_overlap_rows,
    }


def _difficulty_tier(row: dict[str, Any]) -> str | None:
    atom_count = int(row.get("atom_count", 0))
    vqa_count = len(row["vqa_list"])
    features = row["_features"]
    has_relation = bool(features["relation_phrases"])
    if atom_count >= 9 and vqa_count >= 10 and has_relation:
        return "hard"
    if 7 <= atom_count <= 8 and 8 <= vqa_count <= 10 and has_relation:
        return "medium"
    if atom_count <= 5 and vqa_count <= 7 and has_relation:
        return "easy"
    return None


def _select_tier(
    pool: list[dict[str, Any]],
    *,
    count: int,
    already_selected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected = list(already_selected)
    winners: list[dict[str, Any]] = []
    for _ in range(count):
        winner_lines = {item["_source_line"] for item in winners}
        candidates = [
            _score(row, selected)
            for row in pool
            if row["_source_line"] not in winner_lines
        ]
        candidates.sort(
            key=lambda item: (
                item["_selection_score"],
                item["_base_difficulty"],
                -item["_source_line"],
            ),
            reverse=True,
        )
        winner = candidates[0]
        winners.append(winner)
        selected.append(winner)
    return winners


def _score(row: dict[str, Any], selected: list[dict[str, Any]]) -> dict[str, Any]:
    features = row["_features"]
    selected_relations = {
        relation
        for item in selected
        for relation in item["_features"]["relation_phrases"]
    }
    selected_entities = {
        entity
        for item in selected
        for entity in item["_features"]["entities"]
    }
    selected_types = {
        skill
        for item in selected
        for skill in item["_features"]["skill_types"]
    }
    base = (
        int(row.get("atom_count", 0)) * 6
        + len(row["vqa_list"]) * 4
        + len(features["skill_types"]) * 4
        + features["verb_count"] * 12
        + features["position_count"] * 8
        + features["high_count_atoms"] * 2
    )
    new_relations = sorted(features["relation_phrases"] - selected_relations)
    new_entities = sorted(features["entities"] - selected_entities)
    new_types = sorted(features["skill_types"] - selected_types)
    repeated_entities = sorted(features["entities"] & selected_entities)
    novelty = (
        len(new_relations) * 24
        + min(len(new_entities), 3) * 5
        + len(new_types) * 8
    )
    overlap_penalty = len(repeated_entities) * 7
    selection_score = base + novelty - overlap_penalty
    return {
        **row,
        "_base_difficulty": base,
        "_selection_score": selection_score,
        "_selection_reason": {
            "base_difficulty": base,
            "new_relation_phrases": new_relations,
            "new_entities": new_entities,
            "new_skill_types": new_types,
            "repeated_entities": repeated_entities,
            "novelty_bonus": novelty,
            "entity_overlap_penalty": overlap_penalty,
        },
    }


def _features(row: dict[str, Any]) -> dict[str, Any]:
    prompt = row["prompt"].lower()
    relations = {
        phrase for phrase in _RELATION_PHRASES if phrase in prompt
    }
    skills = {str(skill) for skill in row.get("skills", [])}
    entities = set()
    high_count_atoms = 0
    for item in row["vqa_list"]:
        if not (isinstance(item, list) and len(item) == 2):
            continue
        question, answer = str(item[0]), str(item[1]).lower()
        entity = _entity_from_question(question)
        if entity:
            entities.add(entity)
        if _COUNT_VALUES.get(answer, 0) >= 4:
            high_count_atoms += 1
    return {
        "relation_phrases": relations,
        "entities": entities,
        "skill_types": skills,
        "verb_count": sum(skill == "verb" for skill in row.get("skills", [])),
        "position_count": sum(skill == "position" for skill in row.get("skills", [])),
        "high_count_atoms": high_count_atoms,
    }


def _semantic_family_id(row: dict[str, Any]) -> str:
    prompt = row["prompt"].lower()
    ordered_relations = sorted(
        (
            (prompt.find(phrase), phrase)
            for phrase in _RELATION_PHRASES
            if phrase in prompt
        )
    )
    payload = {
        "ordered_relation_phrases": [phrase for _, phrase in ordered_relations],
        "ordered_skills": [str(skill) for skill in row.get("skills", [])],
        "actual_vqa_count": len(row["vqa_list"]),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sf_{hashlib.sha256(encoded).hexdigest()[:16]}"


def _entity_from_question(question: str) -> str | None:
    patterns = (
        r"^How many (.+?) (?:are|is) in the image\?$",
        r"^Are there any (.+?) in the image\?$",
        r"^Is there any (.+?) in the image\?$",
    )
    for pattern in patterns:
        match = re.match(pattern, question, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower().strip()
    return None


def _candidate_from_row(
    row: dict[str, Any],
    *,
    selection_rank: int,
    source_commit: str,
    source_file_sha256: str,
) -> dict[str, Any]:
    prompt_hash = hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest()
    skills = [str(skill) for skill in row["skills"]]
    histogram = dict(sorted(Counter(skills).items()))
    tier = _difficulty_tier(row)
    if tier is None:
        raise ValueError("selected row has no difficulty tier")
    constraints = []
    for index, (item, skill) in enumerate(zip(row["vqa_list"], skills), start=1):
        if not (isinstance(item, list) and len(item) == 2):
            raise ValueError(f"unsupported VQA atom in source line {row['_source_line']}")
        question, expected = str(item[0]), str(item[1])
        constraints.append(
            {
                "constraint_id": f"c_{index:03d}",
                "constraint_type": skill,
                "requirement": f"Expected answer: {expected}",
                "evaluator_question": question,
                "priority": 3,
            }
        )
    features = row["_features"]
    return {
        "schema_version": "0.2",
        "candidate_id": f"flow_dppo_{row['_source_line']:05d}_{prompt_hash[:12]}",
        "prompt_id": f"flow_dppo_train_{row['_source_line']:05d}_{prompt_hash[:12]}",
        "selection_rank": selection_rank,
        "difficulty_tier": tier,
        "selection_score": row["_selection_score"],
        "selection_reason": row["_selection_reason"],
        "source_line": row["_source_line"],
        "source_row_sha256": row["_row_sha256"],
        "semantic_family_id": row["_semantic_family_id"],
        "atom_count": int(row["atom_count"]),
        "original_prompt": row["prompt"],
        "vqa_list": row["vqa_list"],
        "skills": skills,
        "atomic_constraints": constraints,
        "constraint_count": len(constraints),
        "constraint_type_histogram": histogram,
        "constraint_type_combination": sorted(histogram),
        "semantic_features": {
            "entities": sorted(features["entities"]),
            "relation_phrases": sorted(features["relation_phrases"]),
            "high_count_atoms": features["high_count_atoms"],
        },
        "baseline_difficulty_evidence": {
            "difficulty_source": "Flow-DPPO committed metadata only; no live image result used",
            "atom_count": int(row["atom_count"]),
            "vqa_constraint_count": len(row["vqa_list"]),
        },
        "provenance": {
            "source": "flow_dppo_geneval2_synthetic_train",
            "repository": "https://github.com/Tencent-Hunyuan/UniRL",
            "commit": source_commit,
            "source_ref": (
                f"UniRL@{source_commit}:{FLOW_DPPO_DATASET_REF}:"
                f"{row['_source_line']}"
            ),
            "source_file_sha256": source_file_sha256,
            "source_row_sha256": row["_row_sha256"],
            "official_test_set_held_out": True,
        },
    }


def _coverage(selected: list[dict[str, Any]]) -> dict[str, Any]:
    histogram: Counter[str] = Counter()
    entities: set[str] = set()
    relations: set[str] = set()
    tiers: Counter[str] = Counter()
    for candidate in selected:
        histogram.update(candidate["constraint_type_histogram"])
        entities.update(candidate["semantic_features"]["entities"])
        relations.update(candidate["semantic_features"]["relation_phrases"])
        tiers[candidate["difficulty_tier"]] += 1
    return {
        "tier_histogram": dict(sorted(tiers.items())),
        "constraint_type_histogram": dict(sorted(histogram.items())),
        "distinct_entity_count": len(entities),
        "entities": sorted(entities),
        "relation_phrases": sorted(relations),
    }
