from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.constants import VolumeSettings
from modules.core.stage2_orchestrator import Stage2Orchestrator


def _make_ctx(arcs, calculate_arc_from_episode=None):
    ui = MagicMock()
    ui.log = MagicMock()
    return SimpleNamespace(
        ui=ui,
        current_project=SimpleNamespace(arcs=arcs),
        calculate_arc_from_episode=calculate_arc_from_episode,
    )


def _make_bootstrap_ctx():
    ui = MagicMock()
    ui.log = MagicMock()
    db = MagicMock()
    db.load_anchor.side_effect = lambda name: [] if name in {"volumes", "arcs"} else {}
    current_project = SimpleNamespace(
        master_bible={
            "_stage0_contract": {
                "artifact_role": "bi_projection_artifact",
                "projection_source": "treatment.blocks",
                "field_authority": {"plot_roadmap": "MasterBible.plot_roadmap"},
                "runtime_handoff": {"owner": "db_anchor:bible"},
            },
            "MasterBible": {
                "ProjectData": {"MetaInfo": {"grand_objective": "goal"}},
                "plot_roadmap": [
                    {
                        "block_no": 1,
                        "title": "Block 1",
                        "content": {
                            "context": "ctx",
                            "event_villain": "villain",
                            "solution": "solve",
                            "reward": "reward",
                        },
                    }
                ],
            },
        },
        volumes=[{"vol_no": 1, "strategy_doc": "vol"}],
        db=db,
        load_v20_anchor=MagicMock(return_value=None),
        save_v20_anchor=MagicMock(),
        arcs=[],
    )
    return SimpleNamespace(
        ui=ui,
        current_project=current_project,
        selected_genre={"type": "investment"},
        state_tracker_loaded_arcs=0,
        state_tracker=None,
        preset_registry=None,
        sys=SimpleNamespace(api_client=MagicMock()),
        world_state=None,
    )


def test_resolve_arc_number_for_episode_uses_actual_arc_boundaries_when_callback_missing():
    ctx = _make_ctx(
        arcs=[
            {"arc_no": 1, "ep_start": 1, "ep_end": 4},
            {"arc_no": 2, "ep_start": 5, "ep_end": 7},
            {"arc_no": 3, "ep_start": 8, "ep_end": 11},
        ]
    )
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    result = orch._resolve_arc_number_for_episode(5)

    assert result == 2
    ctx.ui.log.assert_any_call("⚠️ [Stage2] arc mapping callback 부재 - fallback 사용")


def test_resolve_arc_number_for_episode_falls_back_to_default_bucket_when_boundaries_missing():
    ctx = _make_ctx(arcs=[{"arc_no": 1, "ep_start": 1, "ep_end": 4}])
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    result = orch._resolve_arc_number_for_episode(9)

    expected = (9 - 1) // VolumeSettings.EPISODES_PER_ARC + 1
    assert result == expected


def test_fit_prompt_text_preserves_tail_context_for_failure_report():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx(arcs=[]))

    text = "HEAD-CONSTRAINT\n" + ("C" * 8000) + "\nTAIL-STAGE2-CONSTRAINT"
    result = orch._fit_prompt_text(text, 6000)

    assert "TAIL-STAGE2-CONSTRAINT" in result
    assert "...(중간 생략)..." in result


def test_compose_rejection_pattern_feedback_preserves_retry_advisories():
    orch = Stage2Orchestrator(app=MagicMock(), context=_make_ctx(arcs=[]))

    feedback = orch._compose_rejection_pattern_feedback(
        [
            {
                "reason": "carryover drift",
                "specific_issue": "restore bridge packet",
                "retry_directives": "repair only the state bridge",
                "runtime_advisory": "verify carryover authority before rewrite",
            }
        ],
        global_arc_no=4,
    )

    assert "carryover drift" in feedback
    assert "restore bridge packet" in feedback
    assert "repair only the state bridge" in feedback
    assert "verify carryover authority before rewrite" in feedback


def test_stage2_failure_report_source_normalizes_constraints_before_reporting():
    src = Path("modules/core/stage2_orchestrator.py").read_text(encoding="utf-8")

    assert "current_constraints = self._fit_prompt_text(" in src
    assert 'constraint_db.generate_constraint_block(global_arc_no) if constraint_db else "N/A"' in src


def test_bootstrap_stage2_arc_pipeline_surfaces_stage0_contract(monkeypatch):
    class DummyConstraintDB:
        def __init__(self, _project):
            self.arc_states = {}

    class DummyStateTracker:
        def __init__(self, preset_registry=None, llm_client=None):
            self.preset_registry = preset_registry
            self.llm_client = llm_client
            self.npc_registry = {}
            self.financial_number_registry = {}

        def bind_db(self, _db):
            return None

        def bind_world_state(self, _world_state):
            return None

        def full_extract_from_arcs(self, _arcs, genre=""):
            return None

        def export_financial_registry(self):
            return {}

    monkeypatch.setattr("modules.core.constraint_db.ConstraintDB", DummyConstraintDB)
    monkeypatch.setattr("modules.domain.agents.state_tracker.StateTracker", DummyStateTracker)

    ctx = _make_bootstrap_ctx()
    orch = Stage2Orchestrator(app=MagicMock(), context=ctx)

    result = orch._bootstrap_stage2_arc_pipeline(target_arc_count=1)

    assert result["ready"] is True
    log_messages = [call.args[0] for call in ctx.ui.log.call_args_list if call.args]
    assert any("[Stage0 Contract] runtime_handoff_owner=db_anchor:bible" in message for message in log_messages)
    assert any("stage2_consumer_mode=db_anchor_first" in message for message in log_messages)
    assert any("projection_source=treatment.blocks" in message for message in log_messages)
    assert any("force_sync_bridge=compatibility_bridge" in message for message in log_messages)
