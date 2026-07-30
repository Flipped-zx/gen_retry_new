# Muse Image Official Technical Blog — Selective Snapshot

## Source identity

- Canonical title: **Introducing Muse Image and Muse Video**
- Publisher/author: **Meta Superintelligence Labs**
- Publication date: **2026-07-07**
- Accessed: **2026-07-29**
- Official page:
  <https://ai.meta.com/blog/introducing-muse-image-muse-video-msl/>
- Evidence class: `official-blog-grounded`

This is the 2026 agentic **Muse Image** release from Meta, not Google's 2023
**Muse: Text-To-Image Generation via Masked Generative Transformers**. Google's
older Muse is a generator architecture and does not make the same agentic
self-refinement claim.

## What the official blog actually discloses

### Agentic generation

Muse Image is described as an agent around image generation rather than a
single prompt-to-image mapping. Its action repertoire includes image
generation, image editing, web search, and code execution. Muse Spark can also
participate in planning and tool use.

### Search and code tools

The blog reports an internal pairwise-preference ablation for search on
knowledge-intensive prompts. The chart shows:

| Category | Search enabled | Search disabled |
| --- | ---: | ---: |
| Identities | 70.2% | 29.8% |
| Brands | 67.9% | 32.1% |
| Landmarks | 67.3% | 32.7% |
| Facts | 56.6% | 43.4% |

It also describes code execution for precise artifacts such as plots and QR
codes. The public post does not disclose the prompt set, sample size, rater or
judge protocol, uncertainty, or significance tests behind the chart.

### Self-refinement

The most relevant behavior for Gen-Retry is a conditional choice among:

- a local edit when the defect is narrow;
- a fresh generation when the draft is globally wrong;
- a tool-use strategy when the missing capability is factual or structural.

Meta says this behavior emerged during reinforcement learning because
self-refinement earned higher reward. The chart reports pairwise preferences
of 57.1% versus 42.9% for text-to-image, 56.3% versus 43.7% for single-image
editing, and 56.6% versus 43.4% for multi-image editing when comparing
self-refinement enabled with disabled. The post publishes no sample sizes,
uncertainty, public trajectory schema, action contract, training target,
reward definition, or reproducible checkpoint.

### Test-time compute

The blog claims that human-preference Elo improves with additional reasoning,
tool calls, and refinement steps. It contrasts deliberate reasoning with
Best-of-N image sampling: Best-of-N reportedly helps early and then saturates,
while reasoning plus tools scales better. The public chart is an internal
ablation and does not expose enough protocol detail for a numerical
cross-system comparison.

For Gen-Retry, the reusable idea is therefore not the claimed curve itself. It
is the requirement to compare an adaptive retry policy against an
**equal-image-call-budget Best-of-N baseline** and to report image, evaluator,
planner, latency, and total-compute cost separately.

### Editing and multi-turn coherence

Muse Image is described as supporting precise edits, coherent repeated edits,
and multi-reference composition. The blog provides examples and Arena
rankings, but not a preservation benchmark that isolates requested changes
from unintended regressions.

## Evidence limits

As of the access date, targeted searches found the official technical blog and
product announcement, but no public Muse Image paper, model card, source code,
weights, evaluator specification, or reproducible ablation protocol. Therefore:

- Muse Image is a related closed-system precedent, not an executable baseline;
- its internal win-rate and Elo charts must not be transcribed as comparable
  Gen-Retry results without missing protocol details;
- the project may borrow experiment questions, not claims of parity,
  superiority, or identical mechanisms;
- the blog's product-specific search, coding, personalization, Muse Spark,
  Content Seal, and multi-reference features are outside Gen-Retry v3's current
  fixed research scope.

The closest genuinely Google-authored verifier-guided precedent is not the
2026 Muse Image system. It is the 2024 RichHF/RAHF work, which uses learned
scalar, spatial, and token-level feedback to filter Muse training candidates
and to drive heatmap-based inpainting followed by score-based selection:

<https://research.google/blog/rich-human-feedback-for-text-to-image-generation/>

That work is recorded separately in `docs/SOURCE_LEDGER.md`; it does not
provide an edit-versus-regenerate planner or canonical cross-attempt memory.

## Repository use

The selective borrowing and proposed ablations are documented in:

`docs/research/muse_image_selective_lessons_and_ablation_plan.md`

The source is also registered in `docs/SOURCE_LEDGER.md`. No Meta text, code,
or media asset is copied into production code or training data.
