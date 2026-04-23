from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_benchmark_records import (
    COMPANION_LINKS_FILENAME,
    _display_relative_path,
    _resolve_benchmark_root,
    _resolve_existing_path,
    _resolve_record_root,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write explicit companion links next to an archived benchmark record.")
    parser.add_argument("record", help="benchmark record path or run_id")
    parser.add_argument(
        "--post-run-evidence-json",
        default="",
        help="optional structured post-run evidence JSON to link",
    )
    parser.add_argument(
        "--post-run-merge-audit-md",
        default="",
        help="optional markdown post-run merge audit path to link",
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


def write_benchmark_companion_links(
    record_identifier: str,
    *,
    workspace_root: str | Path = ROOT,
    benchmark_root: str | Path = "benchmarks",
    post_run_evidence_json: str | Path | None = None,
    post_run_merge_audit_md: str | Path | None = None,
) -> dict[str, str]:
    workspace = Path(workspace_root).resolve()
    benchmark_dir = _resolve_benchmark_root(workspace, benchmark_root)
    record_root, _ = _resolve_record_root(
        str(record_identifier),
        workspace_root=workspace,
        benchmark_root=benchmark_dir,
    )
    payload = {
        "schema_version": "benchmark-companion-links-v1",
        "post_run_evidence_json": _normalize_link_value(post_run_evidence_json, workspace_root=workspace),
        "post_run_merge_audit_md": _normalize_link_value(post_run_merge_audit_md, workspace_root=workspace),
    }
    links_path = record_root / COMPANION_LINKS_FILENAME
    links_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "record_root": _display_relative_path(workspace, record_root),
        "links_path": _display_relative_path(workspace, links_path),
    }


def _normalize_link_value(value: str | Path | None, *, workspace_root: Path) -> str:
    if value in (None, ""):
        return ""
    resolved = _resolve_existing_path(str(value), workspace_root=workspace_root)
    if resolved is None:
        raise FileNotFoundError(f"companion target not found: {value}")
    return _display_relative_path(workspace_root, resolved)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = write_benchmark_companion_links(
        args.record,
        workspace_root=args.workspace_root,
        benchmark_root=args.benchmark_root,
        post_run_evidence_json=args.post_run_evidence_json,
        post_run_merge_audit_md=args.post_run_merge_audit_md,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
