"""[Sweep19] Regression tests for null-guards, falsy-zero handling, and logging levels."""

from __future__ import annotations

import re
from pathlib import Path

from modules.core.repetition_guard import RepetitionGuard


def test_main_a_boot_has_empty_project_guard():
    source = Path("main_a.py").read_text(encoding="utf-8")
    assert "project_name = self._select_project()" in source
    assert "if not project_name:" in source


def test_main_a_critical_error_handler_has_current_project_null_guard():
    source = Path("main_a.py").read_text(encoding="utf-8")
    assert 'if self.current_project and hasattr(self.current_project, "paths")' in source
    assert 'Path("logs") / "error.log"' in source


def test_db_manager_karma_mapping_uses_none_checks_not_or_chain():
    source = Path("modules/core/db_manager.py").read_text(encoding="utf-8")
    assert 'mis = k.get("misunderstanding")' in source
    assert "if mis is None:" in source
    assert 'mis = k.get("value")' in source
    assert 'mis = k.get("point", 0)' in source
    assert 'obs = k.get("obsession")' in source
    assert 'obs = k.get("point")' in source
    assert 'mis = k.get("misunderstanding") or k.get("value") or k.get("point", 0)' not in source


def test_repetition_guard_tracks_real_frequency_and_reports_it():
    guard = RepetitionGuard(threshold=2)
    previous = "alpha beta gamma alpha beta gamma alpha beta gamma"
    banned = guard.build_banned_list([previous])

    assert isinstance(banned, dict)
    assert banned["alpha beta gamma"] == 3

    violations, _ = guard.scan_manuscript("x alpha beta gamma y")
    assert violations
    assert violations[0]["phrase"] == "alpha beta gamma"
    assert violations[0]["frequency"] == 3


def test_project_manager_normalize_seed_id_skips_empty_seed_ids():
    source = Path("modules/core/project_manager.py").read_text(encoding="utf-8")
    assert "for vid in valid_ids:" in source
    assert "if not vid:" in source
    assert "continue" in source


def test_stage3_orchestrator_agents_none_guard_added():
    source = Path("modules/core/stage3_orchestrator.py").read_text(encoding="utf-8")
    assert 'if ctx.agents and hasattr(ctx.agents.get("three_phase_bp"), "get_stats"):' in source
    assert 'if ctx.agents and "state_extractor" in ctx.agents and ctx.current_project.arcs:' in source


def test_chief_writer_final_content_falls_back_when_content_is_none():
    source = Path("modules/domain/agents/chief_writer.py").read_text(encoding="utf-8")
    assert "final_content = _crit_content or manuscript_content" in source


def test_director_ensemble_info_levels_for_normal_progress_events():
    source = Path("modules/domain/agents/director_ensemble.py").read_text(encoding="utf-8")
    assert 'logging.info(f"🎭 [Director] {len(candidates)}개 후보 비교 중...")' in source
    assert 'logging.info(f"🎯 [Director] 후보 {selected_idx + 1} 선택 ({decision}, 점수: {score})")' in source
    assert re.search(r"logging\.info\(\s*f\"✅ \[V60\.97\] 분량 통과 후보:", source)
