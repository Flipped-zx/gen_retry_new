from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.phase5.rollout_audit import audit_rollout_batch


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit a completed Flow-DPPO Geneval2 rollout batch."
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=20)
    parser.add_argument(
        "--episode-id",
        action="append",
        dest="episode_ids",
        help="Audit only these episode IDs; may be repeated.",
    )
    parser.add_argument("--episode-start", type=int)
    parser.add_argument("--episode-end", type=int)
    args = parser.parse_args()
    episode_ids = _resolve_episode_ids(
        episode_ids=args.episode_ids,
        episode_start=args.episode_start,
        episode_end=args.episode_end,
    )
    summary = audit_rollout_batch(
        run_root=args.run_root,
        selection_path=args.selection,
        artifact_path=args.artifact,
        report_path=args.report,
        expected_count=args.expected_count,
        episode_ids=episode_ids,
    )
    print(
        f"{summary['status']}: {summary['validated_episode_count']} episodes, "
        f"{summary['total_image_attempts']} attempts"
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
