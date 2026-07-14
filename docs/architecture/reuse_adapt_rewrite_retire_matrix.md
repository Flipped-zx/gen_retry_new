# Reuse / Adapt / Rewrite / Retire Matrix

| Area | Evidence | Decision | Reason |
|---|---|---|---|
| Geneval2 atom-row loading | legacy `geneval2_result_normalizer.py`, Geneval2 `geneval2_data.jsonl` | Adapt | Field meanings are useful, but v3 needs schema-owned constraints and event payloads. |
| Geneval2 runtime entry | Geneval2 `evaluation.py` | Adapt | Wrap as external evaluator; do not copy CC BY-NC code into v3 core. |
| Qianwen-Image-Edit adapter | legacy `qwen_image_edit_adapter.py`, Qwen runtime `README.md`, `model_index.json` | Rewrite | Legacy adapter is scaffolded and still has regenerate semantics; v3 requires `generate` and `edit` through one adapter. |
| Attempt transition sets | legacy `_transition_sets`, `compute_transition` | Adapt | Correct concepts; v3 needs deterministic reducer from immutable events. |
| Best-so-far | legacy `_best_attempt`, `build_memory` | Adapt | Environment-owned fact; use as reducer logic, not planner target. |
| Offline package handoff | legacy `process_generation_package`, `CandidateJob` manifests | Adapt | Useful idempotent package pattern; v3 should replay events instead of mutating trajectory JSON. |
| Skill retrieval | GenEvolve `KnowledgeTool`, local `skills/*/SKILL.md` | Adapt | Must be a real `query_skill -> tool_response` event. |
| Tool-call/message trajectory | Gen-Searcher `Step` / `Trajectory`, GenEvolve `messages` | Rewrite | Useful separation concept, but raw chats are not v3 memory. |
| Observation masking | Gen-Searcher token masks, legacy masked SFT script | Adapt later | Phase 4 evidence only; no SFT exporter in Phase 1. |
| Artifact IDs | Gen-Searcher/GenEvolve `ImageIdManager` | Adapt | Stable display IDs and private path/source mapping fit v3 artifacts. |
| Web search / image search | Gen-Searcher and GenEvolve tools | Retire for v0.2 | Search/OOD grounding is outside the current main problem. |
| Legacy prompts and teacher free-form diagnostics | legacy teacher prompt/export paths | Retire | v3 assistant target is exactly one canonical action JSON. |
| Production imports from external repos | all external roots | Retire | Repository boundary forbids runtime dependencies on legacy/source roots. |

## Copying Policy

No implementation code is copied in Phase 0. Any future copy requires:

1. exact file path and commit;
2. exact license for that file/subtree;
3. an entry in `docs/SOURCE_LEDGER.md`;
4. adaptation behind a v3 module contract;
5. tests proving v3 semantics.
