#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

checkpoint="${1:-}"
if [[ ! "$checkpoint" =~ ^[0-9]+$ ]]; then
  printf 'usage: %s {20|100|200|...|1000}\n' "$0" >&2
  exit 2
fi
if (( checkpoint != 20 && (checkpoint < 100 || checkpoint > 1000 || checkpoint % 100 != 0) )); then
  printf 'checkpoint must be 20 or a multiple of 100 through 1000\n' >&2
  exit 2
fi

printf -v suffix '%04d' "$checkpoint"
run_root="runs/phase7_flow_dppo1000_v9_fresh8_v1"
selection="artifacts/phase7/flow_dppo1000_v9_official_mix_selected_prompts.json"
artifact="artifacts/phase7/checkpoints/flow_dppo1000_v9_ckpt_${suffix}_audit.json"
report="docs/phase7/checkpoints/flow_dppo1000_v9_ckpt_${suffix}_audit.md"

exec python -m gen_retry.cli.audit_phase5_rollouts \
  --run-root "$run_root" \
  --selection "$selection" \
  --artifact "$artifact" \
  --report "$report" \
  --expected-count "$checkpoint" \
  --episode-start 1 \
  --episode-end "$checkpoint"
