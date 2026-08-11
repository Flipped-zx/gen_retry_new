#!/usr/bin/env bash
set -euo pipefail
umask 077

SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${SERVICE_ROOT}/run/service.pid"

if [[ ! -f "${PID_FILE}" ]]; then
    echo "${SERVICE_ROOT}: not running (no PID file)"
    exit 0
fi

service_pid="$(<"${PID_FILE}")"
if [[ ! "${service_pid}" =~ ^[0-9]+$ ]] || ! kill -0 "${service_pid}" 2>/dev/null; then
    rm -f -- "${PID_FILE}"
    echo "${SERVICE_ROOT}: removed stale PID file"
    exit 0
fi

command_line="$(tr '\0' ' ' < "/proc/${service_pid}/cmdline" 2>/dev/null || true)"
if [[ "${command_line}" != *"qwen_dual_backend.main"* ]]; then
    echo "refusing to signal PID ${service_pid}: command does not match this service" >&2
    exit 1
fi

kill -TERM "${service_pid}"
for _ in $(seq 1 30); do
    if ! kill -0 "${service_pid}" 2>/dev/null; then
        rm -f -- "${PID_FILE}"
        echo "${SERVICE_ROOT}: stopped"
        exit 0
    fi
    sleep 1
done

echo "service did not stop within 30 seconds; sending SIGKILL" >&2
kill -KILL "${service_pid}"
rm -f -- "${PID_FILE}"
