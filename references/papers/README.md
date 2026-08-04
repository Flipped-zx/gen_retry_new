# Paper Catalog

The parent `agentic_image/` directory currently contains a small shared paper
corpus. The PDFs are not duplicated into this Git repository. Instead, this
catalog records the relevant works and routes grounded conclusions into
`docs/SOURCE_LEDGER.md` and `docs/research/`.

| Work | Canonical source | Local depth | Gen-Retry role |
| --- | --- | --- | --- |
| Generation Navigator | arXiv `2605.17969v1` | core, section-grounded | Direct comparison for state-conditioned retry, best-history selection, regression retention, and turn efficiency |
| GenEvolve | arXiv `2605.21605v2` | core, paper + repository grounded | Tool/Skill trajectories, assistant-only masking, artifact-backed rendering; not image-level retry evidence |
| Gen-Searcher | arXiv `2603.28767v3` | core, paper + repository grounded | Tool trajectory serialization, masking, caching, image execution separation; search itself is out of scope |
| GEMS | arXiv `2603.28088v1` | core, section-grounded | Direct prior for verifier vectors, historical best, compressed experience, and on-demand Skills; not a protocol source |
| NEWTON | arXiv `2605.18396v2` | catalogued only | Video/physics planning is outside the current image-retry question |

`generation_navigator_2605.17969/manifest.json` records the newly supplied
PDF's immutable metadata and checksum. Its optional local PDF cache lives in
that same directory but is ignored by Git.

## Inclusion Rule

A paper moves from `catalogued` to `section-grounded` only when its exact
sections are recorded in `docs/SOURCE_LEDGER.md`. A repository-derived claim
also needs commit, path/symbol, dirty status, and license evidence. Broad
related-work similarity is never enough to alter production behavior.
