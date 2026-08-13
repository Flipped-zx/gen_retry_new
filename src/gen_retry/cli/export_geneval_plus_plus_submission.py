from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from gen_retry.cli.prepare_geneval_plus_plus_rollouts import (
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    read_official_rows,
)
from gen_retry.domain.artifacts import sha256_file
from gen_retry.protocol.task_spec_builder import task_spec_from_geneval_plus_plus_row
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.reducer import reduce_events


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export canonical Agent submissions for Geneval++ evaluation."
    )
    parser.add_argument("--preparation-summary", type=Path, required=True)
    parser.add_argument("--benchmark-data", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--jpeg-quality", type=int, default=95)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Smoke/debug only; never use for a formal score.",
    )
    args = parser.parse_args()
    if not 1 <= args.jpeg_quality <= 100:
        raise SystemExit("--jpeg-quality must be in [1, 100]")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise SystemExit(f"refusing non-empty output root: {args.output_root}")

    summary = json.loads(args.preparation_summary.read_text(encoding="utf-8"))
    expected_protocol = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
    }
    if summary.get("protocol") != expected_protocol:
        raise ValueError("preparation summary protocol mismatch")
    benchmark_bytes = args.benchmark_data.read_bytes()
    rows = read_official_rows(benchmark_bytes)
    if summary["benchmark"]["data_sha256"] != hashlib.sha256(
        benchmark_bytes
    ).hexdigest():
        raise ValueError("benchmark file digest differs from preparation summary")

    episodes = summary.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("preparation summary has no episodes")
    expected = summary["benchmark"]["selected_row_count"]
    if len(episodes) != expected or (not args.allow_partial and expected != len(rows)):
        raise ValueError("formal export requires one prepared episode for every official row")

    seen_rows: set[int] = set()
    mappings: list[dict[str, Any]] = []
    args.output_root.mkdir(parents=True, exist_ok=True)
    for episode in episodes:
        row_index = episode["benchmark_row_index"]
        if row_index in seen_rows or row_index < 0 or row_index >= len(rows):
            raise ValueError(f"duplicate or invalid benchmark row index: {row_index}")
        seen_rows.add(row_index)
        source = rows[row_index]
        if (
            source["raw_sha256"] != episode["row_raw_sha256"]
            or source["semantic_sha256"] != episode["row_semantic_sha256"]
        ):
            raise ValueError(f"benchmark provenance mismatch for row {row_index}")
        run_dir = Path(episode["run_dir"])
        stored_metadata = json.loads(
            (run_dir / episode["source_metadata_ref"]).read_text(encoding="utf-8")
        )
        if canonical_json(stored_metadata) != canonical_json(source["row"]):
            raise ValueError(f"stored metadata differs from source row {row_index}")
        task_spec_path = run_dir / "task_spec.json"
        if sha256_file(task_spec_path) != episode["task_spec_sha256"]:
            raise ValueError(f"TaskSpec digest mismatch for row {row_index}")
        stored_task_spec = json.loads(task_spec_path.read_text(encoding="utf-8"))
        expected_task_spec = task_spec_from_geneval_plus_plus_row(
            source["row"],
            episode_id=episode["episode_id"],
            max_image_attempts=summary["max_image_attempts"],
        )
        if canonical_json(stored_task_spec) != canonical_json(expected_task_spec):
            raise ValueError(f"TaskSpec differs from source row {row_index}")

        events = load_events_jsonl(run_dir / "events.jsonl")
        state = reduce_events(events)
        if state.submitted_attempt_id is None:
            raise ValueError(f"episode has no canonical submission: {episode['episode_id']}")
        attempt = state.attempts[state.submitted_attempt_id]
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        entries = [
            item
            for item in manifest["artifacts"]
            if item["artifact_id"] == attempt.image_artifact_id
        ]
        if len(entries) != 1 or entries[0].get("attempt_id") != attempt.attempt_id:
            raise ValueError(f"submitted image manifest binding mismatch: {episode['episode_id']}")
        image_path = (run_dir / entries[0]["uri"]).resolve()
        try:
            image_path.relative_to(run_dir.resolve())
        except ValueError as exc:
            raise ValueError(f"submitted image escapes run directory: {image_path}") from exc
        if not image_path.is_file():
            raise FileNotFoundError(image_path)
        source_sha = sha256_file(image_path)
        if entries[0]["sha256"] != source_sha:
            raise ValueError(f"submitted image digest mismatch: {image_path}")

        output_path = args.output_root / f"{row_index + 1}.jpg"
        with Image.open(image_path) as source_image:
            image = ImageOps.exif_transpose(source_image).convert("RGB")
            image.save(
                output_path,
                format="JPEG",
                quality=args.jpeg_quality,
                subsampling=0,
            )
        mappings.append(
            {
                "benchmark_row_index": row_index,
                "evaluator_image_id": row_index + 1,
                "episode_id": episode["episode_id"],
                "submitted_attempt_id": attempt.attempt_id,
                "image_artifact_id": attempt.image_artifact_id,
                "source_image_sha256": source_sha,
                "exported_jpeg_sha256": sha256_file(output_path),
                "output_ref": str(output_path.resolve()),
            }
        )

    if len(seen_rows) != expected:
        raise ValueError("submission coverage mismatch")
    audit = {
        "schema_version": "0.1",
        "protocol": summary["protocol"],
        "coverage": {
            "expected": expected,
            "exported": len(mappings),
            "complete": len(mappings) == len(rows),
        },
        "submission_policy": "one_canonical_reducer_submitted_image_per_prompt",
        "image_naming": "one_based_row_index_jpeg",
        "jpeg": {"quality": args.jpeg_quality, "subsampling": 0},
        "official_metadata_mutated": False,
        "mappings": sorted(mappings, key=lambda item: item["benchmark_row_index"]),
    }
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(canonical_json(audit) + "\n", encoding="utf-8")
    print(f"exported {len(mappings)} canonical submissions to {args.output_root}")


if __name__ == "__main__":
    main()
