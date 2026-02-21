"""[L3] Stage3 3-episode smoke test using copied real project DB + mocked LLM agents."""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.core.db_manager import DBManager
from modules.core.stage3_context import Stage3Context
from modules.core.stage3_orchestrator import Stage3Orchestrator
from modules.models.blueprint import Blueprint

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "\ucf54\ub371\uc2a4_\ud14c\uc2a4\ud2b8"
REAL_PROJECT_DB = PROJECT_ROOT / "projects" / PROJECT_NAME / "project_data.db"


@contextmanager
def _noop_spinner(*_args, **_kwargs):
    yield


def _normalize_arcs(raw_arcs: object) -> list[dict]:
    """Normalize arcs loaded from DB anchor to a list[dict]."""
    if isinstance(raw_arcs, list):
        return [arc for arc in raw_arcs if isinstance(arc, dict)]
    if isinstance(raw_arcs, dict):
        values = [arc for arc in raw_arcs.values() if isinstance(arc, dict)]
        return sorted(values, key=lambda arc: arc.get("ep_start", 0) if isinstance(arc.get("ep_start"), int) else 0)
    return []


@pytest.fixture
def stage3_env(tmp_path):
    """Stage3 smoke environment with copied DB + bible/arcs loaded."""
    if not REAL_PROJECT_DB.exists():
        pytest.skip(f"Real project DB not found: {REAL_PROJECT_DB}")

    copied_db = tmp_path / "project_data.db"
    shutil.copy2(REAL_PROJECT_DB, copied_db)

    db = DBManager(copied_db)
    bible = db.load_anchor("bible")
    arcs = _normalize_arcs(db.load_anchor("arcs"))

    assert bible, "Bible is empty"
    assert len(arcs) >= 3, f"arcs must be >= 3, got {len(arcs)}"

    # Keep fixture deterministic even if source DB already has blueprints.
    db.cursor.execute("DELETE FROM blueprints")
    db.conn.commit()

    try:
        yield {"db": db, "bible": bible, "arcs": arcs}
    finally:
        db.close()


def _make_mock_blueprint(ep_num: int, arc_data: dict | None = None) -> dict:
    """Create a valid Blueprint payload through the Pydantic model."""
    content = arc_data.get("content", {}) if isinstance(arc_data, dict) else {}
    if not isinstance(content, dict):
        content = {}

    context = str(content.get("context", "market pressure rises"))
    villain = str(content.get("event_villain", "liquidity crunch"))
    solution = str(content.get("solution", "risk control execution"))
    reward = str(content.get("reward", "capital recovery"))

    return Blueprint(
        episode_number=ep_num,
        integrated_scenario=f"Episode {ep_num}: {context[:120]}",
        scene_breakdown={
            "scene_1": {"summary": context[:100], "location": "office"},
            "scene_2": {"summary": villain[:100], "location": "exchange"},
            "scene_3": {"summary": solution[:100], "location": "war-room"},
            "scene_4": {"summary": reward[:100], "location": "office"},
        },
        pacing_notes="fast, escalating pressure",
        target_beat=f"arc pressure episode {ep_num}",
        core_tension=villain[:80],
        expected_ending=reward[:80],
        start_location="office",
        location="office",
    ).model_dump()


def _build_mock_app(db: DBManager, bible: dict, arcs: list[dict]) -> MagicMock:
    """Build a MagicMock app that satisfies Stage3Orchestrator runtime dependencies."""
    app = MagicMock()
    app.ui = MagicMock()
    app.ui.log = MagicMock()

    project = MagicMock()
    project.db = db
    project.arcs = arcs
    project.master_bible = bible
    project.name = PROJECT_NAME

    generated_blueprints: dict[int, dict] = {}

    def _get_blueprint(ep_num: int):
        return generated_blueprints.get(ep_num)

    def _save_blueprint(ep_num: int, bp_data: dict):
        generated_blueprints[ep_num] = bp_data
        db.save_blueprint(ep_num, bp_data)

    project.get_blueprint = MagicMock(side_effect=_get_blueprint)
    project.save_episode_blueprint = MagicMock(side_effect=_save_blueprint)
    project._generated_blueprints = generated_blueprints

    app.current_project = project

    app.current_project.db.get_latest_blueprint_number = MagicMock(return_value=0)
    app._get_max_episode_from_manuscripts = MagicMock(return_value=0)
    app._get_int_input = MagicMock(
        side_effect=lambda _prompt, default=None, min_val=1, max_val=3, **_kw: min(max_val, min_val + 2)
    )

    def _get_arc_context_for_episode(ep_num: int):
        for idx, arc in enumerate(arcs):
            ep_start = arc.get("ep_start")
            ep_end = arc.get("ep_end")
            if isinstance(ep_start, int) and isinstance(ep_end, int) and ep_start <= ep_num <= ep_end:
                return idx, arc
        return None, None

    app._get_arc_context_for_episode = MagicMock(side_effect=_get_arc_context_for_episode)
    app._validate_arc_data_fields = MagicMock(side_effect=lambda arc, _idx: arc)
    app._validate_blueprint_integrity = MagicMock(
        side_effect=lambda bp: isinstance(bp, dict)
        and isinstance(bp.get("integrated_scenario"), str)
        and isinstance(bp.get("scene_breakdown"), dict)
    )
    app._get_protagonist_name = MagicMock(return_value="\uc2dc\uc724")
    app._fix_entity_registry_protagonist = MagicMock(side_effect=lambda registry, _name: registry)
    app._safe_commit = MagicMock(side_effect=lambda: db.conn.commit() or True)
    app._audit_event = MagicMock()
    app._write_audit_summary = MagicMock()

    app.selected_genre = {"type": "investment", "name": "investment"}
    app.state_tracker = MagicMock()
    app.world_state = MagicMock()
    app.fact_ledger = MagicMock()
    app.preset_registry = MagicMock()
    app.sys = MagicMock()
    app.sys.api_client = MagicMock()

    def _mock_generate(**kwargs):
        ep_num = int(kwargs.get("ep_num", 1))
        arc_data = kwargs.get("arc_data", {})
        blueprint = _make_mock_blueprint(ep_num, arc_data if isinstance(arc_data, dict) else None)
        result = {
            "final_verdict": "PASS",
            "phases": {
                "generate": {
                    "selected_strategy": "momentum",
                    "selected_score": 85,
                }
            },
        }
        return blueprint, result

    app.agents = {
        "three_phase_bp": MagicMock(
            generate=MagicMock(side_effect=_mock_generate),
            get_stats=MagicMock(return_value={"pass_rate": "100%"}),
        ),
        "director": MagicMock(),
        "state_extractor": MagicMock(
            extract_cumulative_state=MagicMock(return_value={"entity_registry": {"characters": [{"name": "mentor"}]}})
        ),
    }

    return app


class TestL3Stage3Setup:
    def test_arcs_loaded(self, stage3_env):
        assert len(stage3_env["arcs"]) >= 3

    def test_arc_structure(self, stage3_env):
        arc = stage3_env["arcs"][0]
        assert isinstance(arc.get("ep_start"), int)
        assert isinstance(arc.get("ep_end"), int)
        assert arc["ep_start"] < arc["ep_end"]

    def test_bible_has_plot_roadmap(self, stage3_env):
        bible = stage3_env["bible"]
        mb = bible.get("MasterBible", bible) if isinstance(bible, dict) else {}
        assert isinstance(mb, dict)
        assert "plot_roadmap" in mb


class TestL3Stage3Pipeline:
    @patch("modules.core.spinners.StageSpinner", _noop_spinner)
    def test_stage3_runs_3_episodes(self, stage3_env):
        db = stage3_env["db"]
        app = _build_mock_app(db, stage3_env["bible"], stage3_env["arcs"])
        ctx = Stage3Context.from_app(app)

        orchestrator = Stage3Orchestrator(app=app, context=ctx)
        orchestrator.stage_3_batch_blueprinting()

        assert app.current_project.save_episode_blueprint.call_count == 3
        assert app.agents["three_phase_bp"].generate.call_count == 3
        assert db.get_blueprint(1) is not None
        assert db.get_blueprint(2) is not None
        assert db.get_blueprint(3) is not None
        app._write_audit_summary.assert_called_once_with("stage3_complete")

    @patch("modules.core.spinners.StageSpinner", _noop_spinner)
    def test_blueprint_content_valid(self, stage3_env):
        db = stage3_env["db"]
        app = _build_mock_app(db, stage3_env["bible"], stage3_env["arcs"])
        ctx = Stage3Context.from_app(app)

        orchestrator = Stage3Orchestrator(app=app, context=ctx)
        orchestrator.stage_3_batch_blueprinting()

        for ep_num in (1, 2, 3):
            bp_data = db.get_blueprint(ep_num)
            assert isinstance(bp_data, dict), f"ep {ep_num}: blueprint missing"
            assert "integrated_scenario" in bp_data, f"ep {ep_num}: missing integrated_scenario"
            assert "scene_breakdown" in bp_data, f"ep {ep_num}: missing scene_breakdown"
            assert isinstance(bp_data["scene_breakdown"], dict), f"ep {ep_num}: scene_breakdown must be dict"
