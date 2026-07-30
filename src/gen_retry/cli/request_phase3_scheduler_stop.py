from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.cli.run_phase3_rollouts_parallel import request_admission_stop


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Atomically stop a Phase 3 scheduler from admitting new episodes. "
            "Already active episodes may finish."
        )
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--reason", default="review_blocker")
    args = parser.parse_args()

    stop_file = args.stop_file or args.run_root / "STOP_ADMISSION"
    request_admission_stop(
        run_root=args.run_root,
        stop_admission_file=stop_file,
        reason=args.reason,
    )
    print(f"admission stop requested: {stop_file}")


if __name__ == "__main__":
    main()
