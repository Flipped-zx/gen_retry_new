from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.live_runner import Phase3LiveRunner, RuntimeParams


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=Path("runs/phase3"))
    parser.add_argument("--episode-id", type=str)
    parser.add_argument("--image-steps", type=int, default=40)
    parser.add_argument("--image-height", type=int, default=1024)
    parser.add_argument("--image-width", type=int, default=1024)
    parser.add_argument("--teacher-max-completion-tokens", type=int, default=1400)
    args = parser.parse_args()
    runner = Phase3LiveRunner(
        runtime_params=RuntimeParams(
            image_height=args.image_height,
            image_width=args.image_width,
            image_steps=args.image_steps,
            teacher_max_completion_tokens=args.teacher_max_completion_tokens,
        )
    )
    if args.episode_id:
        results = [runner.run_episode(args.run_root / args.episode_id)]
    else:
        results = runner.run_all(args.run_root)
    for result in results:
        print(
            f"{result.episode_id}: {result.status}; "
            f"submitted={result.submitted_attempt_id}; "
            f"attempts={result.attempts}; events={result.events}"
        )


if __name__ == "__main__":
    main()
