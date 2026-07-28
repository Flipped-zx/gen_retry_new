from __future__ import annotations

import json
from pathlib import Path

from gen_retry.tools.geneval2_adapter import LocalGeneval2Adapter


def test_geneval2_adapter_reuses_complete_cached_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    evaluator_root = tmp_path / "evaluator"
    model_root = tmp_path / "model"
    evaluator_root.mkdir()
    model_root.mkdir()
    image_path = tmp_path / "image.png"
    image_path.write_bytes(b"image")
    report_path = tmp_path / "geneval2" / "a_000.json"
    report_path.parent.mkdir()
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "0.2",
                "attempt_id": "a_000",
                "evaluator": "geneval2",
                "method": "soft_tifa_local_qwen3_vl",
                "normalization": {"method": "cached"},
                "constraint_results": [
                    {
                        "constraint_id": "c_001",
                        "status": "pass",
                        "expected": "Yes",
                        "observed": "Yes",
                        "confidence": 0.9,
                    }
                ],
                "raw_results": [{"constraint_id": "c_001"}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    adapter = LocalGeneval2Adapter(
        evaluator_root=evaluator_root,
        vqa_model_path=model_root,
        artifact_root=tmp_path,
    )
    monkeypatch.setattr(
        adapter,
        "_evaluate",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("cached report must avoid model execution")
        ),
    )

    report = adapter.evaluate_to_report(
        task_spec={
            "constraints": [
                {
                    "constraint_id": "c_001",
                    "evaluator_question": "Is there a cat?",
                    "requirement": "Expected answer: Yes",
                }
            ]
        },
        attempt_id="a_000",
        image_path=image_path,
    )

    assert report.constraint_results[0]["status"] == "pass"
    assert report.manifest_entry["metadata"]["cache_hit"] is True
