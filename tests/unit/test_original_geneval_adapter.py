from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from gen_retry.cli.prepare_official_geneval_rollouts import (
    GENEVAL_TAGS,
    OFFICIAL_ROW_COUNT,
    read_official_rows,
)
from gen_retry.cli.export_official_geneval_submission import main as export_main
from gen_retry.domain.artifacts import sha256_file
from gen_retry.runtime.json_canonical import canonical_json


def _official_shape_rows() -> bytes:
    tags = sorted(GENEVAL_TAGS)
    rows = []
    for index in range(OFFICIAL_ROW_COUNT):
        tag = tags[index % len(tags)]
        row = {
            "tag": tag,
            "include": [{"class": "dog", "count": 1}],
            "prompt": f"dog {index}",
        }
        rows.append(json.dumps(row, separators=(",", ":")))
    return ("\n".join(rows) + "\n").encode()


def test_read_official_rows_requires_553_rows_and_all_tags() -> None:
    rows = read_official_rows(_official_shape_rows())
    assert len(rows) == OFFICIAL_ROW_COUNT
    assert {item["row"]["tag"] for item in rows} == GENEVAL_TAGS
    assert all(len(item["raw_sha256"]) == 64 for item in rows)
    assert all(len(item["semantic_sha256"]) == 64 for item in rows)


def test_read_official_rows_rejects_partial_benchmark() -> None:
    with pytest.raises(ValueError, match="exactly 553"):
        read_official_rows(b'{"tag":"single_object"}\n')


def test_local_official_checkout_all_rows_convert() -> None:
    metadata = Path("/root/private_data/agentic_image/geneval/prompts/evaluation_metadata.jsonl")
    if not metadata.is_file():
        pytest.skip("read-only original GenEval checkout is not available")
    rows = read_official_rows(metadata.read_bytes())
    assert len(rows) == 553


def test_export_uses_only_canonical_submitted_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    benchmark = Path("/root/private_data/agentic_image/geneval/prompts/evaluation_metadata.jsonl")
    if not benchmark.is_file():
        pytest.skip("read-only original GenEval checkout is not available")
    sources = read_official_rows(benchmark.read_bytes())
    source = sources[0]
    run_dir = tmp_path / "run"
    (run_dir / "images").mkdir(parents=True)
    image = run_dir / "images/img_000.png"
    image.write_bytes(b"submitted-image")
    stored_metadata = run_dir / "original_geneval_metadata.json"
    stored_metadata.write_text(canonical_json(source["row"]) + "\n", encoding="utf-8")
    fixture = Path("tests/fixtures/mock_episodes/direct_success/events.jsonl")
    (run_dir / "events.jsonl").write_bytes(fixture.read_bytes())
    (run_dir / "manifest.json").write_text(
        canonical_json({
            "schema_version": "0.2",
            "episode_id": "ep_mock_direct_success",
            "artifacts": [{
                "artifact_id": "img_000",
                "attempt_id": "a_000",
                "artifact_type": "image",
                "uri": "images/img_000.png",
                "sha256": sha256_file(image),
                "media_type": "image/png",
                "producer": "test",
            }],
        }) + "\n",
        encoding="utf-8",
    )
    summary = tmp_path / "prepared.json"
    summary.write_text(canonical_json({
        "protocol": {
            "protocol_id": "original_geneval_metadata_aware_agent",
            "protocol_version": "1",
        },
        "benchmark": {
            "data_sha256": __import__("hashlib").sha256(benchmark.read_bytes()).hexdigest(),
            "selected_row_count": 1,
        },
        "episodes": [{
            "episode_id": "ep_mock_direct_success",
            "run_dir": str(run_dir),
            "benchmark_row_index": 0,
            "row_raw_sha256": source["raw_sha256"],
            "row_semantic_sha256": source["semantic_sha256"],
            "original_metadata_ref": stored_metadata.name,
        }],
    }) + "\n", encoding="utf-8")
    output = tmp_path / "submission"
    audit = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", [
        "export",
        "--preparation-summary", str(summary),
        "--benchmark-data", str(benchmark),
        "--output-root", str(output),
        "--audit-output", str(audit),
        "--allow-partial",
    ])
    export_main()
    assert (output / "00000/samples/00000.png").read_bytes() == b"submitted-image"
    assert json.loads((output / "00000/metadata.jsonl").read_text()) == source["row"]
    assert json.loads(audit.read_text())["coverage"] == {
        "complete": False,
        "expected": 1,
        "exported": 1,
    }
