# W&B SFT Tracking

The LLaMA-Factory recipes emit standard Trainer telemetry through W&B. The
tracked project is `gen-retry-sft` in the `Gen_retry` entity. `plot_loss: true`
also keeps the local `training_loss.png` and `eval_loss.png` artifacts in the
checkpoint directory, so a run remains inspectable without network access.

Authentication is intentionally supplied through the process environment or a
user-level W&B login and is never written to a YAML file, dataset, checkpoint,
or report. For a persistent login outside the repository, use:

```bash
runs/sft_runtime_v2/venv/bin/wandb login --relogin
```

The launcher recognizes a valid `~/.netrc` entry created by that command. An
explicit `WANDB_API_KEY` still takes precedence when a cluster uses a secret
manager. The key itself is never printed or copied into child metadata.

The launcher defaults to `--wandb-mode auto`: it uses online mode when either
credential source is available and otherwise records a complete offline run
under `<output-parent>/wandb`. Use `--wandb-mode offline` to force a
disconnected run, or `--wandb-mode disabled` only for a deliberate
no-tracking diagnostic.

Example formal launch (the token audit must be generated from the same runtime
YAML):

```bash
PYTHONPATH=src python -m gen_retry.cli.run_llamafactory_sft \
  --dataset-dir artifacts/sft/flow_dppo1000_v9_frozen \
  --base-config configs/sft/llamafactory/qwen3_vl_8b_full_sft.yaml \
  --model-name-or-path /models/Qwen3-VL-8B-Instruct \
  --output-dir runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42 \
  --runtime-config runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42/runtime.yaml \
  --wandb-mode auto \
  --wandb-group v9-cold-start \
  --wandb-tags sft,cold-start,selective-skill,full \
  --execute \
  --token-audit-report artifacts/sft/flow_dppo1000_v9_frozen/token_mask_audit.json
```

Run names are part of the base recipe and can be overridden with
`--wandb-run-name`. Recommended comparison suffixes are:

```text
...-flow1000-v9-selective-skill-full-s42
...-flow1000-v9-selective-skill-lora-r16-s42
...-flow1000-v9-no-skill-full-s42
...-flow1000-v9-skill-full-s42
```

The launcher adds the fine-tuning type and seed to W&B tags automatically. It
also sets `WANDB_WATCH=false` and `WANDB_LOG_MODEL=false` so parameter watches
and multi-gigabyte model uploads do not dominate a short cold-start run.

The standard charts are training/evaluation loss, learning rate, gradient norm,
epoch, and throughput. LLaMA-Factory writes local loss plots and
`trainer_state.json`; the repository also provides a dependency-light report
generator that produces a PNG, Markdown, HTML, and JSON summary from that file:

```bash
PYTHONPATH=src python -m gen_retry.cli.visualize_sft_training \
  --trainer-state runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42 \
  --output-dir reports/sft/flow1000_v9_selective_skill_full_s42 \
  --name flow1000_v9_selective_skill_full_s42
```

For online comparisons, use the same group and a different run name for each
ablation; this makes the W&B group comparison directly correspond to the
held-out action and rollout reports.
