# Geneval++ Metadata-Aware SFT Agent Evaluation

## Scope

Protocol ID: `geneval_plus_plus_metadata_aware_agent@1`.

The frozen SFT Planner sees a deterministic rubric derived from Geneval++
metadata before its first action. The existing Geneval2-compatible VQA path is
online proxy feedback only. The formal result is calculated after submission by
Echo-4o's GPT-4.1 evaluator.

This is a metadata-aware Agent protocol with one submitted image per prompt. It
is not the prompt-only single-generation recipe used in the Echo-4o guide.

## Frozen Source

- Repository: `https://github.com/yejy53/Echo-4o.git`
- Commit: `28f36d76558e5f53b9deceda78bf025ef0d0ea24`
- Metadata: `test_scripts/Geneval++.jsonl`, exactly 280 rows
- Metadata SHA-256:
  `9c1216a3f6fe2d99e4ffd63f3a6dba71f3dd7ab30a7c09cb41f03629b35d3e8f`
- Evaluator: `test_scripts/Eval-gpt-4.1-geneval++.py`

Treat the Echo-4o checkout as read-only.

## Conversion

The adapter preserves every official metadata element as Planner-visible
atomic constraints:

- each `include.class/count` becomes an exact-count question;
- `color` becomes a yes/no attribute question;
- `region` becomes a left/right/upper/lower image-region question;
- a larger/smaller pair becomes one relative-size question;
- matching `include N` and `exclude N+1` are one exact-count atom;
- any unsupported field, tag, region, size pattern, row count, or tag balance
  fails closed.

The untouched source row and its raw/semantic hashes are stored with each run.

## Prepare

```bash
export PYTHONPATH=src

python -m gen_retry.cli.prepare_geneval_plus_plus_rollouts \
  --benchmark-data /absolute/path/to/Echo-4o/test_scripts/Geneval++.jsonl \
  --output-root runs/geneval_plus_plus_metadata_aware_agent_v1 \
  --summary-output artifacts/geneval_plus_plus_metadata_aware_agent_v1_prepared.json \
  --max-image-attempts 5
```

Preparation requires all 280 rows and seven tags with 40 rows per tag.
`--limit` is available for smoke execution only; the complete input is still
validated before limiting.

## Run The SFT Planner And Dual Backend

```bash
python -m gen_retry.cli.serve_sft_planner \
  --checkpoint /absolute/path/to/sft-checkpoint \
  --host 127.0.0.1 \
  --port 8765

python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root runs/geneval_plus_plus_metadata_aware_agent_v1 \
  --planner-provider sft \
  --sft-planner-url http://127.0.0.1:8765 \
  --sft-checkpoint /absolute/path/to/sft-checkpoint \
  --execution-profile-id qwen_dual_backend \
  --generate-image-steps 50 \
  --edit-image-steps 40 \
  --image-height 1024 \
  --image-width 1024 \
  --workers-per-device 1 \
  --device-id 1
```

Run the scheduler with `--dry-run` first. The canonical best-attempt selection
uses proxy VQA pass count and Soft-TIFA GM, not the formal Geneval++ result.

## Export Submitted Images

```bash
python -m gen_retry.cli.export_geneval_plus_plus_submission \
  --preparation-summary artifacts/geneval_plus_plus_metadata_aware_agent_v1_prepared.json \
  --benchmark-data /absolute/path/to/Echo-4o/test_scripts/Geneval++.jsonl \
  --output-root artifacts/geneval_plus_plus_metadata_aware_agent_v1_images \
  --audit-output artifacts/geneval_plus_plus_metadata_aware_agent_v1_export_audit.json
```

Formal export requires 280/280 canonical submissions. It verifies source
metadata, submitted Attempt binding, manifest URI containment, and artifact
digest, then writes exactly `1.jpg` through `280.jpg`. `--allow-partial` is for
smoke/debug only.

## Run The Echo-4o Evaluator

The upstream evaluator uses relative paths named `Geneval++.jsonl`, `image`,
and `Output.json`. Create a repository-local evaluation workspace so the
read-only Echo-4o checkout remains untouched:

```bash
export OPENAI_API_KEY='...'

mkdir -p artifacts/geneval_plus_plus_metadata_aware_agent_v1_eval
cp /absolute/path/to/Echo-4o/test_scripts/Geneval++.jsonl \
  artifacts/geneval_plus_plus_metadata_aware_agent_v1_eval/Geneval++.jsonl
ln -s /absolute/path/to/artifacts/geneval_plus_plus_metadata_aware_agent_v1_images \
  artifacts/geneval_plus_plus_metadata_aware_agent_v1_eval/image

cd artifacts/geneval_plus_plus_metadata_aware_agent_v1_eval
python /absolute/path/to/Echo-4o/test_scripts/Eval-gpt-4.1-geneval++.py
```

The result is `Output.json` in that workspace. Do not commit the key or modify
the read-only evidence checkout. Preserve the
evaluator model (`gpt-4.1`), temperature (`0.0`), system prompt, retry count,
and metadata. Record the evaluator commit and script SHA-256 in the report.

## Reporting

Keep proxy metrics and GPT-4.1 metrics in separate sections. Record checkpoint
digest, `qwen_dual_backend@1`, max attempts, actual generate/edit/image-call
counts, online VQA model and thresholds, proxy score policy, one-image
submission policy, 280/280 export coverage, JPEG settings, Echo-4o commit,
evaluator script digest, and GPT-4.1 result artifact digest.
