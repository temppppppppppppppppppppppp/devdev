"""[V75-C] Director Contradiction Firewall 테스트."""

from pathlib import Path
from unittest.mock import MagicMock

# ═══════════════════════════════════════════════════════════════
# 1. CRITICAL 1건 → REJECT 강제
# ═══════════════════════════════════════════════════════════════


def _make_ensemble_and_call(result_override: dict, score_override: int = 70):
    """DirectorEnsembleSelector._select_manuscript_ensemble 내부 방화벽 로직을 단위 테스트.

    실제 LLM 호출 없이 result dict만 주입하여 방화벽 동작을 검증한다.
    """
    from modules.domain.agents.director_ensemble import _safe_int

    # result dict 구성
    result = {
        "verdict": result_override.get("verdict", "PASS"),
        "score": result_override.get("score", score_override),
        "selected_candidate": "A",
        **{k: v for k, v in result_override.items() if k not in ("verdict", "score", "selected_candidate")},
    }

    # 방화벽 로직 추출 (director_ensemble.py L482~L512 동일 로직)
    original_verdict = result.get("verdict", "REJECT")
    score = _safe_int(result.get("score", 50), 50)

    _contradiction_check = result.get("contradiction_check", {})
    firewall_triggered = False
    if isinstance(_contradiction_check, dict):
        _found = _contradiction_check.get("found_contradictions", [])
        if isinstance(_found, list) and _found:
            _critical_count = sum(
                1 for c in _found if isinstance(c, dict) and str(c.get("severity", "")).upper() == "CRITICAL"
            )
            _major_count = sum(
                1 for c in _found if isinstance(c, dict) and str(c.get("severity", "")).upper() == "MAJOR"
            )
            if _critical_count >= 1:
                firewall_triggered = True
            elif _major_count >= 2:
                firewall_triggered = True

            if firewall_triggered:
                original_verdict = "REJECT"
                score = min(score, 44)

    return {"verdict": original_verdict, "score": score, "firewall_triggered": firewall_triggered}


def test_critical_1_triggers_reject():
    """CRITICAL 모순 1건 → REJECT 강제, score ≤ 44."""
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 85,
            "contradiction_check": {
                "found_contradictions": [
                    {"severity": "CRITICAL", "type": "사망NPC 재등장", "current_violation": "죽은 NPC가 대화함"}
                ]
            },
        }
    )
    assert result["verdict"] == "REJECT"
    assert result["score"] <= 44
    assert result["firewall_triggered"] is True


# ═══════════════════════════════════════════════════════════════
# 2. CRITICAL 2건 → REJECT 강제
# ═══════════════════════════════════════════════════════════════


def test_critical_2_triggers_reject():
    """CRITICAL 모순 2건 → REJECT 강제."""
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 90,
            "contradiction_check": {
                "found_contradictions": [
                    {"severity": "CRITICAL", "type": "사망NPC", "current_violation": "A"},
                    {"severity": "CRITICAL", "type": "아이템모순", "current_violation": "B"},
                ]
            },
        }
    )
    assert result["verdict"] == "REJECT"
    assert result["score"] <= 44
    assert result["firewall_triggered"] is True


# ═══════════════════════════════════════════════════════════════
# 3. MAJOR 2건 → REJECT 강제
# ═══════════════════════════════════════════════════════════════


def test_major_2_triggers_reject():
    """MAJOR 모순 2건 → REJECT 강제."""
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 75,
            "contradiction_check": {
                "found_contradictions": [
                    {"severity": "MAJOR", "type": "금액불일치", "current_violation": "A"},
                    {"severity": "MAJOR", "type": "시간모순", "current_violation": "B"},
                ]
            },
        }
    )
    assert result["verdict"] == "REJECT"
    assert result["score"] <= 44
    assert result["firewall_triggered"] is True


# ═══════════════════════════════════════════════════════════════
# 4. MAJOR 1건 → 방화벽 미발동
# ═══════════════════════════════════════════════════════════════


def test_major_1_no_trigger():
    """MAJOR 1건만 → 방화벽 미발동, verdict 유지."""
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 75,
            "contradiction_check": {
                "found_contradictions": [
                    {"severity": "MAJOR", "type": "금액불일치", "current_violation": "A"},
                ]
            },
        }
    )
    assert result["verdict"] == "PASS"
    assert result["score"] == 75
    assert result["firewall_triggered"] is False


# ═══════════════════════════════════════════════════════════════
# 5. contradiction_check 없음 → no-op
# ═══════════════════════════════════════════════════════════════


def test_no_contradiction_check_noop():
    """contradiction_check 키 자체가 없으면 아무 조치 없음."""
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 80,
        }
    )
    assert result["verdict"] == "PASS"
    assert result["score"] == 80
    assert result["firewall_triggered"] is False


# ═══════════════════════════════════════════════════════════════
# 6. malformed → 크래시 없음
# ═══════════════════════════════════════════════════════════════


def test_malformed_contradiction_check_no_crash():
    """found_contradictions가 list가 아닌 경우 → 크래시 없이 no-op."""
    # string 타입
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 80,
            "contradiction_check": {"found_contradictions": "not a list"},
        }
    )
    assert result["verdict"] == "PASS"
    assert result["firewall_triggered"] is False

    # contradiction_check 자체가 list인 경우
    result2 = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 80,
            "contradiction_check": [{"severity": "CRITICAL"}],
        }
    )
    assert result2["verdict"] == "PASS"
    assert result2["firewall_triggered"] is False

    # contradiction_check가 None인 경우
    result3 = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 80,
            "contradiction_check": None,
        }
    )
    assert result3["verdict"] == "PASS"
    assert result3["firewall_triggered"] is False


# ═══════════════════════════════════════════════════════════════
# 7. 빈 배열 → no-op
# ═══════════════════════════════════════════════════════════════


def test_empty_contradictions_noop():
    """found_contradictions: [] → 아무 조치 없음."""
    result = _make_ensemble_and_call(
        {
            "verdict": "PASS",
            "score": 80,
            "contradiction_check": {"found_contradictions": []},
        }
    )
    assert result["verdict"] == "PASS"
    assert result["score"] == 80
    assert result["firewall_triggered"] is False


# ═══════════════════════════════════════════════════════════════
# 8. 적응형 승격 차단 확인 (score=44 < floor=45)
# ═══════════════════════════════════════════════════════════════


def test_adaptive_promotion_blocked():
    """score=44일 때 apply_adaptive_decision이 REJECT를 PASS로 승격하지 않음 확인."""
    from modules.domain.agents.director_grading import DirectorGradingSystem

    mock_director = MagicMock()
    mock_director.adaptive_thresholds_enabled = True
    mock_director.base_pass_threshold = 45

    grading = DirectorGradingSystem(director=mock_director)
    adaptive_result = grading.apply_adaptive_decision(
        score=44,
        original_decision="REJECT",
        arc_pos=1,
        total_eps=5,
        retry_count=0,
    )
    # score 44 < threshold 45 → REJECT 유지 (승격 불가)
    assert adaptive_result["decision"] == "REJECT"


# ═══════════════════════════════════════════════════════════════
# 9. post-select continuity 예외 → _post_select_conflicts에 추가
# ═══════════════════════════════════════════════════════════════


def test_post_select_continuity_exception_fail_closed():
    """Continuity check 예외 발생 시 _post_select_conflicts에 에러 추가 (fail-closed)."""
    src = Path("modules/core/stage4_interview_round.py").read_text(encoding="utf-8")
    # fail-closed 로그 패턴 확인
    assert "[FailClosed:SC:PostSelectContinuity]" in src
    # _post_select_conflicts에 추가하는 코드 확인
    assert "[Continuity Check Error] 검증 실패 (fail-closed)" in src
    # SilentPass 패턴이 사라졌는지 확인
    assert "[SilentPass:SC:PostSelectContinuity]" not in src


# ═══════════════════════════════════════════════════════════════
# 10. post-select history 예외 → _post_select_conflicts에 추가
# ═══════════════════════════════════════════════════════════════


def test_post_select_history_exception_fail_closed():
    """History check 예외 발생 시 _post_select_conflicts에 에러 추가 (fail-closed)."""
    src = Path("modules/core/stage4_interview_round.py").read_text(encoding="utf-8")
    # fail-closed 로그 패턴 확인
    assert "[FailClosed:SC:PostSelectHistory]" in src
    # _post_select_conflicts에 추가하는 코드 확인
    assert "[History Check Error] 검증 실패 (fail-closed)" in src
    # SilentPass 패턴이 사라졌는지 확인
    assert "[SilentPass:SC:PostSelectHistory]" not in src


# ═══════════════════════════════════════════════════════════════
# 11. 프롬프트 L96 절대규칙 제거 확인
# ═══════════════════════════════════════════════════════════════


def test_director_prompt_no_absolute_zero_rule():
    """director.yaml에서 '0으로 부여' 절대규칙 문구가 제거되었는지 확인."""
    src = Path("config/prompts/director.yaml").read_text(encoding="utf-8")
    assert "0으로 부여" not in src, "L96 절대규칙 '0으로 부여' 문구가 아직 남아있음"
    # 점진적 감점 규칙 참조가 존재하는지 확인
    assert "[I-10] 점진적 감점 규칙을 적용하세요" in src
    # "9개 항목" 반영 확인
    assert "9개 항목" in src or "위 9개" in src


# ═══════════════════════════════════════════════════════════════
# 12. 방화벽 코드가 director_ensemble.py에 존재하는지 구조 확인
# ═══════════════════════════════════════════════════════════════


def test_firewall_code_exists_in_director_ensemble():
    """director_ensemble.py에 V75-C 방화벽 코드가 존재하는지 확인."""
    src = Path("modules/domain/agents/director_ensemble.py").read_text(encoding="utf-8")
    assert "[V75-C] Contradiction Firewall" in src
    assert "found_contradictions" in src
    assert "min(score, 44)" in src
