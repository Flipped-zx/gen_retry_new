# External Repository Map

This file is a template. Phase 0 should replace placeholders with verified evidence.

| Source | Absolute path | Commit / version | License | Access | Primary reusable areas |
|---|---|---|---|---|---|
| Legacy Gen-Retry | `<configure>` | `<verify>` | `<verify>` | read-only | Geneval2 adapter, Qianwen adapter, trajectory/SFT audit |
| Gen-Searcher | `<configure>` | `<verify>` | `<verify>` | read-only | message/tool trajectory, masking, decoupled execution |
| GenEvolve | `<configure>` | `<verify>` | `<verify>` | read-only | skill/tool protocol, experience and artifact patterns |
| Geneval2 | `<configure>` | `<verify>` | `<verify>` | read-only/runtime | atom-level evaluator and normalization |

## Rule

No source becomes a v3 runtime dependency merely because it is visible. Reuse requires a module-contract decision and tests in the new repository.
