from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from gen_retry.cli.prepare_official_geneval_rollouts import (
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    read_official_rows,
)
from gen_retry.domain.artifacts import sha256_file
from gen_retry.runtime.event_io import load_events_jsonl
from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.runtime.reducer import reduce_events


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Export canonical Agent submissions for pristine original GenEval evaluation."
        )
    )
    parser.add_argument("--preparation-summary", type=Path, required=True)
    parser.add_argument("--benchmark-data", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Smoke/debug only; never use for a formal score.",
    )
    args = parser.parse_args()
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
    if summary["benchmark"]["data_sha256"] != hashlib.sha256(benchmark_bytes).hexdigest():
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
            (run_dir / episode["original_metadata_ref"]).read_text(encoding="utf-8")
        )
        if canonical_json(stored_metadata) != canonical_json(source["row"]):
            raise ValueError(f"stored metadata differs from source row {row_index}")
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
        image = (run_dir / entries[0]["uri"]).resolve()
        try:
            image.relative_to(run_dir.resolve())
        except ValueError as exc:
            raise ValueError(f"submitted image escapes run directory: {image}") from exc
        if not image.is_file():
            raise FileNotFoundError(image)
        image_sha = sha256_file(image)
        if entries[0]["sha256"] != image_sha:
            raise ValueError(f"submitted image digest mismatch: {image}")
        prompt_dir = args.output_root / f"{row_index:05d}"
        samples_dir = prompt_dir / "samples"
        samples_dir.mkdir(parents=True)
        (prompt_dir / "metadata.jsonl").write_text(
            canonical_json(source["row"]) + "\n", encoding="utf-8"
        )
        shutil.copy2(image, samples_dir / "00000.png")
        mappings.append({
            "benchmark_row_index": row_index,
            "episode_id": episode["episode_id"],
            "submitted_attempt_id": attempt.attempt_id,
            "image_artifact_id": attempt.image_artifact_id,
            "image_sha256": image_sha,
            "output_ref": str((samples_dir / "00000.png").resolve()),
        })
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
        "official_metadata_mutated": False,
        "mappings": sorted(mappings, key=lambda item: item["benchmark_row_index"]),
    }
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(canonical_json(audit) + "\n", encoding="utf-8")
    print(f"exported {len(mappings)} canonical submissions to {args.output_root}")


if __name__ == "__main__":
    main()
