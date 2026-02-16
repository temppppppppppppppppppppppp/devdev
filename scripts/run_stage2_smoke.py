"""Stage 2 mock smoke runner for the 코덱스_테스트 project.

This script runs Stage 2 with mocked LLM agents for 3 blocks, persists results
to the real project DB, and exports arc JSON files under plans/arcs/.

Usage:
    python scripts/run_stage2_smoke.py
"""

from __future__ import annotations

import asyncio
import builtins
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager  # noqa: E402
from modules.core.slack_bot import notifier  # noqa: E402
from modules.core.stage2_context import Stage2Context  # noqa: E402
from modules.core.stage2_orchestrator import Stage2Orchestrator  # noqa: E402
from modules.domain.agents.state_tracker import StateTracker  # noqa: E402

PROJECT_NAME = "\ucf54\ub371\uc2a4_\ud14c\uc2a4\ud2b8"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME
DB_PATH = PROJECT_DIR / "project_data.db"
ARCS_OUTPUT_DIR = PROJECT_DIR / "plans" / "arcs"


def _normalize_block_content(block: object) -> dict[str, str]:
    """Normalize roadmap block to flat content keys."""
    if not isinstance(block, dict):
        return {"context": str(block), "event_villain": "", "solution": "", "reward": ""}

    source = block.get("content", block)
    if not isinstance(source, dict):
        return {"context": str(source), "event_villain": "", "solution": "", "reward": ""}

    return {
        "context": str(source.get("context", "")),
        "event_villain": str(source.get("event_villain", "")),
        "solution": str(source.get("solution", "")),
        "reward": str(source.get("reward", "")),
    }


def _build_tactical_doc(arc_no: int, block_title: str, content: dict[str, str]) -> str:
    """Build a readable tactical_doc JSON string that includes real treatment text."""
    episodes = []
    for i in range(10):
        ep_no = (arc_no - 1) * 10 + i + 1
        episodes.append(
            {
                "ep_no": ep_no,
                "title": f"에피소드 {ep_no}",
                "summary": (
                    f"{content['context'][:120]} | 갈등: {content['event_villain'][:100]} | "
                    f"해결: {content['solution'][:100]} | 보상: {content['reward'][:100]}"
                ),
            }
        )

    tactical_payload = {
        "arc_title": f"골든루트 Arc {arc_no}",
        "block_title": block_title,
        "context": content["context"],
        "event_villain": content["event_villain"],
        "solution": content["solution"],
        "reward": content["reward"],
        "episodes": episodes,
        "detailed_progression": [
            {
                "phase": idx + 1,
                "detail": (
                    f"한시윤의 선택과 실행을 따라 투자 전개를 누적한다. "
                    f"핵심 맥락: {content['context'][:90]} / 장애: {content['event_villain'][:80]} / "
                    f"해결: {content['solution'][:80]} / 보상: {content['reward'][:80]}"
                ),
            }
            for idx in range(24)
        ],
    }
    return json.dumps(tactical_payload, ensure_ascii=False, indent=2)


def make_mock_arc(arc_no: int, block: object) -> dict:
    """Return a Stage2-valid arc payload for a given roadmap block."""
    content = _normalize_block_content(block)
    block_title = ""
    if isinstance(block, dict):
        block_title = str(block.get("title", f"Block {arc_no}"))
    if not block_title:
        block_title = f"Block {arc_no}"

    ep_start = (arc_no - 1) * 10 + 1
    ep_end = arc_no * 10

    return {
        "arc_no": arc_no,
        "global_arc_no": arc_no,
        "ep_start": ep_start,
        "ep_end": ep_end,
        "ep_count": 10,
        "title": f"Arc {arc_no} - {block_title}",
        "tactical_doc": _build_tactical_doc(arc_no, block_title, content),
        "key_events": [f"Arc {arc_no} 핵심 이벤트", "투자 의사결정", "시장 반격"],
        "beat_sequence": [
            f"Arc {arc_no} 도입: {content['context'][:60]}",
            f"Arc {arc_no} 갈등: {content['event_villain'][:60]}",
            f"Arc {arc_no} 해결: {content['solution'][:60]}",
            f"Arc {arc_no} 보상: {content['reward'][:60]}",
            f"Arc {arc_no} 후속 떡밥",
        ],
        "state_constraints": {
            "arc_start_state": {"location": "seoul"},
            "arc_end_state": {"location": "market", "equipment": ["ledger"], "injuries": "normal"},
            "protagonist_items": ["ledger"],
            "items_consumed": [],
            "relationship_changes": [],
            "power_changes": {},
            "foreshadowings": [],
            "continuity_checkpoints": [],
        },
        "joint_docs": {
            "final_location": "market",
            "physical_inventory": ["ledger"],
            "world_joint": "stable",
        },
        "status_shadow": {
            "internal_energy_loss": "0%",
            "expected_injuries": "none",
            "item_consumption": [],
        },
        "constraint_summary": "사망 NPC 없음",
        "hybrid_composition": {"primary": "momentum", "secondary": ["continuity"], "mixing_logic": "smoke"},
        "state_changes": {
            "npc_deaths": [],
            "relationship_changes": [],
            "npc_personality_changes": [],
            "skill_acquisitions": [],
            "major_items": [],
        },
        "content": content,
    }


async def run_stage2_smoke() -> None:
    """Run Stage2 on real DB with mocked agents and export resulting arcs."""
    assert DB_PATH.exists(), f"DB not found: {DB_PATH}"
    ARCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    db = DBManager(DB_PATH)
    original_input = builtins.input

    try:
        bible = db.load_anchor("bible")
        assert bible, "Bible is empty"
        mb = bible.get("MasterBible", bible) if isinstance(bible, dict) else {}
        roadmap = mb.get("plot_roadmap", []) if isinstance(mb, dict) else []
        assert isinstance(roadmap, list) and len(roadmap) >= 3, f"plot_roadmap length is {len(roadmap)}"
        print(f"[OK] Bible load complete: plot_roadmap {len(roadmap)} blocks")

        # Silence optional external side effects.
        notifier.send_notification = lambda *args, **kwargs: None
        builtins.input = lambda *args, **kwargs: ""

        project = MagicMock()
        project.db = db
        project.name = PROJECT_NAME
        project.master_bible = bible
        project.volumes = []
        project.paths = MagicMock()
        project.paths.root = PROJECT_DIR
        project.save_v20_anchor = lambda key, value: db.save_anchor(key, value)
        project.load_v20_anchor = (
            lambda key, default=None: default if db.load_anchor(key) is None else db.load_anchor(key)
        )

        ui = MagicMock()
        ui.log = MagicMock()
        ui.console = MagicMock()
        ui.menu = MagicMock(return_value="3")

        sys_mock = MagicMock()
        sys_mock.api_client = MagicMock()
        sys_mock.hud = MagicMock()
        sys_mock.hud.pro_root = mb.get("protagonist_config", {}) if isinstance(mb, dict) else {}
        sys_mock.lore = MagicMock()

        state_tracker = StateTracker()

        async def _safe_commit_async():
            db.conn.commit()

        async def _enrich_passthrough(curr_b, _prev_b, _next_b, _seeds, transfused_history=""):
            content = _normalize_block_content(curr_b)
            return {
                "content": content,
                "joint_docs": {
                    "final_location": "market",
                    "physical_inventory": ["ledger"],
                    "world_joint": "stable",
                },
                "status_shadow": {
                    "internal_energy_loss": "0%",
                    "expected_injuries": "none",
                    "item_consumption": [],
                },
                "block_theme": content["context"][:60],
                "joint_docs_meta": {"transfused_history": transfused_history[:80]},
            }

        def _generate_four_phase(**kwargs):
            arc_no = int(kwargs.get("arc_no", 1))
            curr_block = kwargs.get("curr_block", roadmap[min(max(arc_no - 1, 0), len(roadmap) - 1)])
            return make_mock_arc(arc_no, curr_block), {"final_verdict": "PASS", "retries": 0}

        analyst = MagicMock()
        analyst.enrich_raw_block_async = AsyncMock(side_effect=_enrich_passthrough)
        analyst.stitch_joints = MagicMock(return_value={"status": "OK"})
        analyst.get_lack_report = MagicMock(return_value={"status": "ok", "martial_deficit": "none"})
        analyst.plan_single_arc_v20 = MagicMock(
            side_effect=lambda **kwargs: make_mock_arc(
                int(kwargs.get("arc_no", 1)),
                roadmap[min(max(int(kwargs.get("arc_no", 1)) - 1, 0), len(roadmap) - 1)],
            )
        )

        weaver = MagicMock()
        weaver.generate_arc_drive = MagicMock(return_value={"desire_vector": "stable", "status": "ok"})

        four_phase = MagicMock()
        four_phase.generate = MagicMock(side_effect=_generate_four_phase)

        director = MagicMock()
        director.audit_strategic_plan = MagicMock(return_value={"decision": "PASS", "score": 82, "reason": "mock ok"})
        director.ask = MagicMock(return_value="ok")

        agents = {
            "analyst": analyst,
            "weaver": weaver,
            "four_phase": four_phase,
            "four_phase_arc_generator": four_phase,
            "director": director,
        }

        ctx = Stage2Context(
            ui=ui,
            current_project=project,
            agents=agents,
            sys=sys_mock,
            state_tracker=state_tracker,
            selected_genre={"type": "investment", "name": "investment"},
            stage_rejection_history=[],
            audit_event=lambda *a, **k: None,
            write_audit_summary=lambda *a, **k: None,
            validate_arc_mapping=lambda arc, *_args, **_kwargs: arc,
            validate_arc_integrity=lambda arc: bool(arc and arc.get("arc_no")),
            safe_commit_async=_safe_commit_async,
            get_max_episode_from_manuscripts=lambda: 0,
            get_int_input=lambda _prompt, **_kw: 3,
            generate_structured_arc_feedback=lambda **_kw: "",
            generate_reverse_feedback_stage3_to_2=lambda **_kw: "",
            fix_entity_registry_protagonist=lambda registry, _name: registry,
            calculate_arc_from_episode=lambda _ep: 0,
            build_strong_kind_feedback=lambda **_kw: "",
            build_minimal_arc_context=lambda *_a, **_k: "",
            build_focused_context=lambda **_kw: "",
            analyze_rejection_pattern_v60=lambda *_a, **_k: "",
            get_adaptive_feedback_intensity=lambda *_a, **_k: {"guidance": "retry"},
            generate_arc_context_v60=lambda _arcs, _arc_no: "",
        )

        app = MagicMock()
        app._state_tracker_loaded_arcs = 0
        app.state_tracker = state_tracker

        print("[RUN] Stage 2 start (3 blocks, mock LLM)...")
        orchestrator = Stage2Orchestrator(app=app, context=ctx)
        await orchestrator.stage_2_arcs_async_logic()
        print("[OK] Stage 2 complete")

        saved_arcs = db.load_anchor("arcs")
        if not isinstance(saved_arcs, list) or not saved_arcs:
            print("[WARN] arcs empty after Stage2. Fallback to manual save mode.")
            manual_arcs = [make_mock_arc(i + 1, roadmap[i]) for i in range(3)]
            db.save_anchor("arcs", manual_arcs)
            saved_arcs = manual_arcs
            print(f"[OK] fallback saved {len(manual_arcs)} arcs into DB")

        # Export arcs to JSON files.
        for arc in saved_arcs:
            if not isinstance(arc, dict):
                continue
            arc_no = int(arc.get("arc_no", 0))
            if arc_no <= 0:
                continue
            out_path = ARCS_OUTPUT_DIR / f"arc_{arc_no}.json"
            out_path.write_text(json.dumps(arc, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[FILE] saved {out_path.name}")

        print(f"[DONE] arcs={len(saved_arcs)} in DB and JSON at {ARCS_OUTPUT_DIR}")
    finally:
        builtins.input = original_input
        db.close()


def main() -> None:
    asyncio.run(run_stage2_smoke())


if __name__ == "__main__":
    main()
