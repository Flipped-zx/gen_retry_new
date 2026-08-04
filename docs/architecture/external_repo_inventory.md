# External Repository Inventory

Phase 0 inspected the configured local roots from `configs/paths/local.yaml`.
The current v3 repository remains the only writable implementation root.

## Local Hierarchy

| Role | Path | Access |
|---|---|---|
| v3 implementation root | `/root/private_data/agentic_image/gen_retry_new` | writable |
| legacy Gen-Retry evidence | `/root/private_data/agentic_image/gen-retry` | read-only |
| Gen-Searcher evidence | `/root/private_data/agentic_image/Gen-Searcher` | read-only |
| GenEvolve evidence | `/root/private_data/agentic_image/GenEvolve` | read-only |
| Geneval2 evaluator | `/root/private_data/agentic_image/GenEval2` | read-only/runtime |
| Qianwen-Image-Edit runtime | `/root/private_data/agentic_image/models/Qwen-Image-Edit-2511` | read-only/runtime |

## Root Evidence

| Source | Repo status | Branch | Commit / version | Dirty status | License evidence | Copying assessment |
|---|---|---|---|---|---|---|
| Legacy Gen-Retry | Git repo; metadata read with per-command `safe.directory` | `main` | `2f03532e5f4685eafd2e47b23f14a3f2f8660aa3` | dirty, many tracked/untracked files | no root `LICENSE` found; vendored `GenEvolve/LICENSE` present | Do not copy code until file-level license is resolved. Reuse design evidence only for Phase 1. |
| Gen-Searcher | Git repo; metadata read by `source_researcher` with per-command `safe.directory` | `main` | `e5078d31859bafee6b6b610f0cd40095cc72e2a4` | mode-only dirty; tracked content matches HEAD | no top-level license; `Gen-DeepResearch-SFT/LICENSE` Apache-2.0, `Gen-DeepResearch-RL/LICENSE` MIT, vendored licenses vary | Do not copy wholesale. Interface ideas only unless exact subtree license is checked. |
| GenEvolve | Git repo; metadata read by `source_researcher` with per-command `safe.directory` | `main` | `23c847c559ccc0f95bbf4b3d8925898463822f4c` | mode-only dirty; tracked source and license content match HEAD | root `LICENSE` is Apache-2.0 | File-level evidence still applies; current audit permits grounded interface/implementation ideas without treating the repo as a runtime dependency. |
| Geneval2 | Git repo; metadata read with per-command `safe.directory` | `main` | `a6e82d2289e8d418f27f0adee77908b07060eea3` | dirty | `LICENSE`: CC BY-NC 4.0, copyright Meta Platforms | Use as evaluator/runtime evidence; do not copy code into v3 without noncommercial-license review. |
| Qianwen-Image-Edit runtime | model artifact directory, not treated as source repo | n/a | `model_index.json` class `QwenImageEditPlusPipeline` | n/a | `README.md` declares Apache-2.0 | Runtime path is configured locally; v3 adapter must not vendor model weights. |

## Inspected Paths

### Legacy Gen-Retry

| Path | Symbols / behavior | Phase 1 use |
|---|---|---|
| `src/gen_retry/evaluators/geneval2_adapter.py` | `Geneval2Adapter.evaluate`, `_evaluate_from_score_list`, `_select_report` | Adapt normalization contract only; v3 adapter must emit schema events. |
| `src/gen_retry/evaluators/geneval2_result_normalizer.py` | `normalize_geneval2_score_list`, `normalize_geneval2_row`, `load_geneval2_score_rows`, `_failure_type` | Reimplement atom-row normalization behind v3 `Geneval2Adapter`. |
| `src/gen_retry/generators/qwen_image_edit_adapter.py` | `QwenImageEditAdapter.edit`, `regenerate`; scaffold only | Retire scaffold shape; v3 needs one adapter with `generate` and `edit` logical modes. |
| `src/gen_retry/collectors/collect_episodes.py` | `EpisodeCollector`, `classify_transition`, `_state_memory`, `_best_attempt`, `_transition_sets` | Reuse transition concepts, not mutable collector structure. |
| `src/gen_retry/offline_planner.py` | `process_generation_package`, `build_memory`, `compute_transition`, `build_teacher_state`, `compact_retry_history` | Adapt offline package/resume ideas into event-sourced replay. |
| `src/gen_retry/collectors/qwen_geneval_batch.py` | `CandidateJob`, `QwenGenevalBatchCollector`, `format_command` | Reuse manifest/idempotent job planning pattern. |
| `scripts/build_geneval2_masked_multiturn_sft.py` | `should_unmask`, `build_conversation`, `validate_rows`, `stable_prompt_split` | Reuse masking checks as Phase 4 evidence; not Phase 1 runtime. |

### Gen-Searcher (`source_researcher`)

| Path | Symbols / behavior | Phase 1 use |
|---|---|---|
| `Gen-DeepResearch-RL/rllm/rllm/agents/agent.py` | `Step`, `Trajectory`, `to_dict`, `from_dict` | Inform event/message separation only. |
| `Gen-DeepResearch-RL/rllm/rllm/workflows/eval_protocol_workflow.py` | `msg_to_dict`, trajectory construction from messages | Inform tool observation vs assistant action separation. |
| `Gen-DeepResearch-RL/rllm/rllm/trainer/tinker/tinker_data_processor.py` | `build_datum_from_step`, `build_datum_from_trajectory`; prompt mask `0.0`, response mask `1.0` | Later SFT masking evidence. |
| `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/gen_image_deepresearch_workflow.py` | agent rollout before image generation/reward | Keep heavy image execution environment-owned. |
| `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/gen_image_deepresearch_reward.py` | `call_qwen_edit_to_generate_image`, `_sanitize_messages_for_save`, `save_generated_image`, `save_trajectory_result` | Use artifact-path provenance; avoid base64 in persisted memory. |
| `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/gen_image_deepresearch_agent.py` | `SYSTEM_PROMPT_GEN_IMAGE`, `ImageIdManager`, tool manifest | Stable artifact IDs and one-action discipline. |
| `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/tools/shared.py` | `CACHE_CONFIG`, `AsyncCacheDB`, `get_cache_key`, `get_cache_async`, `set_cache_async` | Cache design reference only. |

### GenEvolve (`source_researcher`)

| Path | Symbols / behavior | Phase 1 use |
|---|---|---|
| `genevolve/agent.py` | `ImageIdManager`, `_parse_tool_call`, `_parse_answer`, `GenEvolveResult.to_dict`, `_finalize_answer` | Stable image refs; avoid raw chat as v3 memory. |
| `genevolve/system_prompt.py` | `SYSTEM_PROMPT`, `FINAL_STEP_MESSAGE` | One tool call or answer per round as policy inspiration. |
| `genevolve/knowledge_tool.py` | `SKILL_NAMES`, `SkillBank`, `KnowledgeTool.TOOL_DEFINITION`, `KnowledgeTool.call` | Implement v3 `query_skill -> tool_response` interaction. |
| `genevolve/tools/web_search.py` | `WebTextSearchTool`, `ImageSearchTool`, `_local_path_for` | Artifact cache/provenance pattern. |
| `genevolve/generator.py` | `QwenImageEditGenerator.generate`, `QwenImageEditServiceGenerator.generate` | Confirms Qwen Image Edit usage, but v3 must own adapter contract. |
| `scripts/run_agent.py`, `scripts/generate_images.py`, `scripts/evaluate_images.py` | incremental result files and evaluator `--resume` | Use artifact-backed execution idea, not raw result JSON as truth. |

### Geneval2

| Path | Symbols / behavior | Phase 1 use |
|---|---|---|
| `evaluation.py` | `construct_message_with_image`, `send_message_with_image`, `vqa_score`, `tifa`, `soft_tifa`, `main` | Wrap as external evaluator command/runtime only. |
| `geneval2_data.jsonl` | prompt, `atom_count`, `vqa_list`, `skills` | Build `TaskSpec` constraints. |
| `soft_tifa_analysis.py` | `per_skill_analysis` | Optional reporting only. |

### Qianwen-Image-Edit Runtime

| Path | Evidence | Phase 1 use |
|---|---|---|
| `README.md` | `QwenImageEditPlusPipeline` quick start with `image`, `prompt`, seed, cfg, steps | Adapter implementation evidence. |
| `model_index.json` | `_class_name`: `QwenImageEditPlusPipeline`; diffusers components | Local model-path config evidence. |

## Boundary Confirmation

No external repository was modified by Phase 0. The only write operations were inside
`/root/private_data/agentic_image/gen_retry_new`.
