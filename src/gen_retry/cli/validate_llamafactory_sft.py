from __future__ import annotations

import argparse
from pathlib import Path

from gen_retry.sft.llamafactory import validate_llamafactory_dataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a rendered Gen-Retry LLaMA-Factory dataset."
    )
    parser.add_argument("dataset_dir", type=Path)
    args = parser.parse_args()
    result = validate_llamafactory_dataset(args.dataset_dir)
    print(
        "LLaMA-Factory dataset PASS: "
        f"records={result['record_count']} "
        f"images={result['image_binding_count']}"
    )


if __name__ == "__main__":
    main()
