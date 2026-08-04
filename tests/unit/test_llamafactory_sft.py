from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from gen_retry.runtime.json_canonical import canonical_json
from gen_retry.sft.llamafactory import (
    _wandb_subprocess_environment,
    _strip_template_terminator,
    export_llamafactory_dataset,
    prepare_llamafactory_training,
    run_llamafactory_training,
    validate_llamafactory_dataset,
)
from gen_retry.sft.supervision import _assign_splits

ROOT = Path(__file__).resolve().parents[2]


def _action(action_name: str) -> dict:
    if action_name == "generate_image":
        arguments = {
            "target_constraint_ids": ["c_001"],
            "preserve_constraint_ids": [],
            "instruction": "Create exactly one red cube.",
        }
    elif action_name == "edit_image":
        arguments = {
            "source_attempt_id": "a_000",
            "target_constraint_ids": ["c_001"],
            "preserve_constraint_ids": ["c_002"],
            "instruction": "Change only the cube to red and preserve the sphere.",
        }
    elif action_name == "submit_attempt":
        arguments = {
            "selected_attempt_id": "a_000",
            "reason_code": "best_available_under_budget",
        }
    elif action_name == "query_skill":
        arguments = {
            "skill_ids": ["attribute_entity_binding"],
            "target_constraint_ids": ["c_001"],
        }
    else:
        raise AssertionError(action_name)
    return {"schema_version": "0.5", "action": action_name, "arguments": arguments}


def _record(
    episode_id: str,
    split: str,
    action_name: str,
    *,
    image_refs: list[dict] | None = None,
) -> dict:
    action = _action(action_name)
    target = canonical_json(action)
    sample_id = f"{episode_id}_turn_001_evt_001"
    messages = [
        {
            "role": "system",
            "content": "Emit exactly one canonical action.",
            "loss_weight": 0,
            "token_source": "system",
        },
        {
            "role": "user",
            "content": '{"planner_context":{"planner_context_schema_version":"0.7"}}',
            "loss_weight": 0,
            "token_source": "planner_context",
            "image_refs": image_refs or [],
        },
        {
            "role": "assistant",
            "content": target,
            "loss_weight": 1,
            "token_source": "canonical_action",
        },
    ]
    return {
        "schema_version": "0.5",
        "sample_id": sample_id,
        "episode_id": episode_id,
        "request_id": f"{episode_id}_request_001",
        "turn_id": "turn_001",
        "split": split,
        "phase3_label": "trainable_positive",
        "action": action_name,
        "policy_id": "meaningful_retry_v9_test",
        "execution_profile": {
            "profile_id": "qwen_dual_backend",
            "profile_version": "1",
        },
        "planner_context_schema_version": "0.7",
        "score_policy": {
            "policy_id": "geneval2_pass_count_then_gm",
            "policy_version": "1",
        },
        "messages": messages,
        "loss_mask": [
            {"message_index": 0, "role": "system", "loss_weight": 0},
            {"message_index": 1, "role": "user", "loss_weight": 0},
            {"message_index": 2, "role": "assistant", "loss_weight": 1},
        ],
        "target_text_sha256": hashlib.sha256(target.encode()).hexdigest(),
    }


def _write_source(tmp_path: Path, records: list[dict]) -> tuple[Path, Path, Path]:
    records_path = tmp_path / "source" / "sft_dry_run_records.jsonl"
    records_path.parent.mkdir()
    records_path.write_text(
        "".join(canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
    )
    episode_splits = {record["episode_id"]: record["split"] for record in records}
    prompt_groups = {
        hashlib.sha256(record["episode_id"].encode()).hexdigest(): {
            "episode_id": record["episode_id"],
            "split": record["split"],
        }
        for record in records
    }
    split_path = records_path.with_name("sft_split_manifest.json")
    split_path.write_text(
        canonical_json(
            {
                "episode_splits": episode_splits,
                "prompt_groups": prompt_groups,
                "prompt_group_cross_split_violations": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    run_root = tmp_path / "runs"
    for record in records:
        run_dir = run_root / record["episode_id"]
        run_dir.mkdir(parents=True)
        (run_dir / "task_spec.json").write_text(
            canonical_json(
                {
                    "episode_id": record["episode_id"],
                    "original_prompt": record["episode_id"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
    policy = {
        "schema_version": "0.5",
        "policy_id": "meaningful_retry_v9_test",
        "accepted_action_labels": ["recovery_positive", "trainable_positive"],
        "targetable_actions": ["edit_image", "generate_image", "submit_attempt"],
    }
    records_path.with_name("sft_supervision_policy.json").write_text(
        canonical_json(policy) + "\n", encoding="utf-8"
    )
    decisions = []
    for record in records:
        event_id = (
            record["sample_id"].rsplit("_", 2)[-2]
            + "_"
            + record["sample_id"].rsplit("_", 1)[-1]
        )
        decisions.append(
            {
                "episode_id": record["episode_id"],
                "request_id": record["request_id"],
                "turn_id": record["turn_id"],
                "action_event_id": event_id,
                "action": record["action"],
                "phase3_label": record["phase3_label"],
                "include_as_target": True,
                "loss_weight": 1,
                "policy_id": record["policy_id"],
                "split": record["split"],
                "source_label_sha256": hashlib.sha256(
                    canonical_json(record).encode()
                ).hexdigest(),
            }
        )
    records_path.with_name("sft_dry_run_decisions.jsonl").write_text(
        "".join(canonical_json(item) + "\n" for item in decisions),
        encoding="utf-8",
    )
    audit = {
        "policy_id": policy["policy_id"],
        "gate2_validation_experiment_passed": True,
        "target_record_count": len(records),
        "input_label_count": len(decisions),
        "loss_mask_violations": [],
        "noncanonical_target_violations": [],
        "prompt_group_cross_split_violations": [],
        "mixed_execution_profile_violations": [],
        "mixed_context_score_contract_violations": [],
    }
    records_path.with_name("sft_dry_run_audit.json").write_text(
        canonical_json(audit) + "\n", encoding="utf-8"
    )
    return records_path, split_path, run_root


def _three_records(image_refs: list[dict] | None = None) -> list[dict]:
    return [
        _record("phase3_ep_001", "train", "edit_image", image_refs=image_refs),
        _record("phase3_ep_002", "validation", "generate_image"),
        _record("phase3_ep_003", "test", "submit_attempt"),
    ]


def test_export_deduplicates_visible_roles_and_matches_image_tokens(
    tmp_path: Path,
) -> None:
    refs = [
        {
            "artifact_id": "img_000",
            "attempt_id": "a_000",
            "role": "latest",
            "uri": "images/img_000.png",
        },
        {
            "artifact_id": "img_000",
            "attempt_id": "a_000",
            "role": "best",
            "uri": "images/img_000.png",
        },
    ]
    records_path, split_path, run_root = _write_source(tmp_path, _three_records(refs))
    image_path = run_root / "phase3_ep_001" / "images" / "img_000.png"
    image_path.parent.mkdir()
    image_path.write_bytes(b"fake-png-for-contract-test")
    output_dir = tmp_path / "dataset"

    manifest = export_llamafactory_dataset(
        records_path=records_path,
        run_root=run_root,
        output_dir=output_dir,
        split_manifest_path=split_path,
    )

    train_row = json.loads((output_dir / "train.jsonl").read_text())
    provenance = json.loads(
        (output_dir / "provenance.jsonl").read_text().splitlines()[0]
    )
    assert train_row["messages"][1]["content"].count("<image>") == 1
    assert len(train_row["images"]) == 1
    assert train_row["images"][0].startswith("images/")
    assert (output_dir / train_row["images"][0]).is_file()
    assert provenance["images"][0]["visible_roles"] == ["best", "latest"]
    assert manifest["release_status"] == "provisional"
    assert manifest["training_authorized"] is False
    assert manifest["unique_image_count"] == 1
    assert validate_llamafactory_dataset(output_dir)["status"] == "PASS"


def test_export_rejects_context_only_query_skill_target(tmp_path: Path) -> None:
    records = _three_records()
    records[0] = _record("phase3_ep_001", "train", "query_skill")
    records_path, split_path, run_root = _write_source(tmp_path, records)

    with pytest.raises(ValueError, match="context-only"):
        export_llamafactory_dataset(
            records_path=records_path,
            run_root=run_root,
            output_dir=tmp_path / "dataset",
            split_manifest_path=split_path,
        )


def test_export_rejects_non_assistant_loss(tmp_path: Path) -> None:
    records = _three_records()
    records[0]["messages"][1]["loss_weight"] = 1
    records_path, split_path, run_root = _write_source(tmp_path, records)

    with pytest.raises(ValueError, match="message loss weights"):
        export_llamafactory_dataset(
            records_path=records_path,
            run_root=run_root,
            output_dir=tmp_path / "dataset",
            split_manifest_path=split_path,
        )


def test_export_rejects_harmful_action_even_when_mask_is_positive(
    tmp_path: Path,
) -> None:
    records = _three_records()
    records[0]["phase3_label"] = "history_only_harmful"
    records_path, split_path, run_root = _write_source(tmp_path, records)

    with pytest.raises(ValueError, match="non-positive phase3_label"):
        export_llamafactory_dataset(
            records_path=records_path,
            run_root=run_root,
            output_dir=tmp_path / "dataset",
            split_manifest_path=split_path,
        )


def test_validation_rejects_mutated_copied_image(tmp_path: Path) -> None:
    refs = [
        {
            "artifact_id": "img_000",
            "attempt_id": "a_000",
            "role": "latest",
            "uri": "images/img_000.png",
        }
    ]
    records_path, split_path, run_root = _write_source(tmp_path, _three_records(refs))
    source_image = run_root / "phase3_ep_001/images/img_000.png"
    source_image.parent.mkdir()
    source_image.write_bytes(b"immutable-image")
    output_dir = tmp_path / "dataset"
    export_llamafactory_dataset(
        records_path=records_path,
        run_root=run_root,
        output_dir=output_dir,
        split_manifest_path=split_path,
    )
    row = json.loads((output_dir / "train.jsonl").read_text())
    (output_dir / row["images"][0]).write_bytes(b"mutated")
    with pytest.raises(ValueError, match="image hash mismatch"):
        validate_llamafactory_dataset(output_dir)


def test_split_assignment_keeps_duplicate_prompts_in_one_group() -> None:
    prompt_hash = hashlib.sha256(b"same prompt").hexdigest()
    run_index = {
        "phase3_ep_001": {"prompt_group_sha256": prompt_hash},
        "phase3_ep_002": {"prompt_group_sha256": prompt_hash},
        "phase3_ep_003": {"prompt_group_sha256": hashlib.sha256(b"other").hexdigest()},
        "phase3_ep_004": {"prompt_group_sha256": hashlib.sha256(b"third").hexdigest()},
    }
    manifest = _assign_splits(run_index)
    assert (
        manifest["episode_splits"]["phase3_ep_001"]
        == manifest["episode_splits"]["phase3_ep_002"]
    )
    assert manifest["prompt_groups"][prompt_hash]["episode_ids"] == [
        "phase3_ep_001",
        "phase3_ep_002",
    ]
    assert manifest["prompt_group_cross_split_violations"] == []


def test_prepare_blocks_provisional_and_materializes_explicit_smoke_config(
    tmp_path: Path,
) -> None:
    records_path, split_path, run_root = _write_source(tmp_path, _three_records())
    dataset_dir = tmp_path / "dataset"
    export_llamafactory_dataset(
        records_path=records_path,
        run_root=run_root,
        output_dir=dataset_dir,
        split_manifest_path=split_path,
    )
    model_path = tmp_path / "model"
    model_path.mkdir()
    runtime_config = tmp_path / "runtime.yaml"
    kwargs = {
        "dataset_dir": dataset_dir,
        "base_config_path": ROOT
        / "configs"
        / "sft"
        / "llamafactory"
        / "qwen3_vl_8b_lora_sft.yaml",
        "model_name_or_path": str(model_path),
        "output_dir": tmp_path / "checkpoints",
        "runtime_config_path": runtime_config,
    }

    with pytest.raises(PermissionError, match="provisional"):
        prepare_llamafactory_training(**kwargs)

    result = prepare_llamafactory_training(**kwargs, allow_provisional=True)
    config = yaml.safe_load(runtime_config.read_text())
    assert result["status"] == "READY"
    assert config["dataset"] == "gen_retry_sft_train"
    assert config["eval_dataset"] == "gen_retry_sft_validation"
    assert config["train_on_prompt"] is False
    assert config["mask_history"] is True
    assert config["packing"] is False
    assert config["report_to"] == "wandb"
    assert config["run_name"] == "gen-retry-flow1000-v9-selective-skill-lora-r16-s42"
    assert Path(config["deepspeed"]).is_absolute()
    assert Path(config["deepspeed"]).is_file()

    with pytest.raises(PermissionError, match="provisional"):
        run_llamafactory_training(
            runtime_config_path=runtime_config,
            dataset_dir=dataset_dir,
            token_audit_report_path=tmp_path / "forged-audit.json",
        )


def test_wandb_auto_falls_back_to_offline_without_credentials(tmp_path: Path) -> None:
    env, metadata = _wandb_subprocess_environment(
        base_env={},
        runtime_config={
            "report_to": "wandb",
            "run_name": "unit-test-run",
            "output_dir": str(tmp_path / "checkpoints"),
            "finetuning_type": "lora",
            "seed": 42,
        },
        mode="auto",
        entity="Gen_retry",
        project="gen-retry-sft",
        group="unit-tests",
        tags=["sft", "unit"],
        directory=tmp_path / "wandb",
    )
    assert metadata["mode"] == "offline"
    assert env["WANDB_MODE"] == "offline"
    assert env["WANDB_PROJECT"] == "gen-retry-sft"
    assert env["WANDB_ENTITY"] == "Gen_retry"
    assert env["WANDB_RUN_GROUP"] == "unit-tests"
    assert env["WANDB_TAGS"] == "sft,unit,lora,seed-42"
    assert "WANDB_API_KEY" not in metadata


def test_wandb_online_requires_environment_credential(tmp_path: Path) -> None:
    runtime_config = {
        "report_to": "wandb",
        "run_name": "unit-test-run",
        "output_dir": str(tmp_path / "checkpoints"),
    }
    with pytest.raises(RuntimeError, match="WANDB_API_KEY"):
        _wandb_subprocess_environment(
            base_env={},
            runtime_config=runtime_config,
            mode="online",
            entity="Gen_retry",
            project="gen-retry-sft",
            group="unit-tests",
            tags=[],
            directory=tmp_path / "wandb",
        )

    env, metadata = _wandb_subprocess_environment(
        base_env={"WANDB_API_KEY": "test-only-placeholder"},
        runtime_config=runtime_config,
        mode="online",
        entity="Gen_retry",
        project="gen-retry-sft",
        group="unit-tests",
        tags=[],
        directory=tmp_path / "wandb",
    )
    assert metadata["mode"] == "online"
    assert env["WANDB_MODE"] == "online"
    assert metadata["run_name"] == "unit-test-run"


def test_wandb_auto_uses_user_netrc_credentials(tmp_path: Path) -> None:
    netrc_path = tmp_path / "netrc"
    netrc_path.write_text(
        "machine api.wandb.ai login user password test-only-placeholder\n",
        encoding="utf-8",
    )
    env, metadata = _wandb_subprocess_environment(
        base_env={"HOME": str(tmp_path), "NETRC": str(netrc_path)},
        runtime_config={
            "report_to": "wandb",
            "run_name": "unit-test-netrc-run",
            "output_dir": str(tmp_path / "checkpoints"),
        },
        mode="auto",
        entity="Gen_retry",
        project="gen-retry-sft",
        group="unit-tests",
        tags=[],
        directory=tmp_path / "wandb",
    )
    assert metadata["mode"] == "online"
    assert env["WANDB_MODE"] == "online"
    assert "WANDB_API_KEY" not in env


def test_validation_rejects_renderer_contract_tampering(tmp_path: Path) -> None:
    records_path, split_path, run_root = _write_source(tmp_path, _three_records())
    dataset_dir = tmp_path / "dataset"
    export_llamafactory_dataset(
        records_path=records_path,
        run_root=run_root,
        output_dir=dataset_dir,
        split_manifest_path=split_path,
    )
    manifest_path = dataset_dir / "export_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["renderer_contract"]["system_prompt_sha256"] = "0" * 64
    manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="renderer contract"):
        validate_llamafactory_dataset(dataset_dir)


def test_frozen_export_requires_gate_approval_artifact(tmp_path: Path) -> None:
    records_path, split_path, run_root = _write_source(tmp_path, _three_records())
    with pytest.raises(ValueError, match="gate-approval"):
        export_llamafactory_dataset(
            records_path=records_path,
            run_root=run_root,
            output_dir=tmp_path / "dataset",
            split_manifest_path=split_path,
            release_status="frozen",
        )

    review = tmp_path / "gate3_review.md"
    review.write_text("# Gate 3 Review\n\nVerdict: APPROVED\n", encoding="utf-8")
    approval = tmp_path / "gate3_approval.json"
    evidence_paths = {
        "records_sha256": records_path,
        "decisions_sha256": records_path.with_name("sft_dry_run_decisions.jsonl"),
        "split_manifest_sha256": split_path,
        "source_audit_sha256": records_path.with_name("sft_dry_run_audit.json"),
        "supervision_policy_sha256": records_path.with_name(
            "sft_supervision_policy.json"
        ),
    }
    approval.write_text(
        canonical_json(
            {
                "schema_version": "gen_retry_gate3_sft_approval_v1",
                "gate": "Gate 3 SFT Supervision Freeze",
                "verdict": "APPROVED",
                "policy_id": "meaningful_retry_v9_test",
                "source_artifact_sha256": {
                    key: hashlib.sha256(path.read_bytes()).hexdigest()
                    for key, path in evidence_paths.items()
                },
                "review_artifact": {
                    "path": str(review),
                    "sha256": hashlib.sha256(review.read_bytes()).hexdigest(),
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = export_llamafactory_dataset(
        records_path=records_path,
        run_root=run_root,
        output_dir=tmp_path / "frozen_dataset",
        split_manifest_path=split_path,
        release_status="frozen",
        gate_approval_ref=approval,
    )
    assert result["training_authorized"] is True
    assert (
        result["gate_approval_sha256"]
        == hashlib.sha256(approval.read_bytes()).hexdigest()
    )


def test_token_audit_strips_only_template_terminator() -> None:
    target = canonical_json(_action("generate_image"))
    assert _strip_template_terminator(target + "<|im_end|>\n", "<|im_end|>") == target
    with pytest.raises(ValueError, match="EOS"):
        _strip_template_terminator(target + " extra", "<|im_end|>")
