from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase3.trajectory_analysis import analyze_phase3_rollouts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze completed Phase 3 fresh live rollouts.",
    )
    parser.add_argument("--run-root", type=Path, default=Path("runs/phase3"))
    parser.add_argument(
        "--invalid-run-root",
        type=Path,
        default=Path("runs/phase3_invalid"),
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("artifacts/phase3"),
    )
    parser.add_argument("--docs-root", type=Path, default=Path("docs/phase3"))
    parser.add_argument("--expected-count", type=int, default=10)
    parser.add_argument(
        "--episode-id",
        action="append",
        dest="episode_ids",
        help="Analyze only these episode IDs; may be repeated.",
    )
    parser.add_argument("--episode-start", type=int)
    parser.add_argument("--episode-end", type=int)
    args = parser.parse_args()
    episode_ids = _resolve_episode_ids(
        episode_ids=args.episode_ids,
        episode_start=args.episode_start,
        episode_end=args.episode_end,
    )
    result = analyze_phase3_rollouts(
        run_root=args.run_root,
        invalid_run_root=args.invalid_run_root,
        artifact_root=args.artifact_root,
        docs_root=args.docs_root,
        expected_count=args.expected_count,
        episode_ids=episode_ids,
    )
    print(
        "analyzed {episode_count} episodes; labeled {action_label_count} actions; "
        "archived invalid runs={invalid_run_count}".format(**result)
    )


def _resolve_episode_ids(
    *,
    episode_ids: list[str] | None,
    episode_start: int | None,
    episode_end: int | None,
) -> list[str] | None:
    if episode_start is None and episode_end is None:
        return episode_ids
    if episode_start is None or episode_end is None:
        raise SystemExit("--episode-start and --episode-end must be provided together")
    if episode_ids:
        raise SystemExit("--episode-id cannot be combined with an episode range")
    if episode_start <= 0 or episode_end < episode_start:
        raise SystemExit("episode range must satisfy 1 <= start <= end")
    return [
        f"phase3_ep_{index:03d}"
        for index in range(episode_start, episode_end + 1)
    ]


if __name__ == "__main__":
    main()
