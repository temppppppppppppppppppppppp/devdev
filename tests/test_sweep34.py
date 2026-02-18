from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from modules.core.stage2_preflight import Stage2PreflightAnalysis
from modules.domain.agents.director_ensemble import DirectorEnsembleSelector
from modules.domain.agents.state_tracker_npc import StateTrackerNPC
from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_stage2_preflight_parallel_timeout_returns_safe_defaults():
    class _TimeoutFuture:
        def result(self, timeout=None):
            raise TimeoutError("simulated timeout")

    class _TimeoutExecutor:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, *args, **kwargs):
            return _TimeoutFuture()

    ctx = SimpleNamespace(
        perf_timer=MagicMock(),
        agents={},
        state_tracker=None,
        constraint_compiler=None,
        ui=MagicMock(),
        audit_event=MagicMock(),
        cumulative_state_cache=None,
        cumulative_state_cache_key=None,
        sync_cache_key_to_app=None,
        semantic_plot_guard=None,
    )
    host = SimpleNamespace(ctx=ctx)
    preflight = Stage2PreflightAnalysis(host)
    constraint_db = MagicMock()
    constraint_db.generate_constraint_block.return_value = ""

    with patch("modules.core.stage2_preflight.concurrent.futures.ThreadPoolExecutor", _TimeoutExecutor):
        result = preflight._preflight_state_setup(
            all_refined_arcs=[{}],
            arcs_source=[{}],
            arc_idx=0,
            lack_report={},
            grand_obj="",
            global_arc_no=1,
            constraint_db=constraint_db,
        )

    assert result["arc_drive"] == {}
    assert result["cached_preflight_injection"] == ""
    assert result["cached_preflight_result"] == {}


def test_sweep34_source_has_cancel_for_ensemble_loops():
    assert "for f in futures:" in _read("modules/domain/agents/arc_ensemble.py")
    assert "for f in futures:" in _read("modules/domain/agents/blueprint_ensemble.py")
    assert "for f in futures:" in _read("modules/domain/agents/consensus_validator.py")
    assert "for f in futures:" in _read("modules/domain/agents/director_auditor.py")


def test_block_enricher_source_has_outer_timeout_fallback_and_cancel():
    src = _read("modules/domain/agents/block_enricher.py")
    assert "processed_indices = set()" in src
    assert "for future in concurrent.futures.as_completed(futures, timeout=600):" in src
    assert "except Exception as _timeout_err:" in src
    assert "for f in futures:" in src
    assert "f.cancel()" in src


def test_director_ensemble_handles_string_index_and_score():
    de = DirectorEnsembleSelector.__new__(DirectorEnsembleSelector)
    de._d = MagicMock()
    de._d.ask.return_value = "{}"
    de._d._extract_json_robust.return_value = {
        "selected_index": "1",
        "decision": "PASS",
        "score": "85",
        "reason": "ok",
        "comparison_notes": "",
    }

    candidates = [
        {"scene_breakdown": {"s1": {}}, "integrated_scenario": "x" * 1000},
        {"scene_breakdown": {"s1": {}, "s2": {}}, "integrated_scenario": "y" * 1100},
    ]

    result = de.compare_and_select_blueprint(candidates, arc_data={}, ep_num=1)

    assert result["selected_index"] == 1
    assert isinstance(result["selected_index"], int)
    assert result["score"] == 85
    assert isinstance(result["score"], int)


def test_unified_blueprint_validator_compare_confidence_with_string_score():
    ubv = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    director = MagicMock()
    director.compare_and_select_blueprint.return_value = {
        "decision": "PASS",
        "selected_blueprint": {"ok": True},
        "score": "75",
        "selected_index": 0,
        "reason": "ok",
        "feedback": "",
        "comparison_notes": "",
    }

    verdict, result = ubv.validate(
        blueprint={},
        arc_data={},
        constraint_block={},
        director=director,
        working_ep=1,
        all_candidates=[{"a": 1}, {"b": 2}],
    )

    assert verdict == "PASS"
    assert result["confidence"] == 0.9


def test_unified_blueprint_validator_director_score_string_is_coerced():
    ubv = UnifiedBlueprintValidator(context=MagicMock(), client=None)
    director = MagicMock()
    director.audit_manuscript.return_value = {
        "decision": "PASS",
        "reason": "ok",
        "feedback": "",
        "score": "65",
    }

    verdict, result = ubv.validate(
        blueprint={"scene_breakdown": {"scene_1": {}}, "integrated_scenario": "x" * 900},
        arc_data={"tactical_doc": "", "ep_start": 1, "ep_count": 5},
        constraint_block={},
        director=director,
        working_ep=1,
        arc_idx=1,
    )

    assert verdict == "PASS"
    assert result["score"] == 65
    assert result["confidence"] == 0.6


def test_state_tracker_npc_merge_does_not_overwrite_with_empty_values():
    tracker = MagicMock()
    tracker.npc_registry = {"도윤": {"name": "도윤", "status": "alive", "weapon": "장검", "level": 5}}

    other = MagicMock()
    other.npc_registry = {"도윤": {"name": "도윤", "status": "alive", "weapon": "", "level": None}}
    other.protagonist_skills = set()
    other.skill_acquisitions = {}

    npc_module = StateTrackerNPC(tracker)
    npc_module.merge_npc_registry(other)

    assert tracker.npc_registry["도윤"]["weapon"] == "장검"
    assert tracker.npc_registry["도윤"]["level"] == 5


def test_sweep34_source_guards_exist():
    assert "except Exception as _pf_err:" in _read("modules/core/stage2_preflight.py")
    assert "arc_drive = {}" in _read("modules/core/stage2_preflight.py")
    de_src = _read("modules/domain/agents/director_ensemble.py")
    assert "def _safe_int(value, default=0):" in de_src
    assert 'selected_idx = _safe_int(result.get("selected_index", 0), 0)' in de_src
    assert 'score = _safe_int(result.get("score", 70), 70)' in de_src
    ubv_src = _read("modules/domain/agents/unified_blueprint_validator.py")
    assert 'confidence": 0.9 if _safe_int(compare_result.get("score", 0), 0) >= 70 else 0.6' in ubv_src
    assert 'director_score = _safe_int(director_result.get("score", 50), 50)' in ubv_src
    st_src = _read("modules/domain/agents/state_tracker_npc.py")
    # [Sweep64] dead 분기는 원본 필터 유지, non-dead 분기는 0/False 보호 추가
    assert 'v not in ("", None, [], {})' in st_src
