# Original GenEval SFT Rollout Review

Verdict: `PASS_WITH_REQUIRED_CHANGES`

Accepted name: `original_geneval_metadata_aware_agent@1`.

The conversion is a valid deterministic benchmark/runtime adapter, not score
tampering. It is not protocol-equivalent to prompt-only GenEval because the
Planner sees metadata-derived constraints before its first action. Online VQA
pass count and Soft-TIFA GM must remain labeled proxy metrics. The final score
must be independently computed by the pristine original GenEval detector on
exactly one canonical reducer-submitted image per prompt.

Required implementation controls:

- fail closed and cover all 553 rows and six tags;
- preserve every include/exclude, color, count, and position semantic;
- bind dataset, raw-row, and semantic-row hashes plus upstream commit;
- reject missing/duplicate submissions, metadata mismatch, and artifact digest mismatch;
- disclose checkpoint, dual-backend profile, attempt/image-call budget, proxy
  configuration, one-image policy, and detector commit/options;
- do not compare one-image prompt success to upstream best-of-four without a
  separately named matched-budget baseline.

No numbered gate is triggered because canonical protocol and reducer semantics
remain unchanged.
