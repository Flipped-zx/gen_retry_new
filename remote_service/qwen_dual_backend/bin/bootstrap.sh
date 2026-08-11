#!/usr/bin/env bash
set -euo pipefail
umask 077

SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_ROOT="${SERVICE_ROOT}/.venv"
WHEELHOUSE="${SERVICE_ROOT}/wheelhouse"
RUNTIME_REQUIREMENTS="${SERVICE_ROOT}/requirements.runtime.txt"

set +u
source "${DTK_ENV_FILE:-/opt/dtk-26.04/env.sh}" >/dev/null 2>&1
set -u
mkdir -p "${WHEELHOUSE}" "${SERVICE_ROOT}/state"
chmod 700 "${WHEELHOUSE}" "${SERVICE_ROOT}/state"

if [[ ! -x "${VENV_ROOT}/bin/python" ]]; then
    python -m venv --system-site-packages "${VENV_ROOT}"
fi

if ! "${VENV_ROOT}/bin/python" -m pip install \
    --disable-pip-version-check --no-index --find-links "${WHEELHOUSE}" \
    --no-deps -r "${RUNTIME_REQUIREMENTS}"; then
    python -m pip download \
        --disable-pip-version-check --only-binary=:all: --no-deps \
        --dest "${WHEELHOUSE}" -r "${RUNTIME_REQUIREMENTS}"
    chmod 600 "${WHEELHOUSE}"/*.whl
    "${VENV_ROOT}/bin/python" -m pip install \
        --disable-pip-version-check --no-index --find-links "${WHEELHOUSE}" \
        --no-deps -r "${RUNTIME_REQUIREMENTS}"
fi

cd "${SERVICE_ROOT}"
PYTHONNOUSERSITE=1 "${VENV_ROOT}/bin/python" - <<'PY'
import importlib.metadata as metadata
import json
from pathlib import Path

import torch

from qwen_dual_backend.utils import atomic_write_json, utc_now

expected_torch = "2.9.0+das.opt1.dtk2604"
torch_distribution_version = metadata.version("torch")
if torch_distribution_version != expected_torch:
    raise SystemExit(
        f"refusing unverified torch distribution: {torch_distribution_version}"
    )
if ".venv" in str(Path(torch.__file__).resolve()):
    raise SystemExit("vendor torch was shadowed inside the service venv")

packages = [
    "torch", "transformers", "fastapi", "uvicorn", "pydantic", "Pillow",
    "safetensors", "numpy", "psutil", "diffusers", "accelerate",
    "python-multipart", "httpx", "pytest",
]
report = {
    "recorded_at": utc_now(),
    "python": __import__("sys").version.split()[0],
    "packages": {name: metadata.version(name) for name in packages},
    "torch_runtime_version": torch.__version__,
    "torch_file": str(Path(torch.__file__).resolve()),
    "torch_hip": torch.version.hip,
    "accelerator_count": torch.cuda.device_count(),
}
atomic_write_json(Path("state/environment.json"), report)
print(json.dumps(report, indent=2))
PY

PYTHONNOUSERSITE=1 "${VENV_ROOT}/bin/python" -m qwen_dual_backend.preflight
