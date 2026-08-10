from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from gen_retry.rl.config import load_experiment_config
from gen_retry.rl.data import (
    build_naive_grpo_experiment_declaration,
    validate_frozen_rl_data,
)
from gen_retry.runtime.json_canonical import canonical_json


ROOT = Path(__file__).resolve().parents[2]


def _write_frozen_fixture(tmp_path: Path):
    heldout_path = tmp_path / "geneval2_data.jsonl"
    heldout_path.write_text("fixture heldout\n", encoding="utf-8")
    heldout_sha256 = hashlib.sha256(heldout_path.read_bytes()).hexdigest()
    source = json.loads(
        (
            ROOT
            / "tests"
            / "fixtures"
            / "rl_prompt_manifests"
            / "minimal.json"
        ).read_text(encoding="utf-8")
    )
    paths = {}
    for index, split in enumerate(("train", "development", "confirmation"), start=1):
        payload = copy.deepcopy(source)
        payload["split"] = split
        payload["manifest_id"] = f"fixture_{split}"
        payload["boundaries"]["official_geneval2_ref"] = str(heldout_path)
        payload["boundaries"]["official_geneval2_sha256"] = heldout_sha256
        prompt = payload["selected_prompts"][0]
        prompt["prompt_id"] = f"prompt_{index}"
        prompt["original_prompt"] = f"fixture prompt {index}"
        prompt["source_row_sha256"] = str(index) * 64
        prompt["rl_semantic_family_id"] = f"rlsf_{index:016x}"
        prompt["provenance"]["source_row_sha256"] = str(index) * 64
        path = tmp_path / f"{split}.json"
        path.write_text(canonical_json(payload) + "\n", encoding="utf-8")
        paths[split] = path

    config_path = tmp_path / "rl.yaml"
    config_path.write_text("fixture config\n", encoding="utf-8")
    base = load_experiment_config(
        ROOT / "configs" / "rl" / "naive_geneval2_grpo_v0_1.yaml"
    )
    admission = replace(
        base.admission,
        smoke_prompts=1,
        pilot_prompts=1,
        minimum_trainable_prompts=1,
        first_efficacy_prompts=1,
        expand_to_prompts=1,
        train_manifest=paths["train"],
        development_manifest=paths["development"],
        confirmation_manifest=paths["confirmation"],
        experiment_declaration=tmp_path / "declaration.json",
    )
    config = replace(base, admission=admission)
    declaration = build_naive_grpo_experiment_declaration(
        config=config,
        config_path=config_path,
        manifest_paths=paths,
    )
    admission.experiment_declaration.write_text(
        canonical_json(declaration) + "\n", encoding="utf-8"
    )
    return config, config_path, paths


def test_frozen_data_contract_closes_hashes_and_split_families(tmp_path: Path) -> None:
    config, config_path, _ = _write_frozen_fixture(tmp_path)
    result = validate_frozen_rl_data(config=config, config_path=config_path)
    assert {split: item["selected_count"] for split, item in result.items()} == {
        "train": 1,
        "development": 1,
        "confirmation": 1,
    }


def test_frozen_data_contract_rejects_post_declaration_tampering(tmp_path: Path) -> None:
    config, config_path, paths = _write_frozen_fixture(tmp_path)
    paths["development"].write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        validate_frozen_rl_data(config=config, config_path=config_path)
