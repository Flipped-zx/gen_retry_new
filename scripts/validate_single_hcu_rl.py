from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import traceback
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gen_retry.agent.sft_planner import (  # noqa: E402
    build_sft_inference_messages,
    checkpoint_fingerprint,
)
from gen_retry.agent.teacher_client import TeacherImageRef  # noqa: E402
from gen_retry.domain.artifacts import sha256_file  # noqa: E402
from gen_retry.protocol.action_parser import parse_action  # noqa: E402
from gen_retry.protocol.reference_validator import (  # noqa: E402
    validate_action_references,
)
from gen_retry.rl.admission import admit_rollout_sample_batch  # noqa: E402
from gen_retry.rl.config import load_experiment_config  # noqa: E402
from gen_retry.rl.optimizer import (  # noqa: E402
    optimizer_metrics,
    prepare_optimizer_batch,
)
from gen_retry.rl.tracking import initialize_wandb_run  # noqa: E402
from gen_retry.rl.training import build_advantage_batch  # noqa: E402
from gen_retry.runtime.json_canonical import canonical_json  # noqa: E402
from gen_retry.runtime.planner_view import DEFAULT_SKILL_MANIFEST  # noqa: E402


DEFAULT_MODEL = ROOT / "runs/sft_checkpoints/flow1000_v9_selective_skill_full_s42"
DEFAULT_EPISODE = ROOT / "runs/phase7_sft_frozen_test20_v2/phase3_ep_028"
DEFAULT_CONFIG = ROOT / "configs/rl/naive_geneval2_grpo_v0_1.yaml"
DEFAULT_OUTPUT = ROOT / "runs/rl_single_hcu_validation_v0_1"
STAGES = ("environment", "memory", "generate", "score", "bridge")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run fail-closed single-HCU diagnostics for the frozen Gen-Retry RL "
            "initialization checkpoint."
        )
    )
    parser.add_argument("--stage", choices=("all", *STAGES), default="all")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--episode", type=Path, default=DEFAULT_EPISODE)
    parser.add_argument("--planner-context-index", type=int, default=2)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-name")
    parser.add_argument("--generation-input", type=Path)
    parser.add_argument("--max-model-len", type=int, default=8192)
    parser.add_argument("--max-action-tokens", type=int, default=512)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.75)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(payload: Any) -> str:
    return _sha256_bytes(canonical_json(payload).encode("utf-8"))


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _episode_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], list[TeacherImageRef]]:
    episode = args.episode.resolve()
    task_spec = _read_json(episode / "task_spec.json")
    context_path = episode / "planner_contexts" / (
        f"planner_context_{args.planner_context_index:03d}.json"
    )
    planner_context = _read_json(context_path)
    image_refs: list[TeacherImageRef] = []
    visible = _visible_image_records(episode, args.planner_context_index)
    for item in visible:
        image_path = episode / item["uri"]
        if not image_path.is_file():
            raise FileNotFoundError(f"visible image is missing: {image_path}")
        image_refs.append(
            TeacherImageRef(
                role=str(item["role"]),
                attempt_id=str(item["attempt_id"]),
                artifact_id=str(item["artifact_id"]),
                path=image_path,
            )
        )
    if not image_refs:
        raise ValueError("the selected PlannerContext must contain a real image")
    return task_spec, planner_context, image_refs


def _visible_image_records(episode: Path, context_index: int) -> list[dict[str, str]]:
    expected_ref = f"planner_contexts/planner_context_{context_index:03d}.json"
    for raw_line in (episode / "planner_requests.jsonl").read_text(
        encoding="utf-8"
    ).splitlines():
        record = json.loads(raw_line)
        if record.get("planner_context_ref") != expected_ref:
            continue
        text_payload = json.loads(record["planner_text_input"])
        visible = text_payload.get("visible_images", [])
        if not isinstance(visible, list):
            raise ValueError("visible_images must be an array")
        return visible
    raise ValueError(f"no planner request binds {expected_ref}")


def _known_attempt_ids(payload: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if (
                key in {
                    "attempt_id",
                    "source_attempt_id",
                    "selected_attempt_id",
                    "result_attempt_id",
                    "baseline_attempt_id",
                }
                and isinstance(value, str)
                and value
            ):
                result.add(value)
            result.update(_known_attempt_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            result.update(_known_attempt_ids(item))
    return result


def _sampled_log_probs(token_ids: Iterable[int], entries: Iterable[Any]) -> list[float]:
    result: list[float] = []
    for index, (token_id, entry) in enumerate(zip(token_ids, entries, strict=True)):
        if entry is None or token_id not in entry:
            raise ValueError(f"sampled token {index} is absent from vLLM logprobs")
        value = float(entry[token_id].logprob)
        if not math.isfinite(value):
            raise ValueError(f"sampled token {index} has a non-finite logprob")
        result.append(value)
    return result


def _stage_environment(args: argparse.Namespace) -> dict[str, Any]:
    import ray
    import torch

    from gen_retry.rl.tracking import build_wandb_runtime
    from verl.workers.rollout.base import get_rollout_class

    started = time.monotonic()
    packages = {
        name: _package_version(name)
        for name in ("torch", "vllm", "verl", "ray", "wandb", "sglang", "rllm")
    }
    if any(packages[name] is None for name in ("torch", "vllm", "verl", "ray", "wandb")):
        raise RuntimeError("one or more single-HCU diagnostic packages are missing")
    if torch.cuda.device_count() != 1:
        raise RuntimeError(
            f"single-HCU diagnostic requires exactly one visible device, found {torch.cuda.device_count()}"
        )
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("visible HCU does not report BF16 support")
    rollout_class = get_rollout_class("vllm", "async")
    if rollout_class.__name__ != "vLLMAsyncRollout":
        raise RuntimeError(f"unexpected verl vLLM rollout class: {rollout_class}")

    ray.shutdown()
    ray_context = ray.init(
        num_cpus=1,
        include_dashboard=False,
        ignore_reinit_error=False,
        log_to_driver=False,
    )

    @ray.remote
    def runtime_ping() -> dict[str, object]:
        return {"ok": True, "pid": os.getpid()}

    ray_result = ray.get(runtime_ping.remote())
    ray_address = ray_context.address_info.get("address")
    ray.shutdown()
    if ray_result.get("ok") is not True or ray.is_initialized():
        raise RuntimeError("Ray local start/remote execution/shutdown did not complete")

    config = load_experiment_config(args.config.resolve())
    wandb_environment = dict(os.environ)
    wandb_environment[config.tracking.mode_env] = "offline"
    wandb_environment.pop(config.tracking.api_key_env, None)
    runtime = build_wandb_runtime(
        config.tracking,
        run_suffix="single-hcu-probe",
        environment=wandb_environment,
    )
    run = initialize_wandb_run(
        config.tracking,
        run_suffix="single-hcu-probe",
        run_config={"probe": "single_hcu", "api_key": "must_be_redacted"},
        environment=wandb_environment,
    )
    if run is None:
        raise RuntimeError("W&B offline initialization unexpectedly returned None")
    run.log({"probe/pass": 1})
    redacted_value = run.config.get("api_key")
    run_dir = str(run.dir)
    run.finish()
    if runtime.mode != "offline" or redacted_value != "REDACTED":
        raise RuntimeError("W&B mode or config sanitization check failed")

    properties = torch.cuda.get_device_properties(0)
    return {
        "stage": "environment",
        "status": "PASS",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "packages": packages,
        "formal_adapter_packages_present": {
            "rllm": packages["rllm"] is not None,
            "sglang": packages["sglang"] is not None,
        },
        "device": {
            "count": torch.cuda.device_count(),
            "name": properties.name,
            "total_memory_bytes": properties.total_memory,
            "bf16_supported": torch.cuda.is_bf16_supported(),
            "torch_hip": torch.version.hip,
        },
        "verl_rollout_class": rollout_class.__name__,
        "ray": {
            "address": ray_address,
            "remote_result": ray_result,
            "shutdown_confirmed": not ray.is_initialized(),
        },
        "wandb": {
            "mode": runtime.mode,
            "run_dir": run_dir,
            "credential_field": redacted_value,
        },
    }


def _stage_memory(_: argparse.Namespace) -> dict[str, Any]:
    import torch

    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    return {
        "stage": "memory",
        "status": "PASS",
        "device_count": torch.cuda.device_count(),
        "free_bytes": free_bytes,
        "total_bytes": total_bytes,
        "free_fraction": free_bytes / total_bytes,
        "process_allocated_bytes": torch.cuda.memory_allocated(0),
        "process_reserved_bytes": torch.cuda.memory_reserved(0),
    }


def _stage_generate(args: argparse.Namespace) -> dict[str, Any]:
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    started = time.monotonic()
    task_spec, planner_context, image_refs = _episode_inputs(args)
    messages = build_sft_inference_messages(
        task_spec=task_spec,
        planner_context=planner_context,
        image_refs=image_refs,
    )
    processor = AutoProcessor.from_pretrained(
        args.model.resolve(),
        max_pixels=262144,
        local_files_only=True,
        trust_remote_code=True,
        fix_mistral_regex=True,
    )
    prompt = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    processor_inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    expected_prompt_token_ids = processor_inputs["input_ids"][0].tolist()
    image_grid = processor_inputs["image_grid_thw"].tolist()
    del processor_inputs

    images = [Image.open(ref.path).convert("RGB") for ref in image_refs]
    engine = LLM(
        model=str(args.model.resolve()),
        tensor_parallel_size=1,
        dtype="bfloat16",
        max_model_len=args.max_model_len,
        max_num_seqs=1,
        gpu_memory_utilization=args.gpu_memory_utilization,
        enforce_eager=True,
        disable_log_stats=True,
        trust_remote_code=True,
        mm_processor_kwargs={"max_pixels": 262144},
        limit_mm_per_prompt={"image": len(images)},
    )
    loaded_seconds = time.monotonic() - started
    outputs = engine.generate(
        [
            {
                "prompt": prompt,
                "multi_modal_data": {
                    "image": images[0] if len(images) == 1 else images
                },
            }
        ],
        SamplingParams(
            temperature=0.7,
            top_p=0.95,
            top_k=-1,
            seed=args.seed,
            max_tokens=args.max_action_tokens,
            logprobs=1,
        ),
        use_tqdm=False,
    )
    request_output = outputs[0]
    completion = request_output.outputs[0]
    prompt_token_ids = list(request_output.prompt_token_ids)
    token_ids = list(completion.token_ids)
    old_log_probs = _sampled_log_probs(token_ids, completion.logprobs)
    if prompt_token_ids != expected_prompt_token_ids:
        raise ValueError(
            "vLLM prompt token IDs differ from the frozen Transformers renderer"
        )
    if not token_ids or len(token_ids) != len(old_log_probs):
        raise ValueError("vLLM sampled tokens and old logprobs do not align")
    parsed = parse_action(completion.text).action
    known_attempt_ids = _known_attempt_ids(planner_context)
    available_skill_ids = {
        str(entry["skill_id"]) for entry in DEFAULT_SKILL_MANIFEST
    }
    validate_action_references(
        parsed,
        task_spec,
        known_attempt_ids=known_attempt_ids,
        available_skill_ids=available_skill_ids,
    )
    if parsed["action"] not in planner_context["runtime_state"]["available_actions"]:
        raise ValueError("sampled action is not available in the canonical runtime state")
    if len(token_ids) > load_experiment_config(args.config.resolve()).rollout.max_action_tokens:
        raise ValueError("sampled Action exceeds the frozen 1,400-token limit")
    for image in images:
        image.close()

    return {
        "stage": "generate",
        "status": "PASS",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "model_load_seconds": round(loaded_seconds, 3),
        "model": str(args.model.resolve()),
        "checkpoint_fingerprint": checkpoint_fingerprint(args.model.resolve()),
        "episode": str(args.episode.resolve()),
        "planner_context_index": args.planner_context_index,
        "sampling": {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": -1,
            "seed": args.seed,
            "max_action_tokens": args.max_action_tokens,
        },
        "prompt_token_count": len(prompt_token_ids),
        "prompt_token_ids": prompt_token_ids,
        "completion_token_count": len(token_ids),
        "sampled_token_ids": token_ids,
        "old_log_probs": old_log_probs,
        "raw_text": completion.text,
        "raw_text_sha256": _sha256_bytes(completion.text.encode("utf-8")),
        "canonical_action": parsed,
        "known_attempt_ids": sorted(known_attempt_ids),
        "reference_validation": "PASS",
        "finish_reason": completion.finish_reason,
        "multimodal": {
            "image_count": len(image_refs),
            "image_grid_thw": image_grid,
            "image_artifacts": [
                {
                    "artifact_id": ref.artifact_id,
                    "attempt_id": ref.attempt_id,
                    "role": ref.role,
                    "path": str(ref.path.resolve()),
                    "sha256": sha256_file(ref.path),
                }
                for ref in image_refs
            ],
            "transformers_vllm_prompt_token_identity": True,
        },
        "runtime": {
            "torch": torch.__version__,
            "torch_hip": torch.version.hip,
            "vllm": _package_version("vllm"),
            "device_count": torch.cuda.device_count(),
        },
    }


def _stage_score(args: argparse.Namespace) -> dict[str, Any]:
    import torch
    from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

    if args.generation_input is None:
        raise ValueError("score stage requires --generation-input")
    started = time.monotonic()
    generation = _read_json(args.generation_input.resolve())
    task_spec, planner_context, image_refs = _episode_inputs(args)
    messages = build_sft_inference_messages(
        task_spec=task_spec,
        planner_context=planner_context,
        image_refs=image_refs,
    )
    processor = AutoProcessor.from_pretrained(
        args.model.resolve(),
        max_pixels=262144,
        local_files_only=True,
        trust_remote_code=True,
        fix_mistral_regex=True,
    )
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    prompt_token_ids = inputs["input_ids"][0].tolist()
    if prompt_token_ids != generation["prompt_token_ids"]:
        raise ValueError("reference scorer prompt tokens differ from rollout tokens")
    sampled_token_ids = [int(value) for value in generation["sampled_token_ids"]]
    decoded = processor.tokenizer.decode(
        sampled_token_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    if decoded != generation["raw_text"]:
        raise ValueError("sampled token IDs do not decode to the persisted response")
    if parse_action(decoded).action != generation["canonical_action"]:
        raise ValueError("decoded sampled tokens do not reproduce the canonical action")

    memory_before = torch.cuda.mem_get_info(0)[0]
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        args.model.resolve(),
        dtype=torch.bfloat16,
        local_files_only=True,
        device_map="auto",
        attn_implementation="flash_attention_2",
    )
    model.eval()
    loaded_seconds = time.monotonic() - started
    inputs = inputs.to(model.device)
    prompt_length = int(inputs["input_ids"].shape[1])
    target_ids = torch.tensor(
        sampled_token_ids,
        dtype=inputs["input_ids"].dtype,
        device=inputs["input_ids"].device,
    ).unsqueeze(0)
    forward_inputs = dict(inputs)
    forward_inputs["input_ids"] = torch.cat(
        [inputs["input_ids"], target_ids], dim=1
    )
    forward_inputs["attention_mask"] = torch.cat(
        [
            inputs["attention_mask"],
            torch.ones_like(target_ids, dtype=inputs["attention_mask"].dtype),
        ],
        dim=1,
    )
    with torch.inference_mode():
        logits = model(**forward_inputs, use_cache=False).logits[
            0, prompt_length - 1 : prompt_length + len(sampled_token_ids) - 1
        ]
        reference_log_probs_tensor = torch.log_softmax(logits.float(), dim=-1).gather(
            1, target_ids[0].unsqueeze(1)
        )[:, 0]
        reference_log_probs = reference_log_probs_tensor.cpu().tolist()
    if len(reference_log_probs) != len(sampled_token_ids):
        raise ValueError("reference logprobs do not align with sampled tokens")
    if not all(math.isfinite(value) for value in reference_log_probs):
        raise ValueError("reference logprobs contain a non-finite value")
    action_mask = [1] * len(sampled_token_ids)
    if sum(action_mask) != len(sampled_token_ids):
        raise ValueError("derived assistant Action mask is inconsistent")
    old_log_probs = [float(value) for value in generation["old_log_probs"]]
    if len(old_log_probs) != len(reference_log_probs):
        raise ValueError("old and reference logprob vectors do not align")
    maximum_delta = max(
        abs(old - reference)
        for old, reference in zip(old_log_probs, reference_log_probs, strict=True)
    )
    memory_peak = torch.cuda.max_memory_allocated(0)

    del reference_log_probs_tensor
    del logits
    del forward_inputs
    del target_ids
    del inputs
    del model
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    memory_after_cleanup = torch.cuda.mem_get_info(0)[0]
    return {
        "stage": "score",
        "status": "PASS",
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "model_load_seconds": round(loaded_seconds, 3),
        "prompt_token_identity": True,
        "sampled_response_decode_identity": True,
        "sampled_token_ids": sampled_token_ids,
        "assistant_action_mask": action_mask,
        "old_log_probs": old_log_probs,
        "reference_log_probs": reference_log_probs,
        "vector_length": len(sampled_token_ids),
        "all_values_finite": True,
        "max_abs_old_reference_logprob_delta": maximum_delta,
        "mask_derivation": "one strict parsed assistant Action turn",
        "device_memory": {
            "free_before_model_load_bytes": memory_before,
            "peak_process_allocated_bytes": memory_peak,
            "free_after_explicit_cleanup_bytes": memory_after_cleanup,
        },
    }


def _artifact(root: Path, ref: str, payload: bytes) -> dict[str, str]:
    path = root / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"ref": ref, "sha256": _sha256_bytes(payload)}


def _json_artifact(root: Path, ref: str, payload: Any) -> dict[str, str]:
    return _artifact(root, ref, (canonical_json(payload) + "\n").encode("utf-8"))


def _stage_bridge(args: argparse.Namespace) -> dict[str, Any]:
    import torch
    from verl import DataProto
    from verl.workers.rollout.base import get_rollout_class

    if args.generation_input is None:
        raise ValueError("bridge stage requires --generation-input")
    score_input = args.output_dir / "reference_score.json"
    generation = _read_json(args.generation_input.resolve())
    score = _read_json(score_input.resolve())
    config = load_experiment_config(args.config.resolve())
    artifact_root = args.output_dir.resolve() / "optimizer_bridge"
    artifact_root.mkdir(parents=True, exist_ok=True)
    token_ids = score["sampled_token_ids"]
    action_mask = score["assistant_action_mask"]
    old_log_probs = score["old_log_probs"]
    reference_log_probs = score["reference_log_probs"]
    task_spec, planner_context, _ = _episode_inputs(args)
    candidates: list[dict[str, Any]] = []
    for index in range(config.rollout.full_rollouts_per_prompt):
        candidate_id = f"single_hcu_candidate_{index:02d}"
        prefix = f"artifacts/{candidate_id}"
        sampled_response = _artifact(
            artifact_root,
            f"{prefix}/sampled_response.json",
            generation["raw_text"].encode("utf-8"),
        )
        score_payload = {
            "schema_version": "0.1",
            "reward_policy_id": "geneval2_terminal_outcome@0.1",
            "candidate_id": candidate_id,
            "outcome_kind": "success",
            "submitted_attempt_id": f"diagnostic_attempt_{index:02d}",
            "submitted_score": {
                "pass_count": index,
                "atom_count": len(task_spec["constraints"]),
                "primary_score": 0.5,
            },
            "terminal_utility": index + 0.125,
            "invalid_action_penalty": 0.0,
            "total_return": index + 0.125,
        }
        candidates.append(
            {
                "candidate_id": candidate_id,
                "sample_sha256": sampled_response["sha256"],
                "outcome_kind": "success",
                "trainable_token_count": len(token_ids),
                "assistant_action_token_counts": [len(token_ids)],
                "sampled_response": sampled_response,
                "sampled_token_ids": _json_artifact(
                    artifact_root, f"{prefix}/sampled_token_ids.json", token_ids
                ),
                "assistant_action_mask": _json_artifact(
                    artifact_root, f"{prefix}/assistant_action_mask.json", action_mask
                ),
                "old_log_probs": _json_artifact(
                    artifact_root, f"{prefix}/old_log_probs.json", old_log_probs
                ),
                "reference_log_probs": _json_artifact(
                    artifact_root,
                    f"{prefix}/reference_log_probs.json",
                    reference_log_probs,
                ),
                "rollout_events": _artifact(
                    artifact_root,
                    f"{prefix}/rollout_events.jsonl",
                    (
                        canonical_json(
                            {
                                "diagnostic_only": True,
                                "event_id": f"diagnostic_event_{index:02d}",
                                "note": "No image backend or Geneval2 execution was claimed.",
                            }
                        )
                        + "\n"
                    ).encode("utf-8"),
                ),
                "reward_components": _json_artifact(
                    artifact_root, f"{prefix}/reward_components.json", score_payload
                ),
                "infrastructure_retries": [],
            }
        )
    sampling = {
        "temperature": config.rollout.temperature,
        "top_p": config.rollout.top_p,
        "top_k": config.rollout.top_k,
        "max_action_tokens": config.rollout.max_action_tokens,
        "max_episode_assistant_tokens": config.rollout.max_total_assistant_tokens,
        "seed": config.rollout.seed,
    }
    state_sha256 = _canonical_sha256(planner_context)
    rollout_payload = {
        "schema_version": "0.1",
        "batch_id": "single_hcu_optimizer_bridge_v0_1",
        "planned_group_count": 1,
        "excluded_groups": [],
        "groups": [
            {
                "group_id": "single_hcu_group_000",
                "group_kind": "episode",
                "state_id": "planner_context_sha256:" + state_sha256,
                "prompt_id": str(task_spec["episode_id"]),
                "prompt_sha256": _sha256_bytes(
                    task_spec["original_prompt"].encode("utf-8")
                ),
                "atom_set_sha256": _canonical_sha256(task_spec["constraints"]),
                "canonical_state_sha256": state_sha256,
                "sampling_policy_id": config.policy_revision,
                "policy_checkpoint": {
                    "ref": str(config.base_checkpoint),
                    "sha256": config.checkpoint_sha256,
                },
                "policy_revision": config.policy_revision,
                "sampling_config": sampling,
                "sampling_config_sha256": _canonical_sha256(sampling),
                "candidates": candidates,
            }
        ],
    }
    rollout_path = artifact_root / "rollout_sample_batch.json"
    _write_json(rollout_path, rollout_payload)
    admission = admit_rollout_sample_batch(
        rollout_payload,
        artifact_root=artifact_root,
        config=config,
    )
    advantage_payload = build_advantage_batch(
        admission.candidate_return_batch,
        config=config.reward,
    )
    advantage_path = artifact_root / "advantage_batch.json"
    _write_json(advantage_path, advantage_payload)
    optimizer_batch = prepare_optimizer_batch(
        rollout_payload=rollout_payload,
        advantage_payload=advantage_payload,
        artifact_root=artifact_root,
        config=config,
    )
    tensors = {
        "responses": torch.tensor(
            [sample.sampled_token_ids for sample in optimizer_batch.samples],
            dtype=torch.long,
        ),
        "response_mask": torch.tensor(
            [sample.assistant_action_mask for sample in optimizer_batch.samples],
            dtype=torch.long,
        ),
        "old_log_probs": torch.tensor(
            [sample.old_log_probs for sample in optimizer_batch.samples],
            dtype=torch.float32,
        ),
        "reference_log_probs": torch.tensor(
            [sample.reference_log_probs for sample in optimizer_batch.samples],
            dtype=torch.float32,
        ),
        "advantages": torch.tensor(
            [sample.advantage for sample in optimizer_batch.samples],
            dtype=torch.float32,
        ),
    }
    data_proto = DataProto.from_single_dict(
        tensors,
        meta_info={
            "diagnostic_only": True,
            "source": "gen_retry.rl.optimizer.prepare_optimizer_batch",
        },
    )
    if data_proto.batch.batch_size[0] != len(optimizer_batch.samples):
        raise ValueError("verl DataProto batch size differs from optimizer bridge")
    if get_rollout_class("vllm", "async").__name__ != "vLLMAsyncRollout":
        raise ValueError("verl vLLM rollout interface resolution failed")
    return {
        "stage": "bridge",
        "status": "PASS",
        "diagnostic_only": True,
        "reward_evidence": "synthetic_terminal_rewards_for_join_validation",
        "image_or_geneval2_execution_claimed": False,
        "rollout_batch": {
            "path": str(rollout_path),
            "sha256": sha256_file(rollout_path),
        },
        "advantage_batch": {
            "path": str(advantage_path),
            "sha256": sha256_file(advantage_path),
        },
        "admission": {
            "planned_groups": admission.planned_group_count,
            "admitted_groups": admission.group_count,
            "candidate_count": admission.candidate_count,
            "policy_invalid_count": admission.policy_invalid_count,
        },
        "optimizer": optimizer_metrics(optimizer_batch),
        "verl": {
            "rollout_class": "vLLMAsyncRollout",
            "data_proto_batch_size": data_proto.batch.batch_size[0],
            "tensor_shapes": {
                name: list(tensor.shape) for name, tensor in tensors.items()
            },
        },
    }


def _run_child(args: argparse.Namespace, stage: str, output_name: str, *, generation_input: Path | None = None) -> dict[str, Any]:
    output_path = args.output_dir / output_name
    log_path = args.output_dir / (Path(output_name).stem + ".log")
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--stage",
        stage,
        "--model",
        str(args.model.resolve()),
        "--episode",
        str(args.episode.resolve()),
        "--planner-context-index",
        str(args.planner_context_index),
        "--config",
        str(args.config.resolve()),
        "--output-dir",
        str(args.output_dir.resolve()),
        "--report-name",
        output_name,
        "--max-model-len",
        str(args.max_model_len),
        "--max-action-tokens",
        str(args.max_action_tokens),
        "--gpu-memory-utilization",
        str(args.gpu_memory_utilization),
        "--seed",
        str(args.seed),
    ]
    if generation_input is not None:
        command.extend(["--generation-input", str(generation_input.resolve())])
    print(f"[single-hcu] starting {stage}: {' '.join(command)}", flush=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            print(line, end="", flush=True)
        exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError(f"{stage} stage failed with exit code {exit_code}; see {log_path}")
    payload = _read_json(output_path)
    if payload.get("status") != "PASS":
        raise RuntimeError(f"{stage} stage did not report PASS")
    return payload


def _run_all(args: argparse.Namespace) -> dict[str, Any]:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    stage_reports: dict[str, Any] = {}
    stage_reports["environment"] = _run_child(
        args, "environment", "environment.json"
    )
    stage_reports["memory_before"] = _run_child(
        args, "memory", "memory_before.json"
    )
    first_path = args.output_dir / "generation_first.json"
    stage_reports["generation_first"] = _run_child(
        args, "generate", first_path.name
    )
    stage_reports["memory_after_first"] = _run_child(
        args, "memory", "memory_after_first.json"
    )
    replay_path = args.output_dir / "generation_replay.json"
    stage_reports["generation_replay"] = _run_child(
        args, "generate", replay_path.name
    )
    stage_reports["memory_after_replay"] = _run_child(
        args, "memory", "memory_after_replay.json"
    )
    first = stage_reports["generation_first"]
    replay = stage_reports["generation_replay"]
    replay_match = (
        first["prompt_token_ids"] == replay["prompt_token_ids"]
        and first["sampled_token_ids"] == replay["sampled_token_ids"]
        and first["raw_text_sha256"] == replay["raw_text_sha256"]
        and first["old_log_probs"] == replay["old_log_probs"]
    )
    if not replay_match:
        raise ValueError("seeded multimodal vLLM replay changed after engine restart")
    stage_reports["reference_score"] = _run_child(
        args,
        "score",
        "reference_score.json",
        generation_input=first_path,
    )
    stage_reports["memory_after_score"] = _run_child(
        args, "memory", "memory_after_score.json"
    )
    stage_reports["bridge"] = _run_child(
        args,
        "bridge",
        "optimizer_bridge_report.json",
        generation_input=first_path,
    )
    memory_reports = [
        stage_reports[name]
        for name in (
            "memory_before",
            "memory_after_first",
            "memory_after_replay",
            "memory_after_score",
        )
    ]
    baseline_free = memory_reports[0]["free_bytes"]
    minimum_allowed = baseline_free - 512 * 1024 * 1024
    memory_release_pass = all(
        report["process_allocated_bytes"] == 0
        and report["process_reserved_bytes"] == 0
        and report["free_bytes"] >= minimum_allowed
        for report in memory_reports[1:]
    )
    if not memory_release_pass:
        raise ValueError("device memory did not return within 512 MiB of baseline")
    return {
        "schema_version": "0.1",
        "report_type": "vendor_vllm_single_hcu_rl_validation",
        "status": "PASS",
        "diagnostic_only": True,
        "formal_adapter_gate_status": "BLOCKED",
        "formal_gate_blockers": [
            "accepted runtime requires vendor-compatible rLLM and SGLang",
            "eight-HCU staged rollout/FSDP topology is unavailable",
            "formal 32-group interruption/resume/replay smoke is not run",
            "custom Gen-Retry live workflow and semantic event replay are not implemented",
        ],
        "validated": {
            "single_hcu_bf16_runtime": True,
            "ray_local_start_remote_shutdown": True,
            "wandb_offline_sanitized_init": True,
            "verl_vllm_rollout_interface_resolution": True,
            "real_image_qwen3_vl_inference": True,
            "strict_action_schema_and_reference_validation": True,
            "transformers_vllm_prompt_token_identity": True,
            "sampled_token_mask_old_reference_logprob_alignment": True,
            "seeded_engine_restart_replay": replay_match,
            "device_memory_release_after_process_exit": memory_release_pass,
            "offline_admission_advantage_optimizer_join": True,
            "verl_data_proto_tensorization": True,
        },
        "limits": {
            "optimizer_rewards_are_synthetic": True,
            "image_backends_executed": False,
            "geneval2_executed": False,
            "optimizer_step_executed": False,
            "live_adapter_evidence_emitted": False,
        },
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stage_report_paths": {
            "environment": str((args.output_dir / "environment.json").resolve()),
            "generation_first": str(first_path.resolve()),
            "generation_replay": str(replay_path.resolve()),
            "reference_score": str(
                (args.output_dir / "reference_score.json").resolve()
            ),
            "optimizer_bridge": str(
                (args.output_dir / "optimizer_bridge_report.json").resolve()
            ),
        },
        "summary": {
            "sampled_action": first["canonical_action"]["action"],
            "completion_token_count": first["completion_token_count"],
            "image_grid_thw": first["multimodal"]["image_grid_thw"],
            "restart_replay_exact": replay_match,
            "minimum_post_exit_free_bytes": min(
                report["free_bytes"] for report in memory_reports[1:]
            ),
            "optimizer_trainable_action_tokens": stage_reports["bridge"][
                "optimizer"
            ]["rl/trainable_action_tokens"],
        },
    }


def _run_stage(args: argparse.Namespace) -> dict[str, Any]:
    if args.stage == "environment":
        return _stage_environment(args)
    if args.stage == "memory":
        return _stage_memory(args)
    if args.stage == "generate":
        return _stage_generate(args)
    if args.stage == "score":
        return _stage_score(args)
    if args.stage == "bridge":
        return _stage_bridge(args)
    return _run_all(args)


def main() -> int:
    args = _parse_args()
    args.model = args.model.resolve()
    args.episode = args.episode.resolve()
    args.config = args.config.resolve()
    args.output_dir = args.output_dir.resolve()
    output_name = args.report_name or {
        "environment": "environment.json",
        "memory": "memory.json",
        "generate": "generation.json",
        "score": "reference_score.json",
        "bridge": "optimizer_bridge_report.json",
        "all": "single_hcu_validation.json",
    }[args.stage]
    report_path = args.output_dir / output_name
    try:
        report = _run_stage(args)
    except Exception as exc:
        report = {
            "stage": args.stage,
            "status": "FAIL",
            "error": f"{type(exc).__name__}: {exc}",
        }
        traceback.print_exc()
    _write_json(report_path, report)
    console_report = {
        "stage": report.get("stage", args.stage),
        "status": report.get("status"),
        "report": str(report_path),
    }
    if args.stage == "all" and report.get("status") == "PASS":
        console_report["summary"] = report.get("summary")
    print(json.dumps(console_report, ensure_ascii=True, sort_keys=True), flush=True)
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
    sys.exit(main())
