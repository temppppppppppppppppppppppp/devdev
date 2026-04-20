#!/usr/bin/env python3
"""
Stage 2 Forward-Consistency Canary — Headless Runner

목적: deterministic carryover fix가 실제 런에서
  - destroyed item resurrection
  - stale inventory carryover
  - arc_start_state 누락
을 막는지 확인.

Usage:
    python scripts/canary_stage2_headless.py <project_name> [target_arc_count]
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(_REPO_ROOT)
sys.path.insert(0, str(_REPO_ROOT))


def _load_workspace_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(override=True)


_load_workspace_env()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/canary_stage2_headless.py <project_name> [target_arc_count]")
        sys.exit(1)

    project_name = sys.argv[1]
    target_arc_count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    os.environ["GEULDOBI_STAGE2_HEADLESS"] = "1"

    print(f"[Canary] project={project_name}, target_arc_count={target_arc_count}")
    print(f"[Canary] Working directory: {os.getcwd()}")

    # --- Initialize App ---
    from main_a import SovereignApp

    app = SovereignApp()

    # Force investment genre (0_1 is investment fiction)
    from modules.core.constants import GenreTypes, HUDKeys
    app.selected_genre = {
        "name": f"{GenreTypes.get_name(GenreTypes.INVESTMENT)} (Investment Fiction)",
        "type": GenreTypes.INVESTMENT,
        "hud_key": HUDKeys.INVESTMENT_HUD_ROOT,
        "description": "금융 배경, 자본/투자 시스템, 기업/시장",
        "critical_keys": ["capital", "portfolio", "market_position"],
    }

    # Initialize preset registry
    SovereignApp._initialize_selected_genre_preset_registry(app, app.selected_genre)

    # Bind project
    SovereignApp._bind_selected_project(app, project_name)
    SovereignApp._restore_boot_runtime_state(app)

    # Genre alignment (skip confirmation)
    cp = app.current_project
    if cp:
        cp.genre = app.selected_genre
        db = getattr(cp, "db", None)
        if db:
            stored_genre = db.load_anchor("genre_info")
            if not stored_genre:
                db.save_anchor("genre_info", app.selected_genre)

    SovereignApp._initialize_project_genre_runtime(app)
    SovereignApp._initialize_project_runtime_support(app, project_name)

    print(f"[Canary] Project bound: {project_name}")
    print(f"[Canary] DB arcs: {len(app.current_project.db.load_anchor('arcs') or [])}")

    # --- Run Stage 2 ---
    from modules.core.stage2_context import Stage2Context

    app._stage2_orch.ctx = Stage2Context.from_app(app)

    print(f"[Canary] Starting Stage 2 (target_arc_count={target_arc_count})...")
    t0 = time.time()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                app._stage2_orch.stage_2_arcs_async_logic(target_arc_count=target_arc_count),
            )
            future.result(timeout=1200)
    else:
        asyncio.run(
            app._stage2_orch.stage_2_arcs_async_logic(target_arc_count=target_arc_count),
        )

    elapsed = time.time() - t0
    print(f"\n[Canary] Stage 2 completed in {elapsed:.1f}s")

    # Sync state tracker back
    _s2_ctx = app._stage2_orch.ctx
    if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
        app.state_tracker = _s2_ctx.state_tracker
    app._state_tracker_loaded_arcs = getattr(_s2_ctx, "state_tracker_loaded_arcs", 0)

    # --- Report ---
    arcs = app.current_project.db.load_anchor("arcs") or []
    print(f"[Canary] Final arc count: {len(arcs)}")
    for arc in arcs:
        arc_no = arc.get("arc_no", "?")
        inv = arc.get("joint_docs", {}).get("physical_inventory", [])
        start_eq = arc.get("state_constraints", {}).get("arc_start_state", {}).get("equipment", [])
        print(f"  Arc {arc_no}: inventory={len(inv) if isinstance(inv, list) else '?'} items, "
              f"start_equipment={len(start_eq) if isinstance(start_eq, list) else '?'} items")

    print("\n[Canary] Run complete. Inspect DB and artifacts for forward consistency.")


if __name__ == "__main__":
    main()
