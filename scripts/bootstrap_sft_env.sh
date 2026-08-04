#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_root="${GEN_RETRY_SFT_RUNTIME_ROOT:-${repo_root}/runs/sft_runtime_v2}"
venv_root="${runtime_root}/venv"
python_bin="${GEN_RETRY_SFT_PYTHON:-python}"
index_url="${GEN_RETRY_PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
vendor_wheelhouse="${GEN_RETRY_VENDOR_WHEELHOUSE:-}"

mkdir -p "${runtime_root}"
if [[ ! -x "${venv_root}/bin/python" ]]; then
  "${python_bin}" -m venv "${venv_root}"
fi
if ! grep -q '^include-system-site-packages = false$' "${venv_root}/pyvenv.cfg"; then
  echo "Refusing a venv that exposes all system packages: ${venv_root}" >&2
  exit 1
fi

"${venv_root}/bin/python" -m pip install \
  --index-url "${index_url}" \
  --upgrade pip wheel "setuptools>=77.0.3,<80.0.0"

if [[ -n "${vendor_wheelhouse}" ]]; then
  "${venv_root}/bin/python" -m pip install \
  --no-index \
  --find-links "${vendor_wheelhouse}" \
  --no-deps \
    torch torchvision deepspeed flash-attn triton
  vendor_mode="wheelhouse"
else
  base_site="$(${python_bin} -c 'import site; print(site.getsitepackages()[0])')"
  target_site="$(${venv_root}/bin/python -c 'import site; print(site.getsitepackages()[0])')"
  GEN_RETRY_VENDOR_BASE_SITE="${base_site}" \
  GEN_RETRY_VENDOR_TARGET_SITE="${target_site}" \
  GEN_RETRY_VENDOR_MANIFEST="${runtime_root}/vendor_snapshot_manifest.json" \
  "${python_bin}" - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from importlib.metadata import distribution
from pathlib import Path

base_site = Path(os.environ["GEN_RETRY_VENDOR_BASE_SITE"]).resolve()
target_site = Path(os.environ["GEN_RETRY_VENDOR_TARGET_SITE"]).resolve()
manifest_path = Path(os.environ["GEN_RETRY_VENDOR_MANIFEST"]).resolve()
requested = ("torch", "torchvision", "deepspeed", "flash-attn", "triton")
manifest = {"mode": "reflink_or_copy_snapshot", "distributions": {}}

for name in requested:
    dist = distribution(name)
    roots = sorted({str(item).split("/")[0] for item in (dist.files or [])})
    copied = []
    snapshot_roots = []
    for root_name in roots:
        if root_name in {"", ".", ".."}:
            continue
        source = base_site / root_name
        if not source.exists():
            continue
        snapshot_roots.append(root_name)
        destination = target_site / root_name
        if destination.exists():
            continue
        subprocess.run(
            ["cp", "-a", "--reflink=auto", str(source), str(destination)],
            check=True,
        )
        copied.append(root_name)
    metadata_path = Path(dist._path) / "METADATA"
    record_path = Path(dist._path) / "RECORD"
    manifest["distributions"][name] = {
        "version": dist.version,
        "source_site": str(base_site),
        "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "record_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
        "snapshot_roots": snapshot_roots,
        "newly_copied_roots": copied,
    }

manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
  vendor_mode="snapshot"
fi

"${venv_root}/bin/python" -m pip install \
  --index-url "${index_url}" \
  --requirement "${repo_root}/requirements/sft-llamafactory-v0.9.5.txt"
"${venv_root}/bin/python" -m pip install \
  --index-url "${index_url}" \
  --no-deps \
  "llamafactory==0.9.5"
"${venv_root}/bin/python" -m pip install \
  --index-url "${index_url}" \
  --no-deps \
  "wandb==0.28.1"

site_packages="$(${venv_root}/bin/python -c 'import site; print(site.getsitepackages()[0])')"
source_patch="${repo_root}/patches/llamafactory-0.9.5-image-only-torchaudio.patch"
metadata_patch="${repo_root}/patches/llamafactory-0.9.5-image-only-metadata.patch"
mm_plugin="${site_packages}/llamafactory/data/mm_plugin.py"
metadata_file="${site_packages}/llamafactory-0.9.5.dist-info/METADATA"
mm_pre_sha="9a7db6d36ac355b0cf4f8dca79408fa7c06c4b10f273405815b28079b53837dc"
mm_post_sha="0fbdc39f62277ae4caf321c2598496bcbe7163a4f128c2abd896a7f01156dff5"
metadata_pre_sha="5625dc42b1fd381a11e2350439891caca3e5eb2a2096d58845579b27ed5bf886"
metadata_post_sha="b2f04024c1fc87ec57e7d48019f80ffd49401a86a30e0046b50490fb8db8efd4"

apply_version_locked_patch() {
  local target_file="$1"
  local expected_pre="$2"
  local expected_post="$3"
  local patch_file="$4"
  local actual_sha
  actual_sha="$(sha256sum "${target_file}" | awk '{print $1}')"
  if [[ "${actual_sha}" == "${expected_post}" ]]; then
    return
  fi
  if [[ "${actual_sha}" != "${expected_pre}" ]]; then
    echo "Refusing to patch unexpected file: ${target_file}" >&2
    exit 1
  fi
  patch --batch --forward -p1 -d "${site_packages}" < "${patch_file}"
  actual_sha="$(sha256sum "${target_file}" | awk '{print $1}')"
  if [[ "${actual_sha}" != "${expected_post}" ]]; then
    echo "Post-patch SHA mismatch: ${target_file}" >&2
    exit 1
  fi
}

apply_version_locked_patch "${mm_plugin}" "${mm_pre_sha}" "${mm_post_sha}" "${source_patch}"
apply_version_locked_patch \
  "${metadata_file}" \
  "${metadata_pre_sha}" \
  "${metadata_post_sha}" \
  "${metadata_patch}"

# Vendor torch snapshots may not include the torchrun console script. Keep a
# venv-local wrapper so LLaMA-Factory's distributed launcher cannot fall back
# to the system Python and lose the isolated packages.
cat > "${venv_root}/bin/torchrun" <<EOF
#!/usr/bin/env bash
exec "${venv_root}/bin/python" -m torch.distributed.run "\$@"
EOF
chmod +x "${venv_root}/bin/torchrun"

"${venv_root}/bin/python" -m pip check | tee "${runtime_root}/pip_check.txt"
"${venv_root}/bin/python" -m pip freeze --all > "${runtime_root}/pip_freeze.txt"
GEN_RETRY_VENDOR_MODE="${vendor_mode}" \
GEN_RETRY_RUNTIME_MANIFEST="${runtime_root}/runtime_validation.json" \
GEN_RETRY_MM_PLUGIN="${mm_plugin}" \
GEN_RETRY_METADATA_FILE="${metadata_file}" \
"${venv_root}/bin/python" - <<'PY'
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path

import torch
import llamafactory.data

assert version("llamafactory") == "0.9.5"
assert version("wandb") == "0.28.1"
assert "/usr/local/lib/python3.11/site-packages" not in sys.path
for vendor_dist in ("torch", "torchvision", "deepspeed", "flash-attn", "triton"):
    assert Path(distribution(vendor_dist)._path).resolve().is_relative_to(
        Path(sys.prefix).resolve()
    ), vendor_dist
for forbidden in ("vllm", "cupy", "megatron"):
    assert importlib.util.find_spec(forbidden) is None, forbidden
    try:
        version(forbidden)
    except PackageNotFoundError:
        pass
    else:
        raise AssertionError(forbidden)

result = {
    "status": "PASS",
    "vendor_mode": os.environ["GEN_RETRY_VENDOR_MODE"],
    "llamafactory": version("llamafactory"),
    "wandb": version("wandb"),
    "torch": torch.__version__,
    "torch_metadata": version("torch"),
    "torch_hip": torch.version.hip,
    "python": platform.python_version(),
    "torchvision": version("torchvision"),
    "deepspeed": version("deepspeed"),
    "flash_attn": version("flash-attn"),
    "torch_cuda_available": torch.cuda.is_available(),
    "hcu_device_smoke_required": not torch.cuda.is_available(),
    "llamafactory_mm_plugin_sha256": hashlib.sha256(
        Path(os.environ["GEN_RETRY_MM_PLUGIN"]).read_bytes()
    ).hexdigest(),
    "llamafactory_metadata_sha256": hashlib.sha256(
        Path(os.environ["GEN_RETRY_METADATA_FILE"]).read_bytes()
    ).hexdigest(),
}
Path(os.environ["GEN_RETRY_RUNTIME_MANIFEST"]).write_text(
    json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(json.dumps(result, sort_keys=True))
PY

echo "SFT environment ready: ${venv_root}"
echo "Activate with: source ${venv_root}/bin/activate"
