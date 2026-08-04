# External Reference Library

This directory is the repository-local index for external evidence. It does
not make external repositories part of the Gen-Retry runtime.

## Ownership

| Location | Purpose | Source-of-truth role |
| --- | --- | --- |
| `references/papers/` | Paper catalog, immutable metadata, and optional local PDF caches | Source inventory only |
| `references/web/` | Bounded snapshots of web-only primary sources | Source inventory only |
| `docs/SOURCE_LEDGER.md` | Exact claims, source sections/paths, licenses, and adaptation decisions | Grounded evidence ledger |
| `docs/research/` | Cross-source interpretation and experiment implications | Local design analysis |
| `docs/decisions/` | Accepted protocol or architecture decisions | Decision source of truth |

The order matters: a paper or repository can motivate a local experiment, but
it does not silently change a schema, action, reducer, score policy, or SFT
rule. Such a change requires the normal ADR and review-gate process.

## Repository Boundary

- `Gen-Searcher`, `GenEvolve`, Geneval2, and legacy Gen-Retry remain external,
  read-only evidence roots configured through `configs/paths/local.yaml`.
- Other sibling Gen-Retry versions are deliberately excluded from this
  reference library. They are easy to confuse with the current protocol and
  are not part of the current evidence review.
- External source code is not copied or imported here. A future code copy
  still requires exact commit/path/license evidence and a v3 contract.
- Paper PDFs are local reading conveniences. Their metadata and SHA-256 are
  versioned, while the binaries are ignored to avoid repository bloat and
  accidental redistribution. Canonical publisher/arXiv URLs remain the
  portable source locators.

Start with `docs/research/related_work_evidence_map.md` for the consolidated
answer to what Gen-Retry has borrowed, rejected, and still needs to test.
