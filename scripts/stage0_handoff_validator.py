# -*- coding: utf-8 -*-
"""Stage 0 Handoff Validator.

Validates all 4 Stage 0 JSON artifacts for a given work_id against
the contracts/ schemas and checks structural requirements.

Usage:
    python -X utf8 scripts/stage0_handoff_validator.py --work-id chaebol_allowance_zero

Exit code 0 = pass, 1 = fail.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Valid profile enum (must match contracts/*.schema.json)
# ---------------------------------------------------------------------------
VALID_PRIMARY_PROFILES = {
    "business_growth_profile",
    "investment_market_profile",
    "entertainment_media_profile",
    "medical_professional_profile",
    "office_power_profile",
    "tech_startup_profile",
    "urban_power_profile",
    "wuxia",
}

# Stage 0 artifact definitions: (filename, schema_filename)
STAGE0_ARTIFACTS = [
    ("source_manifest.json", "source_manifest.schema.json"),
    ("profile_lock.json", "profile_lock.schema.json"),
    ("material_bundle_summary.json", "material_bundle_summary.schema.json"),
    ("phase0_ready_snapshot.json", "phase0_ready_snapshot.schema.json"),
]
OPENING_CONTRACT_BLOCK_START = 2
OPENING_CONTRACT_BLOCK_END = 6
OPENING_CONTRACT_BLOCK_FIELDS = (
    "first_signboard_block",
    "representative_reevaluation_block",
    "next_battlefield_ticket_block",
)


def _load_json_utf8(path: Path) -> tuple[dict | None, str | None]:
    """Load JSON with UTF-8. Returns (data, error_message)."""
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
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"JSON parse failed for {path}: {exc}"
    if not isinstance(data, dict):
        return None, f"Expected JSON object at top level in {path}, got {type(data).__name__}"
    return data, None


def _load_schema(name: str) -> dict | None:
    """Load a schema from contracts/."""
    schema_path = ROOT / "contracts" / name
    if not schema_path.is_file():
        return None
    try:
        with open(schema_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _check_required_fields(data: dict, schema: dict, file_label: str) -> list[str]:
    """Check that all required fields from schema exist in data."""
    errors: list[str] = []
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"[{file_label}] Missing required field: '{field}'")
    # Recurse one level for object-type required fields
    props = schema.get("properties", {})
    for field, field_schema in props.items():
        if field in data and field_schema.get("type") == "object":
            sub_required = field_schema.get("required", [])
            sub_data = data[field]
            if isinstance(sub_data, dict):
                for sub_field in sub_required:
                    if sub_field not in sub_data:
                        errors.append(f"[{file_label}] Missing required field: '{field}.{sub_field}'")
    return errors


def _check_type(value: Any, expected_type: str) -> bool:
    """Check JSON Schema type against Python value."""
    type_map = {
        "string": str,
        "boolean": bool,
        "integer": int,
        "number": (int, float),
        "array": list,
        "object": dict,
    }
    expected = type_map.get(expected_type)
    if expected is None:
        return True
    # In JSON Schema, boolean is not integer
    if expected_type == "integer" and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def _check_types_shallow(data: dict, schema: dict, file_label: str) -> list[str]:
    """Check top-level field types against schema."""
    errors: list[str] = []
    props = schema.get("properties", {})
    for field, field_schema in props.items():
        if field not in data:
            continue
        expected = field_schema.get("type")
        if expected and not _check_type(data[field], expected):
            errors.append(
                f"[{file_label}] Field '{field}' expected type '{expected}', "
                f"got {type(data[field]).__name__}"
            )
    return errors


def _validate_source_manifest(data: dict) -> list[str]:
    """Source-manifest-specific checks."""
    errors: list[str] = []
    cs = data.get("canonical_sources", [])
    if isinstance(cs, list) and len(cs) == 0:
        errors.append("[source_manifest] canonical_sources must be non-empty")
    wi = data.get("work_identity", {})
    if isinstance(wi, dict):
        pp = wi.get("primary_profile", "")
        if pp and pp not in VALID_PRIMARY_PROFILES:
            errors.append(
                f"[source_manifest] work_identity.primary_profile '{pp}' "
                f"is not a valid profile enum value"
            )
    return errors


def _validate_profile_lock(data: dict) -> list[str]:
    """Profile-lock-specific checks."""
    errors: list[str] = []
    pp = data.get("primary_profile", "")
    if pp and pp not in VALID_PRIMARY_PROFILES:
        errors.append(
            f"[profile_lock] primary_profile '{pp}' is not a valid profile enum value"
        )
    return errors


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_opening_bundle_contract(contract: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return [f"[{label}] opening_bundle_contract must be an object"]

    bundle_window = contract.get("bundle_window")
    if not _is_nonempty_text(bundle_window):
        errors.append(f"[{label}] opening_bundle_contract.bundle_window must be a non-empty string")
    elif not re.search(r"2\s*[~\-]\s*6", str(bundle_window)):
        errors.append(f"[{label}] opening_bundle_contract.bundle_window must lock the TR 2~6 window")

    for field in ("bundle_goal", "macro_battlefield", "timing_reconciliation_note"):
        if not _is_nonempty_text(contract.get(field)):
            errors.append(f"[{label}] opening_bundle_contract.{field} must be a non-empty string")

    macro_map = contract.get("macro_battlefield_map")
    if not isinstance(macro_map, list) or not macro_map:
        errors.append(f"[{label}] opening_bundle_contract.macro_battlefield_map must be a non-empty array")
    elif any(not _is_nonempty_text(item) for item in macro_map):
        errors.append(f"[{label}] opening_bundle_contract.macro_battlefield_map entries must be non-empty strings")

    for field in OPENING_CONTRACT_BLOCK_FIELDS:
        value = contract.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"[{label}] opening_bundle_contract.{field} must be an integer")
            continue
        if value < OPENING_CONTRACT_BLOCK_START or value > OPENING_CONTRACT_BLOCK_END:
            errors.append(
                f"[{label}] opening_bundle_contract.{field} must stay within TR {OPENING_CONTRACT_BLOCK_START}~{OPENING_CONTRACT_BLOCK_END}"
            )

    return errors


def _validate_material_bundle_summary(data: dict) -> list[str]:
    errors: list[str] = []
    contract = data.get("opening_bundle_contract")
    if contract is not None:
        errors.extend(_validate_opening_bundle_contract(contract, "material_bundle_summary"))
    return errors


def _validate_phase0_ready_snapshot(data: dict) -> list[str]:
    """Phase0-ready-snapshot-specific checks."""
    errors: list[str] = []
    audit = data.get("manual_audit_pass")
    if not isinstance(audit, bool):
        errors.append(
            f"[phase0_ready_snapshot] manual_audit_pass must be boolean, "
            f"got {type(audit).__name__}"
        )
    return errors


def _phase0_candidate_paths(work_id: str) -> tuple[Path, ...]:
    return (
        ROOT / "treatments" / "phase0" / f"{work_id}_phase0_design.json",
        ROOT / "treatments" / f"{work_id}_phase0_design.json",
    )


def _validate_phase0_design(data: dict) -> list[str]:
    errors: list[str] = []
    phase0_design = data.get("phase0_design")
    if not isinstance(phase0_design, dict):
        return errors
    contract = phase0_design.get("opening_bundle_contract")
    if contract is not None:
        errors.extend(_validate_opening_bundle_contract(contract, "phase0_design"))
    return errors


def validate(work_id: str) -> tuple[bool, list[str]]:
    """Run full Stage 0 validation. Returns (passed, list_of_messages)."""
    base = ROOT / "treatments" / "preprocess" / work_id
    all_errors: list[str] = []
    all_info: list[str] = []

    for artifact_name, schema_name in STAGE0_ARTIFACTS:
        artifact_path = base / artifact_name
        file_label = artifact_name.replace(".json", "")

        # 1. UTF-8 + JSON parsing
        data, err = _load_json_utf8(artifact_path)
        if err:
            all_errors.append(err)
            continue
        all_info.append(f"[{file_label}] UTF-8 parse OK: {artifact_path}")

        # 2. Load schema
        schema = _load_schema(schema_name)
        if schema is None:
            all_errors.append(f"Schema not found: contracts/{schema_name}")
            continue

        # 3. Required fields
        all_errors.extend(_check_required_fields(data, schema, file_label))

        # 4. Type checks
        all_errors.extend(_check_types_shallow(data, schema, file_label))

        # 5. File-specific checks
        if artifact_name == "source_manifest.json":
            all_errors.extend(_validate_source_manifest(data))
        elif artifact_name == "profile_lock.json":
            all_errors.extend(_validate_profile_lock(data))
        elif artifact_name == "material_bundle_summary.json":
            all_errors.extend(_validate_material_bundle_summary(data))
        elif artifact_name == "phase0_ready_snapshot.json":
            all_errors.extend(_validate_phase0_ready_snapshot(data))

    phase0_path = next((path for path in _phase0_candidate_paths(work_id) if path.is_file()), None)
    if phase0_path is not None:
        phase0_data, err = _load_json_utf8(phase0_path)
        if err:
            all_errors.append(err)
        else:
            all_info.append(f"[phase0_design] UTF-8 parse OK: {phase0_path}")
            all_errors.extend(_validate_phase0_design(phase0_data))

    passed = len(all_errors) == 0
    messages = all_info + all_errors
    return passed, messages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Stage 0 handoff artifacts for a work_id."
    )
    parser.add_argument("--work-id", required=True, help="Canonical work_id (snake_case).")
    args = parser.parse_args()

    passed, messages = validate(args.work_id)

    for msg in messages:
        print(msg)

    if passed:
        print(f"\nPASS: All Stage 0 artifacts valid for '{args.work_id}'.")
        return 0
    else:
        print(f"\nFAIL: Stage 0 validation failed for '{args.work_id}'.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
