#!/usr/bin/env bash
set -euo pipefail

SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${SERVICE_ROOT}/run/service.pid"

if [[ -f "${PID_FILE}" ]]; then
    service_pid="$(<"${PID_FILE}")"
    if [[ "${service_pid}" =~ ^[0-9]+$ ]] && kill -0 "${service_pid}" 2>/dev/null; then
        command_line="$(tr '\0' ' ' < "/proc/${service_pid}/cmdline" 2>/dev/null || true)"
        if [[ "${command_line}" == *"qwen_dual_backend.main"* ]]; then
            echo "running: PID ${service_pid}"
        else
            echo "invalid PID file: PID ${service_pid} belongs to another process" >&2
        fi
    else
        echo "stale PID file: ${PID_FILE}" >&2
    fi
else
    echo "not running: no PID file"
fi

if command -v ss >/dev/null 2>&1; then
    ss -ltnp '( sport = :18080 )' || true
else
    python - <<'PY' || true
import socket

try:
    with socket.create_connection(("127.0.0.1", 18080), timeout=1):
        print("port 18080: accepting TCP connections")
except OSError:
    print("port 18080: not accepting TCP connections")
PY
fi
curl --noproxy '*' --silent --show-error --max-time 3 http://127.0.0.1:18080/healthz || true
echo
curl --noproxy '*' --silent --show-error --max-time 3 http://127.0.0.1:18080/readyz || true
echo
