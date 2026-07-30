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

## Prior Broad Notes

| Source | Evidence | Borrowed idea | Not reused directly | Status |
|---|---|---|---|---|
| GenAgent paper | paper-grounded | Image observation and assistant action interleaving; environment image tokens are not agent targets | Free-form self-judge and prompt rewrite; no atom verifier | Keep as background only |
| GEMS paper | paper-grounded | Compressed memory beats raw thought; skill/memory engineering | History-conditioned rewrite with high free-text ratio | Keep as background only |
| RS-Gen paper | paper-grounded | Generate-review-correct; generate/edit logical actions | Training-free prompted workflow; no public trainable message schema | Keep as background only |
| Codex AGENTS.md official docs | official-doc-grounded | Root `AGENTS.md` project instruction hierarchy | Do not stuff all docs into AGENTS.md | verified 2026-07-14 |
| Codex Subagents official docs | official-doc-grounded | Project subagents can be configured | Exact model IDs remain local config | verified 2026-07-14 |
