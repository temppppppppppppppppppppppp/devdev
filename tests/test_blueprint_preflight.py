"""[TF-49b] Blueprint Preflight Validation — 사전검증 단위 테스트.

v2: Advisory 전달 방식 (Blueprint 직접 패치 제거).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _make_orchestrator(*, enabled=True, min_episode=2):
    """Stage4Orchestrator 인스턴스를 최소한의 mock으로 생성."""
    from modules.core.stage4_orchestrator import Stage4Orchestrator

    app = MagicMock()
    ctx = MagicMock()
    ctx.ui = MagicMock()
    ctx.ui.log = MagicMock()
    ctx.sys = MagicMock()
    ctx.sys.api_client = MagicMock()
    ctx.world_state = MagicMock()
    ctx.world_state.get_summary.return_value = "자산: 15억, 위치: 서울"
    ctx.fact_ledger = MagicMock()
    ctx.fact_ledger.get_canonical_summary.return_value = "총자산=15억"
    ctx.current_project = MagicMock()
    ctx.current_project.name = "test_project"
    ctx.agents = {"three_phase_bp": MagicMock()}

    orch = Stage4Orchestrator(app, context=ctx)

    return orch, ctx


def _make_arc_data(ep_start=1, ep_end=5):
    return {
        "ep_start": ep_start,
        "ep_end": ep_end,
        "tactical_doc": "제2화: 투자 회의에서 전략 수립",
        "episode_details": [
            {"ep_num": 2, "details": ["투자 계획 수립", "파트너 미팅"]},
        ],
    }


def _make_blueprint(ep_num=2):
    return {
        "episode_number": ep_num,
        "scene_breakdown": {"scene_1": "회의실 장면"},
        "integrated_scenario": "투자 전략 수립 에피소드",
    }


# ─── 1. Feature flag disabled ───────────────────────────────────────


def test_preflight_disabled(monkeypatch):
    """enabled=False → 즉시 pass, LLM 호출 없음."""
    orch, ctx = _make_orchestrator()
    monkeypatch.setattr(
        "modules.core.stage4_orchestrator._threshold",
        lambda key, default=None: False if "enabled" in key else default,
    )
    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )
    assert result["passed"] is True
    assert result["patched_blueprint"] is None
    ctx.sys.api_client.models.generate_content.assert_not_called()


# ─── 2. Skip episode 1 ──────────────────────────────────────────────


def test_preflight_skip_ep1(monkeypatch):
    """ep_num < min_episode(2) → skip."""
    orch, ctx = _make_orchestrator()

    def _threshold_mock(key, default=None):
        if "enabled" in key:
            return True
        if "min_episode" in key:
            return 2
        return default

    monkeypatch.setattr("modules.core.stage4_orchestrator._threshold", _threshold_mock)
    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(1),
        arc_data=_make_arc_data(),
        ep_num=1,
    )
    assert result["passed"] is True
    ctx.sys.api_client.models.generate_content.assert_not_called()


# ─── 3. Pass clean ──────────────────────────────────────────────────


def test_preflight_pass_clean(monkeypatch):
    """LLM passed=true → advisory 없음."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps({"passed": True, "issues": [], "summary": "정합성 확인"})
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )
    assert result["passed"] is True
    assert result["patched_blueprint"] is None
    assert result["summary"] == "정합성 확인"
    assert result.get("advisory") is None or result.get("advisory") == ""


# ─── 4. High severity issues → advisory 생성 ─────────────────────────


def test_preflight_high_severity_generates_advisory(monkeypatch):
    """high severity 이슈 → advisory 텍스트 생성, Blueprint 미수정."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [{"category": "수치", "description": "자산 금액 명백 모순", "severity": "high"}],
            "summary": "수치 불일치",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    # Advisory 방식: passed=True (Blueprint 미수정, CW/Director에 전달)
    assert result["passed"] is True
    assert result["patched_blueprint"] is None
    # advisory 텍스트 존재
    assert "advisory" in result
    assert "모순" in result["advisory"]
    assert "제2화" in result["advisory"]


# ─── 5. Advisory 텍스트에 이슈 세부내용 포함 ──────────────────────────


def test_preflight_advisory_contains_issue_details(monkeypatch):
    """advisory 텍스트에 이슈 category/description 포함."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [
                {"category": "NPC", "description": "사망 NPC가 행동함", "severity": "high"},
                {"category": "타임라인", "description": "시간 역행 발생", "severity": "high"},
            ],
            "summary": "복합 모순",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    _adv = result["advisory"]
    assert "NPC" in _adv
    assert "사망" in _adv
    assert "타임라인" in _adv
    assert "시간 역행" in _adv
    assert "원고 작성/심사에 반영" in _adv


# ─── 6. Advisory 방식은 항상 passed=True ──────────────────────────────


def test_preflight_advisory_always_passes(monkeypatch):
    """high severity 있어도 passed=True (Blueprint 미수정, advisory만 전달)."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [
                {"category": "수치", "description": "총자산 불가능 — 명백 모순", "severity": "high"},
                {"category": "NPC", "description": "사망 캐릭터 등장", "severity": "high"},
                {"category": "아이템", "description": "소진 아이템 재사용", "severity": "high"},
            ],
            "summary": "다수 심각한 모순",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    # 모든 이슈에도 passed=True (advisory 전달 방식)
    assert result["passed"] is True
    assert result["patched_blueprint"] is None
    assert result["advisory"]  # 비어있지 않음


# ─── 7. LLM error → fail-open ───────────────────────────────────────


def test_preflight_llm_error_failopen(monkeypatch):
    """API 에러 → pass (fail-open)."""
    orch, ctx = _make_orchestrator()

    ctx.sys.api_client.models.generate_content.side_effect = RuntimeError("API 장애")

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )
    assert result["passed"] is True
    assert result["patched_blueprint"] is None


# ─── 8. Prompt load failure → pass ──────────────────────────────────


def test_preflight_prompt_load_failure(monkeypatch):
    """YAML 로드 실패 → pass."""
    orch, ctx = _make_orchestrator()

    with patch("modules.core.prompt_loader.PromptLoader.load", side_effect=FileNotFoundError("YAML 없음")):
        result = orch._preflight_validate_blueprint(
            blueprint=_make_blueprint(),
            arc_data=_make_arc_data(),
            ep_num=2,
        )

    assert result["passed"] is True
    assert result["patched_blueprint"] is None


# ─── 9. No world_state → 빈 문자열로 진행 ────────────────────────────


def test_preflight_no_worldstate(monkeypatch):
    """world_state=None → 빈 문자열로 진행."""
    orch, ctx = _make_orchestrator()
    ctx.world_state = None

    _llm_response = MagicMock()
    _llm_response.text = json.dumps({"passed": True, "issues": [], "summary": "OK"})
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )
    assert result["passed"] is True


# ─── 10. Escalation logged on high severity ──────────────────────────


def test_preflight_escalation_logged(monkeypatch):
    """high severity 이슈 발견 시 _log_escalation_event 호출."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [{"category": "타임라인", "description": "시간 역행", "severity": "high"}],
            "summary": "타임라인 모순",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    with patch.object(orch, "_log_escalation_event") as mock_log:
        result = orch._preflight_validate_blueprint(
            blueprint=_make_blueprint(),
            arc_data=_make_arc_data(),
            ep_num=2,
        )

    mock_log.assert_called_once_with(2, "TF49b_PREFLIGHT", 1, success=True)
    # advisory 방식: passed=True
    assert result["passed"] is True
    assert result["advisory"]


# ─── 11. Low/medium severity only → PASS, no advisory ───────────────


def test_preflight_low_severity_passes(monkeypatch):
    """LLM이 passed=False지만 severity가 전부 low/medium이면 → PASS, advisory 없음."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [
                {"category": "고증", "description": "4K 모니터 2006년 미존재", "severity": "low"},
                {"category": "수치", "description": "레버리지 수익률 약간 과장", "severity": "medium"},
            ],
            "summary": "사소한 고증 오차",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )
    assert result["passed"] is True
    assert result["patched_blueprint"] is None
    assert len(result["issues"]) == 2
    # low/medium만이면 advisory 없음
    assert result.get("advisory") is None or result.get("advisory") == ""


# ─── 12. Mixed severity → high triggers advisory ────────────────────


def test_preflight_mixed_severity_advisory_on_high(monkeypatch):
    """high severity 이슈가 1건이라도 있으면 → advisory 생성."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [
                {"category": "고증", "description": "4K 모니터 2006년", "severity": "low"},
                {"category": "수치", "description": "자산 금액 명백 모순", "severity": "high"},
            ],
            "summary": "자산 모순 + 사소한 고증",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    assert result["passed"] is True  # advisory 방식은 항상 pass
    assert result["advisory"]  # advisory 텍스트 존재
    assert "모순" in result["advisory"]


# ─── 13. False positive pattern → severity downgraded ────────────────


def test_preflight_false_positive_downgrade(monkeypatch):
    """FALSE_POSITIVE_PATTERNS에 매칭되는 high → low로 다운그레이드."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [
                {"category": "장비", "description": "출처 불분명한 고급 모니터", "severity": "high"},
                {"category": "고증", "description": "2006년 해상도 고증 오류", "severity": "high"},
            ],
            "summary": "장비+고증 이슈",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    # 모두 FALSE_POSITIVE_PATTERNS 매칭 → low로 다운그레이드 → advisory 없음
    assert result["passed"] is True
    assert result.get("advisory") is None or result.get("advisory") == ""
    # severity 다운그레이드 확인
    for iss in result["issues"]:
        assert iss["severity"] == "low"


# ─── 14. CRITICAL pattern survives false-positive check ──────────────


def test_preflight_critical_pattern_stays_high(monkeypatch):
    """CRITICAL_PATTERNS 매칭 이슈는 high 유지 → advisory 생성."""
    orch, ctx = _make_orchestrator()

    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": [
                {"category": "NPC", "description": "사망 캐릭터가 대화함", "severity": "high"},
            ],
            "summary": "사망 NPC 모순",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    # "사망" → CRITICAL_PATTERNS 매칭 → high 유지 → advisory 생성
    assert result["passed"] is True
    assert result["advisory"]
    assert "사망" in result["advisory"]
    assert result["issues"][0]["severity"] == "high"


# ─── 15. No fact_ledger → graceful handling ──────────────────────────


def test_preflight_no_fact_ledger(monkeypatch):
    """fact_ledger=None → 빈 문자열로 진행."""
    orch, ctx = _make_orchestrator()
    ctx.fact_ledger = None

    _llm_response = MagicMock()
    _llm_response.text = json.dumps({"passed": True, "issues": [], "summary": "OK"})
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )
    assert result["passed"] is True


# ─── 16. Advisory max 10 issues truncation ───────────────────────────


def test_preflight_advisory_truncates_at_10(monkeypatch):
    """이슈가 10건 초과 시 advisory에 최대 10건만 포함."""
    orch, ctx = _make_orchestrator()

    _issues = [{"category": f"수치{i}", "description": f"자산 모순 #{i}", "severity": "high"} for i in range(15)]
    _llm_response = MagicMock()
    _llm_response.text = json.dumps(
        {
            "passed": False,
            "issues": _issues,
            "summary": "다수 모순",
        }
    )
    ctx.sys.api_client.models.generate_content.return_value = _llm_response

    result = orch._preflight_validate_blueprint(
        blueprint=_make_blueprint(),
        arc_data=_make_arc_data(),
        ep_num=2,
    )

    _adv = result["advisory"]
    # advisory 내 이슈 줄 수: 헤더 1줄 + 이슈 10줄 + 마지막 안내 1줄 = 12줄
    _issue_lines = [ln for ln in _adv.split("\n") if ln.strip().startswith("- [")]
    assert len(_issue_lines) == 10  # 최대 10건
