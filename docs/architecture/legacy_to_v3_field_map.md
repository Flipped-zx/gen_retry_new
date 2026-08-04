# Legacy To v3 Field Map

> Historical Phase 0 migration map. Later accepted ADRs supersede backend and
> version details in this file; current execution uses
> `qwen_dual_backend@1` under ADR-0006.

This map is evidence for Phase 1 protocol work. It is not a runtime compatibility
layer and does not authorize imports from the legacy repository.

## Action Protocol

| Legacy evidence | Legacy field / behavior | v3 target | Decision |
|---|---|---|---|
| `src/gen_retry/schemas/episode.py` | `InitialPlanAction`, `RetryReplanAction` stored on attempts | `query_skill`, `generate_image`, `edit_image`, `submit_attempt` discriminated union | Rewrite. v3 cannot keep `initial_plan` / `retry_replan` as actions. |
| `src/gen_retry/collectors/collect_episodes.py` | `generator.generate(action.retry_prompt, ...)` for every retry | `generate_image.instruction` or `edit_image.edit_instruction` | Adapt only the instruction field idea. |
| `src/gen_retry/offline_planner.py` | `teacher_action`, `retry_ready_action`, `previous_action` | canonical parsed `action` event | Rewrite so raw teacher output never enters memory. |
| GenEvolve `genevolve/knowledge_tool.py` | `query_knowledge` returns skill markdown | `query_skill -> tool_response` | Adapt into v3 skill store with version/hash. |

## Attempt And Artifact Fields

| Legacy evidence | Legacy field | v3 target | Decision |
|---|---|---|---|
| `src/gen_retry/schemas/episode.py` | `Attempt.round` | `AttemptRecord.attempt_id`, event order | Rewrite with stable IDs; round can be derived. |
| `src/gen_retry/schemas/episode.py` | `Attempt.image_path` | artifact ref with path, hash, media type, producer | Adapt with stronger artifact metadata. |
| `src/gen_retry/offline_planner.py` | `generation.image_id`, `image_path`, `generation_metadata` | `ImageGenerated` / `ImageEdited` event payload | Adapt behind event schemas. |
| Gen-Searcher `ImageIdManager` and GenEvolve `ImageIdManager` | `IMG_###` display IDs mapped to local/source refs | planner-visible artifact IDs plus private artifact registry | Adapt; do not persist base64. |

## Geneval2 And Constraint Fields

| Legacy evidence | Legacy field | v3 target | Decision |
|---|---|---|---|
| Geneval2 `geneval2_data.jsonl` | `prompt`, `atom_count`, `vqa_list`, `skills` | `TaskSpec.constraints[]` | Adapt directly through schema builder. |
| `src/gen_retry/evaluators/geneval2_result_normalizer.py` | `NormalizedConstraint.type`, `target`, `expected`, `detected`, `status`, `details` | canonical per-constraint observation | Adapt field meanings; replace dataclasses with schema payloads. |
| `src/gen_retry/evaluators/geneval2_result_normalizer.py` | `critical_failure_types` | derived evaluator summary | Environment-owned; planner may observe but not predict. |
| `src/gen_retry/evaluators/geneval2_adapter.py` | command or score-list loading | `Geneval2Adapter.evaluate(TaskSpec, artifact)` | Rewrite adapter boundary. |

## Memory And Transition Fields

| Legacy evidence | Legacy field / symbol | v3 target | Decision |
|---|---|---|---|
| `src/gen_retry/collectors/collect_episodes.py` | `_best_attempt`, `_state_memory` | reducer-owned `best_so_far` | Adapt algorithm, not mutable collector state. |
| `src/gen_retry/collectors/collect_episodes.py` | `_transition_sets` | reducer-owned fixed/persistent/new/regressed sets | Adapt with constraint IDs instead of fuzzy dict keys. |
| `src/gen_retry/offline_planner.py` | `compute_transition`, `build_memory` | deterministic reducer output | Adapt tests around replay determinism. |
| `src/gen_retry/offline_planner.py` | `compact_retry_history` | `PlannerView.compact_history` | Adapt, ensuring no raw assistant output or raw evaluator blobs. |

## SFT And Masking Fields

| Legacy evidence | Legacy field / behavior | v3 target | Decision |
|---|---|---|---|
| `scripts/build_geneval2_masked_multiturn_sft.py` | `turn_mask`, `assistant_turn_tags` | exact SFT loss masks | Defer to Phase 4; preserve evidence. |
| Gen-Searcher `tinker_data_processor.py` | prompt/observation mask `0.0`, response/action mask `1.0` | train assistant canonical actions only | Defer to Phase 4; adapt principle. |
| `scripts/build_geneval2_masked_multiturn_sft.py` | risky/recovery tags | harmful action masking policy | Defer to Gate 3. |

## Explicit Retirements

| Legacy item | Reason |
|---|---|
| Separate `rewrite_prompt` / `retry_replan` action surface | Conflicts with v3 fixed action set. |
| Mutable episode JSON as source of truth | Conflicts with event-sourced memory invariant. |
| Raw assistant messages in saved trajectories | Conflicts with v3 memory and SFT target policy. |
| Legacy Qwen generator/regenerator split | Retire the legacy action/backend coupling. Current ADR-0006 routing is `generate_image -> Qwen-Image-2512` and `edit_image -> Qwen-Image-Edit-2511`, while backend fields remain outside the Action. |
