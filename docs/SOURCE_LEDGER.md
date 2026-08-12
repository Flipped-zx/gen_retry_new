# SOURCE_LEDGER

This ledger records external evidence that is already grounded. Do not repeat
broad searches unless a source changes. Code copying still requires file-level
license evidence and a v3 module-contract adaptation.

## Remote Service Deployment Evidence

### model_deploy_10099 Qwen Generate Service

source_name: model_deploy_10099 sanitized Qwen service export
repository_url: internal deployment source, no public repository
absolute_path: `/root/private_data/model_services/qwen_dual_backend/sanitized_export`
commit_hash: n/a; immutable export archive SHA-256 `4ccbf1ddfa6f28d9b18edfb61177101f2d3f3cf9a5ff207c3e2cfb0f5765d9ea`
license: internal project code copied with explicit user authorization; no external redistribution license asserted
evidence_type: repository-grounded deployment implementation
exact_paths:
- path: `qwen_dual_backend/*.py`
  symbol: FastAPI contract, persistent jobs, runtime registry, artifact store
- path: `bin/*.sh`
  symbol: bootstrap, preflight, start, status, stop
- path: `tests/test_service.py`
  symbol: service contract tests
- path: `requirements.*.txt`, `service-env.example`, `README.md`
  symbol: reproducible deployment contract
borrowed_idea: Complete authorized sanitized service implementation.
local_adaptation: Stored outside `src/gen_retry` under `remote_service/qwen_dual_backend`; aligned input and normalized source digests with `RemoteQwenImageAdapter` and added a dedicated Edit-host readiness role. Planner/backend ownership is unchanged.
copy_code: yes, 25-file sanitized export; weights, secrets, host state, logs, caches, images, virtual environments, and backups excluded
notes: model_deploy_10099 remains Generate-only. The reusable Edit path is not rollout-ready until a separate Edit host has weights and passes the live checklist.

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
dirty_status: mode-only dirty; tracked source content matches HEAD
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
dirty_status: mode-only dirty; tracked source and `LICENSE` content match HEAD
license: root `LICENSE` is Apache-2.0
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
- path: `README.md`
  symbol: `prompt-reference program`, `GenEvolve-Data-SFT`
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
local_adaptation: Historical v0.2 routed both logical actions through
  `QianwenImageEditAdapter`. ADR-0006 superseded that design: current
  `qwen_dual_backend@1` routes source-free `generate_image` to Qwen-Image-2512
  and source-conditioned `edit_image` to Qwen-Image-Edit-2511.
copy_code: no
notes: Do not vendor weights or store secrets in config.

## Phase 3 Source Evidence

### Original GenEval Prompt Generation Rules

source_name: Original GenEval prompt sampler
repository_url: local checkout, upstream `https://github.com/djghosh13/geneval`
absolute_path: `/root/private_data/agentic_image/geneval`
commit_hash: `af4902f24d3ca90ebbb446dd9891a59e0f82725f`
dirty_status: dirty
license: MIT
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `prompts/create_prompts.py`
  symbol: `generate_single_object_sample`, `generate_two_object_sample`, `generate_counting_sample`, `generate_color_sample`, `generate_position_sample`, `generate_color_attribution_sample`, `generate_suite`
- path: `prompts/object_names.txt`
  symbol: object vocabulary for sampler
- path: `README.md`
  lines: `51-53`
  evidence: original GenEval prompts are provided and new prompt suites can be sampled with different seeds.
borrowed_idea: Official GenEval expands prompt pools by deterministic rule sampling from objects, counts, colors, and spatial/compositional templates.
local_adaptation: v3 may implement a clean-room Geneval2-compatible synthetic prompt generator, but must not call it official GenEval2 unless upstream publishes those rules.
copy_code: no
notes: GenEval2 local checkout does not contain an equivalent `create_prompts.py`; it currently exposes a fixed 800-row JSONL benchmark plus evaluator/analysis scripts.

### Original GenEval Metadata And Detector Evaluation Contract

source_name: Original GenEval metadata/evaluator
repository_url: `https://github.com/djghosh13/geneval.git`
absolute_path: `/root/private_data/agentic_image/geneval`
commit_hash: `af4902f24d3ca90ebbb446dd9891a59e0f82725f`
dirty_status: tracked content unchanged; checkout has mode-bit changes and untracked model/runtime directories
license: MIT
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `generation/diffusers_generate.py`
  lines: `100-160`
  evidence: only `metadata["prompt"]` enters generation; complete metadata is colocated with samples.
- path: `evaluation/evaluate_images.py`
  lines: `160-220, 261-280`
  evidence: include/exclude, count, color, and position semantics plus directory consumption contract.
- path: `evaluation/summary_scores.py`
  lines: `22-45`
  evidence: image/prompt success, per-tag means, and task macro average.
local_adaptation: `original_geneval_metadata_aware_agent@1` exposes a deterministic metadata-derived rubric to the Planner and uses VQA only as online proxy feedback. Formal scoring uses the pristine detector on one canonical submitted image per prompt.
copy_code: no
notes: This protocol is metadata-aware and is not equivalent to upstream prompt-only four-sample generation.

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

## Qwen-Image-Edit Configuration Evidence

### Gen-Searcher Qwen-Image-Edit Service Defaults

source_name: Gen-Searcher Qwen image service
repository_url: local checkout
absolute_path: `/root/private_data/agentic_image/Gen-Searcher`
commit_hash: `e5078d31859bafee6b6b610f0cd40095cc72e2a4`
dirty_status: mode-only dirty; tracked source content matches HEAD
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `README.md`
  lines: `143-152`
  evidence: Qwen-Image-Edit-2509 is launched as a FastAPI image generator service and exposed through `QWEN_EDIT_APP_URL`.
- path: `qwen_image_api_server/qwen-image-edit/api.py`
  lines: `31-32`
  evidence: default service model is `Qwen/Qwen-Image-Edit-2509`, dtype `torch.bfloat16`.
- path: `qwen_image_api_server/qwen-image-edit/api.py`
  lines: `275-283`
  evidence: request defaults include `seed=0`, `true_cfg_scale=4.0`, `negative_prompt=" "`, `num_inference_steps=40`, `guidance_scale=1.0`, `num_images_per_prompt=1`.
- path: `qwen_image_api_server/qwen-image-edit/api.py`
  lines: `342-353`
  evidence: pipeline call forwards request images, prompt, seed generator, true CFG, negative prompt, steps, guidance, and image count.
- path: `qwen_image_api_server/run_server.bash`
  lines: `6-18`
  evidence: service is run on port 8001 with 8 GPUs and one model per GPU for concurrent requests.
borrowed_idea: Quality-oriented Qwen serving defaults use around 40 denoising steps through a persistent service.
local_adaptation: Phase 3 live rollouts intentionally used 4 steps at 512px for infrastructure throughput, not final-quality rendering.
copy_code: no
notes: Gen-Searcher service code does not expose width/height fields in the request schema shown here; resolution is therefore service/model default unless modified elsewhere.

### GenEvolve Qwen-Image-Edit Renderer Defaults

source_name: GenEvolve Qwen image renderer
repository_url: local checkout
absolute_path: `/root/private_data/agentic_image/GenEvolve`
commit_hash: `23c847c559ccc0f95bbf4b3d8925898463822f4c`
dirty_status: mode-only dirty; tracked source content matches HEAD
license: Apache-2.0
evidence_type: repository-grounded via `source_researcher`
exact_paths:
- path: `README.md`
  lines: `94-107`
  evidence: recommended Qwen rendering path is a separate Qwen-Image-Edit FastAPI service compatible with `POST /generate`.
- path: `README.md`
  lines: `164-175`
  evidence: open-generator path uses `--backend qwen-image-edit-service`; local `qwen-image-edit` is retained only as a local diffusers debug path.
- path: `genevolve/generator.py`
  lines: `89-118`
  evidence: local debug generator defaults to `Qwen/Qwen-Image-Edit-2511`, `num_inference_steps=40`, `true_cfg_scale=4.0`, `guidance_scale=1.0`, `long_side=1024`, `size_multiple=16`.
- path: `genevolve/generator.py`
  lines: `150-176`
  evidence: local diffusers call requires at least one reference image and forwards prompt, reference images, steps, true CFG, guidance, negative prompt, width, and height.
- path: `genevolve/generator.py`
  lines: `188-260`
  evidence: HTTP service client defaults to path `/generate`, timeout 1800, max retries 3, `long_side=1024`, `max_refs=4`, `seed=0`, and sends `num_inference_steps=40`, `true_cfg_scale=4.0`, `guidance_scale=1.0`, `negative_prompt=" "`, width, and height.
- path: `scripts/generate_images.py`
  lines: `114-121`
  evidence: CLI defaults are `--qwen-model-id Qwen/Qwen-Image-Edit-2511`, `--num-inference-steps 40`, `--true-cfg-scale 4.0`, `--seed 0`, and repeated `--service-url`.
borrowed_idea: GenEvolve separates agent rollout from high-quality rendering and uses 40-step, long-side-1024 Qwen rendering for open-generator paths.
local_adaptation: v3 current Phase 3 rollout evidence used lower-quality smoke-style parameters; future quality rollouts should raise steps/resolution before interpreting generator capability.
copy_code: no
notes: GenEvolve requires reference images for the Qwen path; no-reference prompts are routed to other backends or need an explicit source/reference strategy.

## Paper Evidence

### GenEval2 Benchmark Design and Saturation Audit

source_name: GenEval2 paper and official repository
paper: `GenEval 2: Addressing Benchmark Drift in Text-to-Image Evaluation`
arxiv_url: `https://arxiv.org/abs/2512.16853`
version: v1, submitted 2025-12-18
repository_url: `https://github.com/facebookresearch/GenEval2`
repository_commit: `a6e82d2289e8d418f27f0adee77908b07060eea3`
evidence_type: paper-grounded and repository-grounded via `source_researcher`
exact_sections:
- section: `3 / Table 1`
  evidence: recent T2I models reach 94.8--96.7 human score on rewritten
    original-GenEval prompts, while automatic scores can differ from human
    judgment by as much as 17.7 percentage points.
- section: `4.1 Benchmark Curation`
  evidence: GenEval2 prompts contain one to three unique objects and are sampled
    from a documented template and vocabulary; transitive verbs are restricted
    to two animate objects; atomicity ranges from 3 to 10.
- section: `5.2 Soft-TIFA`
  evidence: one VQA question is generated per atom from the same prompt
    templates; arithmetic mean estimates atom-level correctness and geometric
    mean estimates prompt-level correctness.
- section: `5.4 / Table 4`
  evidence: among the eight evaluated models, Gemini has the highest reported
    Soft-TIFA AM (82.8) and GM (44.6).
- section: `8.1 Full Vocabulary of GenEval 2`
  evidence: lists animate and inanimate objects, attributes, prepositions,
    transitive verbs, and counts used by the benchmark.
borrowed_idea: A local Geneval2-compatible generator must encode the published
  semantic restrictions in an AST, not merely emit schema-compatible rows.
local_adaptation: Use the official 800 rows only as a final held-out test; use a
  separately named synthetic source with semantic-family provenance and human
  audit before bulk SFT rollout.
copy_code: no
notes: The official repository publishes the 800 rows and evaluator but no
  prompt-pool generator. Two manual review samples violate the animate-object
  restriction, demonstrating that adapter parsing is not a semantic validator.
  Repository score implementation at commit
  `a6e82d2289e8d418f27f0adee77908b07060eea3` is grounded in
  `evaluation.py:73-100,131-147,186-191`: expected first-token probability
  mass is computed per VQA atom; per-image Soft-TIFA GM is the geometric mean;
  the reported aggregate is `100 * mean(per-image score)`. The official code
  does not add an epsilon before SciPy `gmean`, so any exact zero yields zero.

### Flow-DPPO GenEval2 Synthetic Training Precedent

source_name: Flow-DPPO paper and UniRL repository
paper: `Flow-DPPO: Divergence Proximal Policy Optimization for Flow Matching Models`
arxiv_url: `https://arxiv.org/abs/2606.11025`
version: v2, last revised 2026-06-27
repository_url: `https://github.com/Tencent-Hunyuan/UniRL`
repository_commit: `e1a814ff9de6de644b093c6ed0106869c1881e53`
evidence_type: paper-grounded plus repository-grounded via `source_researcher`
exact_sections:
- section: `4 Experiments / Metrics and Datasets`
  evidence: the authors follow the GenEval2 template to generate 20,000
    synthetic training prompts and evaluate on the 800 officially released
    prompts.
- section: `Appendix G.4 / Tables 3 and 4`
  evidence: FLUX2-klein-base-9B with Flow-DPPO+CPS reaches 92.6 Soft-TIFA GM
    under single-reward GenEval2 training; the paper labels GenEval2 as
    in-domain and PickScore prompts as out-of-domain.
- section: `4.1 / Out-of-domain Behavior and Catastrophic Forgetting`
  evidence: out-of-domain metrics eventually decline as training overfits the
    in-domain GenEval2 reward.
exact_repository_paths:
- path: `datasets/geneval2/synthetic/train.jsonl`
  evidence: committed synthetic GenEval2 training set has 20,000 JSONL rows; row
    fields include `prompt`, `atom_count`, `vqa_list`, and `skills`.
- path: `datasets/geneval2/synthetic/test.jsonl`
  evidence: committed GenEval2 evaluation set has 800 JSONL rows with the same
    `vqa_list`/`skills` structure.
- path: `benchmarks/core/registry.py`
  symbols: `BenchmarkSpec(name="image/geneval2")`, `load_metadata`
  evidence: the benchmark uses `datasets/geneval2/synthetic/test.jsonl` and
    sets `send_metadata=True`, explicitly shipping each record's `vqa_list` to
    the scorer.
- path: `unirl/data/datasets.py`
  symbol: `normalize_prompt_example`
  evidence: when a row has no explicit `metadata`, all non-prompt/media fields
    are preserved as metadata, so `atom_count`, `vqa_list`, and `skills` remain
    attached to the prompt example.
- path: `unirl/data/data_source.py`
  symbols: `_collate_text`, `_prompt_examples_to_batch`
  evidence: normalized prompt-example metadata is carried into `RolloutInputs`.
- path: `unirl/trainer/diffusion.py`
  evidence: diffusion rollout requests copy `inputs.metadata` into `RolloutReq`.
- path: `unirl/reward/local/geneval2.py`
  symbols: `_load_prompt_vqa_map`, `GenEval2RewardScorer._compute_model_rewards`
  evidence: local GenEval2 reward first reads `request.metadata[i]["vqa_list"]`,
    falls back to a prompt-to-VQA map built from JSONL data, and returns 0.0
    when no VQA list is available.
- path: `unirl/reward/local/geneval2.py`
  lines: `31-39,206-226`
  evidence: local Flow-DPPO scoring defaults to per-image geometric mean and
    computes `exp(mean(log(max(atom_probability, 1e-300))))`.
- path: `benchmarks/core/score.py`
  lines: `118-191`
  evidence: benchmark-local full-vocabulary Qwen3-VL scoring uses the same
    `1e-300` geometric-mean floor.
- path: `benchmarks/run.py`
  lines: `224-227`
  evidence: the benchmark metric is the arithmetic mean of per-image scores in
    `[0,1]`; presentation may multiply it by 100.
- path: `unirl-reward-service/reward_service/scorers/geneval2.py`
  symbols: `_load_vqa_dataset`, `GenEval2Scorer._lookup_vqa`, `score`
  evidence: remote reward-service scorer documents Soft-TIFA as requiring a
    per-prompt `vqa_list`; it prefers `ScoreItem.metadata["vqa_list"]`, falls
    back to configured dataset JSONL, and otherwise uses a degenerate VQAScore
    path only when allowed.
borrowed_idea: Large rule-synthetic GenEval2 training is feasible and has a
  published 20,000-prompt precedent.
local_adaptation: Report synthetic-trained results as benchmark-specific
  post-training, retain semantic/template holdouts, and require human and
  out-of-domain audits; do not compare the 92.6 in-domain result directly with
  zero-shot/base-model benchmark scores.
copy_code: no
notes: The UniRL public repository commits the Flow-DPPO GenEval2 synthetic
  train/test JSONL rows with VQA lists, and the reward path consumes those VQA
  lists through metadata. The generic published `examples/diffusion/sd3/
  sd3_flowdppo.yaml` defaults to PickScore data, so the repo confirms the data
  format and reward path but does not expose a single default GenEval2 training
  YAML as the top-level FlowDPPO example. A read-only sparse checkout at commit
  `e1a814ff9de6de644b093c6ed0106869c1881e53` confirmed 20,000 train rows and
  800 held-out rows. Of the train rows, 6,007 have
  `atom_count != len(vqa_list)`; Phase 5 therefore retains both fields and uses
  actual VQA count in difficulty selection. Exact prompt and deterministic
  semantic-family overlaps with the held-out set are excluded before rollout.

### GenEvolve Paper Appendix Prompt Details

source_name: GenEvolve paper local PDF
paper: `GenEvolve: Self-Evolving Image Generation Agents via Tool-Orchestrated Visual Experience Distillation`
absolute_path: `/root/private_data/agentic_image/Chen 等 - 2026 - GenEvolve Self-Evolving Image Generation Agents via Tool-Orchestrated Visual Experience Distillatio.pdf`
arxiv_url: `https://arxiv.org/abs/2605.21605`
version: v2, last revised 2026-05-22
evidence_type: paper-grounded, local PDF text extracted read-only
exact_sections:
- section: `3 Tool-Orchestrated Visual Trajectory Formulation`
  evidence: each generation attempt is a tool-orchestrated visual trajectory whose final output is prompt-reference program `z = (g, R)`.
- section: `A.2 Teacher Trajectory Generation`
  evidence: teacher trajectories are real multi-turn tool loops; accepted trajectories require meaningful tool use; malformed JSON, invalid skills, missing ordinal references, and raw URL leakage are filtered.
- section: `B.2 Prompt-Reference Program Schema`
  evidence: final executable object contains `gen_prompt`, `reference_images`, and paper-level diagnostic metadata such as selected skills/rationale-style fields.
- section: `F Prompt and Template Details`
  evidence: appendix reports representative implementation prompt templates.
- section: `F.4 Representative Implementation Prompt Excerpts`
  evidence: agent rollout prompt requires strict one tool call or answer per round; `query_knowledge` activates named generation skills; final `gen_prompt` references selected images by ordinal phrases rather than raw image IDs.
- section: `Table 9 Supervised trajectory-tuning configuration`
  evidence: loss masking is assistant-token only; user prompts and tool-response tokens are context.
borrowed_idea: Use strict per-turn action formatting, real skill-query tool interactions, tool observations as next-turn context, action-only SFT masking, and readable trajectory traces that show how tool outputs condition later assistant actions.
local_adaptation: Gen-Retry v3 outputs verifier-grounded retry actions (`query_skill`, `generate_image`, `edit_image`, `submit_attempt`) rather than GenEvolve's final prompt-reference program. Skill queries remain planner actions, while image rounds count only Qwen/Geneval attempts.
copy_code: no
notes: Do not copy GenEvolve's search/reference final schema directly; v3 uses Geneval2 atom feedback, best-so-far state, rollback source selection, and executable retry actions.

### GenEvolve Evaluation Protocol And KScore Semantics

source_name: GenEvolve formal evaluator, benchmark, and paper
repository_url: local checkout
absolute_path: `/root/private_data/agentic_image/GenEvolve`
repository_commit: `23c847c559ccc0f95bbf4b3d8925898463822f4c`
license: Apache-2.0
paper: `GenEvolve: Self-Evolving Image Generation Agents via Tool-Orchestrated Visual Experience Distillation`
arxiv_url: `https://arxiv.org/abs/2605.21605`
version: v2, revised 2026-05-22
accessed_date: `2026-08-02`
evidence_type: repository-grounded and paper-grounded via `source_researcher`
exact_repository_paths:
- path: `genevolve/agent.py:276-351,356-390`
  evidence: the multi-turn agent performs search, image search, and Skill
    queries, then emits one final prompt-reference program with one or two
    selected references; it does not generate an image on each agent turn.
- path: `scripts/generate_images.py:79-102`
  evidence: each prompt-reference program makes one backend `generate` call
    and persists one generated image path/status in the result record.
- path: `genevolve/generator.py:89-176,188-279`
  evidence: the Qwen path uses Qwen-Image-Edit-2511, 40 steps, true CFG 4.0,
    guidance 1.0, blank negative prompt, long-side-1024 reference scaling,
    default seed 0, and one returned image; HTTP retries are infrastructure
    retries, not image-quality retries.
- path: `scripts/evaluate_images.py:190-295`
  evidence: the judge rubric separately defines faithfulness, ground-truth-
    relative visual correctness, text accuracy, and ground-truth-relative
    aesthetics, nominally on the set `{0, 0.5, 1}`.
- path: `scripts/evaluate_images.py:40-47,137-178,360-412,678-695`
  evidence: generated image is Image 1, ground truth is Image 2; the default
    judge is `gemini-3.1-pro-preview` through an OpenAI-compatible multimodal
    request with temperature 0; the parser repairs several non-strict output
    forms and retains clipped intermediate numeric values.
- path: `scripts/evaluate_images.py:501-540`
  evidence: released code computes
    `0.1*F + 0.4*V + 0.4*T + 0.1*A`; for no-text rows it sets `T=0.5` and does
    not renormalize, contrary to the paper's stated remaining-dimension
    renormalization.
- path: `scripts/evaluate_images.py:520-593,634-675,715-788`
  evidence: component means are success-only; only overall has a
    missing-as-zero-adjusted form; persisted failed evaluation rows are skipped
    on resume; results and summaries are artifact-backed and atomically
    rewritten.
- path: `README.md:64-66,228-232`
  evidence: GenEvolve-Bench contains 594 prompt/ground-truth pairs, split into
    335 Knowledge-Anchored and 259 Quality-Anchored cases; README claims the
    evaluator follows the paper formula despite the no-text code discrepancy.
exact_paper_sections:
- section: `Method / Prompt-Reference Program and Generation Feedback`
  evidence: self-evolution samples six independent agent trajectories per
    prompt; each final program is rendered once, so the candidates are sibling
    programs rather than successive edits of one generated image.
- section: `Training Details`
  evidence: training reward is `0.5 image KScore + 0.5 program-text
    sufficiency reward`; the latter uses five levels from 0 to 1. The final
    benchmark table reports image KScore components, not this training scalar.
- section: `Evaluation Details / Reward Rubric`
  evidence: formal KScore weights are faithfulness 0.1, visual correctness
    0.4, text accuracy 0.4, and aesthetics 0.1; the paper says no-text rows are
    renormalized over the other three dimensions.
- section: `Main Results / Main Ablation`
  evidence: GenEvolve with Qwen-Image-Edit reports F=0.5303, V=0.1338,
    T=0.4907, A=0.6347, and KScore=0.3663. Raw Qwen-Image aesthetics is 0.6751,
    so aggregate improvement does not establish aesthetics preservation.
borrowed_idea: Preserve independent correctness and quality dimensions,
  artifact/version provenance, explicit failed/missing denominators, and
  stable visual references; compare shallow sibling candidates rather than
  assuming deep edit chains preserve quality.
local_adaptation: Gen-Retry keeps Geneval2 atom/GM semantics unchanged while
  researching a separate quality-anchor and transition-quality audit. It must
  not import KScore as a hidden reducer scalar or treat ground-truth-relative
  aesthetics as directly available when no gold rendering exists.
copy_code: no
notes: GenEvolve does not contain edit-on-edit retry, mask execution, image
  rollback, or an inference-time quality selector. Its README quickstart uses
  Nano Banana Pro by default, so gallery quality is not evidence for the open
  Qwen path. The no-text paper/code discrepancy is unresolved and any
  reproduction must lock one explicit formula version. Detailed local
  analysis: `docs/research/genevolve_evaluation_reference.md`.

### Multi-Turn Image Editing Quality Degradation

source_name: MagicBrush and FreqEdit multi-turn editing evidence
magicbrush_paper: `MagicBrush: A Manually Annotated Dataset for Instruction-Guided Image Editing`
magicbrush_arxiv_url: `https://arxiv.org/abs/2306.10012`
magicbrush_version: v3
freqedit_paper: `FreqEdit`
freqedit_arxiv_url: `https://arxiv.org/abs/2512.01755`
freqedit_version: v2
freqedit_repository_url: `https://github.com/FreqEdit/FreqEdit`
freqedit_repository_commit: `cf7f9857878004fd8d219b9489baccd96e1e31ac`
freqedit_license: MIT
accessed_date: `2026-08-02`
evidence_type: paper-grounded and repository-grounded via `source_researcher`
exact_paper_sections:
- paper: MagicBrush
  section: `Quantitative Evaluation / Mask-free Editing`
  table: `tab:mask-free-quantitative`
  evidence: all evaluated methods degrade in multi-turn editing because
    iterative errors accumulate; the paper's source statement is in
    `sections/5_Experiments.tex:27-39` and the table source is
    `tables/mask-free-editing-v3.tex`.
- paper: MagicBrush
  section: `Human Evaluation / One-on-one Comparison`
  table: `tab:he_comparative`
  evidence: human consistency and image-quality gaps relative to the target
    increase with editing turn; the source statement is in
    `sections/5_Experiments.tex:92-101` and the table source is
    `tables/human_eval_comparative.tex`.
- paper: FreqEdit
  section: `Method / Overview; Wavelet-based Feature Injection; Adaptive
    Injection Strategy; Path Compensation; Quality Guidance for Noise
    Suppression`
  evidence: the method attributes multi-turn deformation, edge
    over-sharpening, and texture collapse to accumulated high-frequency loss;
    it injects reference high-frequency velocity with spatial adaptation and
    path compensation and can use original-image velocity for late quality
    guidance.
- paper: FreqEdit
  section: `Experiments / Implementation and Evaluation Setup; Results`
  evidence: ten-turn Qwen and FLUX experiments report better preservation and
    human preference, with an instruction-following trade-off that prevents
    treating preservation as a free improvement.
exact_repository_paths:
- path: `src/pipelines/FreqEditQwen_pipeline.py:15-30,84-92,290-332`
  evidence: the implementation subclasses the legacy
    `QwenImageEditPipeline` and implements frequency injection and path
    compensation controls.
- path: `src/run_FreqEditQwen.py:13-16,25-32,43-67`
  evidence: the released Qwen experiment loads `Qwen/Qwen-Image-Edit`, records
    Qwen parameters, and executes a ten-turn edit loop.
- path: `docs/parameters.md:3-19`
  evidence: documents recommended FreqEdit parameter settings.
borrowed_idea: Treat every source-output edit as a quality transition; retain
  an original or source-free quality anchor; use frequency/detail proxies only
  as monitoring signals; test shallow branching and backend-side preservation
  under paired human-calibrated evaluation.
local_adaptation: Gen-Retry should first implement an offline quality audit and
  equal-budget shallow-branching experiment. FreqEdit is a separate adapter
  research candidate, not a production dependency, because its released Qwen
  implementation targets the older pipeline rather than 2511's
  `QwenImageEditPlusPipeline`.
copy_code: no
notes: MagicBrush establishes the general multi-turn accumulation problem.
  FreqEdit provides a mechanism hypothesis and mitigation direction, but does
  not validate direct compatibility with the current Gen-Retry adapter.

### Meta Muse Image Agentic Generation Blog

source_name: Meta Muse Image official technical blog
title: `Introducing Muse Image and Muse Video`
official_url: `https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/`
publisher: Meta Superintelligence Labs
published_date: `2026-07-07`
accessed_date: `2026-07-29`
evidence_type: official-blog-grounded via `source_researcher`
local_source_record:
  `references/web/muse_image_meta_2026-07-07/technical_blog_snapshot.md`
exact_sections:
- section: `Muse Image: Agentic Image Generation / Tool Use`
  evidence: the system can invoke search and code tools; the blog presents an
    internal search win-rate ablation but does not disclose the complete prompt
    set, sample size, judge protocol, uncertainty, or numeric table.
- section: `Self-Refinement`
  evidence: the described policy can locally edit a narrow defect, regenerate
    when larger parts are wrong, or switch to tool use; Meta attributes the
    behavior to reinforcement-learning reward rather than a hand-coded route.
    The internal chart reports pairwise preference of 57.1% versus 42.9% for
    text-to-image, 56.3% versus 43.7% for single-image editing, and 56.6%
    versus 43.4% for multi-image editing with refinement enabled versus
    disabled; sample counts and uncertainty are not disclosed.
- section: `Test-Time Compute Scaling`
  evidence: the blog compares deliberate reasoning/tool/refinement compute with
    Best-of-N sampling and says Best-of-N saturates earlier; the public post
    does not expose a reproducible protocol or raw numeric results.
- section: `Image Editing`
  evidence: the product is described as maintaining coherence across editing
    turns, but no public preservation benchmark is specified.
- section: `Image Benchmarks`
  evidence: Arena human-preference rankings are reported as of 2026-07-05;
    these are not comparable to Gen-Retry's Qianwen/Geneval2 protocol.
borrowed_idea: Treat edit versus regenerate as a learned routing decision;
  compare adaptive retry to equal-image-call-budget Best-of-N; report anytime
  quality/cost curves and source-relative target-fix versus preserve-regression.
local_adaptation: Gen-Retry keeps only its current action set and explicit
  Geneval2/canonical-memory ownership. Search, code, Muse Spark,
  personalization, multi-reference composition, and product features remain
  out of scope.
copy_code: no
notes: This 2026 system is from Meta, not Google. Google's 2023 `Muse:
  Text-To-Image Generation via Masked Generative Transformers`
  (`https://muse-model.github.io/`) is a different generator architecture.
  Targeted primary-source searches found no public Muse Image paper, model
  card, code, weights, reward definition, or reproducible ablation protocol as
  of the access date. Muse Image is related-work motivation, not an executable
  or numerically comparable baseline. The page does not publish a reusable
  content license, so the repository stores a canonical URL and selective
  paraphrase rather than vendoring the page or its media.

### Google Rich Human Feedback for T2I

source_name: Google RichHF/RAHF paper, official blog, and utility repository
paper: `Rich Human Feedback for Text-to-Image Generation`
arxiv_url: `https://arxiv.org/abs/2312.10240`
version: v2, last revised 2024-04-09
venue: CVPR 2024
official_blog:
  `https://research.google/blog/rich-human-feedback-for-text-to-image-generation/`
official_blog_date: `2024-06-26`
google_publication:
  `https://research.google/pubs/rich-human-feedback-for-text-to-image-generation/`
repository_url:
  `https://github.com/google-research/google-research/tree/master/richhf_18k`
repository_commit_observed: `a1fcc2d2e342c59ecff810eea28edb010f654a10`
paper_license: CC BY 4.0 on arXiv
utility_license: parent `google-research` repository is Apache-2.0
accessed_date: `2026-07-29`
evidence_type: paper-grounded, official-blog-grounded, and
  repository-grounded via `source_researcher`
exact_sections:
- section: `Paper Sections 3.1--3.3 / Official Blog "Rich human feedback
    collection" and "Rich human feedback prediction"`
  evidence: RichHF annotates global plausibility/alignment/aesthetic/overall
    scores, pixel-level implausibility and misalignment locations, and
    misrepresented or missing prompt words; RAHF predicts score, heatmap, and
    misalignment-sequence outputs.
- section: `Paper Section 4 / Official Blog "Learning from rich human
    feedback"`
  evidence: predicted feedback is used to filter Muse candidates for LoRA
    fine-tuning, guide other generators, and convert implausibility heatmaps
    into masks for Muse inpainting.
- section: `Official Blog region-inpainting procedure`
  evidence: multiple repaired images are generated and the final result is
    selected by the highest RAHF-predicted plausibility score.
- section: `Paper Section 4.1 human evaluation`
  evidence: evaluation uses 100 new TIFA prompts and randomized side-by-side
    judgments; fine-tuned Muse is reported significantly/slightly better in
    21.50%/30.33%, about the same in 31.33%, and
    slightly/significantly worse in 12.67%/4.17%. The paper reports no
    confidence interval for this comparison.
exact_repository_paths:
- path: `richhf_18k/`
  evidence: public utilities and annotation-format support live under the
    Apache-2.0 Google Research parent repository; they are not the full RAHF
    training or inference implementation.
borrowed_idea: Separate the value of detailed atom-level feedback from an
  aggregate-only verifier signal; pair verifier-guided selection with an
  independent human or held-out evaluator audit; measure localized repair and
  unintended regressions separately.
local_adaptation: Gen-Retry retains Geneval2 atom facts rather than importing
  RAHF. A nested `atom-level feedback vs aggregate-only counts vs no verifier`
  ablation can test feedback specificity without adding a heatmap model or
  changing the v0.5 action protocol.
copy_code: no
notes: RichHF supplies learned feedback, candidate filtering, and a fixed
  score/inpainting/select pipeline. It does not provide a sequential
  edit-versus-regenerate planner, immutable event history, historical
  best/lineage, strict one-action output, or recovery supervision. The separate
  RichHF dataset repository has no observed dataset-specific license, so do
  not infer Apache-2.0 for the dataset itself.

### Gen-Searcher Dual Qwen Execution And Local Qwen Model Cards

source_name: Gen-Searcher Qwen evaluation runtime and local Qwen model cards
gen_searcher_commit: `e5078d31859bafee6b6b610f0cd40095cc72e2a4`
accessed_date: `2026-07-29`
evidence_type: repository-grounded and local-model-card-grounded via
  `source_researcher`
exact_repository_paths:
- path: `Gen-DeepResearch-RL/rllm/eval/gen_image_from_results.py:88-108`
  evidence: records with valid reference images use the generated edit prompt
    and image paths; otherwise the original prompt is treated as text-only.
- path: `Gen-DeepResearch-RL/rllm/eval/gen_image_from_results.py:406-506`
  evidence: `DiffuserQwenGenerator` routes text-only calls to Qwen-Image and
    text-plus-image calls to Qwen-Image-Edit; its defaults use 50 generation
    steps with `true_cfg_scale=4.0` and 40 edit steps with
    `true_cfg_scale=4.0`, `guidance_scale=1.0`.
- path: `Gen-DeepResearch-RL/rllm/eval/run_gen_image_from_results.sh:17-37`
  evidence: the evaluation entrypoint defaults to the dual Qwen generator with
    separate generation and editing model IDs.
exact_local_model_paths:
- path: `/root/private_data/agentic_image/models/Qwen-Image-2512/model_index.json`
  evidence: concrete diffusers class is `QwenImagePipeline`.
- path: `/root/private_data/agentic_image/models/Qwen-Image-2512/README.md:47-89`
  evidence: source-free Qwen-Image-2512 usage documents 50 steps,
    `true_cfg_scale=4.0`, and a quality-oriented negative prompt.
- path: `/root/private_data/agentic_image/models/Qwen-Image-Edit-2511/model_index.json`
  evidence: concrete diffusers class is `QwenImageEditPlusPipeline`.
- path: `/root/private_data/agentic_image/models/Qwen-Image-Edit-2511/README.md:39-65`
  evidence: source-conditioned edit usage documents 40 steps,
    `true_cfg_scale=4.0`, and `guidance_scale=1.0`.
borrowed_idea: Route source-free generation and source-conditioned editing to
  their native local Qwen pipelines while retaining one planner action space.
local_adaptation: `qwen_dual_backend@1` maps existing `generate_image` to
  Qwen-Image-2512 and `edit_image` to Qwen-Image-Edit-2511. Backend, model,
  mode, and sampling stay environment-owned and are recorded as provenance,
  not assistant targets.
copy_code: no
notes: Gen-Searcher's cited default model IDs are older Qwen-Image and
  Qwen-Image-Edit-2509 releases. Its FastAPI rollout server is edit-only; the
  dual-route evidence is specifically the evaluation runtime. The local model
  directories are not Git repositories, so their model cards/configs have no
  local commit hash.

### GenEval2 Official Distribution For The 200-Prompt Training Pool

source_name: GenEval2 official repository and dataset
repository_commit: `a6e82d2289e8d418f27f0adee77908b07060eea3`
accessed_date: `2026-07-30`
evidence_type: repository-grounded via `source_researcher`
exact_repository_paths:
- path: `/root/private_data/agentic_image/GenEval2/README.md:16`
  evidence: the benchmark contains 800 prompts with varying compositionality.
- path: `/root/private_data/agentic_image/GenEval2/README.md:27-39`
  evidence: rows expose `prompt`, `atom_count`, `vqa_list`, and `skills`;
    `atom_count` is the benchmark's compositionality/atomicity field.
- path: `/root/private_data/agentic_image/GenEval2/soft_tifa_analysis.py:11-64`
  evidence: analysis is grouped by skill at atom level and by atomicity at
    prompt level; no official easy/medium/hard labels are defined.
- path: `/root/private_data/agentic_image/GenEval2/geneval2_data.jsonl`
  evidence: 800 rows are exactly balanced with 100 prompts for each
    `atom_count` from 3 through 10. Skill atoms total attribute=1214,
    count=2025, object=2025, position=662, and verb=86.
borrowed_idea: Use exact atom-count quotas as the primary official-like
  difficulty distribution and use skill frequencies only as soft coverage
  targets.
local_adaptation: The 200-prompt Flow-DPPO pool takes 25 rows for each
  `atom_count` from 3 through 10. Local reporting tiers are easy=3-5,
  medium=6-8, and hard=9-10; they are explicitly not official labels. The
  official 800 rows, exact prompts, and conservative semantic-family overlaps
  remain held out.
copy_code: no
notes: `atom_count != len(vqa_list)` for 554 of 800 official rows, so every
  selected record retains both fields. The 200 synthetic rows are training
  data and cannot be reported as an official Geneval2 benchmark result.

### Gen-Searcher Agentic Search Paper

source_id: `paper_gen_searcher_arxiv_2603_28767_v3`
source_name: Gen-Searcher paper and local repository
paper: `Gen-Searcher: Reinforcing Agentic Search for Image Generation`
arxiv_url: `https://arxiv.org/abs/2603.28767v3`
version: v3
local_manifest: `references/papers/gen_searcher_2603.28767/manifest.json`
local_pdf_sha256: `7d242893082ac9ee3fefd5ec2285759c4f9b78bb11b9711ebd97743405cb582a`
repository_commit: `e5078d31859bafee6b6b610f0cd40095cc72e2a4`
repository_license: no top-level license; inspected RL subtree is MIT and SFT
  subtree is Apache-2.0, so copying still requires file/subtree verification
accessed_date: `2026-08-02`
evidence_type: paper-grounded and repository-grounded via `source_researcher`
exact_sections:
- section: `3.1 Agentic Search Trajectory`
  evidence: the policy runs a real multi-turn trajectory of search/image tools
    and receives tool observations before the next assistant decision.
- section: `3.3 Training / Reward Design`
  evidence: policy optimization leaves the image generator fixed and combines
    image- and text-side reward rather than training the generator itself.
- section: `4.1 Training Details`
  evidence: overlong or repetitive rollout behavior is explicitly masked or
    filtered during training.
- section: `4.4 Ablations`
  evidence: workflow, SFT, RL, and dual-reward contributions are separated.
- section: `Appendix C Agent Prompt`
  evidence: each round must contain one tool call or one final answer.
exact_repository_paths:
- path: `Gen-DeepResearch-RL/rllm/rllm/engine/agent_execution_engine.py`
  evidence: environment steps and assistant responses are separated, but a
    rollout retry gets a new application UUID rather than resuming canonical
    state.
- path: `Gen-DeepResearch-RL/rllm/rllm/trainer/agent_sft_trainer.py`
  evidence: reward-threshold export can retain assistant reasoning/final text;
    it is not equivalent to v3's executable-action-only positive targets.
- path: `Gen-DeepResearch-RL/vision_deepresearch_async_workflow/gen_image_deepresearch_reward.py`
  evidence: image generation and scoring are environment/reward-owned and
    artifact-backed, but saved results lack content digests, model revisions,
    semantic request IDs, and deterministic replay provenance.
borrowed_idea: Preserve real tool interactions, separate observations from
  action targets, keep the generator frozen/environment-owned, and persist
  artifact references rather than image bytes in planner memory.
local_adaptation: v3 replaces new-application retry and result-JSON recovery
  with immutable events, semantic request IDs, profile locks, digests, and
  deterministic replay. Search itself remains outside the image-retry scope.
copy_code: no
notes: The paper/repository supports agent/tool trajectory design, not v3's
  historical Attempt branching, atom-level retry memory, or canonical resume.

### GEMS Verifier, Memory, And Skill Design

source_id: `paper_gems_arxiv_2603_28088_v1`
source_name: GEMS paper
paper: `GEMS: Agent-Native Multimodal Generation with Memory and Skills`
arxiv_url: `https://arxiv.org/abs/2603.28088v1`
version: v1
local_manifest: `references/papers/gems_2603.28088/manifest.json`
local_pdf_sha256: `e34c537c488e9b0f59bec630e7c6fada034311221a8ef8da59f9e083b1c7be3f`
license: CC BY 4.0 in PDF metadata
accessed_date: `2026-08-02`
evidence_type: paper-grounded via `source_researcher`
exact_sections:
- section: `3.1 Verifier-Guided Iterative Generation`
  evidence: task requirements are represented as atomic binary criteria; a
    verifier vector evaluates candidates and historical best is retained.
- section: `3.2 Experience Memory`
  evidence: the agent conditions on prompt, image, verifier feedback, and
    compressed experience derived from prior interactions.
- section: `3.3 Skill Library`
  evidence: the compact Skill manifest is always available while detailed
    instructions are loaded only when selected.
- section: `4.3 Memory Ablation`
  evidence: images, verifier feedback, and compressed experiences are ablated
    as distinct memory components.
- section: `Appendix A.1 Agent Components`
  evidence: Skill routing and refinement guidance explicitly include
    preservation of already satisfied requirements.
borrowed_idea: Verifier vectors, historical best, compact experience, and
  manifest-plus-on-demand Skill loading are direct precedents that should be
  acknowledged in Gen-Retry related work and ablations.
local_adaptation: v3 makes evaluator facts environment-owned, stores immutable
  events instead of LLM-compressed truth, uses deterministic compact views,
  requires explicit edit lineage, and keeps tool observations/context separate
  from action-only supervision.
copy_code: no
notes: GEMS memory may contain raw reasoning and depends on an LLM compressor.
  It does not establish event-sourced replay, arbitrary historical-source
  recovery, or Gen-Retry's harmful-history/recovery target policy.

### Generation Navigator State-Conditioned Image Retry

source_id: `paper_generation_navigator_arxiv_2605_17969_v1`
source_name: Generation Navigator paper
paper: `Generation Navigator: A State-Aware Agentic Framework for Image Generation`
authors: Jinming Liu, Ruoyu Feng, Yuqi Wang, Wenjun Zeng, Xin Jin
arxiv_url: `https://arxiv.org/abs/2605.17969v1`
doi: `10.48550/arXiv.2605.17969`
version: v1, submitted 2026-05-18
local_manifest: `references/papers/generation_navigator_2605.17969/manifest.json`
local_pdf_sha256: `76dfda0c86c2aba2e757275338c750e0dfb42eee8ef36cd30878a4b60c47e0f4`
license: PDF metadata points to the arXiv non-exclusive distribution license;
  the PDF is an ignored local cache and is not vendored in Git
accessed_date: `2026-08-02`
evidence_type: paper-grounded via `source_researcher` and local PDF inspection
exact_sections:
- section: `3.1 State-Conditioned Action Policy / Equations 1--3`
  evidence: the navigator observes the original prompt plus the selected-path
    action/image/reviewer history, emits `STOP`, `REFINE`, or `REGENERATE`, and
    delivers the highest reviewer-scored candidate across the trajectory.
- section: `3.2.1 Action Trajectory Construction`
  evidence: branch-and-select exploration records state, structured action,
    revised prompt, image, reviewer feedback, and subsequent scores rather
    than training from prompt/image pairs alone.
- section: `3.2.3 PRE-GRPO / Equations 5--8`
  evidence: trajectory reward separates peak discovery, terminal retention,
    normalized turn efficiency, and format correctness; it is a policy-level
    credit-assignment objective, not an image-generator reward.
- section: `Appendix B Pilot Study Details`
  evidence: per-state execution of both candidate actions reports regenerate
    wins in 47.01%, refine in 39.38%, and ties in 13.61%; neither fixed action
    dominates on that paper's three-turn T2I-ReasonBench setup.
- section: `Appendix C.3--C.4 Branch-and-select / Trajectory Filtering`
  evidence: the explorer keeps a full candidate tree but conditions the
    navigator only on the active selected path; SFT retains only trajectories
    with best reviewer score above 4.5 and strictly monotonic score gains,
    discarding plateauing and regressive branches.
- section: `Appendix F Controlled Sampling-Budget Comparison`
  evidence: one-shot, Best-of-3, prompt-enhanced Best-of-3, fixed workflows,
    state-conditioned agents, and trained policies are compared to separate
    sampling gains from action-policy gains.
- section: `Appendix G Best-Score vs. Final-Score Selection`
  evidence: best-score trajectory selection outperforms final-only selection
    under both tested reward variants.
- section: `Appendix L Human Evaluation`
  evidence: eight annotators provide 320 pairwise annotations; the paper
    reports about 70.3% reviewer/human agreement on decisive non-tie pairs,
    supporting reviewer usefulness but not treating it as ground truth.
- section: `Appendix M Limitations and Future Directions`
  evidence: the paper identifies iterative inference latency and dependence on
    an external reviewer as structural costs.
borrowed_idea: Treat image retry as a state-conditioned action problem; report
  historical peak retention, post-peak regression, attempts/turns to peak, and
  equal-image-call baselines rather than only first-to-best improvement.
local_adaptation: Gen-Retry keeps its atom-level Geneval2 facts, immutable
  events, deterministic reducer, explicit historical `source_attempt_id`, and
  explicit `submit_attempt`. Any PRE-style planner RL objective is future work
  requiring a separate design/ADR and review after the v9 SFT freeze.
copy_code: no
notes: The paper is close enough that Gen-Retry must not claim first
  state-aware edit/regenerate routing, first trajectory-best retention, or
  first regression/turn-efficiency objective. Its online refine action uses
  the current image, its SFT data remove non-monotonic branches, its reviewer
  is scalar rather than atom-grounded, and the supplied v1 PDF exposes no
  public code/data repository. It therefore does not establish event-sourced
  canonical memory, arbitrary historical-source recovery, or harmful-context
  recovery supervision.

### LlamaFactory SFT Execution And Mask Semantics

source_id: `llamafactory_v0_9_5_gen_retry_sft_adapter`
source_name: LlamaFactory, Gen-Searcher SFT subtree, and GenEvolve SFT evidence
upstream_repository: `https://github.com/hiyouga/LlamaFactory`
upstream_tag: `v0.9.5`
upstream_commit: `7af909522a951e3ad9f022ea6f88b6755257eaa5`
upstream_license: Apache-2.0
gen_searcher_commit: `e5078d31859bafee6b6b610f0cd40095cc72e2a4`
gen_searcher_sft_license: Apache-2.0
genevolve_commit: `23c847c559ccc0f95bbf4b3d8925898463822f4c`
genevolve_license: Apache-2.0
accessed_date: `2026-08-03`
evidence_type: repository-grounded, paper-grounded, and official-doc-grounded
  via `source_researcher`
exact_repository_paths:
- path: `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-SFT/LLaMA-Factory/examples/train_full/gen_qwen3_sft.yaml:1-55`
  evidence: executable Qwen3-VL-8B full-SFT baseline freezes the vision tower
    and projector, uses ZeRO-3/bf16/FA2, cutoff 32768, two epochs, LR `1e-5`,
    weight decay `1e-6`, cosine schedule, and warmup ratio `0.02`.
- path: `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-SFT/LLaMA-Factory/data/dataset_info.json:2-16`
  evidence: the public training data are registered as ShareGPT/OpenAI
    `messages + images` with system/user/assistant role/content tags.
- path: `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-SFT/LLaMA-Factory/src/llamafactory/data/processor/supervised.py:43-122`
  evidence: prompt tokens are ignored when `train_on_prompt=false`, while
    `mask_history=false` trains every assistant turn; Gen-Searcher's YAML does
    not override the latter default.
- path: `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-SFT/LLaMA-Factory/src/llamafactory/data/mm_plugin.py:188-215`
  evidence: image count must exactly match `<image>` placeholder count.
- path: `/root/private_data/agentic_image/Gen-Searcher/Gen-DeepResearch-SFT/LLaMA-Factory/src/llamafactory/data/loader.py:362-370`
  evidence: an existing `tokenized_path` is loaded while other data arguments
    are ignored, so cache paths must be content/config addressed.
- path: `/root/private_data/agentic_image/GenEvolve/README.md:334-410`
  evidence: GenEvolve releases 9,000 `messages + images` SFT trajectories but
    explicitly does not release its complete training script.
official_upstream_paths:
- url: `https://github.com/hiyouga/LlamaFactory/blob/v0.9.5/data/README.md`
  evidence: official ShareGPT/OpenAI multimodal format requires the number of
    images to equal the number of `<image>` tokens.
- url: `https://github.com/hiyouga/LlamaFactory/blob/v0.9.5/examples/train_lora/qwen3vl_lora_sft.yaml`
  evidence: official Qwen3-VL LoRA example uses `qwen3_vl_nothink`, batch size
    one, and a multimodal dataset.
exact_paper_sections:
- paper: `GenEvolve`, Appendix C.1 Table 9
  evidence: assistant reasoning/tool/final tokens are trained while user and
    tool-response tokens are context; full-SFT hyperparameters match the
    repository-grounded Gen-Searcher baseline on the main optimization tuple.
- paper: `Generation Navigator`, Section 3.2 and Appendix C.4
  evidence: 103K one-epoch state/action trajectories are reported, but the
    training framework and optimizer details are absent and regressive or
    plateau trajectories are filtered out.
borrowed_idea: Use an isolated LlamaFactory environment, ShareGPT/OpenAI
  `messages + images`, 32K Qwen3-VL context, frozen vision/projector for the
  canonical full-SFT baseline, and exact image-placeholder validation.
local_adaptation: Export one exact event-prefix PlannerContext and one
  canonical action per record, set `train_on_prompt=false` and
  `mask_history=true`, use `qwen3_vl_nothink`, validate real non-IGNORE labels,
  keep provenance outside the training columns, bind targets to the source
  policy/decisions/audit, copy images into a content-addressed dataset, and
  prohibit formal execution of provisional data. A frozen launch additionally
  requires a structured Gate 3 receipt and a complete tokenizer audit bound to
  the exact dataset and runtime config.
copy_code: no
notes: Gen-Searcher and GenEvolve train assistant reasoning and tool-call text,
  which is incompatible with Gen-Retry's canonical action-only target. Their
  SFT data also contain observed multi-tool assistant turns despite textual
  one-action rules, so current export performs schema validation rather than
  trusting role alternation. The local LLaMA-Factory 0.9.5 image-only patches
  are pre/post-SHA locked: `mm_plugin.py` changes
  `9a7db6d36ac355b0cf4f8dca79408fa7c06c4b10f273405815b28079b53837dc`
  to `0fbdc39f62277ae4caf321c2598496bcbe7163a4f128c2abd896a7f01156dff5`;
  METADATA changes
  `5625dc42b1fd381a11e2350439891caca3e5eb2a2096d58845579b27ed5bf886`
  to `b2f04024c1fc87ec57e7d48019f80ffd49401a86a30e0046b50490fb8db8efd4`
  by moving torchaudio to an audio extra. Audio still fails explicitly when
  unavailable. No Action, memory, score, target selection, harmful/recovery,
  or query-skill supervision rule changed.

### GenEvolve RL And Visual Experience Distillation

source_id: `genevolve_rl_design_2026_08_07`
source_name: GenEvolve paper and local repository
repository_path: `/root/private_data/agentic_image/GenEvolve`
repository_commit: `23c847c559ccc0f95bbf4b3d8925898463822f4c`
repository_license: Apache-2.0
paper: `GenEvolve: Self-Evolving Image Generation Agents via Tool-Orchestrated Visual Experience Distillation`
arxiv_url: `https://arxiv.org/abs/2605.21605v2`
accessed_date: `2026-08-07`
evidence_type: repository-grounded and paper-grounded via `source_researcher`
exact_repository_paths:
- path: `README.md:374-410`
  evidence: the release documents 9,000 SFT trajectories and 3,175 RL cases,
    but explicitly does not release full training scripts.
- path: `genevolve/agent.py:15-17`
  evidence: privileged teacher context belongs to an unreleased training path.
- path: `genevolve/knowledge_tool.py:7-9`
  evidence: dynamic visual-experience memory belongs to the unreleased path.
exact_paper_sections:
- section: `5.3--5.5; Appendices A.5, C.2, D.2, F`
  evidence: GRPO uses 8 prompts and 6 on-policy rollouts per prompt; outcome
    reward combines image and program-text reward. Best/worst rollouts are
    distilled when their gap is at least 0.20, and the reported objective adds
    a teacher-scored selective distillation loss to GRPO.
borrowed_idea: Grouped fresh on-policy rollout, assistant-only masking, and a
  separately auditable auxiliary credit target.
local_adaptation: Gen-Retry uses immutable Geneval2 transitions and exact
  same-state branch returns; it does not make teacher experience
  environment-owned memory or claim a released executable GenEvolve trainer.
copy_code: no
notes: Algorithm details above are paper-grounded, not executable repository
  evidence.

### Gen-Searcher Executable GRPO And Credit Path

source_id: `gen_searcher_executable_rl_2026_08_07`
source_name: Gen-Searcher local RL subtree
repository_path: `/root/private_data/agentic_image/Gen-Searcher`
repository_commit: `e5078d31859bafee6b6b610f0cd40095cc72e2a4`
license: `Gen-DeepResearch-RL/LICENSE` is MIT
accessed_date: `2026-08-07`
evidence_type: repository-grounded via `source_researcher`
exact_repository_paths:
- path: `Gen-DeepResearch-RL/rllm/pyproject.toml`
  evidence: rLLM declares version 0.2.1, Python >=3.10, Transformers >=4.55,
    and an optional verl dependency requiring torch >=2.8.
- path: `Gen-DeepResearch-RL/rllm/scripts/install_verl.sh`
  evidence: the released installer pins torch 2.6.0, embeds verl 0.6.1, and
    installs SGLang 0.4.6.post5; those pins are not safe for vendor HCU Torch.
- path: `Gen-DeepResearch-RL/rllm/vision_deepresearch_async_workflow/train_image_deepresearch_workflow_fsdp_gen.py`
  evidence: `AgentTrainer` wires workflow, tools, reward, and training.
- path: `Gen-DeepResearch-RL/rllm/vision_deepresearch_async_workflow/run/gen_image_deepresearch_8B_fsdp_8gpu.sh`
  evidence: launch uses grouped GRPO, FSDP 8, SGLang TP 2, LR 1e-6,
    temperature 0.7, top-p 0.95, and `seq-mean-token-sum`.
- path: `Gen-DeepResearch-RL/rllm/rllm/parser/chat_template_parser.py:132-162`
  evidence: user/tool observations are loss-masked and assistant tokens train.
- path: `Gen-DeepResearch-RL/rllm/verl/verl/trainer/ppo/core_algos.py:265-328`
  evidence: scalar group-relative advantage is broadcast across valid
    assistant tokens; no action-specific credit is implemented.
- path: `Gen-DeepResearch-RL/rllm/rllm/trainer/verl/agent_workflow_trainer.py:439-450`
  evidence: KL is inactive unless one of the explicit KL paths is enabled.
borrowed_idea: Grouped rollout, assistant-only masks, artifact-backed
  evaluation, error filtering, and prompt-group normalization.
local_adaptation: Gen-Retry keeps action-level Geneval2 credit, canonical state
  IDs, infrastructure-failure exclusion, zero-variance masking, staged dual-
  backend rollout, persisted old/reference log-probs, and active reference KL.
  Stock rLLM's XML parser and runtime pins are not directly reused.
copy_code: no
notes: No code was copied. Gen-DeepResearch-RL/rLLM is MIT; its embedded verl
  is Apache-2.0.

### User-Provided ABC-GRPO Design Discussion

source_id: `user_chatgpt_share_6a75a336_2026_08_07`
source_name: user-provided ChatGPT shared discussion
url: `https://chatgpt.com/share/6a75a336-e5f0-83e8-a3ab-23bd8dee015b`
accessed_date: `2026-08-07`
evidence_type: local-design discussion, not external empirical evidence
borrowed_idea: Geneval2 terminal reward plus atom transition credit and bounded
  same-state pivot branching.
local_adaptation: HPSv3 and descendant top-k backup are deferred in v0.1.
  Source-relative intervention is paired with reducer-best-relative progress,
  and one-step pivot groups do not fabricate terminal descendant credit.
copy_code: no
notes: Claims used by the design were checked against local repositories and
  papers where applicable.

## Prior Broad Notes

| Source | Evidence | Borrowed idea | Not reused directly | Status |
|---|---|---|---|---|
| GenAgent paper | paper-grounded | Image observation and assistant action interleaving; environment image tokens are not agent targets | Free-form self-judge and prompt rewrite; no atom verifier | Keep as background only |
| GEMS paper | paper-grounded | Verifier vector, historical best, compressed experience, on-demand Skills | Raw reasoning/LLM compression as canonical truth | Promoted to formal entry above |
| RS-Gen paper | paper-grounded | Generate-review-correct; generate/edit logical actions | Training-free prompted workflow; no public trainable message schema | Keep as background only |
| Codex AGENTS.md official docs | official-doc-grounded | Root `AGENTS.md` project instruction hierarchy | Do not stuff all docs into AGENTS.md | verified 2026-07-14 |
| Codex Subagents official docs | official-doc-grounded | Project subagents can be configured | Exact model IDs remain local config | verified 2026-07-14 |
