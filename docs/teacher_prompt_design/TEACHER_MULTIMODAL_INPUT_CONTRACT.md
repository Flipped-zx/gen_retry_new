# Teacher Multimodal Input Contract v1

Date: 2026-07-15

## Purpose

Every Teacher decision must be made from the same evidence the environment owns: prompt, atom rubric, Geneval2 state, compact history, active Skill operators, tool affordances, remaining budget, and the relevant image pixels.

The Teacher must never make image decisions from a path string alone.

## Required Request Fields

Each Teacher request must include:

1. system prompt version and SHA-256;
2. original prompt;
3. atomic constraints with IDs;
4. latest Geneval2 atom results;
5. latest attempt summary;
6. best attempt summary;
7. compact attempt history;
8. fixed, regressed, persistent, and stable-pass state;
9. remaining budget;
10. active Skill operators;
11. tool capabilities;
12. `LATEST_IMAGE` as an actual multimodal image input when any attempt exists;
13. `BEST_IMAGE` as an actual multimodal image input when best differs from latest and is decision-relevant.

## Image Labels

Image text labels must precede image payloads in the same user message:

- `LATEST_IMAGE: attempt <attempt_id>, artifact <artifact_id>`
- `BEST_IMAGE: attempt <attempt_id>, artifact <artifact_id>`
- `BEST_IMAGE_SAME_AS_LATEST: attempt <attempt_id>, artifact <artifact_id>` when the same image is duplicated for role clarity.

The persisted sanitized request must record visible image role, attempt ID, artifact ID, and a path hash. It must not persist raw filesystem paths or credentials.

## Current Implementation

Implemented in `src/gen_retry/agent/teacher_client.py`.

The request now records:

- `system_prompt_version`;
- `system_prompt_sha256`;
- exact sanitized `teacher_text_input`;
- image role/attempt/artifact labels;
- path hashes instead of paths;
- retrieved Skill IDs and active operator summaries.

Focused tests:

- `tests/unit/test_teacher_prompt_contract.py`

## Non-Goals

- Do not store API keys, authorization headers, base URLs, or raw environment variables.
- Do not place raw assistant outputs in persistent memory.
- Do not put image paths into PlannerView.
