# SOURCE_LEDGER

This ledger records external evidence that is already grounded. Do not repeat
broad searches unless a source changes. Code copying still requires file-level
license evidence and a v3 module-contract adaptation.

## Phase 0 Repository Evidence

### Legacy Gen-Retry

source_name: Legacy Gen-Retry
repository_url: local only
absolute_path: `/root/private_data/agentic_image/gen-retry`
commit_hash: `2f03532e5f4685eafd2e47b23f14a3f2f8660aa3`
branch: `main`
dirty_status: dirty, many tracked/untracked files
license: no root license found during Phase 0
evidence_type: repository-grounded
exact_paths:
- path: `src/gen_retry/evaluators/geneval2_adapter.py`
  symbol: `Geneval2Adapter.evaluate`
- path: `src/gen_retry/evaluators/geneval2_result_normalizer.py`
  symbol: `normalize_geneval2_score_list`, `normalize_geneval2_row`, `load_geneval2_score_rows`
- path: `src/gen_retry/collectors/collect_episodes.py`
  symbol: `classify_transition`, `_state_memory`, `_best_attempt`, `_transition_sets`
- path: `src/gen_retry/offline_planner.py`
  symbol: `process_generation_package`, `build_memory`, `compute_transition`, `build_teacher_state`
- path: `scripts/build_geneval2_masked_multiturn_sft.py`
  symbol: `should_unmask`, `build_conversation`, `validate_rows`
borrowed_idea: Geneval2 atom normalization, transition sets, best-so-far, offline manifests, masking checks.
local_adaptation: Reimplement behind v3 schemas, event store, reducer, and strict action protocol.
copy_code: no
notes: Legacy action names and mutable trajectory JSON conflict with v3.

### Gen-Searcher

source_name: Gen-Searcher
repository_url: local checkout, no single top-level license found
absolute_path: `/root/private_data/agentic_image/Gen-Searcher`
commit_hash: `e5078d31859bafee6b6b610f0cd40095cc72e2a4`
branch: `main`
dirty_status: dirty
license: mixed; `Gen-DeepResearch-RL/LICENSE` MIT, `Gen-DeepResearch-SFT/LICENSE` Apache-2.0
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `Gen-DeepResearch-RL/rllm/rllm/agents/agent.py`
  symbol: `Step`, `Trajectory`
- path: `Gen-DeepResearch-RL/rllm/rllm/workflows/eval_protocol_workflow.py`
  symbol: `msg_to_dict`
- path: `Gen-DeepResearch-RL/rllm/rllm/trainer/tinker/tinker_data_processor.py`
  symbol: `build_datum_from_step`, `build_datum_from_trajectory`
- path: `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/gen_image_deepresearch_reward.py`
  symbol: `_sanitize_messages_for_save`, `save_generated_image`, `save_trajectory_result`
- path: `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/gen_image_deepresearch_agent.py`
  symbol: `ImageIdManager`, `SYSTEM_PROMPT_GEN_IMAGE`
borrowed_idea: Separate assistant action targets from observations; store artifact paths not base64; keep heavy image generation/scoring environment-owned.
local_adaptation: Use immutable v3 events and deterministic reducers instead of result JSON as replay truth.
copy_code: no
notes: Search/OOD workflow is outside v0.2.

### GenEvolve

source_name: GenEvolve
repository_url: local checkout
absolute_path: `/root/private_data/agentic_image/GenEvolve`
commit_hash: `23c847c559ccc0f95bbf4b3d8925898463822f4c`
branch: `main`
dirty_status: dirty, including `LICENSE`
license: working-tree `LICENSE` is Apache-2.0; verify before copying
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `genevolve/agent.py`
  symbol: `ImageIdManager`, `_parse_tool_call`, `_parse_answer`, `GenEvolveResult.to_dict`, `_finalize_answer`
- path: `genevolve/knowledge_tool.py`
  symbol: `SkillBank`, `KnowledgeTool.TOOL_DEFINITION`, `KnowledgeTool.call`
- path: `genevolve/system_prompt.py`
  symbol: `SYSTEM_PROMPT`, `FINAL_STEP_MESSAGE`
- path: `genevolve/generator.py`
  symbol: `QwenImageEditGenerator.generate`, `QwenImageEditServiceGenerator.generate`
borrowed_idea: Real skill/tool retrieval and stable image reference provenance.
local_adaptation: v3 skill use must be `query_skill -> tool_response`; raw messages do not become memory.
copy_code: no
notes: Runtime serializes raw chat messages and lacks v3 event/reducer semantics.

### Geneval2

source_name: Geneval2
repository_url: local checkout
absolute_path: `/root/private_data/agentic_image/GenEval2`
commit_hash: `a6e82d2289e8d418f27f0adee77908b07060eea3`
branch: `main`
dirty_status: dirty
license: CC BY-NC 4.0
evidence_type: repository-grounded
exact_paths:
- path: `evaluation.py`
  symbol: `construct_message_with_image`, `send_message_with_image`, `vqa_score`, `tifa`, `soft_tifa`, `main`
- path: `geneval2_data.jsonl`
  symbol: `prompt`, `atom_count`, `vqa_list`, `skills`
borrowed_idea: Atom-level VQA verifier and benchmark metadata.
local_adaptation: Wrap as evaluator; build v3 `TaskSpec` constraints from benchmark rows.
copy_code: no
notes: Treat code as external runtime under noncommercial license.

### Qianwen-Image-Edit Runtime

source_name: Qianwen-Image-Edit-2511 local runtime
repository_url: local model artifact
absolute_path: `/root/private_data/agentic_image/models/Qwen-Image-Edit-2511`
commit_hash: n/a
license: README declares Apache-2.0
evidence_type: repository-grounded local runtime
exact_paths:
- path: `README.md`
  symbol: `QwenImageEditPlusPipeline` quick start
- path: `model_index.json`
  symbol: `_class_name = QwenImageEditPlusPipeline`
borrowed_idea: One local Qianwen-Image-Edit backend can support edit-style calls.
local_adaptation: v3 exposes logical `generate_image` and `edit_image` through one `QianwenImageEditAdapter`.
copy_code: no
notes: Do not vendor weights or store secrets in config.

## Phase 3 Source Evidence

### Legacy Gen-Retry Diagnostic/Action Records

source_name: Legacy Gen-Retry Phase 3 counterfactual evidence
repository_url: local only
absolute_path: `/root/private_data/agentic_image/gen-retry`
commit_hash: `2f03532e5f4685eafd2e47b23f14a3f2f8660aa3`
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `data/trajectories/geneval2_balanced100x5_normal_round0_4_master_trajectories.jsonl`
  fields: `trajectory_id`, `prompt_id`, `original_prompt`, `attempts`, `teacher_action`, `normalized_report`, `transition_from_previous`, `final_status`, `unresolved`
- path: `data/trajectories/geneval2_balanced100x5_normal_round0_4_action_candidates.jsonl`
  fields: `sample_id`, `task_type`, `input_state`, `target_action`, `outcome_after_action`, `include_in_clean_sft`
- path: `data/exchange/gpu_to_api/*`
  fields: `diagnostic_jobs`, `generation_manifest`, `normalized_reports`, atom rows
- path: `data/exchange/api_to_gpu/*/generation_metadata.jsonl`
  fields: `previous_action`, `previous_score`, `previous_failure_types`, `vqa_list`, `skills`, `skill_counts`
borrowed_idea: Historical failure signatures, retry depth, unresolved status, and counterfactual edit-plausibility evidence for prompt selection and analysis.
local_adaptation: Converted to `artifacts/phase3/legacy_diagnostic_action_analysis.jsonl` as counterfactual evidence only.
copy_code: no
notes: Legacy actions/images/attempts are not current-protocol positive SFT targets and are not imported into Phase 3 episodes.

### Geneval2 Prompt Candidate Pool

source_name: Geneval2 prompt metadata for Phase 3 fresh candidate pool
repository_url: local checkout
absolute_path: `/root/private_data/agentic_image/GenEval2`
commit_hash: `a6e82d2289e8d418f27f0adee77908b07060eea3`
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `geneval2_data.jsonl`
  fields: `prompt`, `atom_count`, `vqa_list`, `skills`
- path: `README.md`
  fields: dataset field description
borrowed_idea: Use all 800 Geneval2 prompts as fresh candidate prompts; preserve actual skill taxonomy as v0.2 `constraint_type`.
local_adaptation: Built `artifacts/phase3/candidate_pool.jsonl`, then deterministic selected ten prompts before any live rollout.
copy_code: no
notes: Actual skill taxonomy is `attribute`, `count`, `object`, `position`, `verb`; no invented categories.

## Prior Broad Notes

| Source | Evidence | Borrowed idea | Not reused directly | Status |
|---|---|---|---|---|
| GenAgent paper | paper-grounded | Image observation and assistant action interleaving; environment image tokens are not agent targets | Free-form self-judge and prompt rewrite; no atom verifier | Keep as background only |
| GEMS paper | paper-grounded | Compressed memory beats raw thought; skill/memory engineering | History-conditioned rewrite with high free-text ratio | Keep as background only |
| RS-Gen paper | paper-grounded | Generate-review-correct; generate/edit logical actions | Training-free prompted workflow; no public trainable message schema | Keep as background only |
| Codex AGENTS.md official docs | official-doc-grounded | Root `AGENTS.md` project instruction hierarchy | Do not stuff all docs into AGENTS.md | verified 2026-07-14 |
| Codex Subagents official docs | official-doc-grounded | Project subagents can be configured | Exact model IDs remain local config | verified 2026-07-14 |
