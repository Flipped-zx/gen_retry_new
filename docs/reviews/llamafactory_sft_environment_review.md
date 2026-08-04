# LLaMA-Factory SFT Environment Review

Date: 2026-08-03  
Scope: data adapter, Gate 3 launch guard, token-label audit, split handling,
image immutability, and isolated runtime bootstrap  
Final verdict: **PASS**

The first read-only review returned `REQUEST_CHANGES` for five issues:

1. a weak Gate 3 receipt and executable provisional path;
2. missing positive/recovery label and source-policy binding;
3. duplicate-prompt cross-split risk;
4. mutable external image paths without hash revalidation;
5. a system-site SFT venv containing incompatible rollout dependencies.

The implementation was revised and re-reviewed. The final reviewer confirmed:

- the library training entrypoint derives authorization by revalidating the
  dataset and cannot accept a caller-supplied authorization boolean;
- runtime YAML must name the same dataset directory as the complete audit;
- real tokenized labels match the exact per-split target sequence, SHA-256
  multiset, and action counts;
- positive/recovery supervision, prompt grouping, image containment/hashes,
  renderer fingerprint, and source evidence bindings are enforced;
- the clean venv excludes vLLM/CuPy/Megatron and passes `pip check`;
- the self-contained v3 provisional export validates at 663 records and 593
  image bindings; its six-sample real processor audit has no violations.

External gates remain intentionally open: Gate 3 v9 is not approved, and the
login node has no HCU for the required bf16/FA2/DeepSpeed device smoke. These
are execution prerequisites, not code-review failures.
