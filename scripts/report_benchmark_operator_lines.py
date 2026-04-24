from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_benchmark_companion_links import audit_benchmark_companion_links
from scripts.compare_benchmark_records import compare_benchmark_records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render one-line operator report surfaces for live benchmark records read-only."
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
    parser.add_argument(
        "--pair",
        dest="pairs",
        action="append",
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="explicit benchmark pair to compare and render as a one-line operator surface",
    )
    parser.add_argument(
        "--latest-live-pair",
        action="store_true",
        help="append a comparison for the latest two live benchmark records by run_id",
    )
    parser.add_argument(
        "--issue-5-snapshot",
        action="store_true",
        help="convenience preset for the common issue-5 snapshot path; enables --latest-live-pair",
    )
    return parser.parse_args(argv)


def build_benchmark_operator_line_report(
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
    pairs: list[tuple[str, str]] | None = None,
    latest_live_pair: bool = False,
) -> dict[str, Any]:
    payload = audit_benchmark_companion_links(
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
    )
    record_report_lines = [
        {
            "run_id": str(record.get("run_id", "") or ""),
            "record_root": str(record.get("record_root", "") or ""),
            "operator_report_line": _build_record_operator_report_line(record),
        }
        for record in payload.get("records", [])
        if isinstance(record, dict)
    ]
    compare_pairs = list(pairs or [])
    if latest_live_pair:
        compare_pairs = _append_latest_live_pair(compare_pairs, payload.get("records", []))
    compare_report_lines = [
        _build_compare_report_entry(
            left=left,
            right=right,
            workspace_root=workspace_root,
            benchmark_root=benchmark_root,
        )
        for left, right in compare_pairs
    ]
    return {
        "benchmark_root": payload.get("benchmark_root", ""),
        "summary": payload.get("summary", {}),
        "strict": payload.get("strict", {}),
        "audit_operator_report_line": str(payload.get("operator_report_line", "") or ""),
        "record_report_lines": record_report_lines,
        "compare_report_lines": compare_report_lines,
    }


def _build_record_operator_report_line(record: dict[str, Any]) -> str:
    linked = ",".join(str(item) for item in record.get("linked_surfaces", [])) or "-"
    missing = ",".join(str(item) for item in record.get("missing_surfaces", [])) or "-"
    bits = [
        f"run_id={record.get('run_id', '')}",
        f"status={record.get('status', '')}",
        f"companion_state={record.get('companion_state', '')}",
        f"linked={linked}",
        f"missing={missing}",
    ]
    return "; ".join(bits)


def _append_latest_live_pair(
    existing_pairs: list[tuple[str, str]],
    records: object,
) -> list[tuple[str, str]]:
    if not isinstance(records, list):
        raise ValueError("latest live pair requested but audit payload does not contain record rows")
    live_run_ids = [
        str(record.get("run_id", "") or "")
        for record in records
        if isinstance(record, dict) and str(record.get("run_id", "") or "")
    ]
    if len(live_run_ids) < 2:
        raise ValueError("latest live pair requested but fewer than two live benchmark records are available")
    latest_pair = (live_run_ids[-2], live_run_ids[-1])
    if latest_pair in existing_pairs:
        return existing_pairs
    return existing_pairs + [latest_pair]


def apply_issue_5_snapshot_defaults(args: argparse.Namespace) -> argparse.Namespace:
    if bool(getattr(args, "issue_5_snapshot", False)):
        args.latest_live_pair = True
    return args


def _build_compare_report_entry(
    *,
    left: str,
    right: str,
    workspace_root: str | Path,
    benchmark_root: str | Path,
) -> dict[str, Any]:
    diff = compare_benchmark_records(
        left,
        right,
        workspace_root=workspace_root,
        benchmark_root=benchmark_root,
    )
    delta = diff.get("delta", {})
    payload = {
        "label": f"{left} -> {right}",
        "left_run_id": str(diff.get("left", {}).get("run_id", "") or ""),
        "right_run_id": str(diff.get("right", {}).get("run_id", "") or ""),
        "verdict": str(delta.get("verdict", "") or ""),
        "changed_sections": list(delta.get("changed_sections", [])),
        "operator_report_line": str(delta.get("operator_report_line", "") or ""),
    }
    proof_signal_summary = _build_compare_proof_signal_summary(diff)
    if proof_signal_summary:
        payload["proof_signal_summary"] = proof_signal_summary
    proof_highlights = _build_compare_proof_highlights(diff)
    if proof_highlights:
        payload["proof_highlights"] = proof_highlights
    return payload


def _build_compare_proof_signal_summary(diff: dict[str, Any]) -> str:
    merge_audit_summary = _build_compare_merge_audit_proof_signal_summary(diff)
    if merge_audit_summary:
        return merge_audit_summary
    return _build_compare_native_proof_signal_summary(diff)


def _build_compare_merge_audit_proof_signal_summary(diff: dict[str, Any]) -> str:
    side_bits: list[str] = []
    for side in ("left", "right"):
        side_record = diff.get(side, {})
        if not isinstance(side_record, dict):
            continue
        companion_merge_audit = side_record.get("companion_merge_audit", {})
        if not isinstance(companion_merge_audit, dict) or not companion_merge_audit.get("available"):
            continue
        fragments: list[str] = []
        validation = companion_merge_audit.get("validation", {})
        if isinstance(validation, dict):
            live_status = str(validation.get("live_rerun_status", "") or "")
            if live_status:
                fragments.append(f"live={live_status}")
            replay_probe_count = _coerce_positive_int(validation.get("replay_probe_count"))
            if replay_probe_count > 0:
                fragments.append(f"replay={replay_probe_count}")
            result_signal_count = _coerce_positive_int(validation.get("result_signal_count"))
            if result_signal_count > 0:
                fragments.append(f"signals={result_signal_count}")
        follow_up = companion_merge_audit.get("follow_up", {})
        if isinstance(follow_up, dict):
            open_item_count = _coerce_positive_int(follow_up.get("open_item_count"))
            if open_item_count > 0:
                fragments.append(f"open={open_item_count}")
            consequence_markers = {
                str(item)
                for item in follow_up.get("consequence_markers", [])
                if str(item or "")
            }
            if "remaining_blocker" in consequence_markers:
                fragments.append("blocker")
            addendum_finding_count = _coerce_positive_int(follow_up.get("addendum_finding_count"))
            if addendum_finding_count > 0:
                fragments.append(f"addendum={addendum_finding_count}")
        if fragments:
            side_bits.append(f"{side}:{','.join(fragments)}")
    return "; ".join(side_bits)


def _build_compare_native_proof_signal_summary(diff: dict[str, Any]) -> str:
    side_bits: list[str] = []
    for side in ("left", "right"):
        side_record = diff.get(side, {})
        if not isinstance(side_record, dict):
            continue

        fragments: list[str] = []
        runtime_audit_summary = side_record.get("runtime_audit_summary", {})
        if isinstance(runtime_audit_summary, dict):
            proof_digest_status = str(runtime_audit_summary.get("proof_digest_status", "") or "")
            if proof_digest_status and proof_digest_status != "ok":
                fragments.append(f"digest={proof_digest_status}")
            operational_status = str(runtime_audit_summary.get("operational_status", "") or "")
            if operational_status and operational_status != "ok":
                fragments.append(f"operational={operational_status}")
            stage4_live_session_status = str(runtime_audit_summary.get("stage4_live_session_status", "") or "")
            if stage4_live_session_status and stage4_live_session_status != "ok":
                fragments.append(f"live={stage4_live_session_status}")
            contract_signal_count = _coerce_positive_int(
                runtime_audit_summary.get("stage4_post_pass_contract_signal_count")
            )
            if contract_signal_count > 0:
                fragments.append(f"contracts={contract_signal_count}")

        progress_signals = _select_native_progress_signal_source(side_record)
        if isinstance(progress_signals, dict):
            termination_reason = str(progress_signals.get("termination_reason", "") or "").strip()
            terminated_by_monitor = bool(progress_signals.get("terminated_by_monitor"))
            if terminated_by_monitor or termination_reason:
                fragments.append(f"monitor={termination_reason or 'true'}")

            child_exit_code = _coerce_positive_int(progress_signals.get("child_exit_code"))
            if child_exit_code > 0:
                fragments.append(f"exit={child_exit_code}")

            before_ep = _coerce_positive_int(
                progress_signals.get("latest_written_ep_before", progress_signals.get("before_latest_ep"))
            )
            after_ep = _coerce_positive_int(
                progress_signals.get("latest_written_ep_after", progress_signals.get("after_latest_ep"))
            )
            target_ep = _coerce_positive_int(progress_signals.get("target_ep"))
            if after_ep > before_ep > 0:
                fragments.append(f"advance=+{after_ep - before_ep}")
            elif after_ep > before_ep and after_ep > 0:
                fragments.append(f"advance=+{after_ep - before_ep}")

            effective_latest_ep = after_ep if after_ep > 0 else before_ep
            if target_ep > 0 and effective_latest_ep > 0 and effective_latest_ep < target_ep:
                fragments.append(f"gap={target_ep - effective_latest_ep}")

        if fragments:
            side_bits.append(f"{side}:{','.join(fragments)}")
    return "; ".join(side_bits)


def _coerce_positive_int(value: object) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return 0
    return result if result > 0 else 0


def _build_compare_proof_highlights(diff: dict[str, Any]) -> list[str]:
    delta = diff.get("delta", {})
    watchpoints = delta.get("watchpoints", [])
    if not isinstance(watchpoints, list):
        return []

    merge_audit_priority = {
        "post_run_merge_audit_remaining_blocker_attention": 0,
        "post_run_merge_audit_live_verification_failure": 1,
        "post_run_merge_audit_live_verification_mixed": 2,
        "post_run_merge_audit_top_finding_attention": 3,
        "post_run_merge_audit_severity_attention": 4,
        "post_run_merge_audit_open_follow_up_attention": 5,
        "post_run_merge_audit_remaining_watchpoints": 6,
    }
    merge_audit_highlights = _collect_highlights(
        watchpoints=watchpoints,
        priority=merge_audit_priority,
        summarizer=_summarize_proof_highlight,
    )
    if merge_audit_highlights:
        return merge_audit_highlights

    native_priority = {
        "monitor_termination_recorded": 0,
        "stage4_child_exit_nonzero": 1,
        "stage4_target_gap_remaining": 2,
        "stage4_guarded_summary_stale_reference": 3,
        "stage4_live_session_attention": 4,
        "runtime_operational_status_attention": 5,
        "proof_digest_attention": 6,
        "stage4_target_ep_not_reached": 7,
        "stage4_complete_signal_missing": 8,
    }
    return _collect_highlights(
        watchpoints=watchpoints,
        priority=native_priority,
        summarizer=_summarize_native_proof_highlight,
    )


def _collect_highlights(
    *,
    watchpoints: list[Any],
    priority: dict[str, int],
    summarizer: Any,
) -> list[str]:
    selected = []
    for item in watchpoints:
        if not isinstance(item, dict):
            continue
        watchpoint_id = str(item.get("id", "") or "")
        if watchpoint_id not in priority:
            continue
        selected.append((priority[watchpoint_id], item))
    selected.sort(key=lambda pair: pair[0])

    highlights: list[str] = []
    for _, item in selected:
        highlight = str(summarizer(item) or "").strip()
        if highlight and highlight not in highlights:
            highlights.append(highlight)
        if len(highlights) >= 2:
            break
    return highlights


def _summarize_proof_highlight(watchpoint: dict[str, Any]) -> str:
    watchpoint_id = str(watchpoint.get("id", "") or "")
    side = str(watchpoint.get("side", "") or "").strip()
    message = str(watchpoint.get("message", "") or "").strip()
    side_prefix = f"{side} " if side else ""

    if watchpoint_id == "post_run_merge_audit_remaining_blocker_attention":
        return f"{side_prefix}remaining blocker".strip()
    if watchpoint_id == "post_run_merge_audit_live_verification_failure":
        return f"{side_prefix}live verification failure".strip()
    if watchpoint_id == "post_run_merge_audit_live_verification_mixed":
        return f"{side_prefix}live verification mixed".strip()
    if watchpoint_id == "post_run_merge_audit_top_finding_attention":
        title = message.split(": ", 1)[1].strip() if ": " in message else message
        return f"{side_prefix}top finding {title}".strip()
    if watchpoint_id == "post_run_merge_audit_severity_attention":
        return f"{side_prefix}{message}".strip()
    if watchpoint_id == "post_run_merge_audit_open_follow_up_attention":
        return f"{side_prefix}open follow-up items".strip()
    if watchpoint_id == "post_run_merge_audit_remaining_watchpoints":
        return f"{side_prefix}remaining watchpoints".strip()
    return ""


def _summarize_native_proof_highlight(watchpoint: dict[str, Any]) -> str:
    watchpoint_id = str(watchpoint.get("id", "") or "")
    side = str(watchpoint.get("side", "") or "").strip()
    message = str(watchpoint.get("message", "") or "").strip()
    side_prefix = f"{side} " if side else ""

    if watchpoint_id == "monitor_termination_recorded":
        return f"{side_prefix}monitor termination".strip()
    if watchpoint_id == "stage4_child_exit_nonzero":
        child_exit_code = message.split()[-1] if message else ""
        suffix = f" child exit {child_exit_code}".rstrip()
        return f"{side_prefix}{suffix.strip()}".strip()
    if watchpoint_id == "stage4_target_gap_remaining":
        return f"{side_prefix}target gap remaining".strip()
    if watchpoint_id == "stage4_guarded_summary_stale_reference":
        return f"{side_prefix}guarded summary stale".strip()
    if watchpoint_id == "stage4_live_session_attention":
        status = message.split()[-1] if message else ""
        suffix = f"live session {status}".strip()
        return f"{side_prefix}{suffix}".strip()
    if watchpoint_id == "runtime_operational_status_attention":
        status = message.split()[-1] if message else ""
        suffix = f"operational status {status}".strip()
        return f"{side_prefix}{suffix}".strip()
    if watchpoint_id == "proof_digest_attention":
        status = message.split()[-1] if message else ""
        suffix = f"proof digest {status}".strip()
        return f"{side_prefix}{suffix}".strip()
    if watchpoint_id == "stage4_target_ep_not_reached":
        return f"{side_prefix}target_ep not reached".strip()
    if watchpoint_id == "stage4_complete_signal_missing":
        return f"{side_prefix}stage4_complete missing".strip()
    return ""


def _select_native_progress_signal_source(side_record: dict[str, Any]) -> dict[str, Any]:
    guarded_runner_summary = side_record.get("guarded_runner_summary", {})
    run_id = str(side_record.get("run_id", "") or "")
    if isinstance(guarded_runner_summary, dict) and guarded_runner_summary.get("available"):
        guarded_run_id = str(guarded_runner_summary.get("benchmark_archive_run_id", "") or "")
        if not guarded_run_id or guarded_run_id == run_id:
            return guarded_runner_summary
    note_markers = side_record.get("note_markers", {})
    if isinstance(note_markers, dict):
        return note_markers
    return {}


def format_report_text(payload: dict[str, Any]) -> str:
    lines = ["Benchmark Operator Report Lines"]
    audit_operator_report_line = str(payload.get("audit_operator_report_line", "") or "")
    if audit_operator_report_line:
        lines.append("Audit: " + audit_operator_report_line)
    summary = payload.get("summary", {})
    if isinstance(summary, dict):
        lines.append(
            "Summary: "
            f"live_records={summary.get('live_records', 0)}; "
            f"records_with_missing_targets={summary.get('records_with_missing_targets', 0)}; "
            f"stale_index_rows={summary.get('stale_index_rows', 0)}"
        )
    strict = payload.get("strict", {})
    if isinstance(strict, dict):
        lines.append(f"Strict: {strict.get('status', 'pass')}")
    record_report_lines = payload.get("record_report_lines", [])
    if isinstance(record_report_lines, list) and record_report_lines:
        lines.append("Records:")
        for item in record_report_lines:
            if isinstance(item, dict):
                lines.append("- " + str(item.get("operator_report_line", "") or ""))
    compare_report_lines = payload.get("compare_report_lines", [])
    if isinstance(compare_report_lines, list) and compare_report_lines:
        lines.append("Comparisons:")
        for item in compare_report_lines:
            if isinstance(item, dict):
                bits = [
                    str(item.get("label", "") or ""),
                    str(item.get("operator_report_line", "") or ""),
                    f"verdict={item.get('verdict', '')}",
                    "changed_sections=" + ",".join(str(section) for section in item.get("changed_sections", [])),
                ]
                proof_signal_summary = str(item.get("proof_signal_summary", "") or "")
                if proof_signal_summary:
                    bits.append(f"proof_signals={proof_signal_summary}")
                proof_highlights = item.get("proof_highlights", [])
                if isinstance(proof_highlights, list) and proof_highlights:
                    bits.append("proof_highlights=" + " || ".join(str(part) for part in proof_highlights))
                lines.append("- " + " | ".join(bit for bit in bits if bit))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = apply_issue_5_snapshot_defaults(parse_args(argv))
    payload = build_benchmark_operator_line_report(
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
        pairs=[(str(left), str(right)) for left, right in (args.pairs or [])],
        latest_live_pair=bool(args.latest_live_pair),
    )
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
