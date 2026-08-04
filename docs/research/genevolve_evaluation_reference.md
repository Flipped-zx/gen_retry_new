# GenEvolve Evaluation Reference And Gen-Retry Design Lessons

## Status And Scope

This document records the GenEvolve evaluation design as external evidence for
future Gen-Retry quality-preserving retry work. It is a research reference, not
an accepted Gen-Retry protocol or score-policy change.

The main reason for this record is a distinction that the earlier Gen-Retry
source archaeology did not preserve clearly enough:

```text
GenEvolve agent trajectory
  -> search / image search / Skill queries
  -> one prompt-reference program z = (gen_prompt, references)
  -> one reference-conditioned image render
  -> one final-image evaluation

Gen-Retry trajectory
  -> generate an image Attempt
  -> evaluate atoms
  -> edit or regenerate a historical Attempt
  -> evaluate again
  -> possibly repeat edit-on-edit
  -> submit one historical Attempt
```

GenEvolve therefore does not demonstrate that repeated image editing preserves
texture or rendering quality. It mainly avoids that failure mode by rendering
each final prompt-reference program once from clean external references.

## Provenance

Repository evidence:

- source: `/root/private_data/agentic_image/GenEvolve`
- commit: `23c847c559ccc0f95bbf4b3d8925898463822f4c`
- branch: `main`
- tracked license: Apache-2.0
- evidence access: read-only `source_researcher`

Paper evidence:

- title: `GenEvolve: Self-Evolving Image Generation Agents via Tool-Orchestrated Visual Experience Distillation`
- arXiv: `https://arxiv.org/abs/2605.21605`
- version: v2, revised 2026-05-22
- relevant sections: Method, Experiments, Data Construction, Training Details,
  Evaluation Details, and the main-result and ablation tables

No GenEvolve code is copied into Gen-Retry by this document.

## 1. What GenEvolve Actually Evaluates

### 1.1 The image is rendered once

The GenEvolve agent performs a multi-turn tool trajectory, but the image model
does not participate in those turns:

1. `image_search` downloads external reference images and assigns stable image
   IDs.
2. The agent uses search, image search, and `query_knowledge` observations to
   produce one final `gen_prompt` and one or two selected references.
3. `scripts/generate_images.py` calls `backend.generate(...)` once for that
   program.
4. The Qwen wrapper stores `out.images[0]` as the only candidate image.

Exact repository paths:

- `genevolve/agent.py:276-351`: tool-loop execution
- `genevolve/agent.py:356-390`: final reference ordering and truncation
- `scripts/generate_images.py:79-102`: one generator call and output record
- `genevolve/generator.py:150-176`: one Qwen pipeline call and first output

The released path contains no image-level edit-on-edit loop, history-aware
image rollback, mask or crop execution, image-quality retry, or inference-time
multi-candidate selector. HTTP `max_retries` handles request failures only.

### 1.2 Qwen renderer configuration

The released Qwen path uses:

| Field | Value |
| --- | --- |
| Model | `Qwen-Image-Edit-2511` |
| Inference steps | 40 |
| True CFG | 4.0 |
| Guidance scale | 1.0 |
| Negative prompt | blank string containing one space |
| Reference scaling | first reference long side near 1024 |
| Images per program | 1 |
| Default seed | 0 |

Evidence is in `genevolve/generator.py:89-176` and
`genevolve/generator.py:188-279`.

These values are close to the Gen-Retry production edit configuration. The
important difference is the source and lineage: GenEvolve conditions once on
clean external references, while Gen-Retry can condition on an already edited
Attempt and accumulate rendering drift.

## 2. Dataset And Split Accounting

### 2.1 Formal benchmark

GenEvolve-Bench contains 594 prompt and ground-truth-image pairs:

| Partition | Prompts |
| --- | ---: |
| Knowledge-Anchored | 335 |
| Quality-Anchored | 259 |
| Total | 594 |

The ground-truth image is used by the formal evaluator for visual identity and
quality comparison. This differs from Gen-Retry's current Flow-DPPO/Geneval2
episodes, which have prompt atoms but no per-prompt gold rendering that defines
the desired texture, lighting, or exact identity.

### 2.2 Training-data counts must not be mixed with benchmark counts

The paper and release expose several different denominators:

| Data role | Count / description |
| --- | --- |
| Released SFT trajectories | 9,000 |
| Paper SFT accounting | 8,800 train + 200 held out |
| Ground-truth self-evolution cases | 3,175 |
| Self-evolution pool | 2,575 |
| Optimization / validation within pool | 2,446 / 129 |
| Formal evaluation cases | approximately 600; released benchmark is 594 |

These counts describe different stages. They must not be combined into one
training or evaluation denominator.

## 3. KScore Dimensions

The formal evaluator judges the generated image as Image 1 and the
ground-truth image as Image 2. Every dimension is higher-is-better. The rubric
asks the judge to choose `0`, `0.5`, or `1`, although the released parser will
retain other values in `[0, 1]` if the judge emits them.

### 3.1 Faithfulness

Faithfulness asks whether the generated image satisfies the requested content
and structure:

- subjects and scene;
- props;
- action and relations;
- quantities;
- requested style.

It does not require exact identity agreement with the ground-truth image.

| Score | Meaning |
| ---: | --- |
| 1.0 | All requested content and structure are present. |
| 0.5 | Minor omission or staging error that does not change the core request. |
| 0.0 | A key element, action, relation, count, or requested style is wrong. |

Code evidence: `scripts/evaluate_images.py:237-253`.

### 3.2 Visual correctness

Visual correctness uses stable ground-truth visual details rather than pixel
similarity. Examples include:

- face and hair silhouette;
- clothing design, colors, and patterns;
- prop geometry;
- logo or emblem details;
- landmark facade and massing.

Different camera views and layouts may still pass. A material identity or
grounded-detail mismatch can fail even when the prompt is broadly followed.

| Score | Meaning |
| ---: | --- |
| 1.0 | No material difference from the stable ground-truth identity/details. |
| 0.5 | Clearly the same visual instance with only minor variation. |
| 0.0 | Any substantial identity or grounded-detail mismatch. |

Code evidence: `scripts/evaluate_images.py:190-195,255-270`.

### 3.3 Text accuracy

For tasks containing visible text, all relevant text should be present,
legible, and correct.

| Score | Meaning |
| ---: | --- |
| 1.0 | All relevant text is present, readable, and correct. |
| 0.5 | Some text is wrong or missing, but the intended meaning remains clear. |
| 0.0 | Key text is absent, unreadable, malformed, or incorrect. |

For tasks without readable text, the judge sets `text_accuracy_na=true` and
the released implementation stores `text_accuracy=0.5`. This case has an
important paper/code inconsistency documented in Section 4.

Code evidence: `scripts/evaluate_images.py:272-286`.

### 3.4 Aesthetics

Aesthetics is not an absolute no-reference image-quality score. It is a strict
comparison with the ground-truth image:

| Score | Meaning |
| ---: | --- |
| 1.0 | Masterpiece-level and not worse overall than the ground truth. |
| 0.5 | Very attractive and polished, but below the top or ground-truth level. |
| 0.0 | Clearly worse, ordinary, cluttered, or affected by artifacts/noise. |

Code evidence: `scripts/evaluate_images.py:288-295`.

This dimension is the closest GenEvolve measurement to the Gen-Retry user's
concern about texture and high-quality rendering. It still does not isolate
microtexture preservation, edit drift, non-target-region changes, or
source-to-output consistency.

## 4. KScore Formula And A Critical Reproduction Conflict

For a task with text, the documented aggregate is:

```text
KScore = 0.1 * Faithfulness
       + 0.4 * Visual correctness
       + 0.4 * Text accuracy
       + 0.1 * Aesthetics
```

Consequences:

- aesthetics contributes only 10 percent;
- visual correctness and text accuracy together contribute 80 percent;
- a system can improve total KScore while its aesthetics score decreases;
- total KScore must not be used as evidence that texture or high-quality feel
  was preserved.

### 4.1 Paper semantics for tasks without text

The paper says that when `text_accuracy_na=true`, the score is renormalized
over the remaining three dimensions. The implied formula is:

```text
KScore_paper_no_text =
    (0.1 * F + 0.4 * V + 0.1 * A) / 0.6
```

### 4.2 Released-code semantics for tasks without text

The released evaluator instead assigns `T=0.5` and keeps the original formula:

```text
KScore_release_no_text =
    0.1 * F + 0.4 * V + 0.4 * 0.5 + 0.1 * A
```

Evidence:

- paper: Appendix Evaluation Details / Reward Rubric
- `scripts/evaluate_images.py:501-515`: per-row computation
- `scripts/evaluate_images.py:520-540`: summary computation
- `README.md:228-232`: claims agreement with the paper formula

The release-code formula gives no-text rows a fixed `0.2` contribution and a
maximum overall score of `0.8`. That is incompatible with the paper's stated
renormalized `[0, 1]` semantics.

It is currently unconfirmed which implementation produced every published
main-table value. Any reproduction must version the choice explicitly as, for
example, `genevolve_kscore_paper_renorm` or
`genevolve_kscore_release_code_v1`. Gen-Retry must not silently copy either
formula.

## 5. Formal Evaluation Runtime

### 5.1 Inputs and judge request

The evaluator reads:

- original prompt;
- generated-image path;
- ground-truth-image path;
- generation success metadata.

Generated image is always Image 1 and ground truth is Image 2. Inputs are
converted to JPEG at quality 100 and resized only if the longest side exceeds
4096.

The released defaults are:

| Field | Default |
| --- | --- |
| API shape | OpenAI-compatible multimodal chat completion |
| Judge model | `gemini-3.1-pro-preview` |
| Temperature | 0 |
| Max output tokens | 8192 |
| Request timeout | 300 seconds |
| API retries | up to 20 |

Evidence: `scripts/evaluate_images.py:40-47,137-178,360-392,678-695`.

### 5.2 Parsing behavior

The parser accepts more than strict rubric JSON:

- fenced JSON;
- trailing-comma repair;
- regex recovery of flattened fields;
- arbitrary numeric values clipped to `[0, 1]` and rounded to two decimals.

Therefore the prompt's nominal three-level scale is not a strict data
invariant. A Gen-Retry quality evaluator should schema-validate the normalized
observation and preserve the raw judge response only as a non-memory artifact.

Evidence: `scripts/evaluate_images.py:129-134,306-357,395-412`.

### 5.3 Aggregation and missing cases

Normal dimension means use only rows with `eval_success=true`. The benchmark
summary separately records denominator and missing/failed counts. Only overall
KScore receives an `overall_missing_zero` form:

```text
overall_missing_zero = successful_overall_mean * success_count / denominator
```

The four component metrics do not receive missing-as-zero variants. Reports
must therefore state whether an overall number is success-only or
missing-zero-adjusted.

Evidence: `scripts/evaluate_images.py:520-559,562-593,634-675`.

### 5.4 Resume behavior

The evaluator atomically rewrites `results_eval.json` after completed futures
and finally writes:

- `results_eval.json`;
- `summary.json`;
- `summary.csv`.

On resume, a prior row is skipped if it already has a score dictionary or even
if it only contains the `eval_success` key. A failed evaluation row is
therefore treated as terminal and is not automatically re-judged.

Evidence: `scripts/evaluate_images.py:91-97,715-788`.

This is valid artifact-resume behavior if explicitly intended, but it is not a
quality-retry policy. Gen-Retry should continue to distinguish infrastructure
failure, terminal evaluator failure, and executed image-quality outcome.

## 6. Training Reward Is Not Final Evaluation

For self-evolution training, GenEvolve samples six independent agent
trajectories per prompt. Every trajectory ends in a prompt-reference program,
and every program receives one image render. The six images are siblings, not
successive edits of one image.

The training reward is described as:

```text
training_reward = 0.5 * image KScore
                + 0.5 * program-text sufficiency reward
```

The program-text reward uses the levels:

```text
{0.00, 0.25, 0.50, 0.75, 1.00}
```

It judges whether the prompt-reference program is executable and sufficiently
grounded. Best/worst trajectory comparisons with a reward gap are then used to
distill experience slots such as search, Skill use, references, prompt
construction, and failure patterns.

The paper's final result table reports image KScore components, not the
50/50 training reward. These two scalars must never be compared as if they
were the same metric.

## 7. Main Results Relevant To Quality Preservation

For the GenEvolve Qwen-Image-Edit path, the reported main result is:

| Metric | GenEvolve + Qwen-Image-Edit |
| --- | ---: |
| Faithfulness | 0.5303 |
| Visual correctness | 0.1338 |
| Text accuracy | 0.4907 |
| Aesthetics | 0.6347 |
| KScore | 0.3663 |

The weighted components reproduce the reported total:

```text
0.1 * 0.5303 + 0.4 * 0.1338 + 0.4 * 0.4907 + 0.1 * 0.6347
= 0.3663
```

However:

- raw Qwen-Image aesthetics: `0.6751`;
- Gen-Searcher + Qwen-Image-Edit aesthetics: `0.6377`;
- GenEvolve + Qwen-Image-Edit aesthetics: `0.6347`.

GenEvolve improves its total score while remaining `0.0404` below raw
Qwen-Image on aesthetics. This is direct evidence that an aggregate benchmark
gain does not imply preservation of high-quality rendering.

### 7.1 Stage ablation

| Stage | KScore | Aesthetics |
| --- | ---: | ---: |
| Raw Qwen-Image | 0.2987 | 0.6751 |
| Untuned workflow | 0.3317 | 0.5867 |
| + SFT | 0.3480 | 0.5785 |
| + GRPO | 0.3548 | 0.6197 |
| Full GenEvolve | 0.3663 | 0.6347 |

Interpretation boundaries:

- workflow and SFT improve aggregate KScore while aesthetics initially falls;
- GRPO and full experience distillation recover part of that aesthetics loss;
- full aesthetics still does not recover the raw Qwen-Image level;
- the ablation changes the whole agent/program workflow and training stage;
- it does not isolate an image-edit quality-preservation mechanism;
- none of these stages evaluates repeated edit-on-edit.

## 8. Gallery And Quickstart Are Not Qwen Evaluation Evidence

The README quickstart defaults to Nano Banana Pro, not the released open Qwen
path. The Nano Banana Pro main-table aesthetics score is `0.9222`, far above
the Qwen path's `0.6347`.

Consequently, attractive README or gallery images cannot establish that:

- Qwen-Image-Edit preserves quality across repeated edits;
- the open Qwen backend matches Nano Banana Pro;
- qualitative examples represent the full 594-prompt distribution;
- GenEvolve solves the Gen-Retry edit-on-edit drift problem.

Gallery examples are useful qualitative evidence only when their backend,
prompt-reference program, reference images, seed, and selection policy are
recorded.

## 9. What Transfers To Gen-Retry

### 9.1 Transferable evaluation principles

| GenEvolve lesson | Gen-Retry adaptation |
| --- | --- |
| Report component scores, not only KScore | Continue reporting atoms/GM and add an independent quality view rather than hiding quality inside GM. |
| Compare against a stable visual target | Keep an immutable initial or source-free generation quality anchor when no gold image exists. |
| Sample independent sibling programs | Prefer shallow candidates from a clean anchor over long edit-on-edit chains when budget permits. |
| Evaluate prompt correctness separately from aesthetics | Keep Geneval2 task correctness separate from texture, material, lighting, artifacts, and overall quality. |
| Persist generated and evaluation artifacts | Version the quality evaluator, raw response, normalized result, aggregation policy, and missing-case semantics. |
| Distill best/worst program experiences | Mine quality-preserving and quality-damaging transitions only from executed, evaluator-grounded image pairs. |

### 9.2 Non-transferable assumptions

Gen-Retry must not copy these assumptions directly:

- GenEvolve has a ground-truth image for every formal evaluation case;
- external image search is in scope for the current Gen-Retry problem;
- a single final-image KScore measures transition preservation;
- one render per program validates multi-turn editing;
- a 10-percent aesthetics weight is sufficient for quality-sensitive retry;
- the released no-text KScore semantics are settled;
- program-text sufficiency is equivalent to a retry-action quality target.

### 9.3 Proposed Gen-Retry quality evaluation view

Before changing the reducer or Action Protocol, a research-side evaluation
record should keep separate fields:

```text
task correctness
  - atom pass count
  - Geneval2 Soft-TIFA GM

transition preservation
  - source and quality-anchor attempt IDs
  - edit lineage depth
  - target-region change
  - non-target-region drift
  - identity / composition preservation

rendering quality
  - fine texture and material realism
  - lighting and tonal continuity
  - oversaturation / plastic or clip-art shift
  - ghosting, malformed edges, and other artifacts
  - pairwise preference against the quality anchor

provenance
  - quality evaluator and rubric version
  - input image roles
  - raw-response artifact reference
  - normalized observation
  - missing / failed / success status
```

The initial use should be offline auditing and paired selection research. It
must not silently replace the frozen reducer-best comparator.

### 9.4 Candidate selection lesson

GenEvolve's six training rollouts suggest a useful budget trade-off:

```text
current pattern:
  one candidate -> edit child -> edit child -> edit child

candidate research pattern:
  quality anchor -> shallow candidate A
                 -> shallow candidate B
                 -> optional source-free regeneration C
```

This is a local-design hypothesis, not a conclusion from GenEvolve. The paired
experiment must hold total image calls fixed and report:

- atom pass / GM;
- quality preference against the anchor;
- target fix and preserved-atom regression;
- edit depth;
- failed or missing outputs;
- compute and latency.

### 9.5 Connection to the current 200 Gen-Retry trajectories

The fixed batch under `runs/phase7_flow_dppo200_fresh8_v1` contains 200
episodes and 684 evaluated images. Its 484 retries include 431 edits. The
formal selector uses atom pass-count, Geneval2 GM, and earlier Attempt only;
it has no aesthetics or transition-preservation observation.

A read-only image-side audit gives a more precise boundary for the proposed
quality guard. The audit resized grayscale images to 384 pixels and computed
Laplacian variance, Tenengrad, Gaussian-sigma-2 high-pass deviation, radial
FFT high-frequency energy share, and Sobel fine-edge density. Paired tests
used Wilcoxon statistics and 2,000 bootstrap resamples with seed `20260802`.
These settings are recorded for reproducibility, not promoted as a production
quality evaluator:

- among the 149 retried episodes, first-to-submitted fine-edge density fell in
  79.9 percent of pairs while contrast, saturation, and coarse edge sharpness
  increased;
- among the 119 episodes submitting an edit output, FFT high-frequency share
  fell in 57.1 percent and fine-edge density fell in 91.6 percent;
- this is compatible with loss of natural microtexture plus harder, brighter,
  more saturated, plastic or illustration-like surfaces, not uniform defocus;
- the high-frequency proxy does not decrease monotonically with edit lineage
  depth; a first full-frame edit can already create the largest style shift;
- semantic historical-best rollback blocks some later detail loss, but only as
  a side effect because quality is not part of the comparator.

Representative cases include:

- `phase3_ep_121`: one edit fixes the white-glass zebra atom but washes out
  stripe, face, mane, and refraction detail;
- `phase3_ep_056`: four edits reach 10/10 atoms while photographic pastry and
  feather texture becomes flatter and more saturated;
- `phase3_ep_040`: a later edit removes or washes out several subjects, and
  semantic rollback correctly returns to the initial image;
- `phase3_ep_053`: a raccoon-to-stone texture replacement is semantically
  required, showing why frequency and similarity proxies cannot serve as the
  final quality truth.

These image statistics are monitoring proxies, not human aesthetics labels.
They support a source-output quality gate on every edit. They do not support a
claim that edit depth alone determines quality, so a depth cap should remain a
secondary circuit breaker rather than the primary preservation mechanism.

## 10. Related Multi-Turn Editing Evidence

GenEvolve does not evaluate repeated image editing, but public work confirms
the failure mode:

- MagicBrush, `https://arxiv.org/abs/2306.10012`, reports that all evaluated
  methods degrade in multi-turn editing because iterative errors accumulate;
  human consistency and image-quality gaps grow with edit turns.
- FreqEdit, `https://arxiv.org/abs/2512.01755`, attributes multi-turn subject
  deformation, edge over-sharpening, and texture collapse to accumulated
  high-frequency information loss. It injects reference high-frequency
  velocity during denoising with spatial adaptation and path compensation.

The public FreqEdit implementation at commit
`cf7f9857878004fd8d219b9489baccd96e1e31ac` is MIT-licensed but targets the
older `QwenImageEditPipeline`, not Gen-Retry's
`QwenImageEditPlusPipeline` for 2511. It is evidence for a research direction,
not a production-ready adapter dependency.

## 11. Decisions And Review Boundary

This document supports the following future investigation:

1. Preserve an immutable quality anchor in offline analysis.
2. Compare shallow anchor branching with edit-on-edit under an equal image-call
   budget.
3. Add a versioned quality audit that reports independent dimensions rather
   than one opaque scalar.
4. Keep rubric-best and proposed quality-feasible selection results separate
   until paired human-calibrated evidence exists.
5. Treat visually damaging semantic improvements as context-only candidates
   when evaluating future SFT supervision policy.

Merely recording these observations does not trigger a review gate. Changing
PlannerContext ownership, reducer best semantics, persistent quality facts,
Action fields, or SFT target policy would trigger the applicable high-level
review and Gate 3 re-freeze requirements.

## 12. Claim Boundary

Supported:

- GenEvolve's released Qwen path is one-shot reference-conditioned rendering,
  not multi-turn image retry.
- KScore places only 10 percent weight on aesthetics.
- GenEvolve's Qwen aggregate score improves while its aesthetics remains below
  raw Qwen-Image.
- the released evaluator and paper disagree on no-text KScore handling.
- GenEvolve's component-wise and artifact-backed evaluation design contains
  useful lessons for Gen-Retry quality auditing.

Not supported:

- GenEvolve has solved texture loss under repeated editing.
- GenEvolve gallery quality represents its Qwen benchmark distribution.
- KScore is directly comparable to Geneval2 Soft-TIFA GM.
- GenEvolve's ground-truth-relative aesthetics rubric can be used unchanged
  when Gen-Retry has no gold image.
- any proposed quality metric or threshold is ready to change reducer selection
  without paired calibration and review.
