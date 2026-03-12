"""[L3] Stage2 3-block smoke test using copied real project DB + mocked LLM agents."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from modules.core.db_manager import DBManager
from modules.core.stage2_context import Stage2Context
from modules.core.stage2_orchestrator import Stage2Orchestrator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_PROJECT_DB = PROJECT_ROOT / "projects" / "코덱스_테스트" / "project_data.db"


@pytest.fixture
def test_db(tmp_path):
    """Copy real project DB to temp path so the source DB is never modified."""
    if not REAL_PROJECT_DB.exists():
        pytest.skip(f"Real project DB not found: {REAL_PROJECT_DB}")

    copied_db = tmp_path / "project_data.db"
    shutil.copy2(REAL_PROJECT_DB, copied_db)

    db = DBManager(copied_db)
    # Keep fixture deterministic even if the source project already contains arcs.
    db.save_anchor("arcs", {})
    try:
        yield db
    finally:
        db.close()


def _build_mock_arc(arc_no: int, ep_start: int, source_block: dict) -> dict:
    """Build a Stage2-valid arc payload."""
    content = source_block.get("content", {}) if isinstance(source_block, dict) else {}
    block_title = source_block.get("title", f"block-{arc_no}") if isinstance(source_block, dict) else f"block-{arc_no}"
    context_seed = content.get("context", "") if isinstance(content, dict) else ""

    tactical_seed = f"arc {arc_no} {block_title} {context_seed[:80]}".strip()
    tactical_doc = ((tactical_seed + " detailed progression and consequence sentence. ") * 120).strip()

    return {
        "arc_no": arc_no,
        "global_arc_no": arc_no,
        "ep_start": ep_start,
        "ep_end": ep_start + 3,
        "ep_count": 4,
        "title": f"Arc {arc_no}",
        "tactical_doc": tactical_doc,
        "beat_sequence": [
            f"arc {arc_no} beat one conflict escalates with concrete action",
            f"arc {arc_no} beat two pressure rises with external consequence",
            f"arc {arc_no} beat three strategic response triggers new cost",
            f"arc {arc_no} beat four reversal creates urgent tactical decision",
            f"arc {arc_no} beat five closes with forward hook and payoff",
        ],
        "state_constraints": {
            "arc_start_state": {"location": "office"},
            "arc_end_state": {
                "location": "market",
                "equipment": ["ledger"],
                "injuries": "normal",
                "internal_energy": 90,
            },
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
            "internal_energy_loss": "5%",
            "expected_injuries": "none",
            "item_consumption": [],
        },
        "constraint_summary": "none",
        "hybrid_composition": {
            "primary": "momentum",
            "secondary": ["continuity"],
            "mixing_logic": "smoke",
        },
        "state_changes": {
            "npc_deaths": [],
            "skill_acquisitions": [],
            "relationship_changes": [],
            "major_items": [],
        },
        "content": {
            "context": content.get("context", ""),
            "event_villain": content.get("event_villain", ""),
            "solution": content.get("solution", ""),
            "reward": content.get("reward", ""),
        },
    }


async def _run_stage2_three_blocks(db: DBManager, monkeypatch) -> dict:
    """Run Stage2 with mocked agents and return basic execution stats."""
    bible = db.load_anchor("bible")
    mb = bible.get("MasterBible", bible) if isinstance(bible, dict) else {}
    plot_roadmap = mb.get("plot_roadmap", []) if isinstance(mb, dict) else []

    # Avoid terminal blocking at end-of-stage and any retry prompt path.
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: "")

    # Silence Slack notifier side effects during smoke run.
    from modules.core.slack_bot import notifier

    monkeypatch.setattr(notifier, "send_notification", lambda *args, **kwargs: None)

    project = MagicMock()
    project.db = db
    project.name = "코덱스_테스트_l3_3block_smoke"
    project.master_bible = bible
    project.volumes = []
    project.paths = MagicMock()
    project.paths.root = REAL_PROJECT_DB.parent

    def _save_v20_anchor(key, value):
        db.save_anchor(key, value)

    def _load_v20_anchor(key, default=None):
        value = db.load_anchor(key)
        return default if value is None else value

    project.save_v20_anchor = _save_v20_anchor
    project.load_v20_anchor = _load_v20_anchor

    mock_ui = MagicMock()
    mock_ui.log = MagicMock()
    mock_ui.console = MagicMock()
    mock_ui.menu = MagicMock(return_value="3")

    mock_sys = MagicMock()
    mock_sys.api_client = MagicMock()
    mock_sys.hud = MagicMock()
    mock_sys.hud.pro_root = mb.get("protagonist_config", {}) if isinstance(mb, dict) else {}
    mock_sys.lore = MagicMock()

    async def _safe_commit_async():
        db.conn.commit()

    async def _enrich_passthrough(curr_b, _prev_b, _next_b, _seeds, transfused_history=""):
        payload = curr_b if isinstance(curr_b, dict) else {"context": str(curr_b)}
        return {
            "content": {
                "context": payload.get("context", ""),
                "event_villain": payload.get("event_villain", ""),
                "solution": payload.get("solution", ""),
                "reward": payload.get("reward", ""),
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
            "block_theme": payload.get("context", "")[:60],
            "joint_docs_meta": {"transfused_history": transfused_history[:80]},
        }

    def _generate_four_phase(**kwargs):
        arc_no = int(kwargs.get("arc_no", 1))
        ep_start = int(kwargs.get("ep_start", ((arc_no - 1) * 5) + 1))
        curr_block = kwargs.get("curr_block", {})
        return _build_mock_arc(arc_no, ep_start, curr_block), {"final_verdict": "PASS", "retries": 0}

    mock_analyst = MagicMock()
    mock_analyst.enrich_raw_block_async = AsyncMock(side_effect=_enrich_passthrough)
    mock_analyst.stitch_joints = MagicMock(return_value={"status": "OK"})
    mock_analyst.get_lack_report = MagicMock(return_value={"status": "ok", "martial_deficit": "none"})
    mock_weaver = MagicMock()
    mock_weaver.generate_arc_drive = MagicMock(return_value={"desire_vector": "stable", "status": "ok"})

    mock_four_phase = MagicMock()
    mock_four_phase.generate = MagicMock(side_effect=_generate_four_phase)

    mock_director = MagicMock()
    mock_director.audit_strategic_plan = MagicMock(return_value={"decision": "PASS", "score": 95, "reason": "ok"})
    mock_director.ask = MagicMock(return_value="ok")

    agents = {
        "analyst": mock_analyst,
        "weaver": mock_weaver,
        "four_phase": mock_four_phase,
        "four_phase_arc_generator": mock_four_phase,  # alias for compatibility
        "director": mock_director,
    }

    ctx = Stage2Context(
        ui=mock_ui,
        current_project=project,
        agents=agents,
        sys=mock_sys,
        state_tracker=None,
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
    app.state_tracker = None

    orch = Stage2Orchestrator(app=app, context=ctx)
    await orch.stage_2_arcs_async_logic()

    saved_arcs = db.load_anchor("arcs")
    return {
        "saved_arcs": saved_arcs,
        "enrich_calls": mock_analyst.enrich_raw_block_async.call_count,
        "four_phase_calls": mock_four_phase.generate.call_count,
        "plot_blocks": len(plot_roadmap) if isinstance(plot_roadmap, list) else 0,
    }


class TestSetup:
    def test_bible_exists(self, test_db):
        """Bible and plot_roadmap should exist in copied real project DB."""
        bible = test_db.load_anchor("bible")
        assert bible, "Bible is empty"
        mb = bible.get("MasterBible", bible)
        assert isinstance(mb, dict)
        assert "plot_roadmap" in mb
        roadmap = mb["plot_roadmap"]
        assert isinstance(roadmap, list)
        assert len(roadmap) >= 3, f"plot_roadmap has only {len(roadmap)} blocks"

    def test_genre_is_investment(self, test_db):
        """Golden route bible should point to investment genre."""
        bible = test_db.load_anchor("bible")
        mb = bible.get("MasterBible", bible) if isinstance(bible, dict) else {}
        genre = bible.get("_genre", "") if isinstance(bible, dict) else ""
        has_finance_hud = isinstance(mb, dict) and ("FinanceHUD" in mb or "finance_hud" in mb)
        assert genre == "investment" or has_finance_hud

    def test_arcs_initially_empty(self, test_db):
        """Fixture should start with empty arcs before each smoke run."""
        arcs = test_db.load_anchor("arcs")
        assert not arcs, f"Expected empty arcs before run, got: {type(arcs).__name__} {arcs}"


class TestPipelineSmoke:
    def test_stage2_runs_3_blocks(self, test_db, monkeypatch):
        """Stage2 should run with 3-block input and save arc(s) without crash."""
        result = asyncio.run(_run_stage2_three_blocks(test_db, monkeypatch))

        saved_arcs = result["saved_arcs"]
        assert isinstance(saved_arcs, list)
        assert len(saved_arcs) >= 1
        assert result["plot_blocks"] >= 3
        assert result["enrich_calls"] >= 1
        assert result["four_phase_calls"] >= 1

    def test_saved_arc_structure_valid(self, test_db, monkeypatch):
        """Saved arcs should include Stage2 core fields."""
        result = asyncio.run(_run_stage2_three_blocks(test_db, monkeypatch))

        saved_arcs = result["saved_arcs"]
        assert isinstance(saved_arcs, list)
        assert len(saved_arcs) >= 1

        first_arc = saved_arcs[0]
        assert "arc_no" in first_arc
        assert "ep_start" in first_arc
        assert "ep_end" in first_arc
        assert "tactical_doc" in first_arc
        assert isinstance(first_arc["tactical_doc"], str)
        assert len(first_arc["tactical_doc"]) >= 100
