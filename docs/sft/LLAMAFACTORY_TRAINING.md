# Gen-Retry LLaMA-Factory SFT Environment

## Status

The data adapter, isolated LLaMA-Factory 0.9.5 environment, full/LoRA
recipes, launch guard, and real tokenizer-label audit are implemented. The
formal SFT source is the complete Flow-DPPO 1000 v9 pool under
`runs/phase7_flow_dppo1000_v9_fresh8_v1`. Gate 3 v9 remains **OPEN**, so its
positive action export is not authorized yet. The existing 663-record
checkpoint-200 conversion is only a `provisional` smoke artifact for testing
the training stack and must not be used for the formal run.

W&B tracking is enabled by the canonical recipes; see
[`WANDB_TRAINING.md`](WANDB_TRAINING.md) for the credential-handling launcher
contract, online/offline fallback, run naming, and comparison tags.

The implementation keeps three responsibilities separate:

1. `gen_retry.sft.supervision` selects positive/recovery canonical actions.
2. `gen_retry.sft.llamafactory` verifies that source decision and renders an
   immutable, self-contained `messages + images` dataset.
3. the formal launcher accepts only a structured Gate 3 approval receipt and
   a complete tokenizer-mask audit bound to the exact dataset and runtime
   config.

## Evidence Synthesis

Gen-Searcher commit `e5078d31859bafee6b6b610f0cd40095cc72e2a4` provides an
executable LLaMA-Factory recipe: Qwen3-VL-8B-Instruct, full language-policy
SFT, frozen vision tower/projector, ZeRO-3, bf16, FA2, 32K cutoff, two epochs,
LR `1e-5`, weight decay `1e-6`, cosine schedule, and warmup `0.02`. Its default
`mask_history=false` trains every assistant reasoning/tool/final turn, which
is incompatible with Gen-Retry's strict action-only targets.

GenEvolve commit `23c847c559ccc0f95bbf4b3d8925898463822f4c` and arXiv
`2605.21605v2` ground multi-turn `messages + images`, 9,000 SFT trajectories,
assistant-only loss, and a similar full-SFT optimization recipe. Its public
repository explicitly does not contain the complete training script.

Generation Navigator arXiv `2605.17969v1` supports state-conditioned
`STOP / REFINE / REGENERATE` learning from image/reviewer history. It reports
103K SFT trajectories and one epoch, but not framework, optimizer, LR, batch,
precision, cutoff, or masking details. Its monotonic filter discards plateau
and regressive branches; Gen-Retry instead retains those branches as zero-loss
history that may condition a later recovery target.

The local target remains exactly:

```text
system (loss 0) -> user/PlannerContext/images (loss 0)
                -> assistant/canonical action JSON (loss 1)
```

`query_skill`, raw teacher output, free-text reasoning, environment facts,
harmful actions, and ineffective actions are never positive targets under the
current freeze.

## Data Export And Validation

```bash
PYTHONPATH=src python -m gen_retry.cli.export_llamafactory_sft \
  --records artifacts/phase7/checkpoints/ckpt_200_sft_reconciliation/sft_dry_run_records.jsonl \
  --split-manifest artifacts/phase7/checkpoints/ckpt_200_sft_reconciliation/sft_split_manifest.json \
  --run-root runs/phase7_flow_dppo200_fresh8_v1 \
  --output-dir artifacts/sft/llamafactory_ckpt200_provisional_v3 \
  --release-status provisional
```

The policy, decisions, and source audit default to adjacent `sft_*` artifacts;
explicit CLI overrides are available. Export rejects a record unless:

- its `phase3_label` is `trainable_positive` or `recovery_positive`;
- its exact source decision has `include_as_target=true`, loss `1`, a source
  label hash, and the same policy/action/split;
- the source policy and audit agree and all audit violation sets are empty;
- its target is one canonical v0.5 `generate_image`, `edit_image`, or
  `submit_attempt` action with source mask `0,0,1`;
- its execution profile, PlannerContext/score contract, and system renderer
  fingerprint are homogeneous;
- its original-prompt SHA maps every episode exactly once and recomputed prompt
  groups do not cross splits.

Visible images are copied into `images/<sha256>.<ext>`. Training rows never
point back to mutable `runs/`. Validation recomputes every image hash, all
JSON/JSONL evidence hashes, row/provenance alignment, action counts, split
counts, and `<image>` placeholder counts. The copied source records, decisions,
split manifest, policy, and audit live under `evidence/`.

The upstream split builder now groups `prompt_hash -> [episode_ids]` before it
assigns train/validation/test. Duplicate original prompts therefore cannot be
split across partitions.

## Isolated Environment

```bash
scripts/bootstrap_sft_env.sh
source runs/sft_runtime_v2/venv/bin/activate
python -m pip check
llamafactory-cli version
```

The default PyPI index is the Tsinghua mirror and may be overridden with
`GEN_RETRY_PIP_INDEX_URL`. This is a clean venv without
`--system-site-packages`: vLLM, CuPy, and Megatron are explicitly asserted to
be absent.

Preferred cluster setup supplies exact DAS/HCU wheels with
`GEN_RETRY_VENDOR_WHEELHOUSE`. Because this host has no vendor wheelhouse, the
tested fallback copies a fixed snapshot of the installed vendor Torch,
torchvision, DeepSpeed, FlashAttention, and matching DAS Triton distributions
into the clean venv.
It records versions and metadata hashes in
`runs/sft_runtime_v2/vendor_snapshot_manifest.json`. This snapshot is host/ABI
specific and is weaker than vendor wheels, but it no longer inherits the
rollout stack's incompatible vLLM/CuPy dependencies.

LLaMA-Factory 0.9.5 imports torchaudio unconditionally even for image-only
data. Two version- and SHA-locked patches make torchaudio an `audio` extra and
raise explicitly only when audio is actually used. The bootstrap records the
patched module and METADATA hashes, runs `pip check`, and writes `pip_freeze.txt`
and `runtime_validation.json`.

The current login node has no visible HCU (`libhydmi.so` is unavailable), so
device execution is deliberately not claimed. Inside an allocated HCU job run:

```bash
python -m deepspeed.launcher.runner --num_gpus 1 scripts/sft_hcu_smoke.py
```

That smoke performs bf16 backward, FA2 forward/backward, and one ZeRO-2 step.
Before full ZeRO-3 training, also run a two-HCU one-step LLaMA-Factory smoke.

## Provisional Preflight And Mask Audit

```bash
PYTHONPATH=src python -m gen_retry.cli.run_llamafactory_sft \
  --dataset-dir artifacts/sft/llamafactory_ckpt200_provisional_v3 \
  --model-name-or-path /root/private_data/agentic_image/models/Qwen3-VL-8B-Instruct \
  --output-dir runs/sft_smoke_v3/checkpoints \
  --runtime-config runs/sft_smoke_v3/llamafactory_runtime.yaml \
  --allow-provisional
```

Provisional preflight forcibly adds `max_samples=8` and `max_steps=2` by
default. `--allow-provisional` cannot be combined with `--execute`.

```bash
DISABLE_VERSION_CHECK=1 PYTHONPATH=src \
  runs/sft_runtime_v2/venv/bin/python \
  -m gen_retry.cli.audit_llamafactory_tokens \
  --runtime-config runs/sft_smoke_v3/llamafactory_runtime.yaml \
  --report artifacts/sft/llamafactory_ckpt200_provisional_v3/token_mask_smoke_audit.json \
  --max-samples 3 --disable-version-check
```

The audit executes LLaMA-Factory's real Qwen3-VL processor on CPU without
loading model weights. Every non-`IGNORE_INDEX` label must decode to exactly
one canonical action JSON plus the Qwen template terminator. The report binds
the dataset manifest, runtime YAML, model path/revision, tokenizer/processor
classes, installed LLaMA-Factory version, and patched multimodal module hash.
It also requires the per-split target sequence, target SHA-256 multiset, and
action counts to equal the exact exported subset; schema-valid substitutions
or duplicates therefore fail the audit.

## Frozen Gate And Formal Training

A frozen export requires a JSON receipt with
`schema_version=gen_retry_gate3_sft_approval_v1`, gate name, exact
`verdict=APPROVED`, policy ID, SHA-256 bindings for records/decisions/split/audit/
policy, and a hash-bound review document. The exporter copies both artifacts
into the dataset. Validation derives authorization from this structure; it
does not trust a manually edited `training_authorized` flag.

After Gate 3 v9 approval:

1. export with `--release-status frozen --gate-approval-ref <receipt.json>`;
2. materialize full or LoRA runtime config without `--allow-provisional`;
3. run the token audit without `--max-samples`;
4. launch with `--execute --token-audit-report <complete-pass.json>`.

The launcher verifies `complete=true`, `status=PASS`, LLaMA-Factory 0.9.5,
runtime-config hash, and dataset-manifest hash. Direct invocation of a third-
party `llamafactory-cli` naturally bypasses repository governance; only the
Gen-Retry launcher is the authorized training entrypoint.

## Current Verified Result

The self-contained provisional checkpoint-200 export contains:

- 663 records: 542 train, 56 validation, 65 test;
- 229 generate, 234 edit, and 200 submit targets;
- 593 bindings over 589 content-addressed image artifacts;
- 567 `trainable_positive` and 96 `recovery_positive` targets;
- zero structural, evidence-hash, split, action, or image-hash violations;
- a real LLaMA-Factory 0.9.5 smoke audit over three train and three validation
  records with zero token-mask violations.

This proves the data and tokenizer path. It does not authorize final v9
training, and it does not replace the still-required HCU/FA2/DeepSpeed smoke.
