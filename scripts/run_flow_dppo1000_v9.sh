#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

phase="${1:-}"
if [[ "$phase" != "pilot" && "$phase" != "queue" && "$phase" != "dry-run" ]]; then
  printf 'usage: %s {pilot|queue|dry-run}\n' "$0" >&2
  exit 2
fi

run_root="runs/phase7_flow_dppo1000_v9_fresh8_v1"
stop_file="$run_root/STOP_ADMISSION"
env_file=".env.teacher.local"

if [[ ! -f "$env_file" ]]; then
  printf 'missing local Teacher environment file: %s\n' "$env_file" >&2
  exit 1
fi
if [[ -e "$stop_file" ]]; then
  printf 'admission stop is active: %s\n' "$stop_file" >&2
  exit 1
fi

set -a
source "$env_file"
set +a

episode_args=()
if [[ "$phase" == "pilot" || "$phase" == "dry-run" ]]; then
  for index in $(seq 1 20); do
    printf -v episode_id 'phase3_ep_%03d' "$index"
    episode_args+=(--episode-id "$episode_id")
  done
fi

dry_run_args=()
if [[ "$phase" == "dry-run" ]]; then
  dry_run_args+=(--dry-run)
fi

exec python -m gen_retry.cli.run_phase3_rollouts_parallel \
  --run-root "$run_root" \
  "${episode_args[@]}" \
  --max-workers 8 \
  --workers-per-device 2 \
  --teacher-concurrency 8 \
  --image-steps 40 \
  --image-height 1024 \
  --image-width 1024 \
  --execution-profile-id qwen_dual_backend \
  --stop-admission-file "$stop_file" \
  "${dry_run_args[@]}"
