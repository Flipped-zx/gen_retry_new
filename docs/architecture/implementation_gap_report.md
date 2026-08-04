# Implementation Gap Report

> Historical Phase 0 snapshot. This file records the gap before Gate 1 and is
> not a statement of the current implementation. Use `docs/status.md` for the
> current phase and accepted ADRs for current protocol/backend semantics.

Phase 0 confirms that the local environment has the needed evidence roots and
runtime artifacts, but v3 runtime code is not implemented yet.

## Present

| Item | Evidence |
|---|---|
| v3 clean-room docs, schemas, examples, tasks | current repository |
| local path config | `configs/paths/local.yaml` |
| local model/API config by environment variable names | `configs/models/local.yaml` |
| Qianwen-Image-Edit runtime path | `/root/private_data/agentic_image/models/Qwen-Image-Edit-2511` |
| Geneval2 evaluator root | `/root/private_data/agentic_image/GenEval2` |
| legacy evidence for normalization, transitions, masking | Phase 0 inventory |

## Missing Before Gate 1

| Gap | Needed file(s) | Notes |
|---|---|---|
| Schema validation CLI | `src/gen_retry/cli/validate_schemas.py` | Must validate all versioned schemas. |
| Action parser/validator | `src/gen_retry/protocol/action_parser.py`, `tests/contract/test_action_protocol.py` | Strict JSON only; no semantic auto-repair. |
| TaskSpec builder from Geneval2 rows | `src/gen_retry/protocol/task_spec_builder.py` | Converts `vqa_list` and `skills` to immutable constraints. |
| Event schemas and parser tests | `schemas/episode_event_v0_2.schema.json`, contract tests | Check against module ownership. |
| Artifact ID contract | `src/gen_retry/domain/artifacts.py` or schema-only first | Include path, hash, media type, producer. |
| Event store/reducer design | docs plus tests before implementation | Needed for Phase 2 replay. |
| Planner view contract | `schemas/planner_view_v0_2.schema.json`, fixtures | Must expose best/latest/history without raw outputs. |

## Missing Before Live Pilots

| Gap | Needed file(s) | Notes |
|---|---|---|
| QianwenImageEditAdapter | `src/gen_retry/tools/qianwen_image_edit_adapter.py` | One backend, two logical modes. No live call in Phase 1. |
| Geneval2Adapter | `src/gen_retry/tools/geneval2_adapter.py` | External evaluator wrapper with artifact-backed output. |
| Idempotent runtime manifests | `src/gen_retry/runtime/*` | Request IDs, cache, artifact hashes, resume. |
| Five pilot runner and reports | Phase 3 files | Gate 2 only. |

## Config Cleanup Result

Tracked examples are templates only. Local machine values live in ignored files:

| File | Status | Purpose |
|---|---|---|
| `configs/paths/legacy_repos.example.yaml` | tracked template | placeholders only |
| `configs/models/local.example.yaml` | tracked template | environment variable names only |
| `configs/paths/local.yaml` | ignored local | absolute roots for this machine |
| `configs/models/local.yaml` | ignored local | model IDs and env-var names |

Secrets must be stored in environment variables, not YAML values.

## Conflicts

No authoritative v3 source conflict was found. The main architectural mismatch is
with legacy code: it uses prompt-regeneration actions and mutable trajectory JSON,
so it cannot be used directly for v3.
