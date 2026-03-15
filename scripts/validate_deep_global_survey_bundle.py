from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9 /_-]*):(?:\s*(?P<value>.+?)\s*)?$")
EXEC_DOC_RE = re.compile(r"`(?P<path>docs/[^`]+-execution-ssot\.md)`")
ROADMAP_RE = re.compile(r"`(?P<path>docs/[^`]+-execution-roadmap\.md)`")
REQUIRED_HEADINGS = [
    "## 1. Intent",
    "## 2. Scope Lock",
    "## 3. Coverage Matrix",
    "## 4. Macro View",
    "## 5. Micro View",
    "## 6. Cross-Cut Integrity Matrix",
    "## 7. Operational and Regression View",
    "## 8. Contradiction and Uncertainty Ledger",
    "## 9. Severity and Action Map",
    "## 10. Execution SSOT Mapping",
    "## 11. Single SSOT Roadmap Lineage",
    "## 12. Confidence Summary",
]


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
    if cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned or None


def parse_metadata(path: Path, line_limit: int = 30) -> dict[str, str]:
    metadata: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines[:line_limit]:
        match = META_RE.match(line)
        if not match:
            continue
        key = match.group("key").strip().lower().replace(" ", "_")
        metadata[key] = (match.group("value") or "").strip()
    return metadata


def validate_survey_doc(path: Path, result: ValidationResult) -> None:
    if not path.exists():
        result.fail(f"{path}: file does not exist")
        return

    text = path.read_text(encoding="utf-8")
    metadata = parse_metadata(path)

    required_metadata = {
        "canonical_path",
        "related_evidence_manifest",
        "roadmap_policy",
        "confidence_model",
        "confidence_target",
    }
    for key in sorted(required_metadata):
        if key not in metadata:
            result.fail(f"{path.name}: missing metadata `{key}`")

    roadmap_policy = normalize_relpath(metadata.get("roadmap_policy"))
    if roadmap_policy and roadmap_policy.lower() != "single-ssot":
        result.fail(f"{path.name}: roadmap policy must be `single-ssot`, found `{roadmap_policy}`")

    confidence_target = metadata.get("confidence_target", "")
    if "95" not in confidence_target:
        result.fail(f"{path.name}: confidence target must declare 95% or higher")

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            result.fail(f"{path.name}: missing required heading `{heading}`")

    exec_docs = sorted({match.group("path") for match in EXEC_DOC_RE.finditer(text)})
    roadmaps = sorted({match.group("path") for match in ROADMAP_RE.finditer(text)})

    if not exec_docs:
        result.fail(f"{path.name}: no execution SSOT references found")
    else:
        result.info(f"{path.name}: execution SSOT references={len(exec_docs)}")

    if len(exec_docs) >= 2 and not roadmaps:
        result.fail(f"{path.name}: multiple execution SSOT references found but no roadmap reference")
    elif roadmaps:
        result.info(f"{path.name}: roadmap references={len(roadmaps)}")

    if len(roadmaps) > 1:
        result.fail(f"{path.name}: multiple unique roadmap references found; deep bundle must have one SSOT roadmap")

    if "95" not in text:
        result.warn(f"{path.name}: survey text does not mention the 95% confidence gate outside metadata")


def emit_result(result: ValidationResult, strict: bool) -> int:
    for message in result.infos:
        print(f"PASS: {message}")
    for message in result.warnings:
        print(f"WARN: {message}")
    for message in result.errors:
        print(f"FAIL: {message}")
    print(f"SUMMARY: errors={len(result.errors)} warnings={len(result.warnings)}")
    if result.errors:
        return 1
    if strict and result.warnings:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the structure of a deep global survey bundle.")
    parser.add_argument("--survey-doc", required=True, help="Canonical deep global survey markdown document.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = parser.parse_args()

    survey_doc = Path(args.survey_doc)
    if not survey_doc.is_absolute():
        survey_doc = ROOT / survey_doc

    result = ValidationResult()
    validate_survey_doc(survey_doc, result)
    return emit_result(result, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
