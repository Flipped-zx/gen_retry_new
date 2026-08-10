from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.rl.training import (
    build_advantage_batch,
    load_advantage_batch,
    load_reward_config,
    write_advantage_batch,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build same-state Geneval2 branch-relative RL advantages from "
            "validated candidate returns."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_reward_config(args.config)
    source = load_advantage_batch(args.input)
    output = build_advantage_batch(source, config=config)
    write_advantage_batch(args.output, output)
    print(
        f"wrote {len(output['groups'])} RL advantage groups to {args.output}"
    )


if __name__ == "__main__":
    main()
