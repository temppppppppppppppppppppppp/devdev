from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_benchmark_records import (
    _display_relative_path,
    _resolve_benchmark_root,
    load_benchmark_record,
)
from scripts.link_benchmark_companions import write_benchmark_companion_links


DEFAULT_FILENAME = "native-post-run-evidence.json"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill raw archive-native post-run evidence JSON next to benchmark records and optionally link it."
    )
    parser.add_argument(
        "records",
        nargs="*",
        help="benchmark record path(s) or run_id(s). Use --all-live to target every live archive record.",
    )
    parser.add_argument(
        "--all-live",
        action="store_true",
        help="target every live benchmark record under the benchmark archive root",
    )
    parser.add_argument(
        "--filename",
        default=DEFAULT_FILENAME,
        help="filename to write inside each record root",
    )
    parser.add_argument(
        "--no-link",
        action="store_true",
        help="write the evidence JSON only and skip benchmark_companion_links.json updates",
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


def collect_live_record_identifiers(
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
) -> list[str]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    return [
        _display_relative_path(workspace, manifest_path.parent)
        for manifest_path in sorted(benchmark_dir.glob("*/*/manifest.json"))
    ]


def build_native_post_run_evidence_payload(record: dict[str, Any]) -> dict[str, Any]:
    runtime_audit_summary = record.get("runtime_audit_summary", {})
    guarded_runner_summary = record.get("guarded_runner_summary", {})
    note_markers = record.get("note_markers", {})

    runtime_terminal_state = {
        "status": str(record.get("status", "") or ""),
        "runtime_audit_tag": str(record.get("runtime_audit_tag", "") or ""),
        "target_ep": record.get("target_ep"),
        "latest_session_id": str(record.get("latest_session_id", "") or ""),
    }
    archive_native_summary = {
        "proof_digest_status": "",
        "operational_status": "",
        "stage4_live_session_status": "",
        "stage4_retry_exercised": False,
        "stage4_patch_exercised": False,
        "stage4_target_ep_reached": False,
        "stage4_complete_emitted": False,
        "stage4_post_pass_contract_signal_count": 0,
        "guarded_result_available": False,
        "guarded_result_run_id": "",
        "guarded_target_ep": None,
        "guarded_latest_written_ep_before": None,
        "guarded_latest_written_ep_after": None,
        "guarded_terminated_by_monitor": False,
        "guarded_termination_reason": "",
        "guarded_child_exit_code": None,
        "note_markers": note_markers if isinstance(note_markers, dict) else {},
    }
    if isinstance(runtime_audit_summary, dict):
        archive_native_summary.update(
            {
                "proof_digest_status": str(runtime_audit_summary.get("proof_digest_status", "") or ""),
                "operational_status": str(runtime_audit_summary.get("operational_status", "") or ""),
                "stage4_live_session_status": str(runtime_audit_summary.get("stage4_live_session_status", "") or ""),
                "stage4_retry_exercised": bool(runtime_audit_summary.get("stage4_retry_exercised")),
                "stage4_patch_exercised": bool(runtime_audit_summary.get("stage4_patch_exercised")),
                "stage4_target_ep_reached": bool(runtime_audit_summary.get("stage4_target_ep_reached")),
                "stage4_complete_emitted": bool(runtime_audit_summary.get("stage4_complete_emitted")),
                "stage4_post_pass_contract_signal_count": int(
                    runtime_audit_summary.get("stage4_post_pass_contract_signal_count", 0) or 0
                ),
            }
        )
    if isinstance(guarded_runner_summary, dict):
        archive_native_summary.update(
            {
                "guarded_result_available": bool(guarded_runner_summary.get("available")),
                "guarded_result_run_id": str(guarded_runner_summary.get("benchmark_archive_run_id", "") or ""),
                "guarded_target_ep": guarded_runner_summary.get("target_ep"),
                "guarded_latest_written_ep_before": guarded_runner_summary.get("latest_written_ep_before"),
                "guarded_latest_written_ep_after": guarded_runner_summary.get("latest_written_ep_after"),
                "guarded_terminated_by_monitor": bool(guarded_runner_summary.get("terminated_by_monitor")),
                "guarded_termination_reason": str(guarded_runner_summary.get("termination_reason", "") or ""),
                "guarded_child_exit_code": guarded_runner_summary.get("child_exit_code"),
            }
        )

    return {
        "schema_version": "benchmark-native-post-run-evidence-v1",
        "evidence_role": "archive_native_post_run_evidence",
        "run_id": str(record.get("run_id", "") or ""),
        "record_root": str(record.get("record_root", "") or ""),
        "runtime_terminal_state": runtime_terminal_state,
        "archive_native_summary": archive_native_summary,
    }


def write_native_post_run_evidence(
    record_identifier: str,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
    filename: str = DEFAULT_FILENAME,
    link: bool = True,
) -> dict[str, str]:
    workspace = Path(workspace_root).resolve()
    record = load_benchmark_record(
        record_identifier,
        workspace_root=workspace,
        benchmark_root=benchmark_root,
    )
    record_root = workspace / str(record.get("record_root", "") or "")
    evidence_path = record_root / filename
    payload = build_native_post_run_evidence_payload(record)
    evidence_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sidecar_path = ""
    if link:
        result = write_benchmark_companion_links(
            str(record_root),
            workspace_root=workspace,
            benchmark_root=benchmark_root,
            post_run_evidence_json=evidence_path,
        )
        sidecar_path = str(result.get("links_path", "") or "")

    return {
        "run_id": str(record.get("run_id", "") or ""),
        "record_root": _display_relative_path(workspace, record_root),
        "evidence_path": _display_relative_path(workspace, evidence_path),
        "links_path": sidecar_path,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    requested_records = [str(item) for item in (args.records or []) if str(item or "").strip()]
    if args.all_live:
        requested_records.extend(
            collect_live_record_identifiers(
                workspace_root=args.workspace_root,
                benchmark_root=args.benchmark_root,
            )
        )
    seen: set[str] = set()
    record_identifiers = []
    for item in requested_records:
        if item not in seen:
            seen.add(item)
            record_identifiers.append(item)
    if not record_identifiers:
        raise SystemExit("provide at least one record identifier or use --all-live")

    results = [
        write_native_post_run_evidence(
            record_identifier,
            workspace_root=args.workspace_root,
            benchmark_root=args.benchmark_root,
            filename=args.filename,
            link=not bool(args.no_link),
        )
        for record_identifier in record_identifiers
    ]
    print(json.dumps({"records": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
