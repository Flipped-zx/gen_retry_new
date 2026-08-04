from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.analysis.qwen_raw_prompt_baseline import run_raw_prompt_variant


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one resumable raw-prompt Qwen baseline variant.")
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--variant-index", type=int, required=True)
    args = parser.parse_args()
    result = run_raw_prompt_variant(
        run_root=args.run_root,
        episode_id=args.episode_id,
        variant_index=args.variant_index,
    )
    print(
        f"{result['episode_id']} {result['variant_index']}: "
        f"pass={result['passed_atoms']}/{result['constraint_count']} "
        f"gm={result['gm'] * 100:.2f} cache_hit={result['execution']['cache_hit']}"
    )


if __name__ == "__main__":
    main()
