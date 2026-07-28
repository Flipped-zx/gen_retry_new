# Geneval2-Compatible Synthetic Prompt Pool Review

## Question

Can v3 expand a Geneval2-style prompt pool for future SFT without training on
the official GenEval2 test set?

## Evidence

- Original GenEval provides a rule sampler:
  `/root/private_data/agentic_image/geneval/prompts/create_prompts.py`.
  It samples object, count, color, position, and color-attribution prompts and
  writes generation prompts plus evaluation metadata.
- Original GenEval README explicitly documents rerunning the sampler with a
  different seed:
  `/root/private_data/agentic_image/geneval/README.md`.
- Local GenEval2 has no equivalent prompt generator. Its public surface is the
  fixed `geneval2_data.jsonl`, `evaluation.py`, and `soft_tifa_analysis.py`
  under `/root/private_data/agentic_image/GenEval2`.
- GenEval2 rows contain `prompt`, `atom_count`, `vqa_list`, and `skills`. The
  local 800 rows are balanced at 100 prompts for each `atom_count` from 3
  through 10, with skill taxonomy `attribute`, `count`, `object`, `position`,
  and `verb`.

## Review Result

This is feasible for v3 as a separate synthetic data source, but it should be
named `geneval2_synthetic_v1` or similar, not "official GenEval2 expansion".
The current v3 stack already accepts compatible rows through
`task_spec_from_geneval2_row`; six manually constructed rows in
`artifacts/phase5/geneval2_synthetic_prompt_review_samples.jsonl` validate
through that path.

The correct implementation boundary is:

1. Build a deterministic semantic AST generator.
2. Generate prompt text, `vqa_list`, `skills`, and `atom_count` from the same
   AST.
3. Record `template_id`, `vocab_version`, `source_seed`,
   `semantic_family_id`, and provenance on every row.
4. Keep the official 800 GenEval2 rows as held-out evaluation unless a later
   experiment deliberately defines a separate train/eval split.

## Theoretical Issues

- Test contamination: using official GenEval2 prompts or near-isomorphic
  variants as SFT train data makes later official GenEval2 evaluation unfair.
- Split leakage: v3's current Phase 4 split groups by raw original-prompt hash.
  Synthetic data needs family-level grouping, for example by sorted object
  tuple, attributes, relation, verb, template, and atom-count bucket.
- Template overfitting: a highly regular generator can teach the policy to
  exploit prompt grammar rather than learn verifier-grounded retry behavior.
- VQA correctness: hand-written prompt text and VQA atoms can drift apart. The
  AST must be the single source of truth for both.
- Evaluator gaming: if Soft-TIFA feedback becomes the only teacher filter, the
  policy may learn evaluator quirks. Keep human spot checks and secondary
  evaluator/audit samples.
- Distribution shift: synthetic rows may be more compositional but less natural
  than downstream user prompts. Preserve official GenEval2 only as one held-out
  axis; add non-Geneval prompt families later if the claim expands.
- License: GenEval2 is CC BY-NC 4.0. Derived prompt pools based on its row
  vocabulary/style should be treated as noncommercial and attributed.

## Sample Review

The six sample rows cover:

- atom counts: 6, 7, 8, and 9;
- skills: `attribute`, `count`, `object`, `position`, and `verb`;
- both two-entity and three-entity compositions;
- article-derived count-one VQA atoms that are intentionally not counted in
  `atom_count`, matching the GenEval2 README note.

They are useful as design probes only. They are not enough for SFT and should
not enter a training set without a formal generator, deduplication, family split,
and review audit.

## Recommendation

Proceed with a dedicated Phase 5 synthetic pool generator, but make the
fairness invariant explicit:

```text
official GenEval2 800 rows: held-out eval
geneval2_synthetic_v1 rows: train/validation, family-split before rollout
```

Before producing bulk SFT data, add an invariant test that rejects any train
sample whose `semantic_family_id` collides with held-out official GenEval2 or
with validation/test synthetic families.

This small review does not trigger a review gate. A formal Phase 5 dataset
generator that becomes the main SFT source should get a focused fairness and
data-design review because it affects whether the experiment proves the claimed
generalization.
