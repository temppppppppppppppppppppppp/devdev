from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE_ORDER = ("stage2", "stage3", "stage4")
STAGE_INT_FIELDS = (
    "attempt_count",
    "pass_like_count",
    "reject_count",
    "total_duration_ms",
    "avg_duration_ms",
    "total_tokens",
    "latest_episode",
)
STAGE_FLOAT_FIELDS = ("total_cost_usd",)
STAGE_SIGNAL_DIRECTIONS = {
    "attempt_count": "lower_is_better",
    "pass_like_count": "higher_is_better",
    "reject_count": "lower_is_better",
    "total_duration_ms": "lower_is_better",
    "total_cost_usd": "lower_is_better",
    "total_tokens": "lower_is_better",
}
RUN_META_KEYS = (
    "project_name",
    "project_locator",
    "lane",
    "target_ep",
    "status",
    "runtime_audit_tag",
    "latest_session_id",
    "git_branch",
    "git_head",
    "git_dirty",
)
STATUS_RANK = {
    "operational_failure": 0,
    "interrupted": 1,
    "snapshot": 2,
    "completed": 3,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two archived benchmark records read-only.")
    parser.add_argument("left", help="baseline benchmark record path or run_id")
    parser.add_argument("right", help="comparison benchmark record path or run_id")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument(
        "--benchmark-root",
        default="benchmarks",
        help="benchmark archive root. Relative paths resolve from the workspace root.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(ROOT),
        help="workspace root containing the benchmark archive.",
    )
    return parser.parse_args(argv)


def compare_benchmark_records(
    left_identifier: str,
    right_identifier: str,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    left = load_benchmark_record(left_identifier, workspace_root=workspace, benchmark_root=benchmark_dir)
    right = load_benchmark_record(right_identifier, workspace_root=workspace, benchmark_root=benchmark_dir)
    return build_benchmark_record_diff(left, right)


def load_benchmark_record(
    identifier: str | Path,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    record_root, index_row = _resolve_record_root(str(identifier), workspace_root=workspace, benchmark_root=benchmark_dir)
    manifest = _load_json(record_root / "manifest.json")
    stage_metrics = _load_stage_metrics(record_root, manifest=manifest)

    runtime_summary = manifest.get("runtime_summary", {}) if isinstance(manifest, dict) else {}
    workspace_git = manifest.get("workspace_git", {}) if isinstance(manifest, dict) else {}
    run_id = _pick_first_nonempty(
        manifest.get("run_id") if isinstance(manifest, dict) else None,
        index_row.get("run_id"),
        record_root.name,
    )
    return {
        "identifier": str(identifier),
        "record_root": _display_relative_path(workspace, record_root),
        "run_id": run_id,
        "recorded_at": _pick_first_nonempty(
            manifest.get("recorded_at") if isinstance(manifest, dict) else None,
            index_row.get("recorded_at"),
        ),
        "project_name": _pick_first_nonempty(
            manifest.get("project_name") if isinstance(manifest, dict) else None,
            index_row.get("project_name"),
            record_root.parent.name,
        ),
        "project_locator": _pick_first_nonempty(
            manifest.get("project_locator") if isinstance(manifest, dict) else None,
            index_row.get("project_locator"),
        ),
        "lane": _pick_first_nonempty(
            manifest.get("lane") if isinstance(manifest, dict) else None,
            index_row.get("lane"),
        ),
        "target_ep": _coerce_optional_int(
            _pick_first_nonempty(
                manifest.get("target_ep") if isinstance(manifest, dict) else None,
                index_row.get("target_ep"),
            )
        ),
        "status": _pick_first_nonempty(
            manifest.get("status") if isinstance(manifest, dict) else None,
            index_row.get("status"),
        ),
        "runtime_audit_tag": _pick_first_nonempty(
            runtime_summary.get("runtime_audit_tag") if isinstance(runtime_summary, dict) else None,
            index_row.get("runtime_audit_tag"),
        ),
        "latest_session_id": _pick_first_nonempty(
            runtime_summary.get("latest_session_id") if isinstance(runtime_summary, dict) else None,
            index_row.get("latest_session_id"),
        ),
        "git_branch": _pick_first_nonempty(
            workspace_git.get("branch") if isinstance(workspace_git, dict) else None,
            index_row.get("git_branch"),
        ),
        "git_head": _pick_first_nonempty(
            workspace_git.get("head") if isinstance(workspace_git, dict) else None,
            index_row.get("git_head"),
        ),
        "git_dirty": _coerce_bool(
            _pick_first_nonempty(
                workspace_git.get("dirty") if isinstance(workspace_git, dict) else None,
                index_row.get("git_dirty"),
            )
        ),
        "notes": _pick_first_nonempty(
            manifest.get("notes") if isinstance(manifest, dict) else None,
            index_row.get("notes"),
        ),
        "stage_metrics": stage_metrics,
    }


def build_benchmark_record_diff(left_record: dict[str, Any], right_record: dict[str, Any]) -> dict[str, Any]:
    run_meta_delta: dict[str, dict[str, Any]] = {}
    for key in RUN_META_KEYS:
        if left_record.get(key) != right_record.get(key):
            run_meta_delta[key] = {
                "before": left_record.get(key),
                "after": right_record.get(key),
            }

    stage_metrics_delta: dict[str, dict[str, Any]] = {}
    improvement_signals: list[str] = []
    regression_signals: list[str] = []
    comparable_stages: list[str] = []

    for stage in STAGE_ORDER:
        left_stage = _normalize_stage_metric_row(stage, left_record.get("stage_metrics", {}).get(stage))
        right_stage = _normalize_stage_metric_row(stage, right_record.get("stage_metrics", {}).get(stage))
        if _stage_has_signal(left_stage) or _stage_has_signal(right_stage):
            comparable_stages.append(stage)
        stage_delta: dict[str, Any] = {}
        for field in STAGE_INT_FIELDS:
            delta = int(right_stage[field]) - int(left_stage[field])
            if delta:
                stage_delta[field] = delta
                _classify_metric_signal(
                    stage=stage,
                    field=field,
                    delta=delta,
                    improvements=improvement_signals,
                    regressions=regression_signals,
                )
        for field in STAGE_FLOAT_FIELDS:
            delta = round(float(right_stage[field]) - float(left_stage[field]), 6)
            if abs(delta) >= 1e-9:
                stage_delta[field] = delta
                _classify_metric_signal(
                    stage=stage,
                    field=field,
                    delta=delta,
                    improvements=improvement_signals,
                    regressions=regression_signals,
                )
        if stage_delta:
            stage_metrics_delta[stage] = stage_delta

    if left_record.get("status") != right_record.get("status"):
        status_signal = _classify_status_signal(left_record.get("status"), right_record.get("status"))
        if status_signal == "improvement":
            improvement_signals.append("run_meta.status")
        elif status_signal == "regression":
            regression_signals.append("run_meta.status")

    verdict = _build_verdict(
        comparable_stages=comparable_stages,
        improvements=improvement_signals,
        regressions=regression_signals,
    )
    changed_sections = [
        section
        for section, changed in (
            ("run_meta", bool(run_meta_delta)),
            ("stage_metrics", bool(stage_metrics_delta)),
        )
        if changed
    ]
    return {
        "left": left_record,
        "right": right_record,
        "delta": {
            "run_meta": run_meta_delta,
            "stage_metrics": stage_metrics_delta,
            "comparable_stages": comparable_stages,
            "improvement_signals": improvement_signals,
            "regression_signals": regression_signals,
            "verdict": verdict,
            "changed_sections": changed_sections,
        },
    }


def _resolve_record_root(
    identifier: str,
    *,
    workspace_root: Path,
    benchmark_root: Path,
) -> tuple[Path, dict[str, str]]:
    direct_path = _resolve_existing_path(identifier, workspace_root=workspace_root)
    if direct_path is not None:
        return _coerce_record_root(direct_path), {}

    index_row = _find_index_row(benchmark_root / "benchmark_index.csv", run_id=identifier)
    if index_row:
        record_path = Path(index_row.get("record_path", ""))
        if record_path and not record_path.is_absolute():
            record_path = (workspace_root / record_path).resolve()
        if record_path:
            return _coerce_record_root(record_path), index_row

    glob_matches = list(benchmark_root.glob(f"*/{identifier}/manifest.json"))
    if len(glob_matches) == 1:
        return glob_matches[0].parent.resolve(), {}
    if len(glob_matches) > 1:
        raise ValueError(f"run_id is ambiguous under benchmark root: {identifier}")

    raise FileNotFoundError(f"benchmark record not found: {identifier}")


def _resolve_existing_path(value: str, *, workspace_root: Path) -> Path | None:
    candidate = Path(value)
    if candidate.exists():
        return candidate.resolve()
    workspace_candidate = (workspace_root / candidate).resolve()
    if workspace_candidate.exists():
        return workspace_candidate
    return None


def _coerce_record_root(path: Path) -> Path:
    candidate = path.resolve()
    if candidate.is_file():
        if candidate.name != "manifest.json":
            raise ValueError(f"benchmark record file must be manifest.json: {candidate}")
        candidate = candidate.parent
    manifest_path = candidate / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"benchmark record is missing manifest.json: {candidate}")
    return candidate


def _find_index_row(index_path: Path, *, run_id: str) -> dict[str, str]:
    if not index_path.exists():
        return {}
    with index_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("run_id", "")).strip() == run_id:
                return row
    return {}


def _load_stage_metrics(record_root: Path, *, manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stage_metrics_path = record_root / "stage_metrics.csv"
    metrics = {stage: _normalize_stage_metric_row(stage, None) for stage in STAGE_ORDER}
    if stage_metrics_path.exists():
        with stage_metrics_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                stage = str(row.get("stage", "")).strip()
                if stage:
                    metrics[stage] = _normalize_stage_metric_row(stage, row)
        return metrics

    manifest_metrics = manifest.get("stage_metrics", {}) if isinstance(manifest, dict) else {}
    if isinstance(manifest_metrics, dict):
        for stage, row in manifest_metrics.items():
            metrics[str(stage)] = _normalize_stage_metric_row(str(stage), row)
    return metrics


def _normalize_stage_metric_row(stage: str, row: object) -> dict[str, Any]:
    payload = row if isinstance(row, dict) else {}
    normalized = {
        "stage": stage,
        "source_file": str(payload.get("source_file", "") or ""),
    }
    for field in STAGE_INT_FIELDS:
        normalized[field] = _coerce_int(payload.get(field))
    for field in STAGE_FLOAT_FIELDS:
        normalized[field] = round(_coerce_float(payload.get(field)), 6)
    return normalized


def _classify_metric_signal(
    *,
    stage: str,
    field: str,
    delta: int | float,
    improvements: list[str],
    regressions: list[str],
) -> None:
    direction = STAGE_SIGNAL_DIRECTIONS.get(field)
    if direction == "higher_is_better":
        if delta > 0:
            improvements.append(f"{stage}.{field}")
        elif delta < 0:
            regressions.append(f"{stage}.{field}")
    elif direction == "lower_is_better":
        if delta < 0:
            improvements.append(f"{stage}.{field}")
        elif delta > 0:
            regressions.append(f"{stage}.{field}")


def _classify_status_signal(before: object, after: object) -> str:
    before_rank = STATUS_RANK.get(str(before or "").strip().lower())
    after_rank = STATUS_RANK.get(str(after or "").strip().lower())
    if before_rank is None or after_rank is None or before_rank == after_rank:
        return "neutral"
    return "improvement" if after_rank > before_rank else "regression"


def _build_verdict(
    *,
    comparable_stages: list[str],
    improvements: list[str],
    regressions: list[str],
) -> str:
    if not comparable_stages:
        return "incomparable"
    if improvements and regressions:
        return "mixed"
    if improvements:
        return "better"
    if regressions:
        return "worse"
    return "unchanged"


def _stage_has_signal(stage: dict[str, Any]) -> bool:
    for field in STAGE_INT_FIELDS:
        if int(stage.get(field, 0)):
            return True
    for field in STAGE_FLOAT_FIELDS:
        if abs(float(stage.get(field, 0.0))) >= 1e-9:
            return True
    return False


def _resolve_benchmark_root(workspace_root: Path, benchmark_root: str | Path) -> Path:
    candidate = Path(benchmark_root)
    if candidate.is_absolute():
        return candidate.resolve()
    return (workspace_root / candidate).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _display_relative_path(workspace_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _pick_first_nonempty(*values: object) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return ""


def _coerce_int(value: object) -> int:
    if value in (None, ""):
        return 0
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def _coerce_optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _coerce_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y"}


def _render_text(diff: dict[str, Any], *, left_label: str, right_label: str) -> str:
    delta = diff["delta"]
    lines = [
        f"Benchmark Record Diff: {left_label} -> {right_label}",
        f"Verdict: {delta['verdict']}",
        f"Changed sections: {', '.join(delta['changed_sections']) if delta['changed_sections'] else 'none'}",
    ]
    if delta["run_meta"]:
        run_meta_bits = [
            f"{key}={change['before']} -> {change['after']}"
            for key, change in delta["run_meta"].items()
        ]
        lines.append("Run meta: " + "; ".join(run_meta_bits))
    for stage in STAGE_ORDER:
        stage_delta = delta["stage_metrics"].get(stage)
        if not stage_delta:
            continue
        field_bits = [f"{field}_delta={value}" for field, value in stage_delta.items()]
        lines.append(f"{stage}: " + "; ".join(field_bits))
    lines.append(f"Improvement signals: {delta['improvement_signals']}")
    lines.append(f"Regression signals: {delta['regression_signals']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    diff = compare_benchmark_records(
        args.left,
        args.right,
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
    )
    if args.format == "json":
        print(json.dumps(diff, ensure_ascii=False, indent=2))
    else:
        print(_render_text(diff, left_label=str(args.left), right_label=str(args.right)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
