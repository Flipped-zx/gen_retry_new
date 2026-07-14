#!/usr/bin/env python3
"""Write project-scoped Codex custom agent model IDs without guessing them."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / ".codex" / "agents"


def set_model(path: Path, model: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.startswith("model = ")]
    insert_at = 3 if len(lines) >= 3 else len(lines)
    lines.insert(insert_at, f'model = "{model}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executor-model", required=True)
    parser.add_argument("--reviewer-model", required=True)
    parser.add_argument("--researcher-model", default=None)
    args = parser.parse_args()
    set_model(AGENTS / "executor_xhigh.toml", args.executor_model)
    set_model(AGENTS / "sol_reviewer.toml", args.reviewer_model)
    set_model(AGENTS / "source_researcher.toml", args.researcher_model or args.executor_model)
    print("Configured project-scoped Codex agents.")


if __name__ == "__main__":
    main()
