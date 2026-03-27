from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


_SINK_ALIGNMENT_IGNORED_FIELDS = {
    "stage",
    "session_filter",
    "attempts_considered",
    "coverage",
    "complete_final_attempts",
    "director_lifecycle_attempts",
    "complete_lifecycle_attempts",
    "final_authority_contract",
    "status",
    "session_scoped_attempts",
    "legacy_key_attempts",
    "session_decision_rows_without_attempt_key",
}


def _load_summary(path: str | Path) -> dict[str, Any]:
    candidate = Path(path)
    data = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"summary root must be an object: {candidate}")
    return data


def _normalize_string_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return sorted(str(value).strip() for value in values if str(value).strip())


def _issue_size(value: object) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        if not value:
            return 0
        nested_sizes = [
            _issue_size(item) if isinstance(item, (list, dict)) else 1
            for item in value.values()
        ]
        return sum(nested_sizes) if any(nested_sizes) else len(value)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else 0
    return 1 if str(value).strip() else 0


def _count_sink_alignment_issues(summary: object) -> int:
    if not isinstance(summary, dict):
        return 0
    total = 0
    for key, value in summary.items():
        if key in _SINK_ALIGNMENT_IGNORED_FIELDS:
            continue
        total += _issue_size(value)
    return total


def _normalize_sink_alignment(summary: object) -> dict[str, Any]:
    if not isinstance(summary, dict) or not summary:
        return {"available": False, "status": "missing", "issue_count": 0}
    return {
        "available": True,
        "status": str(summary.get("status") or "missing"),
        "issue_count": _count_sink_alignment_issues(summary),
    }


def _normalize_patch_trace(summary: object) -> dict[str, Any]:
    if not isinstance(summary, dict) or not summary:
        return {
            "available": False,
            "count": 0,
            "structural_attempted_count": 0,
            "strategy_counts": {},
        }
    strategy_counts = summary.get("strategy_counts") or {}
    if not isinstance(strategy_counts, dict):
        strategy_counts = {}
    return {
        "available": True,
        "count": max(0, int(summary.get("count") or 0)),
        "structural_attempted_count": max(0, int(summary.get("structural_attempted_count") or 0)),
        "strategy_counts": {
            str(key): max(0, int(value or 0))
            for key, value in strategy_counts.items()
            if str(key).strip()
        },
    }


def _normalize_retry_required_coverage(summary: object) -> dict[str, Any]:
    if not isinstance(summary, dict) or not summary:
        return {
            "available": False,
            "status": "missing",
            "required_row_count": 0,
            "missing_retry_context_count": 0,
            "exercised": False,
        }
    rows_missing = summary.get("rows_missing_retry_context") or []
    if not isinstance(rows_missing, list):
        rows_missing = []
    required_row_count = max(0, int(summary.get("retry_required_row_count") or 0))
    return {
        "available": True,
        "status": str(summary.get("status") or "missing"),
        "required_row_count": required_row_count,
        "missing_retry_context_count": len(rows_missing),
        "exercised": required_row_count > 0,
    }


def _normalize_proof_status_rollup(summary: object, *, summary_role: str) -> dict[str, Any]:
    if not isinstance(summary, dict) or not summary:
        return {
            "available": False,
            "summary_role": summary_role,
            "status": "not_provided",
            "backend_wide_proof": False,
            "covered_count": 0,
            "uncovered_count": 0,
            "errors": [],
            "warnings": [],
        }
    covered = summary.get("covered_surfaces") or []
    uncovered = summary.get("uncovered_surfaces") or []
    if not isinstance(covered, list):
        covered = []
    if not isinstance(uncovered, list):
        uncovered = []
    return {
        "available": True,
        "summary_role": str(summary.get("summary_role") or summary_role),
        "status": str(summary.get("scope_status") or summary.get("status") or "unknown"),
        "backend_wide_proof": bool(summary.get("backend_wide_proof", False)),
        "covered_count": len(covered),
        "uncovered_count": len(uncovered),
        "errors": _normalize_string_list(summary.get("errors")),
        "warnings": _normalize_string_list(summary.get("warnings")),
    }


def normalize_canary_summary(summary: dict[str, Any]) -> dict[str, Any]:
    source_kind = "generic"
    base_summary = summary
    proof_summary = summary.get("proof_scope_summary")
    summary_role = str(summary.get("summary_role") or "")

    if isinstance(summary.get("stage4_canary_summary"), dict):
        source_kind = "stage34"
        base_summary = summary["stage4_canary_summary"]
        proof_summary = summary.get("multi_stage_proof_scope_summary") or base_summary.get("proof_scope_summary")
        summary_role = str(summary.get("summary_role") or base_summary.get("summary_role") or "")
    elif "patch_trace_summary" in summary or "rationale_contract_summary" in summary:
        source_kind = "stage4"
    elif "sink_alignment_summary" in summary and "episode_telemetry" in summary:
        source_kind = "stage3"

    hard_gates = base_summary.get("hard_gates") or {}
    if not isinstance(hard_gates, dict):
        hard_gates = {}

    sink_alignment_summary = _normalize_sink_alignment(base_summary.get("sink_alignment_summary"))
    current_session_sink_alignment_summary = _normalize_sink_alignment(
        base_summary.get("current_session_sink_alignment_summary")
    )
    stage3_probe_sink_alignment_summary = _normalize_sink_alignment(base_summary.get("stage3_sink_alignment_summary"))

    normalized = {
        "source_kind": source_kind,
        "summary_role": summary_role,
        "hard_gates": {
            "status": str(hard_gates.get("status") or "missing"),
            "errors": _normalize_string_list(hard_gates.get("errors")),
            "warnings": _normalize_string_list(hard_gates.get("warnings")),
        },
        "sink_alignment": {
            "primary": sink_alignment_summary,
            "current_session": current_session_sink_alignment_summary,
            "stage3_probe": stage3_probe_sink_alignment_summary,
            "total_issue_count": (
                sink_alignment_summary["issue_count"]
                + current_session_sink_alignment_summary["issue_count"]
                + stage3_probe_sink_alignment_summary["issue_count"]
            ),
        },
        "patch_trace": _normalize_patch_trace(base_summary.get("patch_trace_summary")),
        "retry_required_coverage": _normalize_retry_required_coverage(
            base_summary.get("rationale_contract_summary")
        ),
        "proof_status_rollup": _normalize_proof_status_rollup(proof_summary, summary_role=summary_role),
    }
    return normalized


def _counter_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    result: dict[str, int] = {}
    keys = sorted(set(before) | set(after))
    for key in keys:
        delta = int(after.get(key, 0)) - int(before.get(key, 0))
        if delta:
            result[key] = delta
    return result


def build_canary_summary_diff(left_summary: dict[str, Any], right_summary: dict[str, Any]) -> dict[str, Any]:
    left = normalize_canary_summary(left_summary)
    right = normalize_canary_summary(right_summary)

    hard_gates_delta = {
        "status_before": left["hard_gates"]["status"],
        "status_after": right["hard_gates"]["status"],
        "added_errors": sorted(set(right["hard_gates"]["errors"]) - set(left["hard_gates"]["errors"])),
        "removed_errors": sorted(set(left["hard_gates"]["errors"]) - set(right["hard_gates"]["errors"])),
        "added_warnings": sorted(set(right["hard_gates"]["warnings"]) - set(left["hard_gates"]["warnings"])),
        "removed_warnings": sorted(set(left["hard_gates"]["warnings"]) - set(right["hard_gates"]["warnings"])),
    }

    sink_alignment_delta = {
        "primary_status_before": left["sink_alignment"]["primary"]["status"],
        "primary_status_after": right["sink_alignment"]["primary"]["status"],
        "primary_issue_delta": (
            right["sink_alignment"]["primary"]["issue_count"] - left["sink_alignment"]["primary"]["issue_count"]
        ),
        "current_session_issue_delta": (
            right["sink_alignment"]["current_session"]["issue_count"]
            - left["sink_alignment"]["current_session"]["issue_count"]
        ),
        "stage3_probe_issue_delta": (
            right["sink_alignment"]["stage3_probe"]["issue_count"]
            - left["sink_alignment"]["stage3_probe"]["issue_count"]
        ),
        "total_issue_delta": right["sink_alignment"]["total_issue_count"] - left["sink_alignment"]["total_issue_count"],
    }

    patch_trace_delta = {
        "count_delta": right["patch_trace"]["count"] - left["patch_trace"]["count"],
        "structural_attempted_delta": (
            right["patch_trace"]["structural_attempted_count"] - left["patch_trace"]["structural_attempted_count"]
        ),
        "strategy_count_delta": _counter_delta(
            left["patch_trace"]["strategy_counts"],
            right["patch_trace"]["strategy_counts"],
        ),
    }

    retry_delta = {
        "status_before": left["retry_required_coverage"]["status"],
        "status_after": right["retry_required_coverage"]["status"],
        "required_row_delta": (
            right["retry_required_coverage"]["required_row_count"]
            - left["retry_required_coverage"]["required_row_count"]
        ),
        "missing_retry_context_delta": (
            right["retry_required_coverage"]["missing_retry_context_count"]
            - left["retry_required_coverage"]["missing_retry_context_count"]
        ),
        "exercised_before": left["retry_required_coverage"]["exercised"],
        "exercised_after": right["retry_required_coverage"]["exercised"],
    }

    proof_delta = {
        "status_before": left["proof_status_rollup"]["status"],
        "status_after": right["proof_status_rollup"]["status"],
        "covered_count_delta": (
            right["proof_status_rollup"]["covered_count"] - left["proof_status_rollup"]["covered_count"]
        ),
        "uncovered_count_delta": (
            right["proof_status_rollup"]["uncovered_count"] - left["proof_status_rollup"]["uncovered_count"]
        ),
        "added_errors": sorted(
            set(right["proof_status_rollup"]["errors"]) - set(left["proof_status_rollup"]["errors"])
        ),
        "removed_errors": sorted(
            set(left["proof_status_rollup"]["errors"]) - set(right["proof_status_rollup"]["errors"])
        ),
        "added_warnings": sorted(
            set(right["proof_status_rollup"]["warnings"]) - set(left["proof_status_rollup"]["warnings"])
        ),
        "removed_warnings": sorted(
            set(left["proof_status_rollup"]["warnings"]) - set(right["proof_status_rollup"]["warnings"])
        ),
    }

    changed_sections = [
        section
        for section, delta in {
            "hard_gates": any(hard_gates_delta.values()),
            "sink_alignment": any(sink_alignment_delta.values()),
            "patch_trace": any(
                [
                    patch_trace_delta["count_delta"],
                    patch_trace_delta["structural_attempted_delta"],
                    bool(patch_trace_delta["strategy_count_delta"]),
                ]
            ),
            "retry_required_coverage": any(
                [
                    retry_delta["required_row_delta"],
                    retry_delta["missing_retry_context_delta"],
                    retry_delta["exercised_before"] != retry_delta["exercised_after"],
                    retry_delta["status_before"] != retry_delta["status_after"],
                ]
            ),
            "proof_status_rollup": any(
                [
                    proof_delta["status_before"] != proof_delta["status_after"],
                    proof_delta["covered_count_delta"],
                    proof_delta["uncovered_count_delta"],
                    bool(proof_delta["added_errors"]),
                    bool(proof_delta["removed_errors"]),
                    bool(proof_delta["added_warnings"]),
                    bool(proof_delta["removed_warnings"]),
                ]
            ),
        }.items()
        if delta
    ]

    return {
        "left": left,
        "right": right,
        "delta": {
            "hard_gates": hard_gates_delta,
            "sink_alignment": sink_alignment_delta,
            "patch_trace": patch_trace_delta,
            "retry_required_coverage": retry_delta,
            "proof_status_rollup": proof_delta,
            "changed_sections": changed_sections,
        },
    }


def _render_text(diff: dict[str, Any], *, left_label: str, right_label: str) -> str:
    delta = diff["delta"]
    lines = [
        f"Canary Summary Diff: {left_label} -> {right_label}",
        f"Changed sections: {', '.join(delta['changed_sections']) if delta['changed_sections'] else 'none'}",
        (
            "Hard gates: "
            f"{delta['hard_gates']['status_before']} -> {delta['hard_gates']['status_after']}; "
            f"+errors={delta['hard_gates']['added_errors']}; -errors={delta['hard_gates']['removed_errors']}; "
            f"+warnings={delta['hard_gates']['added_warnings']}; -warnings={delta['hard_gates']['removed_warnings']}"
        ),
        (
            "Sink alignment: "
            f"primary {delta['sink_alignment']['primary_status_before']} -> "
            f"{delta['sink_alignment']['primary_status_after']}; "
            f"total_issue_delta={delta['sink_alignment']['total_issue_delta']}; "
            f"current_session_issue_delta={delta['sink_alignment']['current_session_issue_delta']}; "
            f"stage3_probe_issue_delta={delta['sink_alignment']['stage3_probe_issue_delta']}"
        ),
        (
            "Patch trace: "
            f"count_delta={delta['patch_trace']['count_delta']}; "
            f"structural_attempted_delta={delta['patch_trace']['structural_attempted_delta']}; "
            f"strategy_count_delta={delta['patch_trace']['strategy_count_delta']}"
        ),
        (
            "Retry-required coverage: "
            f"{delta['retry_required_coverage']['status_before']} -> {delta['retry_required_coverage']['status_after']}; "
            f"required_row_delta={delta['retry_required_coverage']['required_row_delta']}; "
            f"missing_retry_context_delta={delta['retry_required_coverage']['missing_retry_context_delta']}; "
            f"exercised={delta['retry_required_coverage']['exercised_before']} -> "
            f"{delta['retry_required_coverage']['exercised_after']}"
        ),
        (
            "Proof status rollup: "
            f"{delta['proof_status_rollup']['status_before']} -> {delta['proof_status_rollup']['status_after']}; "
            f"covered_count_delta={delta['proof_status_rollup']['covered_count_delta']}; "
            f"uncovered_count_delta={delta['proof_status_rollup']['uncovered_count_delta']}; "
            f"+errors={delta['proof_status_rollup']['added_errors']}; "
            f"+warnings={delta['proof_status_rollup']['added_warnings']}"
        ),
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff read-only canary summary JSON files.")
    parser.add_argument("left", help="path to the baseline canary summary JSON")
    parser.add_argument("right", help="path to the comparison canary summary JSON")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    args = parser.parse_args(argv)

    left_path = Path(args.left)
    right_path = Path(args.right)
    diff = build_canary_summary_diff(_load_summary(left_path), _load_summary(right_path))
    if args.format == "json":
        print(json.dumps(diff, ensure_ascii=False, indent=2))
    else:
        print(_render_text(diff, left_label=left_path.name, right_label=right_path.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
