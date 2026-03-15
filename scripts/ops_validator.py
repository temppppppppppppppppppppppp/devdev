from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TEMP = DOCS / "temp"
DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
META_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 /_-]*):(?:\s*(?P<value>.+?)\s*)?$")
QUEUE_STATE_NAME = "queue-state.json"


@dataclass
class ValidationResult:
    infos: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)


def normalize_relpath(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().strip("`").replace("\\", "/")
    if not cleaned:
        return None
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def parse_metadata(path: Path, line_limit: int = 40) -> dict[str, str]:
    metadata: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines[:line_limit]:
        match = META_RE.match(line)
        if not match:
            continue
        key = match.group("key").strip().lower().replace(" ", "_")
        metadata[key] = (match.group("value") or "").strip()
    return metadata


def iter_dated_dirs() -> list[Path]:
    return sorted(
        [path for path in DOCS.iterdir() if path.is_dir() and DATE_DIR_RE.match(path.name)],
        key=lambda path: path.name,
    )


def find_dated_candidates(filename: str) -> list[Path]:
    candidates: list[Path] = []
    for dated_dir in iter_dated_dirs():
        candidate = dated_dir / filename
        if candidate.exists():
            candidates.append(candidate)
    return candidates


def resolve_declared_path(raw_value: str | None) -> Path | None:
    normalized = normalize_relpath(raw_value)
    if not normalized:
        return None
    return ROOT / normalized


def compare_contents(left: Path, right: Path) -> bool:
    return left.read_text(encoding="utf-8") == right.read_text(encoding="utf-8")


def validate_mirror_document(temp_path: Path, result: ValidationResult) -> None:
    metadata = parse_metadata(temp_path)
    actual_temp_rel = temp_path.relative_to(ROOT).as_posix()

    declared_temp = normalize_relpath(metadata.get("temp_mirror_path"))
    if declared_temp:
        if declared_temp != actual_temp_rel:
            result.fail(
                f"{actual_temp_rel}: Temp Mirror Path metadata points to {declared_temp}, expected {actual_temp_rel}"
            )
    else:
        result.warn(f"{actual_temp_rel}: missing Temp Mirror Path metadata")

    declared_canonical = resolve_declared_path(metadata.get("canonical_path"))
    canonical_path: Path | None = None
    if declared_canonical is not None:
        if not declared_canonical.exists():
            result.fail(
                f"{actual_temp_rel}: Canonical Path metadata points to missing file {declared_canonical.relative_to(ROOT).as_posix()}"
            )
        else:
            canonical_path = declared_canonical
    else:
        result.warn(f"{actual_temp_rel}: missing Canonical Path metadata")
        candidates = find_dated_candidates(temp_path.name)
        if len(candidates) == 1:
            canonical_path = candidates[0]
            result.info(
                f"{actual_temp_rel}: inferred canonical path {canonical_path.relative_to(ROOT).as_posix()}"
            )
        elif len(candidates) == 0:
            result.fail(f"{actual_temp_rel}: no canonical dated counterpart found")
        else:
            canonical_path = candidates[-1]
            candidate_list = ", ".join(candidate.relative_to(ROOT).as_posix() for candidate in candidates)
            result.warn(
                f"{actual_temp_rel}: multiple canonical candidates found; using latest match {canonical_path.relative_to(ROOT).as_posix()} ({candidate_list})"
            )

    if canonical_path is None:
        return

    canonical_rel = canonical_path.relative_to(ROOT).as_posix()
    if canonical_rel.startswith("docs/temp/"):
        result.fail(f"{actual_temp_rel}: canonical path resolves inside docs/temp, which is invalid")
        return

    if not compare_contents(temp_path, canonical_path):
        result.fail(f"{actual_temp_rel}: mirror content differs from canonical {canonical_rel}")
    else:
        result.info(f"{actual_temp_rel}: mirror content matches canonical {canonical_rel}")

    if temp_path.name.endswith("-execution-ssot.md") and "source_survey_docs" not in metadata:
        result.warn(f"{actual_temp_rel}: missing Source Survey Docs metadata")


def validate_queue_state(exec_docs: list[Path], roadmap_path: Path | None, result: ValidationResult) -> None:
    queue_state_path = TEMP / QUEUE_STATE_NAME
    if not queue_state_path.exists():
        return

    try:
        payload = json.loads(queue_state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.fail(f"docs/temp/{QUEUE_STATE_NAME}: invalid JSON ({exc})")
        return

    required_fields = {"version", "generated_at", "queue_mode", "active_item_count", "roadmap", "items"}
    missing_fields = required_fields - payload.keys()
    if missing_fields:
        result.fail(
            f"docs/temp/{QUEUE_STATE_NAME}: missing required fields {sorted(missing_fields)}"
        )
        return

    if payload["version"] != "temp-queue-state-v1":
        result.fail(f"docs/temp/{QUEUE_STATE_NAME}: unsupported version {payload['version']}")

    items = payload["items"]
    if not isinstance(items, list):
        result.fail(f"docs/temp/{QUEUE_STATE_NAME}: items must be an array")
        return

    if payload["active_item_count"] != len(items):
        result.fail(
            f"docs/temp/{QUEUE_STATE_NAME}: active_item_count={payload['active_item_count']} does not match items={len(items)}"
        )

    actual_mode = "empty"
    if len(exec_docs) == 1:
        actual_mode = "single"
    elif len(exec_docs) > 1:
        actual_mode = "aggregate"
    if payload["queue_mode"] != actual_mode:
        result.fail(
            f"docs/temp/{QUEUE_STATE_NAME}: queue_mode={payload['queue_mode']} does not match actual mode {actual_mode}"
        )

    roadmap = payload["roadmap"]
    if roadmap_path is None and roadmap is not None:
        result.fail(f"docs/temp/{QUEUE_STATE_NAME}: roadmap object present but docs/temp/execution-roadmap.md is absent")
    if roadmap_path is not None and roadmap is None:
        result.fail(f"docs/temp/{QUEUE_STATE_NAME}: roadmap is null but docs/temp/execution-roadmap.md exists")

    expected_temp_paths = {path.relative_to(ROOT).as_posix() for path in exec_docs}
    reported_temp_paths: set[str] = set()
    allowed_statuses = {"pending", "in_progress", "completed", "blocked"}

    for index, item in enumerate(items, start=1):
        item_fields = {
            "topic",
            "temp_path",
            "canonical_path",
            "status",
            "depends_on",
            "mirror_present",
            "canonical_present",
        }
        missing_item_fields = item_fields - item.keys()
        if missing_item_fields:
            result.fail(
                f"docs/temp/{QUEUE_STATE_NAME}: item {index} missing fields {sorted(missing_item_fields)}"
            )
            continue

        if item["status"] not in allowed_statuses:
            result.fail(
                f"docs/temp/{QUEUE_STATE_NAME}: item {index} has unsupported status {item['status']}"
            )

        temp_rel = normalize_relpath(item["temp_path"])
        canonical_rel = normalize_relpath(item["canonical_path"])
        if temp_rel is None or canonical_rel is None:
            result.fail(
                f"docs/temp/{QUEUE_STATE_NAME}: item {index} has invalid temp_path or canonical_path"
            )
            continue

        reported_temp_paths.add(temp_rel)
        temp_file = ROOT / temp_rel
        canonical_file = ROOT / canonical_rel
        if bool(item["mirror_present"]) != temp_file.exists():
            result.fail(
                f"docs/temp/{QUEUE_STATE_NAME}: item {index} mirror_present does not match file existence for {temp_rel}"
            )
        if bool(item["canonical_present"]) != canonical_file.exists():
            result.fail(
                f"docs/temp/{QUEUE_STATE_NAME}: item {index} canonical_present does not match file existence for {canonical_rel}"
            )

    if reported_temp_paths != expected_temp_paths:
        result.fail(
            f"docs/temp/{QUEUE_STATE_NAME}: item temp_path set does not match active temp execution docs"
        )


def emit_result(result: ValidationResult, strict: bool) -> int:
    for message in result.infos:
        print(f"PASS: {message}")
    for message in result.warnings:
        print(f"WARN: {message}")
    for message in result.errors:
        print(f"FAIL: {message}")

    error_count = len(result.errors)
    warning_count = len(result.warnings)
    print(f"SUMMARY: errors={error_count} warnings={warning_count}")

    if error_count:
        return 1
    if strict and warning_count:
        return 1
    return 0


def run_validation(strict: bool) -> int:
    result = ValidationResult()

    if not TEMP.exists():
        result.fail("docs/temp: directory is missing")
        return emit_result(result, strict)

    if not (TEMP / "README.md").exists():
        result.warn("docs/temp/README.md is missing")

    exec_docs = sorted(TEMP.glob("*-execution-ssot.md"))
    roadmap_path = TEMP / "execution-roadmap.md"
    roadmap_present = roadmap_path.exists()

    if len(exec_docs) > 1 and not roadmap_present:
        result.fail("docs/temp: multiple execution SSOT mirrors exist but docs/temp/execution-roadmap.md is missing")
    if roadmap_present and len(exec_docs) == 0:
        result.warn("docs/temp/execution-roadmap.md exists but there are no active execution SSOT mirrors")

    for exec_doc in exec_docs:
        validate_mirror_document(exec_doc, result)

    if roadmap_present:
        validate_mirror_document(roadmap_path, result)

    validate_queue_state(exec_docs, roadmap_path if roadmap_present else None, result)

    if not exec_docs:
        result.info("docs/temp: no active execution SSOT mirrors found")
    else:
        result.info(f"docs/temp: {len(exec_docs)} active execution SSOT mirror(s) found")

    return emit_result(result, strict)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate temp execution queue and canonical mirror integrity.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    args = parser.parse_args()
    return run_validation(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
