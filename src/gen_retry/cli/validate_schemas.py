from __future__ import annotations

from gen_retry.protocol.schema_loader import check_all_schemas


def main() -> None:
    checked = check_all_schemas()
    for path in checked:
        print(f"schema ok: {path.relative_to(path.parents[1])}")
    print(f"validated {len(checked)} schemas")


if __name__ == "__main__":
    main()
