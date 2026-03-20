from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.core.stage4_context_builder import Stage4ContextBuilder
from modules.domain.agents.continuity_manuscript import ContinuityManuscriptValidator
from modules.domain.agents.director_auditor import DirectorQualityAuditor
from modules.validation.blocking_validator import BlockingValidator
from modules.validation.scoring_validator import ScoringValidator


def _make_ctx():
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.current_project = MagicMock()
    ctx.current_project.db = MagicMock()
    ctx.current_project.master_bible = {}
    ctx.current_project.genre = {"name": "wuxia"}
    ctx.current_project.load_v20_anchor = MagicMock(return_value=None)
    ctx.world_state = None
    ctx.fact_ledger = None
    ctx.state_tracker = None
    ctx.memory = None
    ctx.foreshadow_tracker = None
    ctx.semantic_plot_guard = None
    ctx.load_narrative_summaries = MagicMock(return_value="")
    return ctx


def test_continuity_manuscript_llm_failure_marks_degraded(monkeypatch):
    inspector = SimpleNamespace(
        context=SimpleNamespace(master_bible={}),
        ask=MagicMock(side_effect=RuntimeError("llm timeout")),
        _extract_json_robust=MagicMock(),
        _format_entity_registry=MagicMock(return_value=""),
        _escape_braces=lambda x: x,
    )
    validator = ContinuityManuscriptValidator(inspector)
    monkeypatch.setattr(validator, "_manuscript_python_precheck", lambda *_a, **_k: {"warnings": []})

    result = validator.inspect_manuscript(
        current_ep=2,
        manuscript="x" * 600,
        blueprint={},
        prev_manuscripts=[{"ep_num": 1, "content": "prev"}],
    )

    assert result["decision"] == "PASS"
    assert result["severity"] == "MINOR"
    assert result["degraded"] is True
    assert isinstance(result.get("degraded_reason", ""), str) and result["degraded_reason"]


def test_continuity_manuscript_incarnation_extract_logs_warning(caplog):
    class _BadContext:
        @property
        def master_bible(self):
            raise RuntimeError("bad bible")

    inspector = SimpleNamespace(context=_BadContext())
    with caplog.at_level("WARNING"):
        validator = ContinuityManuscriptValidator(inspector)

    assert validator._incarnation_type == ""
    assert "incarnation_type" in caplog.text


def test_continuity_manuscript_prompt_preserves_tail_context(monkeypatch):
    inspector = SimpleNamespace(
        context=SimpleNamespace(master_bible={}),
        ask=MagicMock(return_value='{"decision":"PASS","severity":"NONE","violations":[],"warnings":[]}'),
        _extract_json_robust=MagicMock(
            return_value={"decision": "PASS", "severity": "NONE", "violations": [], "warnings": []}
        ),
        _format_entity_registry=MagicMock(return_value=""),
        _escape_braces=lambda x: x,
    )
    validator = ContinuityManuscriptValidator(inspector)
    monkeypatch.setattr(validator, "_manuscript_python_precheck", lambda *_a, **_k: {"warnings": []})
    monkeypatch.setattr(
        validator,
        "_format_prev_manuscripts",
        lambda _prev: "HEAD-PREV\n" + ("P" * 60000) + "\nTAIL-PREV-TIMELINE",
    )

    result = validator.inspect_manuscript(
        current_ep=4,
        manuscript="HEAD-MS\n" + ("M" * 5000) + "\nTAIL-CM",
        blueprint={"integrated_scenario": "HEAD-BP\n" + ("B" * 45000) + "\nTAIL-BP-SCENARIO"},
        prev_manuscripts=[{"ep_num": 3, "content": "prev"}],
    )

    assert result["decision"] == "PASS"
    prompt = inspector.ask.call_args.args[0]
    assert "TAIL-CM" in prompt
    assert "TAIL-PREV-TIMELINE" in prompt
    assert "TAIL-BP-SCENARIO" in prompt
    assert "...(중간 생략)..." in prompt


def test_director_auditor_genre_validation_error_sets_degraded():
    d = SimpleNamespace(guard=MagicMock(), genre="wuxia")
    d.guard.run_deep_validation.side_effect = ValueError("schema mismatch")
    auditor = DirectorQualityAuditor(d)

    result = auditor._run_genre_specific_validation("manuscript", ep_num=3)

    assert result["degraded"] is True
    assert result["summary"]
    assert result["feedback"]


def test_stage4_context_builder_mandatory_context_failure_has_fallback():
    cb = Stage4ContextBuilder(_make_ctx())
    anchor_sys = MagicMock()
    anchor_sys.get_relevant_anchors.return_value = []
    anchor_sys.get_critical_anchors.return_value = []

    with patch(
        "modules.core.stage4_context_builder._build_writer_mandatory_context",
        side_effect=RuntimeError("mandatory context failed"),
    ):
        result = cb.build_mandatory_context(
            next_ep=5,
            arc_data={},
            arc_tactical="",
            prev_text="",
            prev_ending="",
            hud_report="",
            writer_agent=MagicMock(),
            anchor_sys=anchor_sys,
            s4_genre_type="wuxia",
            v50_modules_available=False,
        )

    assert "필수 컨텍스트 로딩 실패" in result["mandatory_context"]


def test_blocking_validator_collects_degraded_checks_into_warnings():
    validator = BlockingValidator(context=None, enable_justification_checks=False)

    def ok(check):
        return {"check": check, "passed": True}

    validator._check_dead_npc_resurrection = lambda *_a, **_k: ok("dead_npc")
    validator._check_unowned_item_usage = lambda *_a, **_k: ok("unowned_item")
    validator._check_destroyed_location_visit = lambda *_a, **_k: ok("destroyed_location")
    validator._check_minimum_length = lambda *_a, **_k: ok("minimum_length")
    validator._check_damaged_item_usage = lambda *_a, **_k: ok("damaged_item")
    validator._check_relationship_consistency = lambda *_a, **_k: {
        "check": "relationship_consistency",
        "passed": True,
        "degraded": True,
        "error": "x",
    }
    validator._check_information_consistency = lambda *_a, **_k: {
        "check": "information_consistency",
        "passed": True,
        "degraded": True,
        "error": "y",
    }

    result = validator.validate("manuscript", {"mode": "BLUEPRINT"})

    assert result["passed"] is True
    assert "degraded: relationship_consistency" in result["warnings"]
    assert "degraded: information_consistency" in result["warnings"]


def test_scoring_validator_show_dont_tell_score_is_int():
    validator = ScoringValidator(client=None)
    result = validator._evaluate_show_dont_tell("simple manuscript text")
    assert isinstance(result["score"], int)


def test_scoring_validator_source_has_non_negative_clamp():
    source = Path("modules/validation/scoring_validator.py").read_text(encoding="utf-8")
    assert 'max(0, min(int(_val["score"]), int(_val["max"])))' in source


def test_base_agent_source_uses_rotation_lock_on_reset():
    source = Path("modules/domain/agents/base_agent.py").read_text(encoding="utf-8")
    assert "with BaseAgent._rotation_lock:" in source


# ── ForeshadowTracker.load_from_arcs ──────────────────────────


def test_foreshadow_tracker_load_from_arcs_basic():
    from modules.core.foreshadow_tracker import ForeshadowTracker

    tracker = ForeshadowTracker()
    arcs = [
        {
            "arc_no": 1,
            "start_episode": 1,
            "foreshadowings": [
                {"id": "secret_letter", "type": "비밀", "description": "비밀 편지"},
                {"id": "sword", "type": "아이템", "description": "봉인된 검"},
            ],
        },
        {
            "arc_no": 2,
            "foreshadowings": [
                {"id": "prophecy", "type": "예언", "description": "대예언"},
            ],
        },
    ]
    count = tracker.load_from_arcs(arcs)
    assert count == 3
    assert len(tracker.get_active_hooks()) == 3


def test_foreshadow_tracker_load_from_arcs_empty():
    from modules.core.foreshadow_tracker import ForeshadowTracker

    tracker = ForeshadowTracker()
    assert tracker.load_from_arcs([]) == 0
    assert tracker.load_from_arcs(None) == 0


def test_foreshadow_tracker_load_from_arcs_invalid_entries():
    from modules.core.foreshadow_tracker import ForeshadowTracker

    tracker = ForeshadowTracker()
    arcs = [
        {"arc_no": 1, "foreshadowings": [{"id": "", "description": ""}]},  # empty hook
        {"arc_no": 2, "foreshadowings": "not a list"},  # invalid type
        "not a dict",  # invalid arc
    ]
    count = tracker.load_from_arcs(arcs)
    assert count == 0
