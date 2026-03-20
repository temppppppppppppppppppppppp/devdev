"""[L3] Stage4 3-episode smoke test with Blueprint input and mocked LLM seams."""

from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from modules.core.db_manager import DBManager
from modules.core.stage4_context import Stage4Context
from modules.core.stage4_orchestrator import Stage4Orchestrator, _RoundOutcome, _SessionConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "\ucf54\ub371\uc2a4_\ud14c\uc2a4\ud2b8"
REAL_PROJECT_DB = PROJECT_ROOT / "projects" / PROJECT_NAME / "project_data.db"

MOCK_MANUSCRIPT = (
    "\uc2dc\uc724\uc740 \ubaa8\ub2c8\ud130 \uc55e\uc5d0\uc11c \uc22b\uc790 \ud750\ub984\uc744 \ub530\ub77c\uac00\uba70 \ud638\ud761\uc744 \uace0\ub978\ub2e4. "
    "\ubc18\ub300 \ub9e4\ub9e4\uac00 \ubb34\ub108\uc9c0\uc790 \ud3ec\uc9c0\uc158\uc744 \uc808\ubc18\uc73c\ub85c \uc815\ub9ac\ud558\uace0 \ub9ac\uc2a4\ud06c \ud55c\ub3c4\ub97c \ub2e4\uc2dc \uc7ac\uc124\uc815\ud588\ub2e4. "
    "\ud300\uc6d0\ub4e4\uc740 \uc5ec\uc804\ud788 \ud749\ubd84\ud588\uc9c0\ub9cc \uc2dc\uc724\uc740 \uc9c0\ud45c\uc640 \ud604\uae08 \ud750\ub984\uc744 \ubd84\ub9ac\ud574 \ud310\ub2e8\ud588\uace0, "
    "\ub2e4\uc74c \ub9e4\uc218 \uc870\uac74\uc744 \ubc14\ub85c \ubb38\uc11c\ud654\ud574 \uacf5\uc720\ud588\ub2e4. "
) * 70


@contextmanager
def _noop_spinner(*_args, **_kwargs):
    """No-op spinner context for stage patches."""
    yield MagicMock(update_detail=MagicMock())


class _NoopReferenceAnchor:
    def __init__(self, *_args, **_kwargs):
        pass


def _normalize_arcs(raw_arcs: object) -> list[dict]:
    """Normalize arcs anchor to list[dict]."""
    if isinstance(raw_arcs, list):
        return [arc for arc in raw_arcs if isinstance(arc, dict)]
    if isinstance(raw_arcs, dict):
        values = [arc for arc in raw_arcs.values() if isinstance(arc, dict)]
        return sorted(values, key=lambda arc: arc.get("ep_start", 0) if isinstance(arc.get("ep_start"), int) else 0)
    return []


@pytest.fixture
def stage4_env(tmp_path):
    """Copied DB + bible/arcs preloaded + clean manuscripts table."""
    if not REAL_PROJECT_DB.exists():
        pytest.skip(f"Real project DB not found: {REAL_PROJECT_DB}")

    copied_db = tmp_path / "project_data.db"
    shutil.copy2(REAL_PROJECT_DB, copied_db)

    db = DBManager(copied_db)
    bible = db.load_anchor("bible")
    arcs = _normalize_arcs(db.load_anchor("arcs"))

    assert bible, "Bible is empty"
    assert len(arcs) >= 1, f"arcs must be >= 1, got {len(arcs)}"
    assert db.get_latest_blueprint_number() >= 3, "blueprints must be >= 3"

    db.cursor.execute("DELETE FROM manuscripts")
    db.conn.commit()

    output_dir = tmp_path / "drafts"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        yield {"db": db, "bible": bible, "arcs": arcs, "output_dir": output_dir}
    finally:
        db.close()


def _make_mock_project(db: DBManager, bible: dict, arcs: list[dict], output_dir: Path):
    """Assemble current_project mock with real DB-backed methods."""
    project = MagicMock()
    project.db = db
    project.get_blueprint = db.get_blueprint
    project.get_latest_episode_number = db.get_latest_episode_number
    project.arcs = arcs
    project.master_bible = bible
    project.genre = {"type": "investment", "name": "investment"}
    project.paths = MagicMock()
    project.paths.drafts = output_dir
    project.name = PROJECT_NAME
    project.load_v20_anchor = lambda key: db.load_anchor(key)
    return project


def _make_stage4_ctx(project) -> Stage4Context:
    """Build Stage4Context with minimal required callbacks and mocks."""
    ui = MagicMock()
    ui.log = MagicMock()
    ui.console = MagicMock()
    ui.console.clear = MagicMock()
    ui.title = MagicMock()

    sys_obj = MagicMock()
    sys_obj.guard = None
    sys_obj.hud = None
    sys_obj.api_client = MagicMock()

    return Stage4Context(
        ui=ui,
        current_project=project,
        agents={},
        sys=sys_obj,
        state_tracker=None,
        selected_genre={"type": "investment", "name": "investment"},
        perf_timer=MagicMock(),
        get_int_input=lambda *a, **kw: kw.get("default", 1),
        build_item_acquisition_timeline=lambda *a, **kw: "",
        load_narrative_summaries=lambda: "",
        get_protagonist_name=lambda: "\uc2dc\uc724",
        generate_narrative_summary=lambda *a, **kw: None,
        flush_audit_buffer=lambda: None,
        safe_commit=lambda: project.db.conn.commit(),
    )


def _mock_prepare_session(output_dir: Path, target_ep: int = 3) -> _SessionConfig:
    """S1 seam: immediately return a valid session config with mocked agents."""
    return _SessionConfig(
        chief_writer=MagicMock(),
        manuscript_validator=MagicMock(),
        consistency_validator=MagicMock(),
        blocking_validator=MagicMock(),
        continuity_validator=MagicMock(),
        s4_genre_type="investment",
        story_context="- \uc7a5\ub974: investment\n- \uc8fc\uc778\uacf5 \uc774\ub984: \uc2dc\uc724",
        style_guide="\uce74\ub9ac\uc2a4\ub9c8 \uc0ac\uc774\ubc84 \ubb38\ud3ec, 4K \uc774\uc0c1",
        target_ep=target_ep,
        output_dir=output_dir,
        v50_modules_available=False,
        total_planned_ep=3,
    )


def _mock_handle_round_outcome(*, round_ctx) -> _RoundOutcome:
    """S2 seam: always return PASS with a long manuscript."""
    next_ep = int(getattr(round_ctx, "next_ep", 1))
    return _RoundOutcome(
        final_manuscript=MOCK_MANUSCRIPT,
        final_title=f"{next_ep}\ud654 \uace8\ub4e0\ub8e8\ud2b8",
        final_state_updates={},
        should_return=False,
    )


def _make_slim_process_pass_result(db: DBManager, output_dir: Path):
    """S3 seam: persist only DB manuscript + txt file, skip heavy post-processing."""

    def _slim(
        *,
        next_ep: int,
        final_manuscript: str,
        final_title: str,
        **_kwargs,
    ) -> bool:
        db.save_manuscript(ep_num=next_ep, title=final_title, content=final_manuscript)
        db.conn.commit()
        out = output_dir / f"ep_{next_ep:04d}.txt"
        out.write_text(f"# {final_title}\n\n{final_manuscript}", encoding="utf-8")
        return True

    return _slim


def _build_orchestrator(stage4_env, *, target_ep: int = 3):
    """Create orchestrator with all required seam/context mocks injected."""
    db = stage4_env["db"]
    output_dir = stage4_env["output_dir"]

    project = _make_mock_project(db, stage4_env["bible"], stage4_env["arcs"], output_dir)
    ctx = _make_stage4_ctx(project)
    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)

    orch._prepare_stage4_session = lambda **_kw: _mock_prepare_session(output_dir, target_ep=target_ep)
    orch._handle_round_outcome = _mock_handle_round_outcome

    slim_process = MagicMock(side_effect=_make_slim_process_pass_result(db, output_dir))
    orch._post_processor = MagicMock()
    orch._post_processor.process_pass_result = slim_process
    orch._post_processor.run_post_episode_tasks = MagicMock()

    orch._context_builder = MagicMock()
    orch._context_builder.prepare_episode_context.return_value = {
        "arc_pos": 1,
        "total_ep_in_arc": 10,
        "arc_tactical": "",
        "prev_text": "",
        "prev_ending": "",
        "prev_manuscripts_text": "",
        "episode_digest": "",
        "hud_report": "",
        "current_inventory": [],
        "current_martial_arts": [],
        "cumulative_bible": {},
        "dead_npcs": [],
        "item_acquisition_timeline": "",
        "chain_link_section": "",
        "world_state_summary": "",
    }
    orch._context_builder.build_mandatory_context.return_value = {
        "reference_anchor_prompt": "",
        "mandatory_context": "",
        "anti_trope_prompt": "",
        "justification_prompt": "",
        "reflexion_prompt": "",
    }
    orch._context_builder.build_round_context.side_effect = lambda **kwargs: SimpleNamespace(next_ep=kwargs["next_ep"])

    return orch, db, output_dir, slim_process


@patch("modules.core.reference_anchor.ReferenceAnchor", _NoopReferenceAnchor)
@patch("modules.core.spinners.StageSpinner", _noop_spinner)
def test_stage4_smoke_3ep(stage4_env):
    """Stage4 smoke should produce 3 manuscripts from blueprints without crashes."""
    orch, db, output_dir, slim_process = _build_orchestrator(stage4_env, target_ep=3)

    orch.stage_4_v2_chief_writer(limit_mode=False)

    for ep in range(1, 4):
        manuscript = db.get_manuscript(ep)
        assert manuscript is not None, f"ep{ep} manuscript missing"
        assert len(manuscript["content"]) >= 4000, f"ep{ep} manuscript too short: {len(manuscript['content'])}"
        assert "\uc2dc\uc724" in manuscript["content"], f"ep{ep} protagonist name missing"

    for ep in range(1, 4):
        file_path = output_dir / f"ep_{ep:04d}.txt"
        assert file_path.exists(), f"{file_path.name} missing"
        assert len(file_path.read_text(encoding="utf-8")) >= 4000

    assert db.get_latest_episode_number() == 4
    assert slim_process.call_count == 3


@patch("modules.core.reference_anchor.ReferenceAnchor", _NoopReferenceAnchor)
@patch("modules.core.spinners.StageSpinner", _noop_spinner)
def test_stage4_loop_termination(stage4_env):
    """Loop should stop at target episode boundary."""
    orch, db, _output_dir, slim_process = _build_orchestrator(stage4_env, target_ep=2)
    orch.ctx.session_logger = MagicMock()
    orch.ctx.audit_event = MagicMock()

    orch.stage_4_v2_chief_writer(limit_mode=False)

    assert db.get_manuscript(1) is not None
    assert db.get_manuscript(2) is not None
    assert db.get_manuscript(3) is None
    assert db.get_latest_episode_number() == 3
    assert slim_process.call_count == 2
    orch.ctx.session_logger.log_decision.assert_called_once()
    decision_kwargs = orch.ctx.session_logger.log_decision.call_args.kwargs
    assert decision_kwargs["stage"] == "stage4_control"
    assert decision_kwargs["decision_type"] == "target_ep_reached"
    assert decision_kwargs["ep_num"] == 2
    assert decision_kwargs["next_ep"] == 3
    assert any(call.args[0] == "target_ep_reached" for call in orch.ctx.audit_event.call_args_list)


@patch("modules.core.reference_anchor.ReferenceAnchor", _NoopReferenceAnchor)
@patch("modules.core.spinners.StageSpinner", _noop_spinner)
def test_stage4_no_blueprint_stops(stage4_env):
    """Loop should stop immediately when no blueprint is available."""
    db = stage4_env["db"]
    db.cursor.execute("DELETE FROM blueprints")
    db.conn.commit()

    orch, db, _output_dir, slim_process = _build_orchestrator(stage4_env, target_ep=3)

    orch.stage_4_v2_chief_writer(limit_mode=False)

    assert db.get_manuscript(1) is None
    assert db.get_latest_episode_number() == 1
    assert slim_process.call_count == 0


@patch("modules.core.reference_anchor.ReferenceAnchor", _NoopReferenceAnchor)
@patch("modules.core.spinners.StageSpinner", _noop_spinner)
def test_stage4_session_none_returns(stage4_env):
    """Session prep returning None should exit gracefully without writes."""
    db = stage4_env["db"]
    project = _make_mock_project(db, stage4_env["bible"], stage4_env["arcs"], stage4_env["output_dir"])
    ctx = _make_stage4_ctx(project)
    orch = Stage4Orchestrator(app=MagicMock(), context=ctx)
    orch._prepare_stage4_session = lambda **_kw: None

    orch.stage_4_v2_chief_writer(limit_mode=False)

    assert db.get_manuscript(1) is None
