# -*- coding: utf-8 -*-
"""Build narrative_ssot Phase0 planning seed from Stage0 authority."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.stage0_phase0_seed import (  # noqa: E402
    build_phase0_seed_from_stage0,
    sync_phase0_seed_from_stage0,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Phase0 planning seed from narrative_ssot Stage0 authority."
    )
    parser.add_argument("--work-id", required=True, help="Canonical work_id (snake_case).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the inferred planning seed summary without writing files.",
    )
    args = parser.parse_args()

    if args.dry_run:
        result = build_phase0_seed_from_stage0(args.work_id, root=ROOT)
        print(f"[dry-run] title={result.phase0_design['title']}")
        print(f"[dry-run] title_resolution={result.title_resolution}")
        work_identity_surface = result.phase0_design.get("work_identity_surface", {})
        if isinstance(work_identity_surface, dict) and work_identity_surface.get("commercial_label"):
            print(f"[dry-run] commercial_label={work_identity_surface['commercial_label']}")
        if isinstance(work_identity_surface, dict) and work_identity_surface.get("slug_aliases"):
            print(f"[dry-run] slug_aliases={', '.join(work_identity_surface['slug_aliases'])}")
        print(f"[dry-run] primary_profile={result.phase0_design['planning_seed_authority']['profile_resolution']}")
        print(
            "[dry-run] opening_macro_battlefield="
            f"{result.phase0_design['opening_bundle_contract']['macro_battlefield']}"
        )
        return 0

    result = sync_phase0_seed_from_stage0(args.work_id, root=ROOT, write=True)
    print(f"Built Phase0 planning seed for: {args.work_id}")
    print(f"Title resolution: {result.title_resolution}")
    print(f"Stage0 source mode: {result.stage0_source_mode}")
    print(
        "Opening macro battlefield: "
        f"{result.phase0_design['opening_bundle_contract']['macro_battlefield']}"
    )
    for path in result.updated_paths:
        print(f"Wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
