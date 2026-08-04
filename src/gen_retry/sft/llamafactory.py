from __future__ import annotations

import hashlib
import io
import json
import math
import netrc as netrc_module
import os
import shutil
import subprocess
from collections import Counter
from contextlib import redirect_stdout
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any

import yaml

from gen_retry.protocol.schema_loader import validate_instance
from gen_retry.runtime.json_canonical import canonical_json

EXPORT_FORMAT_VERSION = "gen_retry_llamafactory_sft_v1"
GATE_APPROVAL_FORMAT_VERSION = "gen_retry_gate3_sft_approval_v1"
SUPPORTED_RELEASE_STATUSES = {"provisional", "frozen"}
SUPPORTED_SPLITS = ("train", "validation", "test")
EXPECTED_ROLES = ("system", "user", "assistant")
EXPECTED_LOSS_WEIGHTS = (0, 0, 1)
TARGETABLE_ACTIONS = {"generate_image", "edit_image", "submit_attempt"}
ALL_TARGETABLE_ACTIONS = TARGETABLE_ACTIONS | {"query_skill"}
POSITIVE_SUPERVISION_LABELS = {"trainable_positive", "recovery_positive"}
LLAMAFACTORY_TEMPLATE = "qwen3_vl_nothink"
DEFAULT_WANDB_ENTITY = "Gen_retry"
DEFAULT_WANDB_PROJECT = "gen-retry-sft"
DEFAULT_WANDB_GROUP = "v9-cold-start"
SUPPORTED_WANDB_MODES = {"auto", "online", "offline", "disabled"}


def export_llamafactory_dataset(
    *,
    records_path: Path,
    run_root: Path,
    output_dir: Path,
    split_manifest_path: Path | None = None,
    supervision_policy_path: Path | None = None,
    decisions_path: Path | None = None,
    source_audit_path: Path | None = None,
    release_status: str = "provisional",
    gate_approval_ref: Path | None = None,
    dataset_prefix: str = "gen_retry_sft",
) -> dict[str, Any]:
    """Convert audited Gen-Retry samples into LLaMA-Factory ShareGPT JSONL.

    The source export remains the authority for target selection. This adapter
    only validates and renders already-selected targets; it never relabels an
    action or promotes a context-only turn.
    """

    records_path = records_path.resolve()
    run_root = run_root.resolve()
    output_dir = output_dir.resolve()
    if release_status not in SUPPORTED_RELEASE_STATUSES:
        raise ValueError(f"unsupported release_status: {release_status}")
    if not dataset_prefix or not dataset_prefix.replace("_", "").isalnum():
        raise ValueError(
            "dataset_prefix must contain only letters, digits, or underscores"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"output directory must be absent or empty: {output_dir}")
    if not records_path.is_file():
        raise FileNotFoundError(records_path)
    if not run_root.is_dir():
        raise FileNotFoundError(run_root)

    split_manifest_path = (
        split_manifest_path.resolve()
        if split_manifest_path is not None
        else records_path.with_name("sft_split_manifest.json")
    )
    supervision_policy_path = (
        supervision_policy_path.resolve()
        if supervision_policy_path is not None
        else records_path.with_name("sft_supervision_policy.json")
    )
    decisions_path = (
        decisions_path.resolve()
        if decisions_path is not None
        else records_path.with_name("sft_dry_run_decisions.jsonl")
    )
    source_audit_path = (
        source_audit_path.resolve()
        if source_audit_path is not None
        else records_path.with_name("sft_dry_run_audit.json")
    )
    split_manifest = _load_json(split_manifest_path)
    episode_splits = split_manifest.get("episode_splits")
    if not isinstance(episode_splits, dict):
        raise ValueError("split manifest must contain episode_splits")
    if split_manifest.get("prompt_group_cross_split_violations"):
        raise ValueError("source split manifest contains prompt-group leakage")

    supervision_policy = _load_json(supervision_policy_path)
    source_audit = _load_json(source_audit_path)
    decisions = _load_jsonl(decisions_path)
    source_records = _load_jsonl(records_path)
    if not source_records:
        raise ValueError("source SFT export is empty")
    decision_index = _validate_source_supervision_evidence(
        source_records=source_records,
        decisions=decisions,
        source_audit=source_audit,
        supervision_policy=supervision_policy,
    )
    evidence_hashes = {
        "records_sha256": _sha256_file(records_path),
        "decisions_sha256": _sha256_file(decisions_path),
        "split_manifest_sha256": _sha256_file(split_manifest_path),
        "source_audit_sha256": _sha256_file(source_audit_path),
        "supervision_policy_sha256": _sha256_file(supervision_policy_path),
    }

    approval_sha256 = None
    approval_ref_text = None
    gate_approval: dict[str, Any] | None = None
    gate_review_ref: Path | None = None
    if release_status == "frozen":
        if gate_approval_ref is None:
            raise ValueError("frozen exports require --gate-approval-ref")
        gate_approval_ref = gate_approval_ref.resolve()
        if not gate_approval_ref.is_file():
            raise FileNotFoundError(gate_approval_ref)
        gate_approval = _load_json(gate_approval_ref)
        gate_review_ref = _validate_gate_approval(
            gate_approval,
            policy_id=_required_string(supervision_policy, "policy_id"),
            evidence_hashes=evidence_hashes,
            approval_path=gate_approval_ref,
        )
        approval_ref_text = str(gate_approval_ref)
        approval_sha256 = _sha256_file(gate_approval_ref)
    elif gate_approval_ref is not None:
        raise ValueError("gate_approval_ref is only valid for frozen exports")

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir()
    evidence_sources = {
        "source_records.jsonl": records_path,
        "supervision_policy.json": supervision_policy_path,
        "source_decisions.jsonl": decisions_path,
        "source_split_manifest.json": split_manifest_path,
        "source_supervision_audit.json": source_audit_path,
    }
    for destination_name, source_path in evidence_sources.items():
        shutil.copy2(source_path, evidence_dir / destination_name)
    if gate_approval_ref is not None:
        shutil.copy2(gate_approval_ref, evidence_dir / "gate3_approval.json")
    if gate_review_ref is not None:
        shutil.copy2(gate_review_ref, evidence_dir / "gate3_review.md")
    rows_by_split: dict[str, list[dict[str, Any]]] = {
        split: [] for split in SUPPORTED_SPLITS
    }
    provenance: list[dict[str, Any]] = []
    sample_ids: set[str] = set()
    action_counts: Counter[str] = Counter()
    action_counts_by_split: dict[str, Counter[str]] = {
        split: Counter() for split in SUPPORTED_SPLITS
    }
    split_counts: Counter[str] = Counter()
    policy_ids: set[str] = set()
    execution_profiles: set[str] = set()
    context_contracts: set[str] = set()
    image_hash_cache: dict[Path, str] = {}
    unique_image_artifacts: dict[str, str] = {}

    prompt_group_by_episode = _prompt_group_by_episode(
        split_manifest,
        run_root=run_root,
    )
    for source in source_records:
        sample_id = _required_string(source, "sample_id")
        if sample_id in sample_ids:
            raise ValueError(f"duplicate sample_id: {sample_id}")
        sample_ids.add(sample_id)

        episode_id = _required_string(source, "episode_id")
        split = _required_string(source, "split")
        expected_split = episode_splits.get(episode_id)
        if split not in SUPPORTED_SPLITS:
            raise ValueError(f"unsupported split for {sample_id}: {split}")
        if expected_split != split:
            raise ValueError(
                f"split mismatch for {sample_id}: record={split}, "
                f"manifest={expected_split}"
            )
        prompt_group_sha256 = prompt_group_by_episode.get(episode_id)
        if prompt_group_sha256 is None:
            raise ValueError(f"prompt group missing for episode: {episode_id}")

        messages = _validate_source_messages(
            source,
            supervision_policy=supervision_policy,
            decision=decision_index.get(sample_id),
        )
        action = json.loads(messages[-1]["content"])
        image_bindings = _resolve_image_bindings(
            source=source,
            run_root=run_root,
            output_dir=output_dir,
            image_hash_cache=image_hash_cache,
        )
        training_messages = [
            {"role": message["role"], "content": message["content"]}
            for message in messages
        ]
        if image_bindings:
            if "<image>" in training_messages[1]["content"]:
                raise ValueError(
                    f"source user content already contains <image> for {sample_id}"
                )
            prefix = "<image>" * len(image_bindings)
            training_messages[1]["content"] = (
                f"{prefix}\n{training_messages[1]['content']}"
            )

        row = {
            "messages": training_messages,
            "images": [binding["dataset_path"] for binding in image_bindings],
        }
        row_index = len(rows_by_split[split])
        rows_by_split[split].append(row)
        action_name = action["action"]
        action_counts[action_name] += 1
        action_counts_by_split[split][action_name] += 1
        split_counts[split] += 1
        policy_ids.add(_required_string(source, "policy_id"))
        profile = source.get("execution_profile")
        if not isinstance(profile, dict):
            raise ValueError(f"missing execution_profile for {sample_id}")
        execution_profiles.add(canonical_json(profile))
        context_contracts.add(
            canonical_json(
                {
                    "planner_context_schema_version": source.get(
                        "planner_context_schema_version"
                    ),
                    "score_policy": source.get("score_policy"),
                }
            )
        )
        for binding in image_bindings:
            existing_hash = unique_image_artifacts.get(binding["dataset_path"])
            if existing_hash is not None and existing_hash != binding["sha256"]:
                raise ValueError("conflicting content-addressed image binding")
            unique_image_artifacts[binding["dataset_path"]] = binding["sha256"]
        provenance.append(
            {
                "sample_id": sample_id,
                "episode_id": episode_id,
                "request_id": _required_string(source, "request_id"),
                "turn_id": _required_string(source, "turn_id"),
                "split": split,
                "row_index": row_index,
                "prompt_group_sha256": prompt_group_sha256,
                "action": action_name,
                "policy_id": source["policy_id"],
                "source_record_sha256": _sha256_text(canonical_json(source)),
                "target_text_sha256": _sha256_text(messages[-1]["content"]),
                "images": image_bindings,
            }
        )

    if len(execution_profiles) != 1:
        raise ValueError("mixed execution profiles are not allowed")
    if len(context_contracts) != 1:
        raise ValueError("mixed PlannerContext/score contracts are not allowed")
    if len(policy_ids) != 1:
        raise ValueError("mixed supervision policies are not allowed")
    system_prompt_hashes = {
        _sha256_text(record["messages"][0]["content"]) for record in source_records
    }
    if len(system_prompt_hashes) != 1:
        raise ValueError("mixed system renderer prompts are not allowed")
    missing_splits = [
        split for split in ("train", "validation") if not rows_by_split[split]
    ]
    if missing_splits:
        raise ValueError(f"required dataset splits are empty: {missing_splits}")

    dataset_info = _dataset_info(dataset_prefix)
    _write_json(output_dir / "dataset_info.json", dataset_info)
    for split, rows in rows_by_split.items():
        _write_jsonl(output_dir / f"{split}.jsonl", rows)
    _write_jsonl(output_dir / "provenance.jsonl", provenance)

    artifact_hashes = {
        name: _sha256_file(output_dir / name)
        for name in [
            "dataset_info.json",
            "train.jsonl",
            "validation.jsonl",
            "test.jsonl",
            "provenance.jsonl",
            "evidence/source_records.jsonl",
            "evidence/supervision_policy.json",
            "evidence/source_decisions.jsonl",
            "evidence/source_split_manifest.json",
            "evidence/source_supervision_audit.json",
            *(
                ["evidence/gate3_approval.json", "evidence/gate3_review.md"]
                if gate_approval is not None
                else []
            ),
        ]
    }
    manifest = {
        "format_version": EXPORT_FORMAT_VERSION,
        "release_status": release_status,
        "training_authorized": release_status == "frozen",
        "gate_approval_ref": approval_ref_text,
        "gate_approval_sha256": approval_sha256,
        "source": {
            "records_path": str(records_path),
            "records_sha256": evidence_hashes["records_sha256"],
            "decisions_path": str(decisions_path),
            "decisions_sha256": evidence_hashes["decisions_sha256"],
            "split_manifest_path": str(split_manifest_path),
            "split_manifest_sha256": evidence_hashes["split_manifest_sha256"],
            "source_audit_path": str(source_audit_path),
            "source_audit_sha256": evidence_hashes["source_audit_sha256"],
            "supervision_policy_path": str(supervision_policy_path),
            "supervision_policy_sha256": evidence_hashes["supervision_policy_sha256"],
            "run_root": str(run_root),
        },
        "dataset_names": {
            split: f"{dataset_prefix}_{split}" for split in SUPPORTED_SPLITS
        },
        "record_count": len(source_records),
        "split_counts": dict(sorted(split_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "action_counts_by_split": {
            split: dict(sorted(counts.items()))
            for split, counts in action_counts_by_split.items()
        },
        "policy_ids": sorted(policy_ids),
        "execution_profiles": sorted(execution_profiles),
        "context_score_contracts": sorted(context_contracts),
        "image_binding_count": sum(len(item["images"]) for item in provenance),
        "unique_image_count": len(unique_image_artifacts),
        "image_artifacts": dict(sorted(unique_image_artifacts.items())),
        "renderer_contract": {
            "adapter": "gen_retry.sft.llamafactory@v1",
            "source_renderer": "gen_retry.sft.supervision.render_messages",
            "system_prompt_sha256": next(iter(system_prompt_hashes)),
            "image_injection": (
                "prepend one <image> token per unique visible artifact"
            ),
        },
        "llamafactory_contract": {
            "version": "0.9.5",
            "formatting": "sharegpt_openai_messages",
            "template": LLAMAFACTORY_TEMPLATE,
            "train_on_prompt": False,
            "mask_history": True,
            "assistant_targets_per_record": 1,
            "image_placeholder_invariant": "count(<image>) == len(images)",
        },
        "artifacts": artifact_hashes,
    }
    _write_json(output_dir / "export_manifest.json", manifest)
    validation = validate_llamafactory_dataset(output_dir)
    return {**manifest, "validation": validation}


def validate_llamafactory_dataset(dataset_dir: Path) -> dict[str, Any]:
    dataset_dir = dataset_dir.resolve()
    manifest = _load_json(dataset_dir / "export_manifest.json")
    if manifest.get("format_version") != EXPORT_FORMAT_VERSION:
        raise ValueError("unsupported LLaMA-Factory export format")
    dataset_info = _load_json(dataset_dir / "dataset_info.json")
    dataset_names = manifest.get("dataset_names") or {}
    artifact_hashes = manifest.get("artifacts") or {}
    image_artifacts = manifest.get("image_artifacts") or {}
    provenance = _load_jsonl(dataset_dir / "provenance.jsonl")
    policy_evidence = _load_json(dataset_dir / "evidence/supervision_policy.json")
    allowed_actions = set(policy_evidence.get("targetable_actions") or TARGETABLE_ACTIONS)
    if not allowed_actions.issubset(ALL_TARGETABLE_ACTIONS):
        problems = ["supervision policy enables unsupported actions"]
    else:
        problems = []
    provenance_by_row: dict[tuple[str, int], dict[str, Any]] = {}
    split_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    action_counts_by_split: dict[str, Counter[str]] = {
        split: Counter() for split in SUPPORTED_SPLITS
    }
    total_image_bindings = 0
    referenced_image_paths: set[str] = set()
    validated_image_hashes: dict[str, str] = {}

    try:
        training_authorized = _validate_release_contract(
            dataset_dir=dataset_dir,
            manifest=manifest,
        )
    except Exception as exc:
        training_authorized = False
        problems.append(f"release contract invalid: {exc}")

    for item in provenance:
        key = (item.get("split"), item.get("row_index"))
        if key in provenance_by_row:
            problems.append(f"duplicate provenance row: {key}")
        elif key[0] not in SUPPORTED_SPLITS or not isinstance(key[1], int):
            problems.append(f"invalid provenance row key: {key}")
        else:
            provenance_by_row[key] = item

    for artifact_name, expected_hash in artifact_hashes.items():
        artifact_path = (dataset_dir / artifact_name).resolve()
        if not artifact_path.is_relative_to(dataset_dir):
            problems.append(f"unsafe artifact path: {artifact_name}")
            continue
        if not artifact_path.is_file():
            problems.append(f"missing artifact: {artifact_name}")
        elif _sha256_file(artifact_path) != expected_hash:
            problems.append(f"artifact hash mismatch: {artifact_name}")

    for split in SUPPORTED_SPLITS:
        dataset_name = dataset_names.get(split)
        entry = dataset_info.get(dataset_name) if dataset_name else None
        expected_entry = _dataset_info_entry(f"{split}.jsonl")
        if entry != expected_entry:
            problems.append(f"dataset_info mismatch for split {split}")
        rows = _load_jsonl(dataset_dir / f"{split}.jsonl")
        for row_index, row in enumerate(rows):
            prefix = f"{split}.jsonl:{row_index + 1}"
            messages = row.get("messages")
            images = row.get("images")
            if not isinstance(messages, list) or len(messages) != 3:
                problems.append(f"{prefix}: expected exactly three messages")
                continue
            roles = [message.get("role") for message in messages]
            if tuple(roles) != EXPECTED_ROLES:
                problems.append(f"{prefix}: invalid roles {roles}")
                continue
            if not isinstance(images, list) or not all(
                isinstance(path, str) and path for path in images
            ):
                problems.append(f"{prefix}: images must be a string list")
                continue
            placeholder_count = sum(
                str(message.get("content", "")).count("<image>") for message in messages
            )
            if placeholder_count != len(images):
                problems.append(
                    f"{prefix}: image placeholders={placeholder_count}, "
                    f"images={len(images)}"
                )
            for image_path in images:
                referenced_image_paths.add(image_path)
                resolved = (dataset_dir / image_path).resolve()
                if not resolved.is_relative_to(dataset_dir):
                    problems.append(f"{prefix}: image escapes dataset {image_path}")
                elif not resolved.is_file():
                    problems.append(f"{prefix}: missing image {image_path}")
                else:
                    expected_image_hash = image_artifacts.get(image_path)
                    if expected_image_hash is None:
                        problems.append(f"{prefix}: unregistered image {image_path}")
                    else:
                        actual_image_hash = validated_image_hashes.get(image_path)
                        if actual_image_hash is None:
                            actual_image_hash = _sha256_file(resolved)
                            validated_image_hashes[image_path] = actual_image_hash
                        if actual_image_hash != expected_image_hash:
                            problems.append(
                                f"{prefix}: image hash mismatch {image_path}"
                            )
            provenance_item = provenance_by_row.get((split, row_index))
            if provenance_item is None:
                problems.append(f"{prefix}: missing provenance row")
            else:
                provenance_images = provenance_item.get("images") or []
                if [item.get("dataset_path") for item in provenance_images] != images:
                    problems.append(f"{prefix}: provenance image order mismatch")
                for item in provenance_images:
                    if image_artifacts.get(item.get("dataset_path")) != item.get(
                        "sha256"
                    ):
                        problems.append(f"{prefix}: provenance image hash mismatch")
            try:
                action = json.loads(messages[-1]["content"])
                validate_instance(action, "action_protocol_v0_5.schema.json")
                if action.get("action") not in allowed_actions:
                    problems.append(f"{prefix}: context-only action was exported")
                if messages[-1]["content"] != canonical_json(action):
                    problems.append(f"{prefix}: assistant action is not canonical JSON")
                action_counts[action.get("action", "unknown")] += 1
                action_counts_by_split[split][action.get("action", "unknown")] += 1
            except Exception as exc:  # validation reports all row failures together
                problems.append(f"{prefix}: invalid assistant target: {exc}")
            split_counts[split] += 1
            total_image_bindings += len(images)

    if dict(sorted(split_counts.items())) != manifest.get("split_counts", {}):
        problems.append("split counts do not match manifest")
    if dict(sorted(action_counts.items())) != manifest.get("action_counts", {}):
        problems.append("action counts do not match manifest")
    rendered_action_counts_by_split = {
        split: dict(sorted(counts.items()))
        for split, counts in action_counts_by_split.items()
    }
    if rendered_action_counts_by_split != manifest.get("action_counts_by_split"):
        problems.append("split action counts do not match manifest")
    if total_image_bindings != manifest.get("image_binding_count"):
        problems.append("image binding count does not match manifest")
    if len(image_artifacts) != manifest.get("unique_image_count"):
        problems.append("unique image count does not match manifest")
    if referenced_image_paths != set(image_artifacts):
        problems.append("registered and referenced image sets do not match")
    if len(provenance_by_row) != sum(split_counts.values()):
        problems.append("provenance row count does not match dataset")
    if problems:
        raise ValueError(
            "LLaMA-Factory dataset validation failed:\n- " + "\n- ".join(problems)
        )
    return {
        "status": "PASS",
        "record_count": sum(split_counts.values()),
        "split_counts": dict(sorted(split_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "action_counts_by_split": rendered_action_counts_by_split,
        "image_binding_count": total_image_bindings,
        "training_authorized": training_authorized,
    }


def prepare_llamafactory_training(
    *,
    dataset_dir: Path,
    base_config_path: Path,
    model_name_or_path: str,
    output_dir: Path,
    runtime_config_path: Path,
    allow_provisional: bool = False,
    smoke_max_samples: int = 8,
    smoke_max_steps: int = 2,
    wandb_mode: str = "auto",
    wandb_run_name: str | None = None,
) -> dict[str, Any]:
    """Materialize an absolute-path training config after safety checks."""

    dataset_dir = dataset_dir.resolve()
    output_dir = output_dir.resolve()
    runtime_config_path = runtime_config_path.resolve()
    validation = validate_llamafactory_dataset(dataset_dir)
    manifest = _load_json(dataset_dir / "export_manifest.json")
    training_authorized = validation["training_authorized"]
    if not training_authorized and not allow_provisional:
        raise PermissionError(
            "dataset is provisional; Gate 3 approval is required for training. "
            "Use --allow-provisional only for an explicit smoke test."
        )
    if allow_provisional and (smoke_max_samples < 1 or smoke_max_steps < 1):
        raise ValueError("provisional smoke limits must be positive")
    model_path = Path(model_name_or_path).expanduser()
    if model_path.is_absolute() and not model_path.exists():
        raise FileNotFoundError(model_path)

    config = yaml.safe_load(base_config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("base LLaMA-Factory config must be a YAML mapping")
    dataset_names = manifest["dataset_names"]
    config.update(
        {
            "model_name_or_path": model_name_or_path,
            "dataset_dir": str(dataset_dir),
            "dataset": dataset_names["train"],
            "eval_dataset": dataset_names["validation"],
            "output_dir": str(output_dir),
        }
    )
    _configure_wandb_training_args(
        config,
        mode=wandb_mode,
        run_name=wandb_run_name,
    )
    if allow_provisional:
        config["max_samples"] = smoke_max_samples
        config["max_steps"] = smoke_max_steps
    deepspeed_path = config.get("deepspeed")
    if isinstance(deepspeed_path, str):
        resolved_deepspeed = Path(deepspeed_path)
        if not resolved_deepspeed.is_absolute():
            repository_root = Path(__file__).resolve().parents[3]
            resolved_deepspeed = repository_root / resolved_deepspeed
        resolved_deepspeed = resolved_deepspeed.resolve()
        if not resolved_deepspeed.is_file():
            raise FileNotFoundError(resolved_deepspeed)
        config["deepspeed"] = str(resolved_deepspeed)
    _validate_training_config(config)
    runtime_config_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return {
        "status": "READY",
        "dataset_release_status": manifest["release_status"],
        "training_authorized": training_authorized,
        "allow_provisional": allow_provisional,
        "smoke_limits": (
            {"max_samples": smoke_max_samples, "max_steps": smoke_max_steps}
            if allow_provisional
            else None
        ),
        "runtime_config_path": str(runtime_config_path),
        "output_dir": str(output_dir),
        "dataset_validation": validation,
    }


def run_llamafactory_training(
    *,
    runtime_config_path: Path,
    dataset_dir: Path,
    token_audit_report_path: Path,
    cli_path: str = "llamafactory-cli",
    wandb_mode: str = "auto",
    wandb_entity: str = DEFAULT_WANDB_ENTITY,
    wandb_project: str = DEFAULT_WANDB_PROJECT,
    wandb_group: str = DEFAULT_WANDB_GROUP,
    wandb_tags: list[str] | None = None,
    wandb_dir: Path | None = None,
) -> None:
    validation = validate_llamafactory_dataset(dataset_dir)
    if not validation["training_authorized"]:
        raise PermissionError(
            "provisional datasets cannot be executed by this launcher"
        )
    audit_report = _validate_complete_token_audit(
        report_path=token_audit_report_path,
        runtime_config_path=runtime_config_path,
        dataset_dir=dataset_dir,
    )
    executable = shutil.which(cli_path)
    if executable is None:
        raise FileNotFoundError(
            f"{cli_path} is not installed; run scripts/bootstrap_sft_env.sh first"
        )
    runtime_config = yaml.safe_load(runtime_config_path.read_text(encoding="utf-8"))
    if not isinstance(runtime_config, dict):
        raise ValueError("runtime config must be a YAML mapping")
    uses_wandb = _report_to_contains_wandb(runtime_config.get("report_to"))
    _validate_llamafactory_cli_environment(
        Path(executable),
        audit_report,
        require_wandb=uses_wandb,
    )
    env, tracking = _wandb_subprocess_environment(
        base_env=os.environ,
        runtime_config=runtime_config,
        mode=wandb_mode,
        entity=wandb_entity,
        project=wandb_project,
        group=wandb_group,
        tags=wandb_tags or [],
        directory=wandb_dir,
    )
    if tracking["enabled"]:
        print(
            "W&B tracking: "
            f"mode={tracking['mode']} entity={tracking['entity']} "
            f"project={tracking['project']} group={tracking['group']} "
            f"run={tracking['run_name']}"
        )
    subprocess.run(
        [executable, "train", str(runtime_config_path.resolve())],
        check=True,
        env=env,
    )


def audit_llamafactory_tokenization(
    *,
    runtime_config_path: Path,
    report_path: Path,
    max_samples: int | None = None,
    disable_version_check: bool = False,
) -> dict[str, Any]:
    """Audit the labels produced by LLaMA-Factory's own SFT processor.

    LLaMA-Factory is an optional training dependency, so imports stay inside
    this function. The audit runs tokenizer/processor preprocessing on CPU and
    does not instantiate model weights.
    """

    if disable_version_check:
        os.environ["DISABLE_VERSION_CHECK"] = "1"
    try:
        import llamafactory.data.mm_plugin as llamafactory_mm_plugin
        from llamafactory.data import get_dataset, get_template_and_fix_tokenizer
        from llamafactory.extras.constants import IGNORE_INDEX
        from llamafactory.hparams import get_train_args
        from llamafactory.model import load_tokenizer
    except ImportError as exc:
        raise RuntimeError(
            "LLaMA-Factory is not available; run scripts/bootstrap_sft_env.sh"
        ) from exc
    actual_llamafactory_version = package_version("llamafactory")
    if actual_llamafactory_version != "0.9.5":
        raise RuntimeError(
            "token audit requires exactly LLaMA-Factory 0.9.5, found "
            f"{actual_llamafactory_version}"
        )

    config = yaml.safe_load(runtime_config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("runtime config must be a YAML mapping")
    _validate_training_config(config)
    wandb_version = None
    if _report_to_contains_wandb(config.get("report_to")):
        try:
            wandb_version = package_version("wandb")
        except PackageNotFoundError as exc:
            raise RuntimeError(
                "W&B is required by this runtime config; run scripts/bootstrap_sft_env.sh"
            ) from exc
    config.update(
        {
            "bf16": False,
            "fp16": False,
            "deepspeed": None,
            "preprocessing_num_workers": 1,
            "dataloader_num_workers": 0,
            "report_to": "none",
        }
    )
    if max_samples is not None:
        if max_samples < 1:
            raise ValueError("max_samples must be positive")
        config["max_samples"] = max_samples
    effective_max_samples = config.get("max_samples")
    dataset_dir = Path(config["dataset_dir"]).resolve()
    manifest = _load_json(dataset_dir / "export_manifest.json")
    expected_targets_by_split: dict[str, list[str]] = {}
    expected_actions: Counter[str] = Counter()
    dataset_policy = _load_json(dataset_dir / "evidence/supervision_policy.json")
    targetable_actions = set(dataset_policy.get("targetable_actions") or TARGETABLE_ACTIONS)
    if not targetable_actions.issubset(ALL_TARGETABLE_ACTIONS):
        raise RuntimeError("dataset supervision policy enables unsupported actions")
    for split in ("train", "validation"):
        rows = _load_jsonl(dataset_dir / f"{split}.jsonl")
        if effective_max_samples is not None:
            rows = rows[: int(effective_max_samples)]
        targets = [row["messages"][-1]["content"] for row in rows]
        expected_targets_by_split[split] = targets
        expected_actions.update(json.loads(target)["action"] for target in targets)

    model_args, data_args, training_args, _, _ = get_train_args(config)
    tokenizer_module = load_tokenizer(model_args)
    tokenizer = tokenizer_module["tokenizer"]
    processor = tokenizer_module["processor"]
    template = get_template_and_fix_tokenizer(tokenizer, data_args)
    with redirect_stdout(io.StringIO()):
        dataset_module = get_dataset(
            template,
            model_args,
            data_args,
            training_args,
            "sft",
            tokenizer,
            processor,
        )

    violations: list[str] = []
    split_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    actual_targets_by_split: dict[str, list[str]] = {
        "train": [],
        "validation": [],
    }
    input_lengths: list[int] = []
    target_lengths: list[int] = []
    for dataset_key, split in (
        ("train_dataset", "train"),
        ("eval_dataset", "validation"),
    ):
        dataset = dataset_module.get(dataset_key)
        if dataset is None:
            violations.append(f"missing tokenized {split} dataset")
            continue
        for index, example in enumerate(dataset):
            labels = [token for token in example["labels"] if token != IGNORE_INDEX]
            if not labels:
                violations.append(f"{split}:{index}: no trainable token")
                continue
            decoded = tokenizer.decode(labels, skip_special_tokens=False)
            try:
                target_text = _strip_template_terminator(decoded, tokenizer.eos_token)
                action = json.loads(target_text)
                validate_instance(action, "action_protocol_v0_5.schema.json")
                if action.get("action") not in targetable_actions:
                    raise ValueError("context-only action received loss")
                if target_text != canonical_json(action):
                    raise ValueError("decoded target is not canonical JSON")
                actual_targets_by_split[split].append(target_text)
                action_counts[action["action"]] += 1
            except Exception as exc:  # collect all mask failures in one report
                violations.append(f"{split}:{index}: {exc}")
            split_counts[split] += 1
            input_lengths.append(len(example["input_ids"]))
            target_lengths.append(len(labels))

    complete = effective_max_samples is None
    for split in ("train", "validation"):
        expected_targets = expected_targets_by_split[split]
        if split_counts[split] != len(expected_targets):
            violations.append(
                f"{split}: tokenized={split_counts[split]}, "
                f"expected={len(expected_targets)}"
            )
        if actual_targets_by_split[split] != expected_targets:
            violations.append(f"{split}: tokenized target sequence differs from export")
    if action_counts != expected_actions:
        violations.append(
            "tokenized action counts differ from the exact exported target subset"
        )
    if complete:
        manifest_trainable_actions: Counter[str] = Counter()
        for split in ("train", "validation"):
            manifest_trainable_actions.update(
                manifest["action_counts_by_split"].get(split, {})
            )
        if action_counts != manifest_trainable_actions:
            violations.append("complete tokenized action counts differ from manifest")
    audit = {
        "status": "PASS" if not violations else "FAIL",
        "llamafactory_version": actual_llamafactory_version,
        "wandb_version": wandb_version,
        "llamafactory_mm_plugin_sha256": _sha256_file(
            Path(llamafactory_mm_plugin.__file__).resolve()
        ),
        "runtime_config_path": str(runtime_config_path.resolve()),
        "runtime_config_sha256": _sha256_file(runtime_config_path),
        "dataset_manifest_sha256": _sha256_file(dataset_dir / "export_manifest.json"),
        "complete": complete,
        "max_samples_per_split": effective_max_samples,
        "model_name_or_path": config["model_name_or_path"],
        "model_revision": config.get("model_revision", "main"),
        "tokenizer_class": type(tokenizer).__name__,
        "processor_class": type(processor).__name__ if processor is not None else None,
        "eos_token": tokenizer.eos_token,
        "split_counts": dict(sorted(split_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "expected_action_counts": dict(sorted(expected_actions.items())),
        "target_sequence_sha256_by_split": {
            split: _sha256_text(canonical_json(targets))
            for split, targets in actual_targets_by_split.items()
        },
        "expected_target_sequence_sha256_by_split": {
            split: _sha256_text(canonical_json(targets))
            for split, targets in expected_targets_by_split.items()
        },
        "target_multiset_sha256": _target_multiset_sha256(
            [
                target
                for targets in actual_targets_by_split.values()
                for target in targets
            ]
        ),
        "expected_target_multiset_sha256": _target_multiset_sha256(
            [
                target
                for targets in expected_targets_by_split.values()
                for target in targets
            ]
        ),
        "input_token_percentiles": _integer_percentiles(input_lengths),
        "target_token_percentiles": _integer_percentiles(target_lengths),
        "mask_contract": {
            "ignore_index": IGNORE_INDEX,
            "decoded_non_ignore_tokens": (
                "canonical action JSON plus template terminator"
            ),
            "template": config["template"],
            "train_on_prompt": config["train_on_prompt"],
            "mask_history": config["mask_history"],
        },
        "violations": violations,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(report_path, audit)
    if violations:
        raise ValueError("token-mask audit failed:\n- " + "\n- ".join(violations))
    return audit


def _validate_source_supervision_evidence(
    *,
    source_records: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    source_audit: dict[str, Any],
    supervision_policy: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    policy_id = _required_string(supervision_policy, "policy_id")
    accepted_labels = supervision_policy.get("accepted_action_labels")
    targetable_actions = supervision_policy.get("targetable_actions")
    if not isinstance(accepted_labels, list) or not accepted_labels:
        raise ValueError("supervision policy has no accepted_action_labels")
    if set(accepted_labels) != POSITIVE_SUPERVISION_LABELS:
        raise ValueError("supervision policy changes the approved positive labels")
    if not isinstance(targetable_actions, list) or not targetable_actions:
        raise ValueError("supervision policy has no targetable_actions")
    if not set(targetable_actions).issubset(ALL_TARGETABLE_ACTIONS):
        raise ValueError("supervision policy enables unsupported target actions")
    if source_audit.get("policy_id") != policy_id:
        raise ValueError("source audit and supervision policy disagree")
    if source_audit.get("gate2_validation_experiment_passed") is not True:
        raise ValueError("source supervision audit did not pass")
    for key in (
        "loss_mask_violations",
        "noncanonical_target_violations",
        "prompt_group_cross_split_violations",
        "mixed_execution_profile_violations",
        "mixed_context_score_contract_violations",
    ):
        if source_audit.get(key):
            raise ValueError(f"source supervision audit contains {key}")
    if source_audit.get("target_record_count") != len(source_records):
        raise ValueError("source audit target count does not match records")
    if source_audit.get("input_label_count") != len(decisions):
        raise ValueError("source audit decision count does not match decisions")

    decision_index: dict[str, dict[str, Any]] = {}
    included_count = 0
    for decision in decisions:
        event_id = decision.get("action_event_id")
        episode_id = decision.get("episode_id")
        turn_id = decision.get("turn_id")
        if not all(
            isinstance(value, str) and value
            for value in (event_id, episode_id, turn_id)
        ):
            continue
        sample_id = f"{episode_id}_{turn_id}_{event_id}"
        if sample_id in decision_index:
            raise ValueError(f"duplicate supervision decision for {sample_id}")
        decision_index[sample_id] = decision
        if decision.get("include_as_target") is True:
            source_label_sha256 = decision.get("source_label_sha256")
            if not _is_sha256(source_label_sha256):
                raise ValueError(
                    f"included decision lacks source label hash: {sample_id}"
                )
            included_count += 1
    if included_count != len(source_records):
        raise ValueError("included supervision decisions do not match target records")
    return decision_index


def _validate_gate_approval(
    approval: dict[str, Any],
    *,
    policy_id: str,
    evidence_hashes: dict[str, str],
    approval_path: Path,
) -> Path:
    if approval.get("schema_version") != GATE_APPROVAL_FORMAT_VERSION:
        raise ValueError("unsupported Gate 3 approval artifact")
    if approval.get("gate") != "Gate 3 SFT Supervision Freeze":
        raise ValueError("approval artifact names the wrong gate")
    if approval.get("verdict") != "APPROVED":
        raise ValueError("Gate 3 verdict is not APPROVED")
    if approval.get("policy_id") != policy_id:
        raise ValueError("Gate 3 approval binds a different policy")
    if approval.get("source_artifact_sha256") != evidence_hashes:
        raise ValueError("Gate 3 approval does not bind exact source artifacts")
    review = approval.get("review_artifact")
    if not isinstance(review, dict):
        raise ValueError("Gate 3 approval lacks review_artifact")
    review_path_value = review.get("path")
    review_sha256 = review.get("sha256")
    if not isinstance(review_path_value, str) or not review_path_value:
        raise ValueError("Gate 3 approval review path is invalid")
    review_path = Path(review_path_value)
    if not review_path.is_absolute():
        review_path = approval_path.parent / review_path
    review_path = review_path.resolve()
    if not review_path.is_file() or _sha256_file(review_path) != review_sha256:
        raise ValueError("Gate 3 review artifact is missing or hash-mismatched")
    review_text = review_path.read_text(encoding="utf-8")
    if "Gate 3" not in review_text or "APPROV" not in review_text.upper():
        raise ValueError("Gate 3 review artifact does not contain an approval verdict")
    return review_path


def _validate_release_contract(*, dataset_dir: Path, manifest: dict[str, Any]) -> bool:
    release_status = manifest.get("release_status")
    if release_status not in SUPPORTED_RELEASE_STATUSES:
        raise ValueError("invalid release_status")
    source = manifest.get("source")
    if not isinstance(source, dict):
        raise ValueError("manifest source evidence is missing")
    evidence_bindings = {
        "records_sha256": "evidence/source_records.jsonl",
        "decisions_sha256": "evidence/source_decisions.jsonl",
        "split_manifest_sha256": "evidence/source_split_manifest.json",
        "source_audit_sha256": "evidence/source_supervision_audit.json",
        "supervision_policy_sha256": "evidence/supervision_policy.json",
    }
    source_hashes: dict[str, str] = {}
    for hash_key, relative_path in evidence_bindings.items():
        expected = source.get(hash_key)
        artifact_path = dataset_dir / relative_path
        if not isinstance(expected, str) or _sha256_file(artifact_path) != expected:
            raise ValueError(f"source evidence hash mismatch: {relative_path}")
        source_hashes[hash_key] = expected
    policy = _load_json(dataset_dir / "evidence/supervision_policy.json")
    policy_id = _required_string(policy, "policy_id")
    if manifest.get("policy_ids") != [policy_id]:
        raise ValueError("manifest policy_ids do not match policy evidence")
    source_records = _load_jsonl(dataset_dir / "evidence/source_records.jsonl")
    decisions = _load_jsonl(dataset_dir / "evidence/source_decisions.jsonl")
    source_audit = _load_json(dataset_dir / "evidence/source_supervision_audit.json")
    decision_index = _validate_source_supervision_evidence(
        source_records=source_records,
        decisions=decisions,
        source_audit=source_audit,
        supervision_policy=policy,
    )
    if manifest.get("record_count") != len(source_records):
        raise ValueError("manifest record_count does not match source records")
    system_prompt_hashes = {
        _sha256_text(record["messages"][0]["content"]) for record in source_records
    }
    expected_renderer_contract = {
        "adapter": "gen_retry.sft.llamafactory@v1",
        "source_renderer": "gen_retry.sft.supervision.render_messages",
        "system_prompt_sha256": (
            next(iter(system_prompt_hashes)) if len(system_prompt_hashes) == 1 else None
        ),
        "image_injection": "prepend one <image> token per unique visible artifact",
    }
    if manifest.get("renderer_contract") != expected_renderer_contract:
        raise ValueError("renderer contract does not match copied source records")
    for source_record in source_records:
        sample_id = _required_string(source_record, "sample_id")
        _validate_source_messages(
            source_record,
            supervision_policy=policy,
            decision=decision_index.get(sample_id),
        )

    derived_authorized = release_status == "frozen"
    if manifest.get("training_authorized") is not derived_authorized:
        raise ValueError("training_authorized is inconsistent with release_status")
    if not derived_authorized:
        if manifest.get("gate_approval_ref") is not None:
            raise ValueError("provisional export unexpectedly has Gate 3 approval")
        if manifest.get("gate_approval_sha256") is not None:
            raise ValueError("provisional export unexpectedly has approval hash")
        return False

    approval_path = dataset_dir / "evidence/gate3_approval.json"
    if _sha256_file(approval_path) != manifest.get("gate_approval_sha256"):
        raise ValueError("copied Gate 3 approval hash mismatch")
    approval = _load_json(approval_path)
    copied_review = dataset_dir / "evidence/gate3_review.md"
    approval_for_validation = dict(approval)
    approval_for_validation["review_artifact"] = dict(
        approval.get("review_artifact") or {},
        path=str(copied_review),
    )
    _validate_gate_approval(
        approval_for_validation,
        policy_id=policy_id,
        evidence_hashes=source_hashes,
        approval_path=approval_path,
    )
    return True


def _validate_complete_token_audit(
    *,
    report_path: Path,
    runtime_config_path: Path,
    dataset_dir: Path,
) -> dict[str, Any]:
    report = _load_json(report_path.resolve())
    if report.get("status") != "PASS" or report.get("complete") is not True:
        raise PermissionError("formal training requires a complete PASS token audit")
    if report.get("runtime_config_sha256") != _sha256_file(
        runtime_config_path.resolve()
    ):
        raise PermissionError("token audit is for a different runtime config")
    runtime_config = yaml.safe_load(runtime_config_path.read_text(encoding="utf-8"))
    if (
        not isinstance(runtime_config, dict)
        or Path(runtime_config.get("dataset_dir", "")).resolve()
        != dataset_dir.resolve()
    ):
        raise PermissionError("runtime config points to a different dataset directory")
    manifest_path = dataset_dir.resolve() / "export_manifest.json"
    if report.get("dataset_manifest_sha256") != _sha256_file(manifest_path):
        raise PermissionError("token audit is for a different dataset manifest")
    if report.get("llamafactory_version") != "0.9.5":
        raise PermissionError("token audit used an unapproved LLaMA-Factory version")
    runtime_config = yaml.safe_load(runtime_config_path.read_text(encoding="utf-8"))
    if _report_to_contains_wandb(runtime_config.get("report_to")):
        wandb_version = report.get("wandb_version")
        if not isinstance(wandb_version, str) or not wandb_version:
            raise PermissionError("token audit did not record the W&B runtime version")
    return report


def _validate_llamafactory_cli_environment(
    executable: Path,
    audit_report: dict[str, Any],
    *,
    require_wandb: bool = False,
) -> None:
    first_line = executable.read_text(encoding="utf-8").splitlines()[0]
    if not first_line.startswith("#!"):
        raise PermissionError("LLaMA-Factory CLI has no auditable Python shebang")
    # Preserve a venv interpreter symlink. Resolving it to the base Python
    # drops the venv site-packages and makes an identical audited environment
    # appear unavailable.
    python_path = Path(first_line[2:].strip()).expanduser()
    if not python_path.is_absolute():
        python_path = (executable.parent / python_path).absolute()
    if not python_path.is_file():
        raise PermissionError("LLaMA-Factory CLI Python environment is unavailable")
    wandb_probe = (
        ", 'wandb_version':version('wandb')" if require_wandb else ""
    )
    probe = subprocess.run(
        [
            str(python_path),
            "-c",
            (
                "import hashlib,json; from importlib.metadata import version; "
                "import llamafactory.data.mm_plugin as m; "
                "from pathlib import Path; "
                "print(json.dumps({'version':version('llamafactory'),"
                "'mm_plugin_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()"
                f"{wandb_probe}}}))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(probe.stdout.strip().splitlines()[-1])
    expected = {
        "version": audit_report.get("llamafactory_version"),
        "mm_plugin_sha256": audit_report.get("llamafactory_mm_plugin_sha256"),
    }
    if require_wandb:
        expected["wandb_version"] = audit_report.get("wandb_version")
    if actual != expected:
        raise PermissionError(
            "training CLI environment differs from token-audit environment"
        )


def _configure_wandb_training_args(
    config: dict[str, Any],
    *,
    mode: str,
    run_name: str | None,
) -> None:
    if mode not in SUPPORTED_WANDB_MODES:
        raise ValueError(f"unsupported W&B mode: {mode}")
    if mode == "disabled":
        config["report_to"] = "none"
        config.pop("run_name", None)
        return
    config["report_to"] = "wandb"
    if run_name is not None:
        config["run_name"] = _validate_wandb_text("run_name", run_name)
    elif not isinstance(config.get("run_name"), str) or not config["run_name"].strip():
        raise ValueError("W&B tracking requires an explicit run_name")


def _wandb_subprocess_environment(
    *,
    base_env: dict[str, str],
    runtime_config: dict[str, Any],
    mode: str,
    entity: str,
    project: str,
    group: str,
    tags: list[str],
    directory: Path | None,
) -> tuple[dict[str, str], dict[str, Any]]:
    if mode not in SUPPORTED_WANDB_MODES:
        raise ValueError(f"unsupported W&B mode: {mode}")
    uses_wandb = _report_to_contains_wandb(runtime_config.get("report_to"))
    if mode == "disabled":
        if uses_wandb:
            raise ValueError(
                "runtime config enables W&B but launcher mode is disabled; "
                "prepare the config with --wandb-mode disabled"
            )
        return dict(base_env), {"enabled": False, "mode": "disabled"}
    if not uses_wandb:
        raise ValueError(
            "runtime config does not enable W&B; prepare it without "
            "--wandb-mode disabled"
        )

    entity = _validate_wandb_text("entity", entity)
    project = _validate_wandb_text("project", project)
    group = _validate_wandb_text("group", group)
    run_name = _validate_wandb_text("run_name", runtime_config.get("run_name"))
    normalized_tags = [_validate_wandb_tag(tag) for tag in tags]
    finetuning_type = runtime_config.get("finetuning_type")
    if isinstance(finetuning_type, str) and finetuning_type:
        normalized_tags.append(finetuning_type)
    seed = runtime_config.get("seed")
    if isinstance(seed, int):
        normalized_tags.append(f"seed-{seed}")
    normalized_tags = list(dict.fromkeys(normalized_tags))

    env = dict(base_env)
    has_api_key = _wandb_credentials_available(env)
    resolved_mode = mode
    if mode == "auto":
        resolved_mode = "online" if has_api_key else "offline"
    if resolved_mode == "online" and not has_api_key:
        raise RuntimeError(
            "W&B online mode requires WANDB_API_KEY or a user-level wandb login"
        )

    output_dir = Path(str(runtime_config["output_dir"])).resolve()
    wandb_dir = (
        directory.expanduser().resolve()
        if directory is not None
        else output_dir.parent / "wandb"
    )
    wandb_dir.mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "WANDB_MODE": resolved_mode,
            "WANDB_ENTITY": entity,
            "WANDB_PROJECT": project,
            "WANDB_RUN_GROUP": group,
            "WANDB_JOB_TYPE": "sft",
            "WANDB_TAGS": ",".join(normalized_tags),
            "WANDB_DIR": str(wandb_dir),
            "WANDB_LOG_MODEL": "false",
            "WANDB_WATCH": "false",
            "WANDB_SILENT": "true",
        }
    )
    return env, {
        "enabled": True,
        "mode": resolved_mode,
        "entity": entity,
        "project": project,
        "group": group,
        "run_name": run_name,
        "tags": normalized_tags,
        "directory": str(wandb_dir),
    }


def _report_to_contains_wandb(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "wandb"
    if isinstance(value, list):
        return any(
            isinstance(item, str) and item.lower() == "wandb" for item in value
        )
    return False


def _wandb_credentials_available(env: dict[str, str]) -> bool:
    """Check for credentials without reading or exposing the credential value.

    W&B supports both ``WANDB_API_KEY`` and a user-level netrc entry.  The
    launcher inherits the latter when a user has run ``wandb login``.  Tests
    that omit ``HOME`` remain deterministic and do not inspect the caller's
    real home directory.
    """

    if env.get("WANDB_API_KEY", "").strip():
        return True
    netrc_path = env.get("NETRC")
    if netrc_path is None:
        home = env.get("HOME")
        if not home:
            return False
        netrc_path = str(Path(home).expanduser() / ".netrc")
    try:
        credentials = netrc_module.netrc(netrc_path).authenticators("api.wandb.ai")
    except (FileNotFoundError, OSError, netrc_module.NetrcParseError):
        return False
    return bool(credentials and credentials[2])


def _validate_wandb_text(field: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"W&B {field} must be a non-empty string")
    normalized = value.strip()
    if "\n" in normalized or "\r" in normalized or "\x00" in normalized:
        raise ValueError(f"W&B {field} contains control characters")
    return normalized


def _validate_wandb_tag(value: Any) -> str:
    tag = _validate_wandb_text("tag", value)
    if "," in tag:
        raise ValueError("W&B tags cannot contain commas")
    return tag


def _validate_source_messages(
    source: dict[str, Any],
    *,
    supervision_policy: dict[str, Any],
    decision: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    sample_id = _required_string(source, "sample_id")
    policy_id = _required_string(supervision_policy, "policy_id")
    accepted_labels = set(supervision_policy.get("accepted_action_labels") or [])
    policy_actions = set(supervision_policy.get("targetable_actions") or [])
    phase3_label = source.get("phase3_label")
    if source.get("policy_id") != policy_id:
        raise ValueError(f"{sample_id}: source policy is not the supplied policy")
    if phase3_label not in accepted_labels:
        raise ValueError(f"{sample_id}: non-positive phase3_label {phase3_label}")
    if decision is None:
        raise ValueError(f"{sample_id}: no matching supervision decision")
    decision_contract = {
        "include_as_target": True,
        "loss_weight": 1,
        "phase3_label": phase3_label,
        "policy_id": policy_id,
        "action": source.get("action"),
        "split": source.get("split"),
    }
    for key, expected in decision_contract.items():
        if decision.get(key) != expected:
            raise ValueError(f"{sample_id}: supervision decision mismatch for {key}")
    messages = source.get("messages")
    if not isinstance(messages, list) or len(messages) != 3:
        raise ValueError(f"{sample_id}: expected exactly three source messages")
    roles = tuple(message.get("role") for message in messages)
    weights = tuple(message.get("loss_weight") for message in messages)
    if roles != EXPECTED_ROLES:
        raise ValueError(f"{sample_id}: invalid roles {roles}")
    if weights != EXPECTED_LOSS_WEIGHTS:
        raise ValueError(f"{sample_id}: invalid message loss weights {weights}")
    loss_mask = source.get("loss_mask")
    if not isinstance(loss_mask, list) or len(loss_mask) != 3:
        raise ValueError(f"{sample_id}: missing exact loss mask")
    for index, (mask, role, weight) in enumerate(
        zip(loss_mask, EXPECTED_ROLES, EXPECTED_LOSS_WEIGHTS, strict=True)
    ):
        if (
            mask.get("message_index") != index
            or mask.get("role") != role
            or mask.get("loss_weight") != weight
        ):
            raise ValueError(f"{sample_id}: loss mask mismatch at message {index}")
    if not all(isinstance(message.get("content"), str) for message in messages):
        raise ValueError(f"{sample_id}: every message requires string content")
    try:
        action = json.loads(messages[-1]["content"])
    except json.JSONDecodeError as exc:
        raise ValueError(f"{sample_id}: assistant target is not JSON") from exc
    validate_instance(action, "action_protocol_v0_5.schema.json")
    if action.get("action") not in ALL_TARGETABLE_ACTIONS:
        raise ValueError(f"{sample_id}: action is context-only under the freeze")
    if action.get("action") not in policy_actions:
        raise ValueError(
            f"{sample_id}: action is context-only under the supplied policy"
        )
    if source.get("action") != action.get("action"):
        raise ValueError(f"{sample_id}: top-level action does not match target")
    if messages[-1]["content"] != canonical_json(action):
        raise ValueError(f"{sample_id}: target is not deterministic canonical JSON")
    if source.get("target_text_sha256") != _sha256_text(messages[-1]["content"]):
        raise ValueError(f"{sample_id}: target hash mismatch")
    return messages


def _strip_template_terminator(decoded: str, eos_token: str | None) -> str:
    if not eos_token:
        raise ValueError("tokenizer has no EOS token")
    suffix = eos_token + "\n"
    if decoded.endswith(suffix):
        return decoded[: -len(suffix)]
    if decoded.endswith(eos_token):
        return decoded[: -len(eos_token)]
    raise ValueError("decoded labels do not end with the template EOS token")


def _resolve_image_bindings(
    *,
    source: dict[str, Any],
    run_root: Path,
    output_dir: Path,
    image_hash_cache: dict[Path, str],
) -> list[dict[str, Any]]:
    sample_id = source["sample_id"]
    episode_id = source["episode_id"]
    user_message = source["messages"][1]
    refs = user_message.get("image_refs") or []
    if not isinstance(refs, list):
        raise ValueError(f"{sample_id}: image_refs must be a list")
    episode_root = (run_root / episode_id).resolve()
    if not episode_root.is_relative_to(run_root):
        raise ValueError(f"{sample_id}: episode_id escapes run root")
    if not episode_root.is_dir():
        raise FileNotFoundError(episode_root)
    bindings: list[dict[str, Any]] = []
    grouped_refs: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for ref in refs:
        if not isinstance(ref, dict):
            raise ValueError(f"{sample_id}: image ref must be an object")
        artifact_id = _required_string(ref, "artifact_id")
        uri = _required_string(ref, "uri")
        key = (artifact_id, uri)
        grouped_refs.setdefault(key, []).append(ref)

    for (artifact_id, uri), matching_refs in grouped_refs.items():
        attempt_ids = {_required_string(ref, "attempt_id") for ref in matching_refs}
        roles = {_required_string(ref, "role") for ref in matching_refs}
        if len(attempt_ids) != 1:
            raise ValueError(f"{sample_id}: one artifact/URI maps to multiple attempts")
        uri_path = Path(uri)
        if uri_path.is_absolute() or ".." in uri_path.parts:
            raise ValueError(f"{sample_id}: unsafe image URI {uri}")
        source_path = (episode_root / uri_path).resolve()
        if not source_path.is_relative_to(episode_root):
            raise ValueError(f"{sample_id}: image escapes episode root {uri}")
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        image_hash = image_hash_cache.get(source_path)
        if image_hash is None:
            image_hash = _sha256_file(source_path)
            image_hash_cache[source_path] = image_hash
        suffix = source_path.suffix.lower()
        if not suffix or len(suffix) > 10:
            raise ValueError(f"{sample_id}: invalid image suffix {source_path.suffix}")
        dataset_relative_path = Path("images") / f"{image_hash}{suffix}"
        dataset_image_path = output_dir / dataset_relative_path
        dataset_image_path.parent.mkdir(exist_ok=True)
        if dataset_image_path.exists():
            if _sha256_file(dataset_image_path) != image_hash:
                raise ValueError("content-addressed image path has conflicting bytes")
        else:
            shutil.copy2(source_path, dataset_image_path)
        bindings.append(
            {
                "artifact_id": artifact_id,
                "attempt_id": next(iter(attempt_ids)),
                "visible_roles": sorted(roles),
                "dataset_path": dataset_relative_path.as_posix(),
                "source_path": str(source_path),
                "sha256": image_hash,
            }
        )
    return bindings


def _validate_training_config(config: dict[str, Any]) -> None:
    required = {
        "stage": "sft",
        "do_train": True,
        "template": LLAMAFACTORY_TEMPLATE,
        "enable_thinking": False,
        "train_on_prompt": False,
        "mask_history": True,
        "packing": False,
        "freeze_vision_tower": True,
        "freeze_multi_modal_projector": True,
        "flash_attn": "fa2",
    }
    for key, expected in required.items():
        if config.get(key) != expected:
            raise ValueError(f"training config requires {key}={expected!r}")
    if config.get("finetuning_type") not in {"lora", "full"}:
        raise ValueError("finetuning_type must be lora or full")
    if int(config.get("cutoff_len", 0)) < 4096:
        raise ValueError("cutoff_len must be at least 4096 for canonical contexts")
    if config.get("overwrite_output_dir") is not False:
        raise ValueError("overwrite_output_dir must remain false")


def _dataset_info(dataset_prefix: str) -> dict[str, Any]:
    return {
        f"{dataset_prefix}_{split}": _dataset_info_entry(f"{split}.jsonl")
        for split in SUPPORTED_SPLITS
    }


def _dataset_info_entry(file_name: str) -> dict[str, Any]:
    return {
        "file_name": file_name,
        "formatting": "sharegpt",
        "columns": {"messages": "messages", "images": "images"},
        "tags": {
            "role_tag": "role",
            "content_tag": "content",
            "user_tag": "user",
            "assistant_tag": "assistant",
            "system_tag": "system",
        },
    }


def _prompt_group_by_episode(
    split_manifest: dict[str, Any],
    *,
    run_root: Path,
) -> dict[str, str]:
    result: dict[str, str] = {}
    episode_splits = split_manifest.get("episode_splits") or {}
    if not isinstance(episode_splits, dict):
        raise ValueError("split manifest episode_splits must be an object")
    prompt_groups = split_manifest.get("prompt_groups") or {}
    if not isinstance(prompt_groups, dict):
        raise ValueError("split manifest prompt_groups must be an object")
    for prompt_hash, record in prompt_groups.items():
        if not isinstance(record, dict):
            raise ValueError("split manifest prompt-group record must be an object")
        split = record.get("split")
        episode_ids = record.get("episode_ids")
        if episode_ids is None:
            episode_ids = [record.get("episode_id")]
        if (
            not isinstance(episode_ids, list)
            or not episode_ids
            or not all(isinstance(item, str) and item for item in episode_ids)
            or split not in SUPPORTED_SPLITS
        ):
            raise ValueError("invalid prompt-group split record")
        for episode_id in episode_ids:
            existing = result.get(episode_id)
            if existing is not None:
                raise ValueError(
                    f"episode belongs to multiple prompt groups: {episode_id}"
                )
            if episode_splits.get(episode_id) != split:
                raise ValueError(
                    f"prompt-group split disagrees for episode: {episode_id}"
                )
            result[episode_id] = prompt_hash

    if set(result) != set(episode_splits):
        raise ValueError(
            "prompt-group membership does not cover episode_splits exactly"
        )
    actual_group_splits: dict[str, set[str]] = {}
    for episode_id, split in episode_splits.items():
        episode_root = (run_root / episode_id).resolve()
        if not episode_root.is_relative_to(run_root):
            raise ValueError(f"episode_id escapes run root: {episode_id}")
        task_spec = _load_json(episode_root / "task_spec.json")
        prompt_hash = _sha256_text(_required_string(task_spec, "original_prompt"))
        if result.get(episode_id) != prompt_hash:
            raise ValueError(f"prompt-group hash mismatch for episode: {episode_id}")
        actual_group_splits.setdefault(prompt_hash, set()).add(split)
    leaks = {
        prompt_hash: sorted(splits)
        for prompt_hash, splits in actual_group_splits.items()
        if len(splits) > 1
    }
    if leaks:
        raise ValueError(f"recomputed prompt-group cross-split leakage: {leaks}")
    return result


def _integer_percentiles(values: list[int]) -> dict[str, int]:
    if not values:
        return {}
    ordered = sorted(values)

    def percentile(q: float) -> int:
        index = min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1)
        return ordered[index]

    return {
        "p50": percentile(0.50),
        "p90": percentile(0.90),
        "p95": percentile(0.95),
        "max": ordered[-1],
    }


def _target_multiset_sha256(targets: list[str]) -> str:
    counts = Counter(_sha256_text(target) for target in targets)
    return _sha256_text(canonical_json(dict(sorted(counts.items()))))


def _required_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"required non-empty string field missing: {key}")
    return value


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object at {path}:{line_number}")
            records.append(value)
    return records


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(canonical_json(record) + "\n" for record in records),
        encoding="utf-8",
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
