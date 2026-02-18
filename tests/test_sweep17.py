"""[Sweep17] Regression checks for logging level and fallback consistency fixes."""

import re
from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_validation_orchestrator_info_logs_and_advisory_fallback_key():
    source = _read("modules/validation/validation_orchestrator.py")

    assert 'logging.info("[V56] TIER 0.25: PRE-LLM 검증 중...")' in source
    assert 'logging.info("✅ PRE-LLM 통과")' in source
    assert 'logging.info("✅ CONTINUITY 통과")' in source
    assert "logging.info(f\"✅ BLOCKING 통과 (0/{blocking_result.get('failure_count', 0)} 실패)\")" in source
    assert 'logging.info("✅ CONSISTENCY 통과")' in source
    assert 'logging.info("✅ CATHARSIS: 적절한 타이밍")' in source
    assert 'advisory_result = {"suggestions": []}' in source


def test_blueprint_ensemble_timeout_warning_and_perf_info():
    source = _read("modules/domain/agents/blueprint_ensemble.py")

    assert 'logging.warning(f"⏰ [V61.3] {strategy_name} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")' in source
    assert re.search(r'logging\.warning\(\s*f"⏰ \[V61\.3\] 블루프린트 앙상블 타임아웃', source)
    assert (
        'logging.info(f"[PerfTimer:BlueprintEnsemble] bp_ep{ep_num}_ensemble={time.monotonic() - _tp_t0:.2f}s")'
        in source
    )


def test_director_auditor_success_debug_logs_use_info():
    source = _read("modules/domain/agents/director_auditor.py")

    assert (
        'logging.info(f"📖 [V67] Director 컨텍스트 확대: {len(loaded_parts)}화 이전 원고 로드 (ep {ep_num})")' in source
    )
    assert "logging.info(f\"🔍 [V60.55 DEBUG] 주인공 이름 검증: '{protagonist_name}'\")" in source


def test_director_continuity_dead_timeline_block_removed():
    source = _read("modules/domain/agents/director_continuity.py")
    assert (
        'if prev_ending_state.get("timeline") and new_blueprint.get("ending_state", {}).get("timeline"):' not in source
    )


def test_reflexion_manager_load_success_log_is_info():
    source = _read("modules/core/reflexion_manager.py")
    assert 'logging.info(f"📚 [Reflexion] 과거 실패 패턴 {len(self.memory)}개 로드됨")' in source
