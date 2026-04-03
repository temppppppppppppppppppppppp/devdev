# -*- coding: utf-8 -*-
"""Sync canonical research few-shot assets into narrative_ssot mirror paths.

This script copies the current authoritative reference manifest and all saved
card markdown files into `narrative_ssot/10_reference_bank/` as UTF-8 text.

Authoritative source is the research-stage few-shot root under `material_ssot`.

Usage:
    python -X utf8 scripts/sync_narrative_reference_bank.py
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "material_ssot" / "10_research" / "20_fewshot_bank"
SOURCE_CARDS = SOURCE_ROOT / "cards"
SOURCE_MANIFEST = SOURCE_ROOT / "reference_card_manifest.json"

DEST_ROOT = ROOT / "narrative_ssot" / "10_reference_bank"
DEST_CARDS = DEST_ROOT / "cards"
DEST_MANIFEST = DEST_ROOT / "reference_card_manifest.json"
DEST_STATUS = DEST_ROOT / "mirror_status.json"


def _assert_within_workspace(path: Path) -> None:
    resolved_root = ROOT.resolve()
    resolved_path = path.resolve()
    if resolved_root not in [resolved_path, *resolved_path.parents]:
        raise RuntimeError(f"Path escaped workspace root: {resolved_path}")


def _read_utf8(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _write_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if not SOURCE_MANIFEST.is_file():
        raise SystemExit(f"Missing source manifest: {SOURCE_MANIFEST}")
    if not SOURCE_CARDS.is_dir():
        raise SystemExit(f"Missing source cards dir: {SOURCE_CARDS}")

    _assert_within_workspace(DEST_ROOT)
    _assert_within_workspace(DEST_CARDS)
    _assert_within_workspace(DEST_MANIFEST)
    _assert_within_workspace(DEST_STATUS)

    DEST_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_text = _read_utf8(SOURCE_MANIFEST)
    _write_utf8(DEST_MANIFEST, manifest_text)

    if DEST_CARDS.exists():
        shutil.rmtree(DEST_CARDS)
    DEST_CARDS.mkdir(parents=True, exist_ok=True)

    card_files = sorted(SOURCE_CARDS.glob("*.md"))
    for source_file in card_files:
        dest_file = DEST_CARDS / source_file.name
        _write_utf8(dest_file, _read_utf8(source_file))

    status = {
        "mirror_mode": "copy_utf8_text",
        "authoritative_source": str(SOURCE_ROOT.relative_to(ROOT)).replace("\\", "/"),
        "mirrored_manifest": str(DEST_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "mirrored_cards_root": str(DEST_CARDS.relative_to(ROOT)).replace("\\", "/"),
        "synced_at_utc": datetime.now(timezone.utc).isoformat(),
        "card_count": len(card_files),
        "notes": [
            "material_ssot research few-shot bank is authoritative after Wave 1 cutover",
            "narrative_ssot mirror is for new structure adoption and traceability"
        ]
    }
    DEST_STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Synced manifest to: {DEST_MANIFEST}")
    print(f"Synced {len(card_files)} cards to: {DEST_CARDS}")
    print(f"Wrote mirror status: {DEST_STATUS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
