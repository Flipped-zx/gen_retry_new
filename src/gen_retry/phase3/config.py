from __future__ import annotations

from pathlib import Path


def read_local_paths(path: Path = Path("configs/paths/local.yaml")) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"missing local path config: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        value = value.strip().strip("\"'")
        if value and value.lower() not in {"null", "none"}:
            values[key.strip()] = value
    return values


def configured_path(key: str, *, config_path: Path = Path("configs/paths/local.yaml")) -> Path:
    values = read_local_paths(config_path)
    if key not in values:
        raise KeyError(f"{key} is not configured in {config_path}")
    return Path(values[key]).expanduser()
