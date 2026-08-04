"""Summarize and visualize LLaMA-Factory/Hugging Face SFT runs.

The parser intentionally extracts only numeric training metrics.  Trainer
state files can contain arbitrary metadata, so reports never copy that
metadata (or input paths) into generated artifacts.
"""

from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

from gen_retry.runtime.json_canonical import canonical_json


_SECRET_KEY_PARTS = (
    "secret",
    "token",
    "api_key",
    "apikey",
    "password",
    "credential",
    "authorization",
    "wandb",
)
_STRUCTURAL_KEYS = {
    "step",
    "global_step",
    "trainer_step",
    "epoch",
    "timestamp",
    "time",
    "metrics",
}
_TRAIN_METRIC_KEYS = {
    "eval_loss": "eval_loss",
    "learning_rate": "learning_rate",
    "grad_norm": "grad_norm",
}


def summarize_sft_training(
    *,
    trainer_state_path: Path,
    action_metrics_path: Path | None = None,
) -> dict[str, Any]:
    """Return a JSON-safe summary of a trainer state and optional action log.

    ``trainer_state_path`` may point at ``trainer_state.json`` or at a
    LLaMA-Factory output directory containing that file.  Missing metric
    fields are represented by empty series and ``None`` summary values.
    Malformed action-metric lines are counted and skipped.
    """

    resolved_state_path = _resolve_trainer_state_path(trainer_state_path)
    payload = _load_trainer_payload(resolved_state_path)
    raw_history = payload.get("log_history", [])
    if not isinstance(raw_history, list):
        raise ValueError("trainer_state.log_history must be a list")
    history = [entry for entry in raw_history if isinstance(entry, dict)]

    series = _training_series(history)
    latest_step = _latest_step(history, payload)
    max_steps = _positive_number(payload.get("max_steps"))
    if max_steps is None:
        max_steps = _positive_number(_last_value(history, "max_steps"))
    latest_epoch = _last_number(history, "epoch")
    if latest_epoch is None:
        latest_epoch = _finite_number(payload.get("epoch"))
    train_runtime = _last_number(history, "train_runtime")
    if train_runtime is None:
        train_runtime = _last_number(history, "runtime")
    steps_per_second = _last_number(history, "train_steps_per_second")
    if steps_per_second is None:
        steps_per_second = _last_number(history, "steps_per_second")

    step_times = _numeric_values(
        history,
        ("step_time", "step_time_seconds", "train_step_time"),
    )
    median_step_seconds = _median(step_times)
    if median_step_seconds is None and train_runtime is not None and latest_step:
        median_step_seconds = train_runtime / latest_step
    if steps_per_second is None and median_step_seconds and median_step_seconds > 0:
        steps_per_second = 1.0 / median_step_seconds
    elif (
        median_step_seconds is None
        and steps_per_second is not None
        and steps_per_second > 0
    ):
        median_step_seconds = 1.0 / steps_per_second

    progress_fraction = None
    if max_steps and latest_step is not None:
        progress_fraction = min(1.0, max(0.0, latest_step / max_steps))
    estimated_total = None
    if max_steps and median_step_seconds is not None:
        estimated_total = max_steps * median_step_seconds
    estimated_remaining = None
    if estimated_total is not None and train_runtime is not None:
        estimated_remaining = max(0.0, estimated_total - train_runtime)

    action_summary = _summarize_action_metrics(action_metrics_path)
    summary: dict[str, Any] = {
        "schema_version": "0.1",
        "analysis_id": "sft_training_run",
        "source": {
            "source_type": "trainer_state_or_log_history",
            "log_record_count": len(history),
            "action_metrics_provided": action_metrics_path is not None,
        },
        "training": {
            "latest_step": latest_step,
            "max_steps": max_steps,
            "progress_fraction": progress_fraction,
            "latest_epoch": latest_epoch,
            "train_loss": _series_stats(series["train_loss"]),
            "eval_loss": _series_stats(series["eval_loss"]),
            "learning_rate": _series_stats(series["learning_rate"]),
            "grad_norm": _series_stats(series["grad_norm"]),
        },
        "timing": {
            "train_runtime_seconds": train_runtime,
            "steps_per_second": steps_per_second,
            "median_step_seconds": median_step_seconds,
            "estimated_total_seconds": estimated_total,
            "estimated_remaining_seconds": estimated_remaining,
        },
        "series": series,
        "action_metrics": action_summary,
    }
    return _finite_json(summary)


def write_sft_training_report(
    *,
    summary: dict[str, Any],
    output_dir: Path,
    stem: str = "sft_training",
) -> dict[str, Path]:
    """Write summary JSON, Markdown, HTML, and a PNG diagnostics plot."""

    _validate_stem(stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{stem}.summary.json"
    markdown_path = output_dir / f"{stem}.report.md"
    html_path = output_dir / f"{stem}.report.html"
    plot_path = output_dir / f"{stem}.curves.png"
    artifact_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    plot_sft_training(summary=summary, output_path=plot_path)
    markdown_path.write_text(
        render_sft_training_markdown(summary=summary, image_name=plot_path.name),
        encoding="utf-8",
    )
    html_path.write_text(
        render_sft_training_html(summary=summary, image_name=plot_path.name),
        encoding="utf-8",
    )
    return {
        "summary": artifact_path,
        "markdown": markdown_path,
        "html": html_path,
        "plot": plot_path,
    }


def plot_sft_training(*, summary: dict[str, Any], output_path: Path) -> None:
    """Render loss, optimizer, gradient, and optional action curves."""

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - exercised in minimal envs
        raise RuntimeError(
            "matplotlib is required for SFT plots; install the SFT requirements"
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    series = summary.get("series", {})
    action_series = summary.get("action_metrics", {}).get("series", {})
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    loss_axis = axes[0, 0]
    train_loss = series.get("train_loss", [])
    eval_loss = series.get("eval_loss", [])
    if train_loss:
        _plot_series(loss_axis, train_loss, "Train / eval loss", "train_loss")
    if eval_loss:
        _plot_series(
            loss_axis,
            eval_loss,
            "Train / eval loss",
            "eval_loss",
            color="tab:orange",
        )
    if not train_loss and not eval_loss:
        loss_axis.set_title("Train / eval loss")
        loss_axis.text(
            0.5,
            0.5,
            "No data",
            ha="center",
            va="center",
            transform=loss_axis.transAxes,
        )
        loss_axis.set_xlabel("step")
        loss_axis.grid(alpha=0.25)
    _plot_series(
        axes[0, 1], series.get("learning_rate", []), "Learning rate", "learning_rate"
    )
    _plot_series(axes[1, 0], series.get("grad_norm", []), "Gradient norm", "grad_norm")
    action_axis = axes[1, 1]
    selected_action_keys = list(action_series)[:4]
    for index, key in enumerate(selected_action_keys):
        _plot_series(
            action_axis,
            action_series[key],
            "Action metrics" if index == 0 else "",
            key,
            color=f"C{index}",
        )
    if not selected_action_keys:
        action_axis.set_title("Action metrics (none provided)")
        action_axis.text(
            0.5,
            0.5,
            "No action metrics JSONL",
            ha="center",
            va="center",
            transform=action_axis.transAxes,
        )
    action_axis.set_xlabel("step")
    fig.suptitle("SFT training diagnostics")
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def render_sft_training_markdown(*, summary: dict[str, Any], image_name: str) -> str:
    training = summary["training"]
    timing = summary["timing"]
    lines = [
        "# SFT Training Report",
        "",
        "This report contains numeric metrics extracted from the trainer log.",
        "",
        "## Run overview",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Latest step | {_fmt(training['latest_step'])} / {_fmt(training['max_steps'])} |",
        f"| Progress | {_fmt_percent(training['progress_fraction'])} |",
        f"| Latest epoch | {_fmt(training['latest_epoch'])} |",
        f"| Train runtime | {_fmt_seconds(timing['train_runtime_seconds'])} |",
        f"| Steps / second | {_fmt(timing['steps_per_second'])} |",
        f"| Estimated remaining | {_fmt_seconds(timing['estimated_remaining_seconds'])} |",
        "",
        f"![SFT curves]({image_name})",
        "",
        "## Metric summary",
        "",
        "| Series | Count | First | Best/min | Latest |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for key in ("train_loss", "eval_loss", "learning_rate", "grad_norm"):
        stats = training[key]
        lines.append(
            f"| {key} | {_fmt(stats['count'])} | {_fmt(stats['first'])} | "
            f"{_fmt(stats['minimum'])} | {_fmt(stats['latest'])} |"
        )
    action_metrics = summary.get("action_metrics", {})
    lines.extend(["", "## Action metrics", ""])
    if not action_metrics.get("metrics"):
        lines.append("No action metrics were provided.")
    else:
        lines.extend([
            f"Parsed {action_metrics.get('record_count', 0)} records "
            f"({action_metrics.get('malformed_line_count', 0)} malformed lines skipped).",
            "",
            "| Metric | Count | Mean | Latest |",
            "| --- | ---: | ---: | ---: |",
        ])
        for key, stats in action_metrics["metrics"].items():
            lines.append(
                f"| {key} | {_fmt(stats['count'])} | {_fmt(stats['mean'])} | "
                f"{_fmt(stats['latest'])} |"
            )
    return "\n".join(lines) + "\n"


def render_sft_training_html(*, summary: dict[str, Any], image_name: str) -> str:
    """Render a self-contained, escaped HTML report referencing the PNG plot."""

    markdown = render_sft_training_markdown(summary=summary, image_name=image_name)
    # Keep HTML dependency-free.  The Markdown text is escaped as a readable
    # preformatted report, while the PNG remains directly viewable in browsers.
    escaped_markdown = html.escape(markdown)
    image = html.escape(image_name, quote=True)
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<title>SFT training report</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:1100px;"
        "margin:2rem auto;padding:0 1rem;color:#222}pre{white-space:pre-wrap}"
        "img{max-width:100%;height:auto}</style></head><body>"
        f"<img src=\"{image}\" alt=\"SFT training curves\">"
        f"<details open><summary>Text summary</summary><pre>{escaped_markdown}</pre>"
        "</details></body></html>\n"
    )


def _resolve_trainer_state_path(path: Path) -> Path:
    path = Path(path)
    if path.is_dir():
        path = path / "trainer_state.json"
    if not path.is_file():
        raise FileNotFoundError(f"trainer state not found: {path}")
    return path


def _load_trainer_payload(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid trainer state JSON: {path}") from exc
    if isinstance(value, list):
        return {"log_history": value}
    if not isinstance(value, dict):
        raise ValueError("trainer state must be an object or log_history list")
    return value


def _training_series(history: list[dict[str, Any]]) -> dict[str, list[dict[str, float]]]:
    series: dict[str, list[dict[str, float]]] = {
        "train_loss": [],
        "eval_loss": [],
        "learning_rate": [],
        "grad_norm": [],
    }
    for ordinal, entry in enumerate(history, start=1):
        step = _finite_number(entry.get("step"))
        if step is None:
            step = float(ordinal)
        train_loss = _finite_number(entry.get("train_loss"))
        if train_loss is None:
            train_loss = _finite_number(entry.get("loss"))
        if train_loss is not None:
            series["train_loss"].append({"step": step, "value": train_loss})
        for source, target in _TRAIN_METRIC_KEYS.items():
            value = _finite_number(entry.get(source))
            if value is not None:
                series[target].append({"step": step, "value": value})
    return series


def _summarize_action_metrics(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"record_count": 0, "malformed_line_count": 0, "metrics": {}, "series": {}}
    if not path.is_file():
        raise FileNotFoundError(f"action metrics JSONL not found: {path}")
    series: dict[str, list[dict[str, float]]] = {}
    malformed = 0
    record_count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(record, dict):
            malformed += 1
            continue
        record_count += 1
        step = _finite_number(
            record.get("step", record.get("global_step", record.get("trainer_step")))
        )
        if step is None:
            step = float(record_count)
        values: dict[str, Any] = {}
        nested = record.get("metrics")
        if isinstance(nested, dict):
            values.update(_flatten_numeric_metrics(nested))
        values.update(
            _flatten_numeric_metrics(
                {
                    key: value
                    for key, value in record.items()
                    if key not in _STRUCTURAL_KEYS
                }
            )
        )
        for key, raw_value in values.items():
            value = _finite_number(raw_value)
            if value is None or not _safe_metric_key(key):
                continue
            series.setdefault(key, []).append({"step": step, "value": value})
    metrics = {key: _series_stats(values) for key, values in sorted(series.items())}
    return {
        "record_count": record_count,
        "malformed_line_count": malformed,
        "metrics": metrics,
        "series": {key: values for key, values in sorted(series.items())},
    }


def _flatten_numeric_metrics(
    value: dict[str, Any], prefix: str = ""
) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, child in value.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(child, dict):
            flattened.update(_flatten_numeric_metrics(child, name))
        elif isinstance(child, (bool, int, float)) and not isinstance(child, str):
            flattened[name] = child
    return flattened


def _safe_metric_key(key: str) -> bool:
    lowered = key.lower()
    return not any(part in lowered for part in _SECRET_KEY_PARTS)


def _validate_stem(stem: str) -> None:
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", stem)
        or stem in {".", ".."}
    ):
        raise ValueError(
            "report stem must contain only letters, digits, dot, dash, or underscore"
        )


def _latest_step(
    history: list[dict[str, Any]], payload: dict[str, Any]
) -> float | int | None:
    candidate = _finite_number(payload.get("global_step"))
    history_steps = [_finite_number(entry.get("step")) for entry in history]
    history_steps = [step for step in history_steps if step is not None]
    if history_steps:
        candidate = (
            max(history_steps)
            if candidate is None
            else max(candidate, max(history_steps))
        )
    if candidate is None:
        return None
    return int(candidate) if candidate.is_integer() else candidate


def _last_value(history: list[dict[str, Any]], key: str) -> Any:
    for entry in reversed(history):
        if key in entry:
            return entry[key]
    return None


def _last_number(history: list[dict[str, Any]], key: str) -> float | None:
    return _finite_number(_last_value(history, key))


def _numeric_values(history: list[dict[str, Any]], keys: Iterable[str]) -> list[float]:
    values: list[float] = []
    for entry in history:
        for key in keys:
            value = _finite_number(entry.get(key))
            if value is not None:
                values.append(value)
                break
    return values


def _series_stats(values: list[dict[str, float]]) -> dict[str, Any]:
    numbers = [item["value"] for item in values]
    if not numbers:
        return {
            "count": 0,
            "first": None,
            "minimum": None,
            "minimum_step": None,
            "mean": None,
            "latest": None,
            "latest_step": None,
        }
    minimum = min(numbers)
    minimum_item = next(item for item in values if item["value"] == minimum)
    latest_item = values[-1]
    return {
        "count": len(numbers),
        "first": numbers[0],
        "minimum": minimum,
        "minimum_step": minimum_item["step"],
        "mean": sum(numbers) / len(numbers),
        "latest": latest_item["value"],
        "latest_step": latest_item["step"],
    }


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _positive_number(value: Any) -> float | None:
    number = _finite_number(value)
    return number if number is not None and number > 0 else None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _plot_series(
    axis: Any,
    values: list[dict[str, float]],
    title: str,
    label: str,
    *,
    color: str | None = None,
) -> None:
    if values:
        axis.plot(
            [item["step"] for item in values],
            [item["value"] for item in values],
            marker=".",
            label=label,
            color=color,
        )
        if label:
            axis.legend(loc="best")
    else:
        axis.text(0.5, 0.5, "No data", ha="center", va="center", transform=axis.transAxes)
    if title:
        axis.set_title(title)
    axis.set_xlabel("step")
    axis.grid(alpha=0.25)


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _fmt_percent(value: Any) -> str:
    return "-" if value is None else f"{float(value) * 100:.1f}%"


def _fmt_seconds(value: Any) -> str:
    return "-" if value is None else f"{float(value):.1f}s"


def _finite_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _finite_json(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_finite_json(child) for child in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value
