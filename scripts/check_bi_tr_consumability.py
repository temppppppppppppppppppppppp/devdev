"""BI/TR consumability filter for pair checks and quarantine scans."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.response_schemas import (
    validate_bible_structure,
    validate_phase0_files,
    validate_treatment_structure,
)
from modules.core.stage0_handoff import build_plot_roadmap_from_treatment, validate_plot_roadmap_entries

DEFAULT_BIBLE_DIR = ROOT / "bible" / "_quarantine"
DEFAULT_TREATMENT_DIR = ROOT / "treatments" / "_quarantine"
RUNTIME_PROTAGONIST_KEYS = ("world_origin", "incarnation_type", "pov", "external_pov_insert_policy")


@dataclass
class ConsumabilityReport:
    work_key: str
    bible_path: str | None
    treatment_path: str | None
    verdicts: dict[str, str]
    salvage_ready: bool
    repair_needed: bool
    bible_valid: bool
    treatment_valid: bool
    phase0_valid: bool
    canonical_block_count: int
    bible_errors: list[str] = field(default_factory=list)
    bible_warnings: list[str] = field(default_factory=list)
    treatment_errors: list[str] = field(default_factory=list)
    treatment_warnings: list[str] = field(default_factory=list)
    phase0_errors: list[str] = field(default_factory=list)
    phase0_warnings: list[str] = field(default_factory=list)
    canonical_roadmap_warnings: list[str] = field(default_factory=list)
    embedded_roadmap_warnings: list[str] = field(default_factory=list)
    protagonist_config_keys: list[str] = field(default_factory=list)
    runtime_protagonist_keys_present: list[str] = field(default_factory=list)
    runtime_protagonist_keys_missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _load_json_utf8(path: Path | None) -> tuple[Any | None, str | None]:
    if path is None:
        return None, None
    if not path.is_file():
        return None, f"File not found: {path}"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, f"Cannot read {path}: {exc}"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, f"UTF-8 decode failed for {path}: {exc}"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"JSON parse failed for {path}: {exc}"


def _normalize_work_key(value: str) -> str:
    value = re.sub(r"^\d+_", "", value)
    return value.strip("_").lower()


def infer_bible_work_key(path: Path) -> str:
    stem = path.stem
    for pattern in (r"^\d+_bi_(.+)$", r"^\d+_(.+)_bi$", r"^(.+)_bi$"):
        match = re.match(pattern, stem)
        if match:
            return _normalize_work_key(match.group(1))
    return _normalize_work_key(stem)


def infer_treatment_work_key(path: Path) -> str | None:
    stem = path.stem
    match = re.match(r"^(.+?)_tr_block_", stem)
    if match:
        return _normalize_work_key(match.group(1))
    return None


def _get_bible_root(bible_data: Any) -> dict[str, Any]:
    if not isinstance(bible_data, dict):
        return {}
    master = bible_data.get("MasterBible")
    return master if isinstance(master, dict) else bible_data


def _roadmap_warnings_for_bible(bible_data: Any) -> list[str]:
    bible_root = _get_bible_root(bible_data)
    roadmap = bible_root.get("plot_roadmap")
    if roadmap is None:
        return ["plot_roadmap missing"]
    return validate_plot_roadmap_entries(roadmap)


def _treatment_priority(path: Path) -> tuple[int, int, int, str]:
    stem = path.stem.lower()
    block_match = re.search(r"_tr_block_(\d+)(?:_(\d+))?", stem)
    start_no = int(block_match.group(1)) if block_match else 0
    end_no = int(block_match.group(2) or block_match.group(1)) if block_match else 0
    if stem.endswith("_draft"):
        tier = 3
    elif stem.endswith("_densified"):
        tier = 2
    elif stem.endswith("_candidate"):
        tier = 1
    else:
        tier = 0
    return (tier, end_no, start_no, stem)


def choose_preferred_treatment(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=_treatment_priority)


def _status_from_ready(valid: bool, warnings: list[str], *, allow_warnings: bool = False) -> str:
    if not valid:
        return "fail"
    if warnings and not allow_warnings:
        return "mixed"
    return "pass"


def inspect_pair(
    *,
    bible_path: Path | None,
    treatment_path: Path | None,
    work_key: str | None = None,
) -> ConsumabilityReport:
    work_key = work_key or (
        infer_bible_work_key(bible_path)
        if bible_path is not None
        else infer_treatment_work_key(treatment_path) or "unknown"
    )
    bible_data, bible_load_error = _load_json_utf8(bible_path)
    treatment_data, treatment_load_error = _load_json_utf8(treatment_path)

    bible_errors: list[str] = [bible_load_error] if bible_load_error else []
    treatment_errors: list[str] = [treatment_load_error] if treatment_load_error else []
    bible_warnings: list[str] = []
    treatment_warnings: list[str] = []
    phase0_errors: list[str] = []
    phase0_warnings: list[str] = []
    canonical_roadmap_warnings: list[str] = []
    embedded_roadmap_warnings: list[str] = []
    notes: list[str] = []
    canonical_block_count = 0

    bible_valid = False
    treatment_valid = False
    phase0_valid = False

    if bible_data is not None and not bible_errors:
        bible_valid, extra_errors, bible_warnings = validate_bible_structure(bible_data)
        bible_errors.extend(extra_errors)
        embedded_roadmap_warnings = _roadmap_warnings_for_bible(bible_data)

    if treatment_data is not None and not treatment_errors:
        treatment_valid, extra_errors, treatment_warnings = validate_treatment_structure(treatment_data)
        treatment_errors.extend(extra_errors)
        canonical_roadmap = build_plot_roadmap_from_treatment(treatment_data)
        canonical_block_count = len(canonical_roadmap)
        canonical_roadmap_warnings = validate_plot_roadmap_entries(canonical_roadmap)

    if bible_data is not None and treatment_data is not None and not bible_load_error and not treatment_load_error:
        phase0_valid, phase_report = validate_phase0_files(bible_data, treatment_data)
        phase0_errors.extend(phase_report["bible"]["errors"])
        phase0_errors.extend(phase_report["treatment"]["errors"])
        phase0_warnings.extend(phase_report["bible"]["warnings"])
        phase0_warnings.extend(phase_report["treatment"]["warnings"])
        canonical_block_count = max(canonical_block_count, phase_report["treatment"]["block_count"])

    protagonist_config = _get_bible_root(bible_data).get("protagonist_config", {})
    if not isinstance(protagonist_config, dict):
        protagonist_config = {}
        if bible_data is not None and bible_valid:
            notes.append("protagonist_config is not a dict")
    protagonist_keys = sorted(protagonist_config.keys())
    runtime_present = [key for key in RUNTIME_PROTAGONIST_KEYS if protagonist_config.get(key)]
    runtime_missing = [key for key in RUNTIME_PROTAGONIST_KEYS if key not in runtime_present]
    if runtime_missing:
        notes.append("runtime protagonist subset is partial")

    tr_status = _status_from_ready(treatment_valid and not treatment_load_error, canonical_roadmap_warnings)
    if bible_path is None:
        notes.append("bible file missing")
    if treatment_path is None:
        notes.append("treatment file missing")
    if bible_valid:
        bi_standalone_status = "pass" if not embedded_roadmap_warnings else "mixed"
    else:
        bi_standalone_status = "fail"
    if not phase0_valid or treatment_path is None or bible_path is None:
        pair_status = "fail"
    elif tr_status == "pass":
        pair_status = "pass"
    else:
        pair_status = "mixed"

    return ConsumabilityReport(
        work_key=work_key,
        bible_path=str(bible_path) if bible_path else None,
        treatment_path=str(treatment_path) if treatment_path else None,
        verdicts={
            "tr_consumability": tr_status,
            "bi_standalone_roadmap_readiness": bi_standalone_status,
            "pair_consumability": pair_status,
        },
        salvage_ready=pair_status == "pass",
        repair_needed=pair_status == "mixed",
        bible_valid=bible_valid,
        treatment_valid=treatment_valid,
        phase0_valid=phase0_valid,
        canonical_block_count=canonical_block_count,
        bible_errors=bible_errors,
        bible_warnings=bible_warnings,
        treatment_errors=treatment_errors,
        treatment_warnings=treatment_warnings,
        phase0_errors=phase0_errors,
        phase0_warnings=phase0_warnings,
        canonical_roadmap_warnings=canonical_roadmap_warnings,
        embedded_roadmap_warnings=embedded_roadmap_warnings,
        protagonist_config_keys=protagonist_keys,
        runtime_protagonist_keys_present=runtime_present,
        runtime_protagonist_keys_missing=runtime_missing,
        notes=notes,
    )


def scan_quarantine(bible_dir: Path, treatment_dir: Path) -> list[ConsumabilityReport]:
    bible_paths = sorted(path for path in bible_dir.glob("*.json") if path.is_file())
    treatment_paths = sorted(path for path in treatment_dir.glob("*.json") if path.is_file())

    treatments_by_key: dict[str, list[Path]] = {}
    for path in treatment_paths:
        work_key = infer_treatment_work_key(path)
        if work_key is None:
            continue
        treatments_by_key.setdefault(work_key, []).append(path)

    results: list[ConsumabilityReport] = []
    matched_keys: set[str] = set()
    for bible_path in bible_paths:
        work_key = infer_bible_work_key(bible_path)
        preferred_treatment = choose_preferred_treatment(treatments_by_key.get(work_key, []))
        if preferred_treatment is not None:
            matched_keys.add(work_key)
        results.append(
            inspect_pair(bible_path=bible_path, treatment_path=preferred_treatment, work_key=work_key)
        )

    for work_key, candidates in sorted(treatments_by_key.items()):
        if work_key in matched_keys:
            continue
        results.append(
            inspect_pair(
                bible_path=None,
                treatment_path=choose_preferred_treatment(candidates),
                work_key=work_key,
            )
        )
    return results


def _print_text_report(results: list[ConsumabilityReport]) -> None:
    salvage_count = sum(1 for result in results if result.salvage_ready)
    repair_count = sum(1 for result in results if result.repair_needed)
    blocked_count = len(results) - salvage_count - repair_count
    print(
        f"Scanned {len(results)} item(s) | salvage-ready={salvage_count} | "
        f"repair-needed={repair_count} | blocked={blocked_count}"
    )
    for result in results:
        verdicts = result.verdicts
        print(
            f"- {result.work_key}: pair={verdicts['pair_consumability']} "
            f"(tr={verdicts['tr_consumability']}, bi={verdicts['bi_standalone_roadmap_readiness']}) "
            f"blocks={result.canonical_block_count}"
        )
        if result.notes:
            print(f"  notes: {', '.join(result.notes)}")
        if result.bible_errors:
            print(f"  bible_errors: {' | '.join(result.bible_errors)}")
        if result.treatment_errors:
            print(f"  treatment_errors: {' | '.join(result.treatment_errors)}")
        if result.canonical_roadmap_warnings:
            print(f"  tr_roadmap_warnings: {len(result.canonical_roadmap_warnings)}")
        if result.embedded_roadmap_warnings:
            print(f"  bi_roadmap_warnings: {len(result.embedded_roadmap_warnings)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check BI/TR consumability or scan quarantine artifacts.")
    parser.add_argument("--bible", type=Path, help="Path to BI JSON")
    parser.add_argument("--treatment", type=Path, help="Path to TR JSON")
    parser.add_argument("--bible-dir", type=Path, default=DEFAULT_BIBLE_DIR, help="BI scan directory")
    parser.add_argument("--treatment-dir", type=Path, default=DEFAULT_TREATMENT_DIR, help="TR scan directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    if args.bible or args.treatment:
        results = [inspect_pair(bible_path=args.bible, treatment_path=args.treatment)]
    else:
        results = scan_quarantine(args.bible_dir, args.treatment_dir)

    if args.json:
        print(json.dumps({"results": [asdict(result) for result in results]}, ensure_ascii=False, indent=2))
    else:
        _print_text_report(results)

    return 1 if any(result.verdicts["pair_consumability"] == "fail" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
