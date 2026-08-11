#!/usr/bin/env bash
set -euo pipefail

SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set +u
source "${DTK_ENV_FILE:-/opt/dtk-26.04/env.sh}" >/dev/null 2>&1
set -u
cd "${SERVICE_ROOT}"
exec env PYTHONNOUSERSITE=1 "${SERVICE_ROOT}/.venv/bin/python" \
    -m qwen_dual_backend.preflight "$@"
