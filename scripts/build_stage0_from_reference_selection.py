# -*- coding: utf-8 -*-
"""Build narrative_ssot Stage0 preprocess drafts from reference_selection.

Usage:
    python -X utf8 scripts/build_stage0_from_reference_selection.py --work-id demo_work
    python -X utf8 scripts/build_stage0_from_reference_selection.py --work-id demo_work --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.reference_selection_stage0 import (  # noqa: E402
    build_stage0_selection_draft,
    sync_stage0_from_reference_selection,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Stage0 preprocess drafts from narrative_ssot reference_selection."
    )
    parser.add_argument("--work-id", required=True, help="Canonical work_id (snake_case).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the inferred Stage0 summary without writing files.",
    )
    args = parser.parse_args()

    if args.dry_run:
        result = build_stage0_selection_draft(args.work_id, root=ROOT)
        print(f"[dry-run] primary_profile={result.profile_lock['primary_profile']}")
        print(
            "[dry-run] opening_bundle_contract="
            f"{result.material_bundle_summary['opening_bundle_contract']['macro_battlefield']}"
        )
        print(f"[dry-run] selected_cards={len(result.selected_cards)}")
        return 0

    result = sync_stage0_from_reference_selection(args.work_id, root=ROOT, write=True)
    print(f"Built Stage0 preprocess draft for: {args.work_id}")
    print(f"Primary profile: {result.profile_lock['primary_profile']}")
    print(
        "Opening macro battlefield: "
        f"{result.material_bundle_summary['opening_bundle_contract']['macro_battlefield']}"
    )
    for path in result.updated_paths:
        print(f"Wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
