from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from gen_retry.cli.export_geneval_plus_plus_submission import main as export_main
from gen_retry.cli.prepare_geneval_plus_plus_rollouts import (
    GENEVAL_PLUS_PLUS_TAGS,
    OFFICIAL_ROW_COUNT,
    read_official_rows,
)
from gen_retry.domain.artifacts import sha256_file
from gen_retry.protocol.task_spec_builder import task_spec_from_geneval_plus_plus_row
from gen_retry.runtime.json_canonical import canonical_json


BENCHMARK = Path(
    "/root/private_data/agentic_image/Echo-4o/test_scripts/Geneval++.jsonl"
)


def _official_shape_rows() -> bytes:
    tags = sorted(GENEVAL_PLUS_PLUS_TAGS)
    rows = []
    for index in range(OFFICIAL_ROW_COUNT):
        tag = tags[index // 40]
        row = {
            "tag": tag,
            "include": [{"class": "dog", "count": 1}],
            "prompt": f"dog {index}",
        }
        rows.append(json.dumps(row, separators=(",", ":")))
    return ("\n".join(rows) + "\n").encode()


def test_read_official_rows_requires_280_rows_and_balanced_tags() -> None:
    rows = read_official_rows(_official_shape_rows())
    assert len(rows) == OFFICIAL_ROW_COUNT
    assert {item["row"]["tag"] for item in rows} == GENEVAL_PLUS_PLUS_TAGS
    assert all(len(item["raw_sha256"]) == 64 for item in rows)
    assert all(len(item["semantic_sha256"]) == 64 for item in rows)


def test_read_official_rows_rejects_partial_benchmark() -> None:
    with pytest.raises(ValueError, match="exactly 280"):
        read_official_rows(b'{"tag":"counting"}\n')


def test_local_echo4o_all_rows_convert() -> None:
    if not BENCHMARK.is_file():
        pytest.skip("read-only Echo-4o checkout is not available")
    rows = read_official_rows(BENCHMARK.read_bytes())
    assert len(rows) == 280


def test_export_uses_submitted_image_and_one_based_jpeg_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not BENCHMARK.is_file():
        pytest.skip("read-only Echo-4o checkout is not available")
    sources = read_official_rows(BENCHMARK.read_bytes())
    source = sources[0]
    run_dir = tmp_path / "run"
    (run_dir / "images").mkdir(parents=True)
    image_path = run_dir / "images/img_000.png"
    Image.new("RGB", (16, 12), color=(20, 120, 200)).save(image_path)
    metadata = run_dir / "geneval_plus_plus_metadata.json"
    metadata.write_text(canonical_json(source["row"]) + "\n", encoding="utf-8")
    task_spec_path = run_dir / "task_spec.json"
    task_spec_path.write_text(
        canonical_json(
            task_spec_from_geneval_plus_plus_row(
                source["row"],
                episode_id="ep_mock_direct_success",
                max_image_attempts=3,
            )
        )
        + "\n",
        encoding="utf-8",
    )
    fixture = Path("tests/fixtures/mock_episodes/direct_success/events.jsonl")
    (run_dir / "events.jsonl").write_bytes(fixture.read_bytes())
    (run_dir / "manifest.json").write_text(
        canonical_json(
            {
                "schema_version": "0.2",
                "episode_id": "ep_mock_direct_success",
                "artifacts": [
                    {
                        "artifact_id": "img_000",
                        "attempt_id": "a_000",
                        "artifact_type": "image",
                        "uri": "images/img_000.png",
                        "sha256": sha256_file(image_path),
                        "media_type": "image/png",
                        "producer": "test",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path = tmp_path / "prepared.json"
    summary_path.write_text(
        canonical_json(
            {
                "protocol": {
                    "protocol_id": "geneval_plus_plus_metadata_aware_agent",
                    "protocol_version": "1",
                },
                "benchmark": {
                    "data_sha256": hashlib.sha256(BENCHMARK.read_bytes()).hexdigest(),
                    "selected_row_count": 1,
                },
                "max_image_attempts": 3,
                "episodes": [
                    {
                        "episode_id": "ep_mock_direct_success",
                        "run_dir": str(run_dir),
                        "benchmark_row_index": 0,
                        "row_raw_sha256": source["raw_sha256"],
                        "row_semantic_sha256": source["semantic_sha256"],
                        "source_metadata_ref": metadata.name,
                        "task_spec_sha256": sha256_file(task_spec_path),
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "submission"
    audit = tmp_path / "audit.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export",
            "--preparation-summary",
            str(summary_path),
            "--benchmark-data",
            str(BENCHMARK),
            "--output-root",
            str(output),
            "--audit-output",
            str(audit),
            "--allow-partial",
        ],
    )
    export_main()
    exported = output / "1.jpg"
    assert exported.is_file()
    with Image.open(exported) as image:
        assert image.format == "JPEG"
        assert image.size == (16, 12)
    mapping = json.loads(audit.read_text())["mappings"][0]
    assert mapping["submitted_attempt_id"] == "a_000"
    assert mapping["evaluator_image_id"] == 1
