from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".log",
    ".md",
    ".ps1",
    ".psm1",
    ".py",
    ".scss",
    ".spec",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
ROOT_FILE_ALLOWLIST = {"AGENTS.md", ".pre-commit-config.yaml"}
EXCLUDED_DIR_NAMES = {
    ".cache",
    ".claude",
    ".git",
    ".hypothesis",
    ".pyarmor",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "dist",
    "node_modules",
    "python-embed",
    "win-unpacked",
}
DOUBLE_QUESTION_RE = re.compile(r"(?<!\?)\?\?(?!\?)")
GENERATED_SURVEY_REPORT_RE = re.compile(r"mojibake-global-survey-.*\.json$")
ALT_DECODERS = ("cp949", "euc-kr", "latin-1")
DEFAULT_ARCHIVE_MANIFEST = Path("docs/2026-03-13/mojibake-archive-manifest.json")
DEFAULT_MATERIAL_QUARANTINE_LEDGER = Path("docs/2026-03-13/material-quarantine-ledger.json")


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def is_generated_survey_report(path: Path) -> bool:
    return path.suffix.lower() == ".json" and bool(GENERATED_SURVEY_REPORT_RE.fullmatch(path.name))


def iter_text_files(root: Path, ignore_paths: set[Path] | None = None) -> list[Path]:
    files: list[Path] = []
    ignore_paths = ignore_paths or set()
    for path in root.rglob("*"):
        if not path.is_file() or should_skip(path):
            continue
        if is_generated_survey_report(path):
            continue
        if path.resolve() in ignore_paths:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in ROOT_FILE_ALLOWLIST:
            continue
        files.append(path)
    return files


def top_bucket(path: Path) -> str:
    if len(path.parts) == 1:
        return "<root>"
    return path.parts[0]


def line_samples(text: str, limit: int) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        signals: list[str] = []
        if "\ufffd" in line:
            signals.append("fffd")
        if "???" in line:
            signals.append("q3")
        elif DOUBLE_QUESTION_RE.search(line):
            signals.append("q2")
        if not signals:
            continue
        samples.append(
            {
                "line": line_no,
                "signals": signals,
                "text": line[:280],
            }
        )
        if len(samples) >= limit:
            break
    return samples


def alt_decodes(raw: bytes, preview_chars: int) -> dict[str, str]:
    previews: dict[str, str] = {}
    for encoding in ALT_DECODERS:
        try:
            previews[encoding] = raw.decode(encoding)[:preview_chars]
        except UnicodeDecodeError:
            continue
    return previews


def producer_hits(root: Path) -> list[dict[str, object]]:
    producer_tokens = (
        "cp949",
        'errors="replace"',
        'errors="ignore"',
        "PYTHONIOENCODING",
        "Set-Content",
        "Add-Content",
        "Out-File",
        "TextIOWrapper",
    )
    producer_roots = [
        Path("main_a.py"),
        Path("main.js"),
        Path("build"),
        Path("geuldobi-desktop/src"),
        Path("modules"),
        Path("scripts"),
    ]
    hits: list[dict[str, object]] = []
    for producer_root in producer_roots:
        target = root / producer_root
        if not target.exists():
            continue
        files = [target] if target.is_file() else iter_text_files(target)
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                matched = [token for token in producer_tokens if token in line]
                if not matched:
                    continue
                hits.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "line": line_no,
                        "tokens": matched,
                        "text": line[:280],
                    }
                )
    return hits


def load_archive_manifest(root: Path, manifest_path: Path | None) -> dict[str, object]:
    target = manifest_path or (root / DEFAULT_ARCHIVE_MANIFEST)
    if not target.is_absolute():
        target = (root / target).resolve()
    if not target.exists():
        return {"path": "", "entries": [], "quarantine_paths": set()}

    payload = json.loads(target.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    quarantine_paths: set[Path] = set()
    normalized_entries: list[dict[str, object]] = []
    for entry in entries:
        rel_path = Path(str(entry.get("path", "") or ""))
        if not rel_path.parts:
            continue
        resolved = (root / rel_path).resolve()
        quarantine_paths.add(resolved)
        normalized_entry = dict(entry)
        normalized_entry["path"] = rel_path.as_posix()
        normalized_entry["exists"] = resolved.exists()
        normalized_entries.append(normalized_entry)
    return {
        "path": target.relative_to(root).as_posix() if target.exists() else "",
        "entries": normalized_entries,
        "quarantine_paths": quarantine_paths,
    }


def load_material_quarantine_ledger(root: Path, ledger_path: Path | None) -> dict[str, object]:
    target = ledger_path or (root / DEFAULT_MATERIAL_QUARANTINE_LEDGER)
    if not target.is_absolute():
        target = (root / target).resolve()
    if not target.exists():
        return {"path": "", "entries": [], "quarantine_paths": set()}

    payload = json.loads(target.read_text(encoding="utf-8"))
    entries = payload.get("entries", [])
    quarantine_paths: set[Path] = set()
    normalized_entries: list[dict[str, object]] = []
    for entry in entries:
        rel_path = Path(str(entry.get("path", "") or ""))
        if not rel_path.parts:
            continue
        resolved = (root / rel_path).resolve()
        quarantine_paths.add(resolved)
        normalized_entry = dict(entry)
        normalized_entry["path"] = rel_path.as_posix()
        normalized_entry["exists"] = resolved.exists()
        normalized_entries.append(normalized_entry)
    return {
        "path": target.relative_to(root).as_posix() if target.exists() else "",
        "entries": normalized_entries,
        "quarantine_paths": quarantine_paths,
    }


def survey(
    root: Path,
    sample_limit: int,
    ignore_paths: set[Path] | None = None,
    archive_manifest_path: Path | None = None,
    material_quarantine_path: Path | None = None,
) -> dict[str, object]:
    archive_manifest = load_archive_manifest(root, archive_manifest_path)
    material_quarantine = load_material_quarantine_ledger(root, material_quarantine_path)
    quarantine_paths = set(archive_manifest["quarantine_paths"]) | set(material_quarantine["quarantine_paths"])
    text_files = iter_text_files(root, ignore_paths=(ignore_paths or set()) | quarantine_paths)
    suspicious_files: list[dict[str, object]] = []
    utf8_fail_files: list[dict[str, object]] = []
    bucket_counts: dict[str, dict[str, int]] = {}

    for path in text_files:
        rel_path = path.relative_to(root)
        bucket = top_bucket(rel_path)
        bucket_counts.setdefault(
            bucket,
            {
                "files": 0,
                "utf8_fail_files": 0,
                "fffd_files": 0,
                "q3_files": 0,
                "q2_files": 0,
            },
        )
        bucket_counts[bucket]["files"] += 1

        try:
            raw = path.read_bytes()
        except OSError:
            continue

        if b"\x00" in raw:
            continue

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            utf8_fail_files.append(
                {
                    "path": rel_path.as_posix(),
                    "error": str(exc),
                    "alt_decodes": alt_decodes(raw, 200),
                }
            )
            bucket_counts[bucket]["utf8_fail_files"] += 1
            continue

        fffd_count = text.count("\ufffd")
        q3_count = text.count("???")
        q2_count = len(DOUBLE_QUESTION_RE.findall(text))
        if not any((fffd_count, q3_count, q2_count)):
            continue

        if fffd_count:
            bucket_counts[bucket]["fffd_files"] += 1
        if q3_count:
            bucket_counts[bucket]["q3_files"] += 1
        if q2_count:
            bucket_counts[bucket]["q2_files"] += 1

        suspicious_files.append(
            {
                "path": rel_path.as_posix(),
                "bucket": bucket,
                "fffd_count": fffd_count,
                "q3_count": q3_count,
                "q2_count": q2_count,
                "samples": line_samples(text, sample_limit),
            }
        )

    suspicious_files.sort(
        key=lambda row: (
            -int(bool(row["fffd_count"])),
            -int(bool(row["q3_count"])),
            -int(row["fffd_count"]),
            -int(row["q3_count"]),
            -int(row["q2_count"]),
            row["path"],
        )
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": root.resolve().as_posix(),
        "mode": "static-read-only",
        "text_files_scanned": len(text_files),
        "archive_manifest_path": archive_manifest["path"],
        "quarantined_archive_file_count": len(archive_manifest["entries"]),
        "material_quarantine_ledger_path": material_quarantine["path"],
        "quarantined_material_file_count": len(material_quarantine["entries"]),
        "suspicious_file_count": len(suspicious_files) + len(utf8_fail_files),
        "utf8_fail_file_count": len(utf8_fail_files),
        "fffd_file_count": sum(1 for row in suspicious_files if row["fffd_count"]),
        "q3_file_count": sum(1 for row in suspicious_files if row["q3_count"]),
        "q2_file_count": sum(1 for row in suspicious_files if row["q2_count"]),
        "excluded_dir_names": sorted(EXCLUDED_DIR_NAMES),
        "excluded_generated_report_pattern": "mojibake-global-survey-*.json",
    }
    return {
        "summary": summary,
        "quarantined_archive_files": archive_manifest["entries"],
        "quarantined_material_files": material_quarantine["entries"],
        "bucket_counts": bucket_counts,
        "utf8_fail_files": utf8_fail_files,
        "suspicious_files": suspicious_files,
        "producer_hits": producer_hits(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only mojibake survey for the current workspace.")
    parser.add_argument(
        "--root",
        default=".",
        help="Workspace root to scan.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="UTF-8 JSON output path.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=3,
        help="Maximum suspicious line samples to retain per file.",
    )
    parser.add_argument(
        "--archive-manifest",
        default="",
        help="Optional archive quarantine manifest. Defaults to docs/2026-03-13/mojibake-archive-manifest.json when present.",
    )
    parser.add_argument(
        "--material-quarantine-ledger",
        default="",
        help="Optional material quarantine ledger. Defaults to docs/2026-03-13/material-quarantine-ledger.json when present.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = survey(
        root,
        sample_limit=args.sample_limit,
        ignore_paths={output_path.resolve()},
        archive_manifest_path=Path(args.archive_manifest) if args.archive_manifest else None,
        material_quarantine_path=Path(args.material_quarantine_ledger) if args.material_quarantine_ledger else None,
    )
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"wrote: {output_path.resolve().as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
