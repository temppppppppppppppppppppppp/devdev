# -*- coding: utf-8 -*-
"""Narrative Router CLI.

Determines the current pipeline stage and family for a given work_id
by checking filesystem artifacts. Outputs JSON status.

Usage:
    python -X utf8 scripts/narrative_router.py --work-id chaebol_allowance_zero
    python -X utf8 scripts/narrative_router.py --work-id my_wuxia_novel --genre wuxia
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.narrative_router.artifact_paths import (  # noqa: E402
    resolve_bi_path,
    resolve_phase0_path,
    resolve_tr_path,
)

# ---------------------------------------------------------------------------
# Profile enum used for family detection
# ---------------------------------------------------------------------------
BLOCKGUIDE_PROFILES = frozenset([
    "business_growth_profile",
    "investment_market_profile",
    "entertainment_media_profile",
    "medical_professional_profile",
    "office_power_profile",
    "tech_startup_profile",
    "urban_power_profile",
])

WUXIA_GENRES = frozenset(["wuxia", "muhyeop", "seonhyeop", "gangho"])

# ---------------------------------------------------------------------------
# Harness path constants (relative to ROOT)
# ---------------------------------------------------------------------------
BLOCKGUIDE_HARNESSES = {
    "stage0": "전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md",
    "planning": "docs/blockguide/treatment-planning-harness.md",
    "production": "docs/blockguide/treatment-production-harness-v2.md",
    "bi": "docs/blockguide/bi-production-harness-v1.md",
}
WUXGUIDE_HARNESSES = {
    "stage0": "전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md",
    "planning": "docs/wuxguide/wuxia-planning-harness.md",
    "production": "docs/wuxguide/wuxia-production-harness.md",
    "bi": "docs/wuxguide/wuxia-bi-production-harness.md",
}


def _safe_load_json(path: Path) -> dict | None:
    """Load a JSON file with UTF-8, returning None on any failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _detect_family(genre: str | None, work_id: str) -> str:
    """Resolve family to 'blockguide' or 'wuxguide'."""
    # 1. Explicit genre hint
    if genre:
        genre_lower = genre.lower().replace(" ", "").replace("-", "")
        if genre_lower in WUXIA_GENRES or "무협" in genre or "선협" in genre or "강호" in genre:
            return "wuxguide"
        return "blockguide"

    # 2. Check profile_lock.json if it exists
    profile_lock_path = ROOT / "treatments" / "preprocess" / work_id / "profile_lock.json"
    data = _safe_load_json(profile_lock_path)
    if data:
        primary = data.get("primary_profile", "")
        if primary == "wuxia":
            return "wuxguide"
        if primary in BLOCKGUIDE_PROFILES:
            return "blockguide"

    # 3. Default
    return "blockguide"


def _check_stage0_artifacts(work_id: str) -> dict[str, bool]:
    """Check existence and UTF-8 parsability of all 4 Stage 0 files."""
    base = ROOT / "treatments" / "preprocess" / work_id
    files = {
        "source_manifest": base / "source_manifest.json",
        "profile_lock": base / "profile_lock.json",
        "material_bundle_summary": base / "material_bundle_summary.json",
        "phase0_ready_snapshot": base / "phase0_ready_snapshot.json",
    }
    result = {}
    for key, path in files.items():
        result[key] = _safe_load_json(path) is not None
    return result


def _get_manual_audit_pass(work_id: str) -> bool:
    """Read phase0_ready_snapshot and return manual_audit_pass value."""
    path = ROOT / "treatments" / "preprocess" / work_id / "phase0_ready_snapshot.json"
    data = _safe_load_json(path)
    if data and isinstance(data.get("manual_audit_pass"), bool):
        return data["manual_audit_pass"]
    return False


def _determine_stage(work_id: str, stage0_status: dict[str, bool]) -> str:
    """Determine current pipeline stage per SSOT stage detection table."""
    # Stage 0: any artifact missing or manual_audit_pass != true
    all_present = all(stage0_status.values())
    if not all_present:
        return "stage0"
    if not _get_manual_audit_pass(work_id):
        return "stage0"

    # Check downstream artifacts
    phase0_path = resolve_phase0_path(work_id, root=ROOT)
    tr_path = resolve_tr_path(work_id, root=ROOT)
    bi_path = resolve_bi_path(work_id, root=ROOT)

    phase0_exists = phase0_path.is_file()
    tr_exists = tr_path.is_file()
    bi_exists = bi_path.is_file()

    if not phase0_exists:
        return "planning"
    if not tr_exists:
        return "production"
    if not bi_exists:
        return "bi"
    return "complete"


def route(work_id: str, genre: str | None = None) -> dict:
    """Build the full routing result dict."""
    family = _detect_family(genre, work_id)
    stage0_status = _check_stage0_artifacts(work_id)
    current_stage = _determine_stage(work_id, stage0_status)

    # Artifact existence flags
    phase0_exists = resolve_phase0_path(work_id, root=ROOT).is_file()
    tr_exists = resolve_tr_path(work_id, root=ROOT).is_file()
    bi_exists = resolve_bi_path(work_id, root=ROOT).is_file()

    harnesses = WUXGUIDE_HARNESSES if family == "wuxguide" else BLOCKGUIDE_HARNESSES
    next_harness = harnesses.get(current_stage, "")

    return {
        "work_id": work_id,
        "family": family,
        "current_stage": current_stage,
        "next_harness": next_harness,
        "artifacts": {
            "stage0": all(stage0_status.values()),
            "phase0": phase0_exists,
            "tr": tr_exists,
            "bi": bi_exists,
        },
        "stage0_detail": stage0_status,
        "manual_audit_pass": _get_manual_audit_pass(work_id),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Narrative pipeline router: detect family and current stage for a work_id."
    )
    parser.add_argument("--work-id", required=True, help="Canonical work_id (snake_case).")
    parser.add_argument("--genre", default=None, help="Genre hint (e.g. wuxia, hunter, investment).")
    parser.add_argument("--json", action="store_true", help="Print JSON output (default is JSON anyway).")
    args = parser.parse_args()

    result = route(args.work_id, args.genre)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
