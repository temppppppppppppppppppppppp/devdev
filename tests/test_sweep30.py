from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_state_extractor_cumulative_uses_copy_for_latest_state():
    source = _read("modules/domain/agents/state_extractor.py")
    assert "current_state = dict(self.extract_state(latest_arc))" in source


def test_project_manager_hud_change_detects_zero_values():
    source = _read("modules/core/project_manager.py")
    assert "if new_hud.get(key) is not None and new_hud.get(key) != old_hud.get(key):" in source


def test_critic_score_zero_is_rendered():
    source = _read("modules/domain/agents/critic.py")
    assert "if score is not None:" in source


def test_pre_llm_validator_find_index_zero_is_detected():
    source = _read("modules/validation/pre_llm_validator.py")
    assert "if same_day_idx >= 0 and days_later_idx >= 0 and days_later_idx < same_day_idx:" in source


def test_stage2_validation_pipeline_none_safe_slicing():
    source = _read("modules/core/stage2_validation_pipeline.py")
    assert "(ci.get('issue', '?') or '?')[:80]" in source
    assert '(i.get("message", "") or "")[:30]' in source


def test_arc_corrector_none_safe_slicing():
    source = _read("modules/domain/agents/arc_corrector.py")
    assert "(issue.get('message', '') or '')[:50]" in source
    assert "(correction_result.get('summary', '') or '')[:50]" in source
    assert "(correction_result.get('reason', '') or '')[:50]" in source


def test_unified_blueprint_and_feedback_none_safe_slicing():
    ubv = _read("modules/domain/agents/unified_blueprint_validator.py")
    fbs = _read("modules/core/feedback_system.py")
    assert "(director_reason or '')[:50]" in ubv
    assert '(v.get("description", "위반사항 수정") or "위반사항 수정")[:80]' in fbs
    assert '(v.get("description", "") or "")[:150]' in fbs
