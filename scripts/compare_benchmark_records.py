from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPANION_LINKS_FILENAME = "benchmark_companion_links.json"
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


def _watchpoint(
    watchpoint_id: str,
    *,
    severity: str,
    scope: str,
    message: str,
    side: str = "",
) -> dict[str, str]:
    payload = {
        "id": watchpoint_id,
        "severity": severity,
        "scope": scope,
        "message": message,
    }
    if side:
        payload["side"] = side
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two archived benchmark records read-only.")
    parser.add_argument("left", help="baseline benchmark record path or run_id")
    parser.add_argument("right", help="comparison benchmark record path or run_id")
    parser.add_argument(
        "--left-evidence-json",
        default="",
        help="optional structured post-run evidence JSON companion for the baseline side",
    )
    parser.add_argument(
        "--right-evidence-json",
        default="",
        help="optional structured post-run evidence JSON companion for the comparison side",
    )
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
    left_evidence_json: str | Path | None = None,
    right_evidence_json: str | Path | None = None,
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    left = load_benchmark_record(
        left_identifier,
        workspace_root=workspace,
        benchmark_root=benchmark_dir,
        companion_evidence_json=left_evidence_json,
    )
    right = load_benchmark_record(
        right_identifier,
        workspace_root=workspace,
        benchmark_root=benchmark_dir,
        companion_evidence_json=right_evidence_json,
    )
    return build_benchmark_record_diff(left, right)


def load_benchmark_record(
    identifier: str | Path,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
    companion_evidence_json: str | Path | None = None,
) -> dict[str, Any]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    record_root, index_row = _resolve_record_root(str(identifier), workspace_root=workspace, benchmark_root=benchmark_dir)
    manifest = _load_json(record_root / "manifest.json")
    stage_metrics = _load_stage_metrics(record_root, manifest=manifest)
    runtime_audit_summary = _load_runtime_audit_summary(record_root)
    companion_links = _load_companion_links(record_root, workspace_root=workspace)
    effective_evidence_path = companion_evidence_json
    if effective_evidence_path in (None, ""):
        linked_evidence_path = str(companion_links.get("post_run_evidence_json_resolved", "") or "")
        if linked_evidence_path:
            effective_evidence_path = linked_evidence_path
    companion_evidence = _load_companion_evidence(effective_evidence_path, workspace_root=workspace)

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
        "runtime_audit_summary": runtime_audit_summary,
        "companion_links": companion_links,
        "companion_evidence": companion_evidence,
        "guarded_runner_summary": _load_stage4_guarded_result(record_root),
        "note_markers": _extract_note_markers(
            _pick_first_nonempty(
                manifest.get("notes") if isinstance(manifest, dict) else None,
                index_row.get("notes"),
            )
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
    remediation_hints = _collect_delta_remediation_hints(left_record=left_record, right_record=right_record)
    watchpoints = _build_watchpoints(
        left_record=left_record,
        right_record=right_record,
        stage_metrics_delta=stage_metrics_delta,
    )
    changed_sections = [
        section
        for section, changed in (
            ("run_meta", bool(run_meta_delta)),
            ("stage_metrics", bool(stage_metrics_delta)),
            ("remediation_hints", bool(remediation_hints)),
            ("watchpoints", bool(watchpoints)),
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
            "remediation_hints": remediation_hints,
            "watchpoints": watchpoints,
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
    stale_index_path = ""
    if index_row:
        record_path = Path(index_row.get("record_path", ""))
        if record_path and not record_path.is_absolute():
            record_path = (workspace_root / record_path).resolve()
        if record_path:
            try:
                return _coerce_record_root(record_path), index_row
            except FileNotFoundError:
                stale_index_path = str(record_path)

    glob_matches = list(benchmark_root.glob(f"*/{identifier}/manifest.json"))
    if len(glob_matches) == 1:
        return glob_matches[0].parent.resolve(), index_row
    if len(glob_matches) > 1:
        raise ValueError(f"run_id is ambiguous under benchmark root: {identifier}")
    if stale_index_path:
        raise FileNotFoundError(
            f"stale benchmark_index.csv record_path for run_id {identifier}: "
            f"missing manifest.json under {stale_index_path}"
        )

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


def _load_runtime_audit_summary(record_root: Path) -> dict[str, Any]:
    summary_path = record_root / "logs" / "runtime_audit_summary.json"
    if not summary_path.exists():
        return {
            "available": False,
            "summary_role": "",
            "latest_event_type": "",
            "proof_digest_status": "",
            "operational_status": "",
            "operational_latest_session_id": "",
            "stage4_live_session_status": "",
            "stage4_retry_exercised": False,
            "stage4_patch_exercised": False,
            "stage4_target_ep_reached": False,
            "stage4_complete_emitted": False,
            "stage4_post_pass_contract_signal_count": 0,
        }
    payload = _load_json(summary_path)
    proof_digest = payload.get("proof_digest", {}) if isinstance(payload, dict) else {}
    operational_metadata = proof_digest.get("operational_metadata", {}) if isinstance(proof_digest, dict) else {}
    stage4_live_session = operational_metadata.get("stage4_live_session", {}) if isinstance(operational_metadata, dict) else {}
    return {
        "available": True,
        "summary_role": str(payload.get("summary_role", "") or ""),
        "latest_event_type": str(payload.get("latest_event_type", "") or ""),
        "proof_digest_status": str(proof_digest.get("status", "") or "") if isinstance(proof_digest, dict) else "",
        "operational_status": (
            str(operational_metadata.get("status", "") or "") if isinstance(operational_metadata, dict) else ""
        ),
        "operational_latest_session_id": (
            str(operational_metadata.get("latest_session_id", "") or "")
            if isinstance(operational_metadata, dict)
            else ""
        ),
        "stage4_live_session_status": (
            str(stage4_live_session.get("status", "") or "") if isinstance(stage4_live_session, dict) else ""
        ),
        "stage4_retry_exercised": (
            _coerce_bool(stage4_live_session.get("retry_exercised")) if isinstance(stage4_live_session, dict) else False
        ),
        "stage4_patch_exercised": (
            _coerce_bool(stage4_live_session.get("patch_exercised")) if isinstance(stage4_live_session, dict) else False
        ),
        "stage4_target_ep_reached": (
            _coerce_bool(stage4_live_session.get("target_ep_reached")) if isinstance(stage4_live_session, dict) else False
        ),
        "stage4_complete_emitted": (
            _coerce_bool(stage4_live_session.get("stage4_complete_emitted"))
            if isinstance(stage4_live_session, dict)
            else False
        ),
        "stage4_post_pass_contract_signal_count": (
            _coerce_int(stage4_live_session.get("post_pass_contract_signal_count"))
            if isinstance(stage4_live_session, dict)
            else 0
        ),
    }


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


def _load_stage4_guarded_result(record_root: Path) -> dict[str, Any]:
    summary_path = record_root / "logs" / "stage4_direct_supervised_guarded_result.json"
    if not summary_path.exists():
        return {
            "available": False,
            "benchmark_archive_run_id": "",
            "target_ep": None,
            "latest_written_ep_before": None,
            "latest_written_ep_after": None,
            "terminated_by_monitor": False,
            "termination_reason": "",
            "child_exit_code": None,
        }
    payload = _load_json(summary_path)
    benchmark_archive = payload.get("benchmark_archive", {}) if isinstance(payload, dict) else {}
    return {
        "available": True,
        "benchmark_archive_run_id": (
            str(benchmark_archive.get("run_id", "") or "") if isinstance(benchmark_archive, dict) else ""
        ),
        "target_ep": _coerce_optional_int(payload.get("target_ep")) if isinstance(payload, dict) else None,
        "latest_written_ep_before": (
            _coerce_optional_int(payload.get("latest_written_ep_before")) if isinstance(payload, dict) else None
        ),
        "latest_written_ep_after": (
            _coerce_optional_int(payload.get("latest_written_ep_after")) if isinstance(payload, dict) else None
        ),
        "terminated_by_monitor": (
            _coerce_bool(payload.get("terminated_by_monitor")) if isinstance(payload, dict) else False
        ),
        "termination_reason": str(payload.get("termination_reason", "") or "") if isinstance(payload, dict) else "",
        "child_exit_code": _coerce_optional_int(payload.get("child_exit_code")) if isinstance(payload, dict) else None,
    }


def _load_companion_links(record_root: Path, *, workspace_root: Path) -> dict[str, Any]:
    links_path = record_root / COMPANION_LINKS_FILENAME
    if not links_path.exists():
        return {
            "available": False,
            "source_path": "",
            "schema_version": "",
            "post_run_evidence_json": "",
            "post_run_evidence_json_resolved": "",
            "post_run_evidence_json_missing": False,
            "post_run_merge_audit_md": "",
            "post_run_merge_audit_md_resolved": "",
            "post_run_merge_audit_md_missing": False,
            "supporting_context_md": "",
            "supporting_context_md_resolved": "",
            "supporting_context_md_missing": False,
        }
    payload = _load_json(links_path)
    evidence_raw = str(payload.get("post_run_evidence_json", "") or "") if isinstance(payload, dict) else ""
    merge_audit_raw = str(payload.get("post_run_merge_audit_md", "") or "") if isinstance(payload, dict) else ""
    supporting_context_raw = str(payload.get("supporting_context_md", "") or "") if isinstance(payload, dict) else ""
    evidence_path = _resolve_existing_path(evidence_raw, workspace_root=workspace_root) if evidence_raw else None
    merge_audit_path = _resolve_existing_path(merge_audit_raw, workspace_root=workspace_root) if merge_audit_raw else None
    supporting_context_path = (
        _resolve_existing_path(supporting_context_raw, workspace_root=workspace_root) if supporting_context_raw else None
    )
    return {
        "available": True,
        "source_path": _display_relative_path(workspace_root, links_path),
        "schema_version": str(payload.get("schema_version", "") or "") if isinstance(payload, dict) else "",
        "post_run_evidence_json": evidence_raw,
        "post_run_evidence_json_resolved": (
            _display_relative_path(workspace_root, evidence_path) if evidence_path is not None else ""
        ),
        "post_run_evidence_json_missing": bool(evidence_raw and evidence_path is None),
        "post_run_merge_audit_md": merge_audit_raw,
        "post_run_merge_audit_md_resolved": (
            _display_relative_path(workspace_root, merge_audit_path) if merge_audit_path is not None else ""
        ),
        "post_run_merge_audit_md_missing": bool(merge_audit_raw and merge_audit_path is None),
        "supporting_context_md": supporting_context_raw,
        "supporting_context_md_resolved": (
            _display_relative_path(workspace_root, supporting_context_path)
            if supporting_context_path is not None
            else ""
        ),
        "supporting_context_md_missing": bool(supporting_context_raw and supporting_context_path is None),
    }


def _load_companion_evidence(
    evidence_json: str | Path | None,
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    if evidence_json in (None, ""):
        return {
            "available": False,
            "source_path": "",
            "hard_gates_status": "",
            "sink_alignment_status": "",
            "final_authority_status": "",
            "gate_repair_status": "",
        }
    candidate = _resolve_existing_path(str(evidence_json), workspace_root=workspace_root)
    if candidate is None:
        raise FileNotFoundError(f"companion evidence JSON not found: {evidence_json}")
    payload = _load_json(candidate)
    hard_gates = payload.get("hard_gates", {}) if isinstance(payload, dict) else {}
    sink_alignment = payload.get("current_session_sink_alignment_summary", {}) if isinstance(payload, dict) else {}
    final_authority = payload.get("final_authority_contract_summary", {}) if isinstance(payload, dict) else {}
    gate_repair = payload.get("gate_repair_surface_summary", {}) if isinstance(payload, dict) else {}
    return {
        "available": True,
        "source_path": _display_relative_path(workspace_root, candidate),
        "hard_gates_status": str(hard_gates.get("status", "") or "") if isinstance(hard_gates, dict) else "",
        "sink_alignment_status": (
            str(sink_alignment.get("status", "") or "") if isinstance(sink_alignment, dict) else ""
        ),
        "final_authority_status": (
            str(final_authority.get("status", "") or "") if isinstance(final_authority, dict) else ""
        ),
        "gate_repair_status": (
            str(gate_repair.get("status", "") or "") if isinstance(gate_repair, dict) else ""
        ),
    }


def _classify_missing_companion_surfaces(companion_links: object) -> list[str]:
    if not isinstance(companion_links, dict):
        return []
    missing_surfaces: list[str] = []
    for field in ("post_run_evidence_json", "post_run_merge_audit_md", "supporting_context_md"):
        if bool(companion_links.get(f"{field}_missing")):
            missing_surfaces.append(field)
    return missing_surfaces


def _build_companion_link_remediation_hints(
    *,
    side: str,
    run_id: str,
    record_root: str,
    companion_links: object,
    missing_surfaces: list[str],
) -> list[dict[str, str]]:
    if not isinstance(companion_links, dict):
        return []
    hints: list[dict[str, str]] = []
    flag_by_surface = {
        "post_run_evidence_json": "--post-run-evidence-json",
        "post_run_merge_audit_md": "--post-run-merge-audit-md",
        "supporting_context_md": "--supporting-context-md",
    }
    placeholder_by_surface = {
        "post_run_evidence_json": "<valid-json-path>",
        "post_run_merge_audit_md": "<valid-markdown-path>",
        "supporting_context_md": "<valid-markdown-path>",
    }
    for surface in missing_surfaces:
        flag = flag_by_surface.get(surface, "")
        if not flag:
            continue
        raw_value = str(companion_links.get(surface, "") or "")
        replacement = raw_value or placeholder_by_surface.get(surface, "<valid-path>")
        hints.append(
            {
                "side": side,
                "run_id": run_id,
                "record_root": record_root,
                "surface": surface,
                "current_value": raw_value,
                "suggested_flag": flag,
                "suggested_command": (
                    f"python scripts/link_benchmark_companions.py {run_id} "
                    f"{flag} {replacement}"
                ),
            }
        )
    return hints


def _collect_delta_remediation_hints(
    *,
    left_record: dict[str, Any],
    right_record: dict[str, Any],
) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    for side, record in (("left", left_record), ("right", right_record)):
        companion_links = record.get("companion_links", {})
        missing_surfaces = _classify_missing_companion_surfaces(companion_links)
        hints.extend(
            _build_companion_link_remediation_hints(
                side=side,
                run_id=str(record.get("run_id", "") or ""),
                record_root=str(record.get("record_root", "") or ""),
                companion_links=companion_links,
                missing_surfaces=missing_surfaces,
            )
        )
    return hints


def _extract_note_markers(notes: object) -> dict[str, Any]:
    text = str(notes or "").strip()
    markers = {
        "terminated_by_monitor": False,
        "termination_reason": "",
        "target_ep": None,
        "max_attempts": None,
        "before_latest_ep": None,
        "after_latest_ep": None,
        "runtime_audit_tag": "",
        "child_exit_code": None,
        "terminated_ep": None,
        "terminated_attempt_num": None,
    }
    if not text:
        return markers
    kv_map: dict[str, str] = {}
    for segment in text.split(";"):
        chunk = segment.strip()
        if not chunk or "=" not in chunk:
            continue
        key, raw_value = chunk.split("=", 1)
        kv_map[key.strip().lower()] = raw_value.strip()
    lowered = text.lower()
    markers["terminated_by_monitor"] = _coerce_bool(kv_map.get("terminated_by_monitor")) or (
        "terminated_by_monitor=true" in lowered
    )
    markers["termination_reason"] = kv_map.get("termination_reason", "")
    markers["target_ep"] = _coerce_optional_int(kv_map.get("target_ep"))
    markers["max_attempts"] = _coerce_optional_int(kv_map.get("max_attempts"))
    markers["before_latest_ep"] = _coerce_optional_int(kv_map.get("before_latest_ep"))
    markers["after_latest_ep"] = _coerce_optional_int(kv_map.get("after_latest_ep"))
    markers["runtime_audit_tag"] = kv_map.get("runtime_audit_tag", "")
    markers["child_exit_code"] = _coerce_optional_int(kv_map.get("child_exit_code"))
    markers["terminated_ep"] = _coerce_optional_int(kv_map.get("terminated_ep"))
    markers["terminated_attempt_num"] = _coerce_optional_int(kv_map.get("terminated_attempt_num"))
    return markers


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


def _build_watchpoints(
    *,
    left_record: dict[str, Any],
    right_record: dict[str, Any],
    stage_metrics_delta: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    watchpoints: list[dict[str, str]] = []

    status_signal = _classify_status_signal(left_record.get("status"), right_record.get("status"))
    if status_signal == "improvement":
        watchpoints.append(
            _watchpoint(
                "status_upgraded",
                severity="info",
                scope="run",
                message=f"status improved from {left_record.get('status')} to {right_record.get('status')}",
            )
        )
    elif status_signal == "regression":
        watchpoints.append(
            _watchpoint(
                "status_regressed",
                severity="warn",
                scope="run",
                message=f"status regressed from {left_record.get('status')} to {right_record.get('status')}",
            )
        )

    if left_record.get("runtime_audit_tag") != right_record.get("runtime_audit_tag"):
        watchpoints.append(
            _watchpoint(
                "runtime_audit_tag_changed",
                severity="info",
                scope="run",
                message=(
                    "runtime_audit_tag changed from "
                    f"{left_record.get('runtime_audit_tag')} to {right_record.get('runtime_audit_tag')}"
                ),
            )
        )

    for side, record in (("left", left_record), ("right", right_record)):
        runtime_audit_summary = record.get("runtime_audit_summary", {})
        if isinstance(runtime_audit_summary, dict):
            proof_digest_status = str(runtime_audit_summary.get("proof_digest_status", "") or "")
            if proof_digest_status and proof_digest_status != "ok":
                watchpoints.append(
                    _watchpoint(
                        "proof_digest_attention",
                        severity="warn",
                        scope="runtime_audit_summary",
                        side=side,
                        message=f"{side} proof_digest.status is {proof_digest_status}",
                    )
                )
            operational_status = str(runtime_audit_summary.get("operational_status", "") or "")
            if operational_status and operational_status != "ok":
                watchpoints.append(
                    _watchpoint(
                        "runtime_operational_status_attention",
                        severity="warn",
                        scope="runtime_audit_summary",
                        side=side,
                        message=f"{side} operational_metadata.status is {operational_status}",
                    )
                )
            stage4_live_session_status = str(runtime_audit_summary.get("stage4_live_session_status", "") or "")
            if stage4_live_session_status and stage4_live_session_status != "ok":
                watchpoints.append(
                    _watchpoint(
                        "stage4_live_session_attention",
                        severity="warn",
                        scope="stage4",
                        side=side,
                        message=f"{side} stage4_live_session.status is {stage4_live_session_status}",
                    )
                )
            operational_latest_session_id = str(runtime_audit_summary.get("operational_latest_session_id", "") or "")
            record_latest_session_id = str(record.get("latest_session_id", "") or "")
            if (
                operational_latest_session_id
                and record_latest_session_id
                and operational_latest_session_id != record_latest_session_id
            ):
                watchpoints.append(
                    _watchpoint(
                        "runtime_latest_session_id_mismatch",
                        severity="warn",
                        scope="runtime_audit_summary",
                        side=side,
                        message=(
                            f"{side} operational latest_session_id {operational_latest_session_id} "
                            f"does not match record latest_session_id {record_latest_session_id}"
                        ),
                    )
                )
            if bool(runtime_audit_summary.get("stage4_retry_exercised")):
                watchpoints.append(
                    _watchpoint(
                        "stage4_retry_exercised",
                        severity="info",
                        scope="stage4",
                        side=side,
                        message=f"{side} stage4_live_session exercised retry",
                    )
                )
            if bool(runtime_audit_summary.get("stage4_patch_exercised")):
                watchpoints.append(
                    _watchpoint(
                        "stage4_patch_exercised",
                        severity="info",
                        scope="stage4",
                        side=side,
                        message=f"{side} stage4_live_session exercised patch",
                    )
                )
            if stage4_live_session_status == "ok" and not bool(runtime_audit_summary.get("stage4_target_ep_reached")):
                watchpoints.append(
                    _watchpoint(
                        "stage4_target_ep_not_reached",
                        severity="warn",
                        scope="stage4",
                        side=side,
                        message=f"{side} stage4 live session did not emit target_ep_reached",
                    )
                )
            if stage4_live_session_status == "ok" and not bool(runtime_audit_summary.get("stage4_complete_emitted")):
                watchpoints.append(
                    _watchpoint(
                        "stage4_complete_signal_missing",
                        severity="warn",
                        scope="stage4",
                        side=side,
                        message=f"{side} stage4 live session did not emit stage4_complete",
                    )
                )
            contract_signal_count = _coerce_int(runtime_audit_summary.get("stage4_post_pass_contract_signal_count"))
            if contract_signal_count > 0:
                watchpoints.append(
                    _watchpoint(
                        "stage4_post_pass_contract_signals_recorded",
                        severity="info",
                        scope="stage4",
                        side=side,
                        message=f"{side} stage4 post_pass_contract_signal_count is {contract_signal_count}",
                    )
                )
        companion_evidence = record.get("companion_evidence", {})
        companion_links = record.get("companion_links", {})
        if isinstance(companion_links, dict) and companion_links.get("available"):
            missing_surfaces = _classify_missing_companion_surfaces(companion_links)
            remediation_hints = _build_companion_link_remediation_hints(
                side=side,
                run_id=str(record.get("run_id", "") or ""),
                record_root=str(record.get("record_root", "") or ""),
                companion_links=companion_links,
                missing_surfaces=missing_surfaces,
            )
            if missing_surfaces:
                watchpoints.append(
                    _watchpoint(
                        "benchmark_companion_missing_target",
                        severity="warn",
                        scope="benchmark_companion_links",
                        side=side,
                        message=(
                            f"{side} benchmark companion state is missing_target "
                            f"for {','.join(missing_surfaces)}"
                        ),
                    )
                )
                for hint in remediation_hints:
                    watchpoints.append(
                        _watchpoint(
                            "benchmark_companion_remediation_hint",
                            severity="info",
                            scope="benchmark_companion_links",
                            side=side,
                            message=(
                                f"{side} remediation {hint.get('surface')}: "
                                f"{hint.get('suggested_command')}"
                            ),
                        )
                    )
            if bool(companion_links.get("post_run_evidence_json_missing")):
                watchpoints.append(
                    _watchpoint(
                        "post_run_evidence_link_missing",
                        severity="warn",
                        scope="benchmark_companion_links",
                        side=side,
                        message=(
                            f"{side} companion links reference missing post_run_evidence_json "
                            f"{companion_links.get('post_run_evidence_json')}"
                        ),
                    )
                )
            if bool(companion_links.get("post_run_merge_audit_md_missing")):
                watchpoints.append(
                    _watchpoint(
                        "post_run_merge_audit_link_missing",
                        severity="warn",
                        scope="benchmark_companion_links",
                        side=side,
                        message=(
                            f"{side} companion links reference missing post_run_merge_audit_md "
                            f"{companion_links.get('post_run_merge_audit_md')}"
                        ),
                    )
                )
            elif str(companion_links.get("post_run_merge_audit_md_resolved", "") or ""):
                watchpoints.append(
                    _watchpoint(
                        "post_run_merge_audit_linked",
                        severity="info",
                        scope="benchmark_companion_links",
                        side=side,
                        message=(
                            f"{side} companion links include post_run_merge_audit_md "
                            f"{companion_links.get('post_run_merge_audit_md_resolved')}"
                        ),
                    )
                )
            if bool(companion_links.get("supporting_context_md_missing")):
                watchpoints.append(
                    _watchpoint(
                        "supporting_context_link_missing",
                        severity="warn",
                        scope="benchmark_companion_links",
                        side=side,
                        message=(
                            f"{side} companion links reference missing supporting_context_md "
                            f"{companion_links.get('supporting_context_md')}"
                        ),
                    )
                )
            elif str(companion_links.get("supporting_context_md_resolved", "") or ""):
                watchpoints.append(
                    _watchpoint(
                        "supporting_context_linked",
                        severity="info",
                        scope="benchmark_companion_links",
                        side=side,
                        message=(
                            f"{side} companion links include supporting_context_md "
                            f"{companion_links.get('supporting_context_md_resolved')}"
                        ),
                    )
                )
        if isinstance(companion_evidence, dict) and companion_evidence.get("available"):
            hard_gates_status = str(companion_evidence.get("hard_gates_status", "") or "")
            if hard_gates_status == "fail":
                watchpoints.append(
                    _watchpoint(
                        "post_run_hard_gates_failed",
                        severity="warn",
                        scope="post_run_evidence_json",
                        side=side,
                        message=f"{side} companion evidence reports hard_gates.status=fail",
                    )
                )
            sink_alignment_status = str(companion_evidence.get("sink_alignment_status", "") or "")
            if sink_alignment_status and sink_alignment_status != "ok":
                watchpoints.append(
                    _watchpoint(
                        "post_run_sink_alignment_attention",
                        severity="warn",
                        scope="post_run_evidence_json",
                        side=side,
                        message=f"{side} companion evidence reports sink alignment status {sink_alignment_status}",
                    )
                )
            final_authority_status = str(companion_evidence.get("final_authority_status", "") or "")
            if final_authority_status and final_authority_status != "ok":
                watchpoints.append(
                    _watchpoint(
                        "post_run_final_authority_attention",
                        severity="warn",
                        scope="post_run_evidence_json",
                        side=side,
                        message=f"{side} companion evidence reports final authority status {final_authority_status}",
                    )
                )
            gate_repair_status = str(companion_evidence.get("gate_repair_status", "") or "")
            if gate_repair_status and gate_repair_status != "ok":
                watchpoints.append(
                    _watchpoint(
                        "post_run_gate_repair_attention",
                        severity="warn",
                        scope="post_run_evidence_json",
                        side=side,
                        message=f"{side} companion evidence reports gate repair status {gate_repair_status}",
                    )
                )
        note_markers = record.get("note_markers", {}) if isinstance(record.get("note_markers", {}), dict) else {}
        guarded_runner_summary = (
            record.get("guarded_runner_summary", {})
            if isinstance(record.get("guarded_runner_summary", {}), dict)
            else {}
        )
        use_guarded_summary = False
        if guarded_runner_summary:
            guarded_run_id = str(guarded_runner_summary.get("benchmark_archive_run_id", "") or "")
            if guarded_run_id and guarded_run_id != str(record.get("run_id", "") or ""):
                watchpoints.append(
                    _watchpoint(
                        "stage4_guarded_summary_stale_reference",
                        severity="warn",
                        scope="stage4_guarded_result",
                        side=side,
                        message=(
                            f"{side} archived guarded summary points at benchmark run {guarded_run_id}, "
                            f"not {record.get('run_id')}"
                        ),
                    )
                )
            elif guarded_runner_summary.get("available"):
                use_guarded_summary = True

        structured_termination_reason = ""
        structured_terminated_by_monitor = False
        structured_target_ep: int | None = None
        structured_before_ep: int | None = None
        structured_after_ep: int | None = None
        structured_child_exit_code: int | None = None
        structured_scope = "notes"
        if use_guarded_summary:
            structured_scope = "stage4_guarded_result"
            structured_termination_reason = str(guarded_runner_summary.get("termination_reason", "") or "")
            structured_terminated_by_monitor = bool(guarded_runner_summary.get("terminated_by_monitor"))
            structured_target_ep = _coerce_optional_int(guarded_runner_summary.get("target_ep"))
            structured_before_ep = _coerce_optional_int(guarded_runner_summary.get("latest_written_ep_before"))
            structured_after_ep = _coerce_optional_int(guarded_runner_summary.get("latest_written_ep_after"))
            structured_child_exit_code = _coerce_optional_int(guarded_runner_summary.get("child_exit_code"))
        elif note_markers:
            structured_termination_reason = str(note_markers.get("termination_reason", "") or "")
            structured_terminated_by_monitor = bool(note_markers.get("terminated_by_monitor"))
            structured_target_ep = _coerce_optional_int(note_markers.get("target_ep"))
            structured_before_ep = _coerce_optional_int(note_markers.get("before_latest_ep"))
            structured_after_ep = _coerce_optional_int(note_markers.get("after_latest_ep"))
            structured_child_exit_code = _coerce_optional_int(note_markers.get("child_exit_code"))

        if structured_terminated_by_monitor or structured_termination_reason:
            reason_tail = f" ({structured_termination_reason})" if structured_termination_reason else ""
            watchpoints.append(
                _watchpoint(
                    "monitor_termination_recorded",
                    severity="warn",
                    scope=structured_scope,
                    side=side,
                    message=f"{side} record indicates monitor termination{reason_tail}",
                )
            )
        if structured_child_exit_code not in (None, 0):
            watchpoints.append(
                _watchpoint(
                    "stage4_child_exit_nonzero",
                    severity="warn",
                    scope=structured_scope,
                    side=side,
                    message=f"{side} record child_exit_code is {structured_child_exit_code}",
                )
            )
        if structured_before_ep is not None and structured_after_ep is not None and structured_after_ep > structured_before_ep:
            watchpoints.append(
                _watchpoint(
                    "stage4_rerun_progress_recorded",
                    severity="info",
                    scope=structured_scope,
                    side=side,
                    message=(
                        f"{side} record advanced latest_written_ep from "
                        f"{structured_before_ep} to {structured_after_ep}"
                    ),
                )
            )
        if structured_target_ep is not None and structured_after_ep is not None and structured_after_ep < structured_target_ep:
            watchpoints.append(
                _watchpoint(
                    "stage4_target_gap_remaining",
                    severity="warn",
                    scope=structured_scope,
                    side=side,
                    message=(
                        f"{side} record stopped at latest_written_ep {structured_after_ep} "
                        f"before target_ep {structured_target_ep}"
                    ),
                )
            )

    stage4_delta = stage_metrics_delta.get("stage4", {})
    if stage4_delta:
        attempt_delta = stage4_delta.get("attempt_count", 0)
        if attempt_delta < 0:
            watchpoints.append(
                _watchpoint(
                    "stage4_attempt_count_improved",
                    severity="info",
                    scope="stage4",
                    message=f"stage4 attempt_count improved by {-attempt_delta}",
                )
            )
        elif attempt_delta > 0:
            watchpoints.append(
                _watchpoint(
                    "stage4_attempt_count_regressed",
                    severity="warn",
                    scope="stage4",
                    message=f"stage4 attempt_count increased by {attempt_delta}",
                )
            )

        pass_like_delta = stage4_delta.get("pass_like_count", 0)
        if pass_like_delta > 0:
            watchpoints.append(
                _watchpoint(
                    "stage4_pass_like_improved",
                    severity="info",
                    scope="stage4",
                    message=f"stage4 pass_like_count improved by {pass_like_delta}",
                )
            )
        elif pass_like_delta < 0:
            watchpoints.append(
                _watchpoint(
                    "stage4_pass_like_regressed",
                    severity="warn",
                    scope="stage4",
                    message=f"stage4 pass_like_count regressed by {-pass_like_delta}",
                )
            )

        cost_delta = stage4_delta.get("total_cost_usd", 0.0)
        if isinstance(cost_delta, (int, float)) and abs(float(cost_delta)) >= 1e-9:
            if float(cost_delta) < 0:
                watchpoints.append(
                    _watchpoint(
                        "stage4_cost_improved",
                        severity="info",
                        scope="stage4",
                        message=f"stage4 total_cost_usd decreased by {abs(float(cost_delta)):.6f}",
                    )
                )
            else:
                watchpoints.append(
                    _watchpoint(
                        "stage4_cost_regressed",
                        severity="warn",
                        scope="stage4",
                        message=f"stage4 total_cost_usd increased by {float(cost_delta):.6f}",
                    )
                )

    return watchpoints


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
    if delta["watchpoints"]:
        watchpoint_bits = [
            f"{item['id']}[{item.get('side', 'shared')}]"
            for item in delta["watchpoints"]
        ]
        lines.append("Watchpoints: " + ", ".join(watchpoint_bits))
    if delta["remediation_hints"]:
        remediation_bits = [
            f"{item['side']}:{item['surface']} -> {item['suggested_command']}"
            for item in delta["remediation_hints"]
        ]
        lines.append("Remediation hints: " + " | ".join(remediation_bits))
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
        left_evidence_json=args.left_evidence_json,
        right_evidence_json=args.right_evidence_json,
    )
    if args.format == "json":
        print(json.dumps(diff, ensure_ascii=False, indent=2))
    else:
        print(_render_text(diff, left_label=str(args.left), right_label=str(args.right)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
