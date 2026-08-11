#!/usr/bin/env bash
set -euo pipefail
umask 077

SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="${SERVICE_ROOT}/run/service.pid"
LOG_FILE="${SERVICE_ROOT}/logs/service.log"

set +u
source "${DTK_ENV_FILE:-/opt/dtk-26.04/env.sh}" >/dev/null 2>&1
if [[ -f "${SERVICE_ROOT}/.service-env" ]]; then
    source "${SERVICE_ROOT}/.service-env"
fi
set -u
mkdir -p "${SERVICE_ROOT}/run" "${SERVICE_ROOT}/logs" "${SERVICE_ROOT}/state"
chmod 700 "${SERVICE_ROOT}/run" "${SERVICE_ROOT}/logs" "${SERVICE_ROOT}/state"

pid_is_service() {
    local process_id="$1"
    [[ -r "/proc/${process_id}/cmdline" ]] || return 1
    local command_line
    command_line="$(tr '\0' ' ' < "/proc/${process_id}/cmdline")"
    [[ "${command_line}" == *"qwen_dual_backend.main"* ]]
}

if [[ -f "${PID_FILE}" ]]; then
    existing_pid="$(<"${PID_FILE}")"
    if [[ "${existing_pid}" =~ ^[0-9]+$ ]] && kill -0 "${existing_pid}" 2>/dev/null; then
        if pid_is_service "${existing_pid}"; then
            echo "${SERVICE_ROOT}: already running with PID ${existing_pid}"
            exit 0
        fi
        echo "refusing to reuse PID file owned by another live process: ${existing_pid}" >&2
        exit 1
    fi
    rm -f -- "${PID_FILE}"
fi

port_is_available() {
    python - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    listener.bind(("0.0.0.0", 18080))
PY
}

if ! port_is_available; then
    echo "refusing to start: TCP port 18080 is already occupied" >&2
    if command -v ss >/dev/null 2>&1; then
        ss -ltnp '( sport = :18080 )' >&2 || true
    fi
    exit 1
fi

if [[ ! -x "${SERVICE_ROOT}/.venv/bin/python" ]]; then
    echo "persistent venv is missing; run bin/bootstrap.sh" >&2
    exit 1
fi

cd "${SERVICE_ROOT}"
nohup setsid env PYTHONNOUSERSITE=1 "${SERVICE_ROOT}/.venv/bin/python" \
    -m qwen_dual_backend.main >>"${LOG_FILE}" 2>&1 </dev/null &
service_pid=$!
temporary_pid="${PID_FILE}.tmp.$$"
printf '%s\n' "${service_pid}" > "${temporary_pid}"
chmod 600 "${temporary_pid}"
mv -f -- "${temporary_pid}" "${PID_FILE}"

for _ in $(seq 1 60); do
    if curl --noproxy 127.0.0.1,localhost --silent --fail --max-time 2 http://127.0.0.1:18080/healthz >/dev/null; then
        echo "${SERVICE_ROOT}: started with PID ${service_pid} on 0.0.0.0:18080"
        exit 0
    fi
    if ! kill -0 "${service_pid}" 2>/dev/null; then
        echo "service exited during startup; inspect ${LOG_FILE}" >&2
        rm -f -- "${PID_FILE}"
        exit 1
    fi
    sleep 1
done

echo "service did not become healthy within 60 seconds; inspect ${LOG_FILE}" >&2
kill -TERM "${service_pid}" 2>/dev/null || true
rm -f -- "${PID_FILE}"
exit 1
