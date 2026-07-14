# Phase 3 Selection Provenance

This selection was made before any Phase 3 live rollout.

- Candidate pool artifact: `artifacts/phase3/candidate_pool.jsonl`
- Selected prompts artifact: `artifacts/phase3/selected_ten_prompts.json`
- Coverage matrix artifact: `artifacts/phase3/constraint_coverage_matrix.json`
- Selector: deterministic greedy `difficulty + new_coverage + rare_combination_bonus - imbalance_penalty - semantic_duplication_penalty`.
- Legacy evidence use: difficulty and failure-signature context only.
- Legacy images or attempts imported: no.
- First action requirement for future rollouts: fresh `generate_image` or
  allowed `query_skill` followed by fresh generation.

## Selected Source Rows

- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:563`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:604`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:617`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:624`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:672`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:694`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:708`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:724`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:725`
- `geneval2@a6e82d2289e8d418f27f0adee77908b07060eea3:geneval2_data.jsonl:796`
