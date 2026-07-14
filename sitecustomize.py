"""Make the local src layout importable for repository-root python -m commands."""

from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# The base environment has unrelated pytest plugins that import optional GPU
# stacks during collection. Keep project test runs isolated and deterministic.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

if SRC.is_dir():
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
