from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


COUNT_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

VAGUE_PHRASES = [
    "fix the failed parts",
    "preserve all correct evidence",
    "make the image satisfy",
    "adjust as needed",
    "modify only the failed parts",
    "already-correct visual evidence",
]

TARGET_OPERATION_TERMS = [
    "add",
    "remove",
    "reposition",
    "move",
    "replace",
    "make",
    "show",
    "adjust",
    "keep",
]

SPATIAL_TERMS = [
    "behind",
    "in front",
    "foreground",
    "background",
    "left",
    "right",
    "above",
    "below",
    "center",
    "farther",
    "depth",
    "occluding",
    "oriented",
    "facing",
    "toward",
]

PRESERVATION_TERMS = ["preserve", "keep", "unchanged", "do not change", "remain"]
FORBIDDEN_CHANGE_TERMS = ["no extra", "do not add", "without adding", "no unrelated", "do not redraw"]
GLOBAL_REWRITE_TERMS = [
    "redraw the entire",
    "redraw the whole",
    "recreate the scene",
    "reconstruct the scene",
    "replace the whole",
    "entire scene",
]
CONTRADICTION_PATTERNS = [
    "toward/behind",
    "front/behind",
    "behind/in front",
]
RELATION_TERMS = [
    "behind",
    "in front of",
    "to the left of",
    "to the right of",
    "on top of",
    "left of",
    "right of",
    "above",
    "below",
    "inside",
    "on",
    "chasing",
    "following",
    "facing",
]
STOPWORDS = {
    "a",
    "an",
    "any",
    "are",
    "in",
    "is",
    "of",
    "on",
    "the",
    "there",
    "visible",
}


@dataclass(frozen=True)
class InstructionQualityReport:
    action: str
    verdict: str
    target_constraint_ids: list[str]
    preserve_constraint_ids: list[str]
    exact_count_coverage: list[dict[str, Any]]
    required_entity_coverage: list[dict[str, Any]]
    attribute_coverage: list[dict[str, Any]]
    spatial_grounding: dict[str, Any]
    semantic_blocks: dict[str, bool]
    forbidden_change_coverage: dict[str, Any]
    vague_language_flags: list[str]
    contradiction_flags: list[str]
    incompatible_count_flags: list[str]
    overbroad_edit_flags: list[str]
    unsupported_content_flags: list[str]
    preserve_modify_conflict_flags: list[str]
    source_attempt_consistency: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "verdict": self.verdict,
            "target_constraint_ids": self.target_constraint_ids,
            "preserve_constraint_ids": self.preserve_constraint_ids,
            "exact_count_coverage": self.exact_count_coverage,
            "required_entity_coverage": self.required_entity_coverage,
            "attribute_coverage": self.attribute_coverage,
            "spatial_grounding": self.spatial_grounding,
            "semantic_blocks": self.semantic_blocks,
            "forbidden_change_coverage": self.forbidden_change_coverage,
            "vague_language_flags": self.vague_language_flags,
            "contradiction_flags": self.contradiction_flags,
            "incompatible_count_flags": self.incompatible_count_flags,
            "overbroad_edit_flags": self.overbroad_edit_flags,
            "unsupported_content_flags": self.unsupported_content_flags,
            "preserve_modify_conflict_flags": self.preserve_modify_conflict_flags,
            "source_attempt_consistency": self.source_attempt_consistency,
            "notes": self.notes,
        }


def evaluate_instruction_quality(
    action: dict[str, Any],
    task_spec: dict[str, Any],
    *,
    known_attempt_ids: list[str] | None = None,
) -> InstructionQualityReport:
    action_type = action["action"]
    if action_type not in {"generate_image", "edit_image"}:
        raise ValueError(f"instruction quality only applies to image actions: {action_type}")
    args = action["arguments"]
    instruction = (
        args.get("instruction")
        or args.get("generation_instruction")
        or args.get("edit_instruction")
        or ""
    )
    text = instruction.lower()
    target_ids = list(args.get("target_constraint_ids", []))
    preserve_ids = list(args.get("preserve_constraint_ids", []))
    constraints = {
        constraint["constraint_id"]: constraint
        for constraint in task_spec.get("constraints", [])
    }
    target_constraints = [constraints[cid] for cid in target_ids if cid in constraints]
    preserve_constraints = [constraints[cid] for cid in preserve_ids if cid in constraints]
    instruction_constraints = (
        list(constraints.values())
        if action_type == "generate_image"
        else _unique_constraints(target_constraints + preserve_constraints)
    )

    count_coverage = _count_coverage(text, target_constraints)
    entity_coverage = _required_entity_coverage(text, instruction_constraints)
    attribute_coverage = _attribute_coverage(text, instruction_constraints)
    spatial_grounding = _spatial_grounding(text, target_constraints)
    forbidden_change_coverage = _forbidden_change_coverage(action_type, text, target_constraints)
    semantic_blocks = _semantic_blocks(
        action_type,
        text,
        preserve_ids,
        spatial_grounding,
        forbidden_change_coverage,
    )
    vague_flags = [phrase for phrase in VAGUE_PHRASES if phrase in text]
    contradiction_flags = _contradiction_flags(text)
    incompatible_count_flags = _incompatible_count_flags(
        text,
        target_constraints,
        context_constraints=list(constraints.values()),
    )
    overbroad_flags = _overbroad_flags(action_type, text)
    unsupported_flags = _unsupported_content_flags(text, task_spec)
    preserve_modify_conflict_flags = _preserve_modify_conflicts(
        text,
        target_constraints,
        preserve_constraints,
        target_ids,
        preserve_ids,
    )
    source_consistency = _source_attempt_consistency(action, known_attempt_ids or [])

    notes: list[str] = []
    if any(not item["covered"] for item in count_coverage):
        notes.append("missing exact count wording for one or more targeted count constraints")
    if any(not item["covered"] for item in entity_coverage):
        notes.append("missing required entity wording for one or more selected constraints")
    if any(not item["covered"] for item in attribute_coverage):
        notes.append("missing required attribute/entity binding")
    if spatial_grounding["required"] and not spatial_grounding["covered"]:
        notes.append("missing concrete spatial/orientation/depth grounding")
    if forbidden_change_coverage["required"] and not forbidden_change_coverage["covered"]:
        notes.append("missing forbidden-change or no-extra wording")
    if action_type == "edit_image":
        missing_blocks = [name for name, covered in semantic_blocks.items() if not covered]
        if missing_blocks:
            notes.append("edit instruction missing semantic blocks: " + ", ".join(missing_blocks))

    reject_reasons = (
        contradiction_flags
        + incompatible_count_flags
        + overbroad_flags
        + unsupported_flags
        + preserve_modify_conflict_flags
        + [f"missing entity: {item['entity']}" for item in entity_coverage if not item["covered"]]
        + [
            f"missing attribute binding: {item['entity']} {item['attribute']}"
            for item in attribute_coverage
            if not item["covered"]
        ]
        + [
            f"missing exact count: {item['constraint_id']}"
            for item in count_coverage
            if not item["covered"]
        ]
        + (
            ["missing forbidden-change wording"]
            if forbidden_change_coverage["required"] and not forbidden_change_coverage["covered"]
            else []
        )
        + (
            [
                "missing semantic block: " + name
                for name, covered in semantic_blocks.items()
                if action_type == "edit_image" and not covered
            ]
        )
        + ([] if source_consistency["known"] else ["unknown source_attempt_id"])
    )
    if reject_reasons:
        verdict = "reject"
    elif (
        vague_flags
        or unsupported_flags
        or any(not item["covered"] for item in count_coverage)
        or (spatial_grounding["required"] and not spatial_grounding["covered"])
        or any(not covered for covered in semantic_blocks.values())
    ):
        verdict = "warn"
    else:
        verdict = "pass"

    return InstructionQualityReport(
        action=action_type,
        verdict=verdict,
        target_constraint_ids=target_ids,
        preserve_constraint_ids=preserve_ids,
        exact_count_coverage=count_coverage,
        required_entity_coverage=entity_coverage,
        attribute_coverage=attribute_coverage,
        spatial_grounding=spatial_grounding,
        semantic_blocks=semantic_blocks,
        forbidden_change_coverage=forbidden_change_coverage,
        vague_language_flags=vague_flags,
        contradiction_flags=contradiction_flags,
        incompatible_count_flags=incompatible_count_flags,
        overbroad_edit_flags=overbroad_flags,
        unsupported_content_flags=unsupported_flags,
        preserve_modify_conflict_flags=preserve_modify_conflict_flags,
        source_attempt_consistency=source_consistency,
        notes=notes,
    )


def _count_coverage(text: str, constraints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for constraint in constraints:
        if constraint.get("constraint_type") != "count":
            continue
        expected = _expected_answer(constraint)
        expected_number = COUNT_WORDS.get(expected)
        entities = _constraint_entities(constraint)
        entity = entities[0] if entities else ""
        candidates = {expected}
        if expected_number is not None:
            candidates.add(str(expected_number))
        covered = False
        if entity:
            covered = any(
                _count_entity_present(text, candidate, entity)
                for candidate in candidates
            )
        else:
            covered = any(re.search(rf"\b{re.escape(candidate)}\b", text) for candidate in candidates)
        results.append(
            {
                "constraint_id": constraint["constraint_id"],
                "expected": expected,
                "entity": entity,
                "covered": covered,
            }
        )
    return results


def _required_entity_coverage(text: str, constraints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    results = []
    for constraint in constraints:
        for entity in _constraint_entities(constraint):
            key = (constraint["constraint_id"], entity)
            if key in seen:
                continue
            seen.add(key)
            results.append(
                {
                    "constraint_id": constraint["constraint_id"],
                    "entity": entity,
                    "covered": _term_present(text, entity),
                }
            )
    return results


def _attribute_coverage(text: str, constraints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for constraint in constraints:
        if constraint.get("constraint_type") != "attribute":
            continue
        entity, attribute = _attribute_terms(constraint)
        if not entity or not attribute:
            continue
        results.append(
            {
                "constraint_id": constraint["constraint_id"],
                "entity": entity,
                "attribute": attribute,
                "covered": _term_present(text, entity) and _term_present(text, attribute),
            }
        )
    return results


def _spatial_grounding(text: str, constraints: list[dict[str, Any]]) -> dict[str, Any]:
    required = any(
        constraint.get("constraint_type") in {"position", "verb"}
        for constraint in constraints
    )
    matched = [term for term in SPATIAL_TERMS if term in text]
    return {
        "required": required,
        "covered": (not required) or len(matched) >= 2,
        "matched_terms": matched,
    }


def _semantic_blocks(
    action_type: str,
    text: str,
    preserve_ids: list[str],
    spatial_grounding: dict[str, Any],
    forbidden_change_coverage: dict[str, Any],
) -> dict[str, bool]:
    if action_type == "generate_image":
        return {
            "target_operation": any(term in text for term in TARGET_OPERATION_TERMS),
            "spatial_grounding": spatial_grounding["covered"],
            "preservation_lock": True,
            "forbidden_changes": forbidden_change_coverage["covered"],
        }
    return {
        "target_operation": any(term in text for term in TARGET_OPERATION_TERMS),
        "spatial_grounding": spatial_grounding["covered"],
        "preservation_lock": (not preserve_ids) or any(term in text for term in PRESERVATION_TERMS),
        "forbidden_changes": forbidden_change_coverage["covered"],
    }


def _forbidden_change_coverage(
    action_type: str,
    text: str,
    target_constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    has_count_target = any(
        constraint.get("constraint_type") == "count"
        for constraint in target_constraints
    )
    required = action_type == "edit_image" or has_count_target
    matched = [term for term in FORBIDDEN_CHANGE_TERMS if term in text]
    matched.extend(
        term
        for term in ["duplicate", "duplicates", "cropped", "fused", "merged", "reflection", "reflected"]
        if term in text
    )
    return {
        "required": required,
        "covered": (not required) or bool(matched),
        "matched_terms": sorted(set(matched)),
    }


def _contradiction_flags(text: str) -> list[str]:
    flags = [pattern for pattern in CONTRADICTION_PATTERNS if pattern in text]
    regex_patterns = {
        "behind and in front": r"\bbehind\s+and\s+in front\b|\bin front\s+and\s+behind\b",
        "toward slash behind": r"\b(?:forward|toward)\b[^.]{0,40}/[^.]{0,40}\bbehind\b",
        "ambiguous alternative relation": r"\b(?:behind|in front of|above|below|left of|right of)\b\s+or\s+\b(?:behind|in front of|above|below|left of|right of|beside|near)\b",
    }
    for label, pattern in regex_patterns.items():
        if re.search(pattern, text):
            flags.append(label)
    return sorted(set(flags))


def _incompatible_count_flags(
    text: str,
    constraints: list[dict[str, Any]],
    *,
    context_constraints: list[dict[str, Any]] | None = None,
) -> list[str]:
    flags = []
    all_entities = {
        entity
        for constraint in (context_constraints or constraints)
        for entity in _constraint_entities(constraint)
    }
    for constraint in constraints:
        if constraint.get("constraint_type") != "count":
            continue
        expected = _expected_answer(constraint)
        expected_number = COUNT_WORDS.get(expected)
        entities = _constraint_entities(constraint)
        if expected_number is None or not entities:
            continue
        for entity in entities:
            for observed in sorted(
                _final_count_claims_for_entity(
                    text,
                    entity,
                    other_entities=all_entities - {entity},
                )
            ):
                if observed != expected_number:
                    flags.append(
                        f"{constraint['constraint_id']} expects {expected_number} {entity}, instruction says {observed}"
                    )
    return flags


def _preserve_modify_conflicts(
    text: str,
    target_constraints: list[dict[str, Any]],
    preserve_constraints: list[dict[str, Any]],
    target_ids: list[str],
    preserve_ids: list[str],
) -> list[str]:
    flags = []
    overlap = sorted(set(target_ids) & set(preserve_ids))
    if overlap:
        flags.append("same constraints targeted and preserved: " + ", ".join(overlap))
    target_entities = {
        entity
        for constraint in target_constraints
        for entity in _constraint_entities(constraint)
    }
    preserved_entities = {
        entity
        for constraint in preserve_constraints
        for entity in _constraint_entities(constraint)
    }
    for entity in sorted(target_entities & preserved_entities):
        variants = "|".join(re.escape(variant) for variant in _term_variants(entity))
        preserve_unchanged = re.search(
            rf"\b(?:preserve|keep)\b(?:\s+[a-z-]+){{0,6}}\s+"
            rf"(?:{variants})\b(?:\s+[a-z-]+){{0,4}}\s+unchanged\b",
            text,
        )
        modify_entity = re.search(
            rf"\b(?:remove|replace|change|reposition|move|adjust)\b[^.]*\b(?:{variants})\b",
            text,
        )
        if preserve_unchanged and modify_entity:
            flags.append(f"{entity} is requested as both unchanged and modified")
    return flags


def _overbroad_flags(action_type: str, text: str) -> list[str]:
    if action_type != "edit_image":
        return []
    flags = []
    for term in GLOBAL_REWRITE_TERMS:
        if term not in text:
            continue
        if (
            f"do not {term}" in text
            or f"no {term}" in text
            or re.search(rf"do not [^.]*\b{re.escape(term)}\b", text)
        ):
            continue
        flags.append(term)
    return flags


def _unsupported_content_flags(text: str, task_spec: dict[str, Any]) -> list[str]:
    del task_spec
    flags = []
    if "new " in text and not any(phrase in text for phrase in ["without adding", "do not add"]):
        flags.append("introduces new content wording")
    return flags


def _source_attempt_consistency(action: dict[str, Any], known_attempt_ids: list[str]) -> dict[str, Any]:
    if action["action"] != "edit_image":
        return {"required": False, "source_attempt_id": None, "known": True}
    source_attempt_id = action["arguments"].get("source_attempt_id")
    return {
        "required": True,
        "source_attempt_id": source_attempt_id,
        "known": source_attempt_id in known_attempt_ids,
    }


def _expected_answer(constraint: dict[str, Any]) -> str:
    requirement = constraint.get("requirement", "")
    _, _, tail = requirement.partition(":")
    return tail.strip().lower()


def _unique_constraints(constraints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for constraint in constraints:
        constraint_id = constraint["constraint_id"]
        if constraint_id in seen:
            continue
        seen.add(constraint_id)
        unique.append(constraint)
    return unique


def _constraint_entities(constraint: dict[str, Any]) -> list[str]:
    question = constraint.get("evaluator_question", "").strip().lower().rstrip("?")
    constraint_type = constraint.get("constraint_type")
    phrases: list[str] = []
    if constraint_type == "count":
        match = re.search(r"\bhow many\s+(.+?)\s+(?:are|is|can|do|does)\b", question)
        if match:
            phrases.append(match.group(1))
    elif constraint_type == "object":
        match = re.search(r"\bany\s+(.+?)\s+(?:in|on|visible|present|$)", question)
        if match:
            phrases.append(match.group(1))
    elif constraint_type == "attribute":
        entity, _ = _attribute_terms(constraint)
        if entity:
            phrases.append(entity)
    elif constraint_type in {"position", "verb"}:
        for relation in sorted(RELATION_TERMS, key=len, reverse=True):
            pattern = rf"\b(?:are|is)\s+the\s+(.+?)\s+{re.escape(relation)}\s+the\s+(.+)$"
            match = re.search(pattern, question)
            if match:
                phrases.extend([match.group(1), match.group(2)])
                break
    return _unique_terms(_noun_from_phrase(phrase) for phrase in phrases)


def _attribute_terms(constraint: dict[str, Any]) -> tuple[str, str]:
    question = constraint.get("evaluator_question", "").strip().lower().rstrip("?")
    match = re.search(r"\b(?:are|is)\s+the\s+(.+?)\s+([a-z][a-z-]*)$", question)
    if not match:
        return "", ""
    entity = _noun_from_phrase(match.group(1))
    attribute = _clean_term(match.group(2))
    if attribute in STOPWORDS:
        attribute = ""
    return entity, attribute


def _noun_from_phrase(phrase: str) -> str:
    words = [
        _clean_term(word)
        for word in re.findall(r"[a-z][a-z-]*", phrase.lower())
    ]
    words = [word for word in words if word and word not in STOPWORDS]
    return words[-1] if words else ""


def _clean_term(term: str) -> str:
    return term.strip("- ").lower()


def _unique_terms(terms: Any) -> list[str]:
    seen = set()
    unique = []
    for term in terms:
        if not term or term in seen:
            continue
        seen.add(term)
        unique.append(term)
    return unique


def _term_present(text: str, term: str) -> bool:
    return any(re.search(rf"\b{re.escape(variant)}\b", text) for variant in _term_variants(term))


def _term_variants(term: str) -> set[str]:
    variants = {term}
    if term.endswith("s") and len(term) > 3:
        variants.add(term[:-1])
    elif term:
        variants.add(term + "s")
    return variants


def _count_entity_present(text: str, count_word: str, entity: str) -> bool:
    variants = "|".join(re.escape(variant) for variant in _term_variants(entity))
    count = re.escape(count_word)
    return bool(
        re.search(rf"\b{count}\b(?:\s+[a-z-]+){{0,4}}\s+(?:{variants})\b", text)
        or re.search(rf"\b(?:{variants})\b(?:\s+[a-z-]+){{0,4}}\s+\b{count}\b", text)
    )


def _final_count_claims_for_entity(
    text: str,
    entity: str,
    *,
    other_entities: set[str] | None = None,
) -> set[int]:
    variants = "|".join(re.escape(variant) for variant in _term_variants(entity))
    count_pattern = "|".join([re.escape(word) for word in COUNT_WORDS] + [r"\d+"])
    claims = set()
    for match in re.finditer(
        rf"\b(?P<count>{count_pattern})\b(?:\s+[a-z-]+){{0,4}}\s+(?:{variants})\b",
        text,
    ):
        if not _is_explicit_final_count_claim(text, match.start(), match.end()):
            continue
        if any(
            _term_present(match.group(0), other_entity)
            for other_entity in (other_entities or set())
        ):
            continue
        if _is_nonfinal_count_context(text, match.start(), match.end()) or _is_relation_count_context(
            match.group(0)
        ):
            continue
        count = match.group("count")
        claims.add(int(count) if count.isdigit() else COUNT_WORDS[count])
    return claims


def _is_explicit_final_count_claim(text: str, start: int, end: int) -> bool:
    prefix = text[max(0, start - 20) : start]
    suffix = text[end : min(len(text), end + 16)]
    return bool(
        re.search(r"\bexactly\s*$", prefix)
        or re.search(r"\btotal(?:\s+number\s+of)?\s*$", prefix)
        or re.search(r"^\s+total\b", suffix)
    )


def _is_nonfinal_count_context(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 36) : min(len(text), end + 36)]
    return bool(
        re.search(
            r"\b(?:add|adding|remove|removing|additional|missing|existing|currently|"
            r"observed|added|rows?\s+of)\b",
            window,
        )
        or re.search(
            r"\b(?:upper|lower|top|bottom|first|second)\b[^.]{0,25}\brow\b",
            window,
        )
        or re.search(
            r"\bdo not\b[^.]{0,50}\b(?:leave|make|create|keep|show|contain)\b",
            window,
        )
    )


def _is_relation_count_context(match_text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:behind|in front|left|right|above|below|beside|toward|towards|chasing|following|facing)\b",
            match_text,
        )
    )


def _entity_terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))
