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
local_adaptation: v3 exposes logical `generate_image` and `edit_image` through one `QianwenImageEditAdapter`.
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
dirty_status: dirty
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
dirty_status: dirty
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

## Prior Broad Notes

| Source | Evidence | Borrowed idea | Not reused directly | Status |
|---|---|---|---|---|
| GenAgent paper | paper-grounded | Image observation and assistant action interleaving; environment image tokens are not agent targets | Free-form self-judge and prompt rewrite; no atom verifier | Keep as background only |
| GEMS paper | paper-grounded | Compressed memory beats raw thought; skill/memory engineering | History-conditioned rewrite with high free-text ratio | Keep as background only |
| RS-Gen paper | paper-grounded | Generate-review-correct; generate/edit logical actions | Training-free prompted workflow; no public trainable message schema | Keep as background only |
| Codex AGENTS.md official docs | official-doc-grounded | Root `AGENTS.md` project instruction hierarchy | Do not stuff all docs into AGENTS.md | verified 2026-07-14 |
| Codex Subagents official docs | official-doc-grounded | Project subagents can be configured | Exact model IDs remain local config | verified 2026-07-14 |
