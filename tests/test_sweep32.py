from pathlib import Path

from modules.domain.agents.constraint_compiler import ConstraintCompiler
from modules.domain.agents.state_extractor import StateExtractor


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_constraint_compiler_handles_non_dict_location_and_energy():
    compiler = ConstraintCompiler()
    state_extractor_result = {
        "protagonist_state": {"location": "서울", "internal_energy": 85, "injuries": []},
        "inventory": {"current_items": ["검"]},
        "next_arc_constraints": {"must_start_with": "이전 상태 계승"},
    }

    out = compiler._extract_current_state({}, state_extractor_result)

    assert out["location"] == "서울"
    assert out["internal_energy"] == 85


def test_state_extractor_validate_and_fix_result_handles_invalid_shapes():
    extractor = StateExtractor.__new__(StateExtractor)
    raw = {
        "protagonist_state": {"injuries": "골절", "internal_energy": 85},
        "inventory": {"current_items": []},
    }
    original_arc = {"joint_docs": {}}

    out = extractor._validate_and_fix_result(raw, original_arc)

    assert out["next_arc_constraints"]["recovery_scene_required"] is False
    assert out["next_arc_constraints"]["min_time_skip_days"] == 0


def test_base_agent_source_has_thread_safe_context_cache_eviction():
    src = _read("modules/domain/agents/base_agent.py")
    assert "list(self._context_caches.keys())" in src
    assert "self._context_caches.pop(old_key, None)" in src
    assert "except RuntimeError:" in src


def test_state_extractor_source_has_injuries_energy_type_guards():
    src = _read("modules/domain/agents/state_extractor.py")
    assert "if not isinstance(injuries, list):" in src
    assert "if not isinstance(energy, dict):" in src
    assert "if isinstance(inj, dict)" in src


def test_block_enricher_source_has_future_timeouts():
    src = _read("modules/domain/agents/block_enricher.py")
    assert "as_completed(futures, timeout=600)" in src
    assert "future.result(timeout=60)" in src


def test_arc_draft_validator_source_has_items_list_guards():
    src = _read("modules/domain/agents/arc_draft_validator.py")
    assert "if not isinstance(current_items, list):" in src
    assert "if not isinstance(items_acquired, list):" in src


def test_director_auditor_source_handles_non_dict_char_logic_result():
    src = _read("modules/domain/agents/director_auditor.py")
    assert "if not isinstance(char_logic_result, dict):" in src
    assert (
        "char_logic_result = char_logic_result[0] if isinstance(char_logic_result, list) and char_logic_result else {}"
        in src
    )


def test_continuity_manuscript_source_has_scene_breakdown_dict_guards():
    src = _read("modules/domain/agents/continuity_manuscript.py")
    assert "if scene_breakdown and isinstance(scene_breakdown, dict):" in src
    assert "if not scene_breakdown or not isinstance(scene_breakdown, dict):" in src


def test_stage2_finalizer_and_scene_checks_source_have_dict_guards():
    s2f = _read("modules/core/stage2_finalizer.py")
    bvs = _read("modules/validation/blocking_validator_scene_checks.py")
    assert 'if _as.get("npc_status") and isinstance(_as["npc_status"], dict):' in s2f
    assert "if not scene_breakdown or not isinstance(scene_breakdown, dict):" in bvs


def test_preflight_checker_source_has_status_and_inventory_guards():
    src = _read("modules/domain/agents/preflight_checker.py")
    assert "if not isinstance(status, dict):" in src
    assert "', '.join(str(i) for i in inventory[:10])" in src


def test_data_collector_source_catches_type_error_on_dump():
    src = _read("modules/core/data_collector.py")
    assert src.count("except (OSError, TypeError) as e:") >= 2


def test_pacing_analyzer_source_uses_positive_break_condition():
    src = _read("modules/core/pacing_analyzer.py")
    assert "if total_breaks > 0 else len(manuscript)" in src
