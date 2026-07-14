# Phase 3 Candidate Pool Report

Candidate pool source is Geneval2 prompt metadata. No live image generation
or evaluator calls were run while constructing this pool.

- Candidate count: 800
- Historical-evidence matched candidates: 99
- Constraint type counts: {'attribute': 1214, 'count': 2025, 'object': 2025, 'position': 662, 'verb': 86}
- Constraint-count distribution: {3: 59, 4: 21, 5: 101, 6: 105, 7: 75, 8: 113, 9: 128, 10: 143, 11: 55}

The actual Geneval2 skill taxonomy is preserved as constraint types:
`attribute`, `count`, `object`, `position`, and `verb`.

Legacy evidence, when present, is difficulty/context evidence only. It
does not import legacy images or legacy attempts into Phase 3 episodes.
