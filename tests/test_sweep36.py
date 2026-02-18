from pathlib import Path

from modules.models.blueprint import Blueprint


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_continuity_arc_vacuous_truth_guard_present():
    src = _read("modules/domain/agents/continuity_arc.py")
    assert "intra_only = violations and all(" in src


def test_analyst_hud_error_is_logged_and_truncated():
    src = _read("modules/domain/agents/analyst.py")
    idx = src.index("HUD 로드 오류")
    section = src[max(0, idx - 180) : idx + 240]
    assert "logging.warning" in section
    assert "[:50]" in section


def test_block_enricher_validate_causal_chain_logs_warning():
    src = _read("modules/domain/agents/block_enricher.py")
    assert 'logging.warning(f"[BlockEnricher] validate_causal_chain 실패 (non-blocking): {e}")' in src


def test_stage2_preflight_critical_state_failure_logs_stacktrace():
    src = _read("modules/core/stage2_preflight.py")
    idx = src.index("critical_state_extraction_failed")
    section = src[max(0, idx - 500) : idx + 120]
    assert "logging.warning(" in section
    assert "exc_info=True" in section


def test_blueprint_episode_number_creates_ep_num_alias():
    bp = Blueprint.model_validate({"episode_number": 5, "integrated_scenario": "x"})
    dumped = bp.model_dump()
    assert dumped.get("episode_number") == 5
    assert dumped.get("ep_num") == 5


def test_blueprint_ep_num_creates_episode_number_alias():
    bp = Blueprint.model_validate({"ep_num": 7, "integrated_scenario": "x"})
    dumped = bp.model_dump()
    assert dumped.get("episode_number") == 7


def test_main_a_arc_calc_uses_5_episode_buckets():
    src = _read("main_a.py")
    idx = src.index("def _calculate_arc_from_episode")
    section = src[idx : idx + 260]
    assert "// 5 + 1" in section
    assert "// 10 + 1" not in section


def test_stage2_orchestrator_smart_skip_has_no_dead_pass_branch():
    src = _read("modules/core/stage2_orchestrator.py")
    idx = src.index("skip_arc_no = self.ctx.calculate_arc_from_episode(existing_ms_max_ep)")
    section = src[idx : idx + 350]
    assert "if skip_arc_no > done_count:" in section
    assert "if skip_arc_no <= done_count:" not in section
