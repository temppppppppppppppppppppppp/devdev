"""실파이프라인 감사 00_20260306 — BUG/STRUCT 패치 검증 테스트."""
import re

import pytest


# ── BUG-1: "금지 아이템: 다음" 오탐 방지 ──────────────────────────


class TestBug1PreflightMarker:
    """preflight_checker 제목 라인에서 ❌ 제거 → 개별 아이템 앞에만 배치."""

    def test_title_line_no_emoji(self):
        """제목 라인에 ❌가 없고, 개별 아이템 앞에 ❌가 있어야 함."""
        import inspect
        from modules.domain.agents import preflight_checker as mod

        source = inspect.getsource(mod)

        # 제목 라인: "❌ 다음" 패턴이 없어야 함
        assert '❌ 다음 아이템' not in source
        assert '❌ 다음 수여물' not in source

        # 개별 아이템에 ❌ 배치 확인
        assert 'f"   ❌ {' in source

    def test_regex_does_not_capture_title_words(self):
        """arc_ensemble의 regex가 제목 마커에서 '다음'을 잡지 않아야 함."""
        # 신규 포맷
        constraint_block = (
            "[아이템 획득 금지 (이미 보유 중)]:\n"
            "   ❌ 법인인감 - Arc 1에서 획득\n"
            "   ❌ 통장 - Arc 1에서 획득\n"
            "[수여물 재수여 금지]:\n"
            "   ❌ 명함 - Arc 2에서 수여\n"
        )
        forbidden_items = re.findall(r"❌\s*([가-힣\w]+)", constraint_block)
        assert "다음" not in forbidden_items
        assert "법인인감" in forbidden_items
        assert "통장" in forbidden_items
        assert "명함" in forbidden_items

    def test_old_format_would_capture_title(self):
        """기존 포맷이었다면 '다음'이 캡처되는 것을 재현."""
        old_block = "❌ 다음 아이템 획득 금지 (이미 보유 중):\n   • 법인인감 - 이유\n"
        forbidden_items = re.findall(r"❌\s*([가-힣\w]+)", old_block)
        assert "다음" in forbidden_items  # 기존 포맷의 오탐 재현


# ── BUG-2: internal_energy 프롬프트 예시 장르 중립화 ────────────


def test_bug2_no_internal_energy_in_prompt():
    """preflight_checker 프롬프트에서 internal_energy/martial_level 제거 확인."""
    from modules.domain.agents.preflight_checker import PREFLIGHT_ANALYSIS_PROMPT

    # 프롬프트 예시에서 무협 전용 필드가 없어야 함
    assert '"internal_energy": 85' not in PREFLIGHT_ANALYSIS_PROMPT
    assert '"martial_level"' not in PREFLIGHT_ANALYSIS_PROMPT
    # 장르 중립 대체 확인
    assert "key_stat" in PREFLIGHT_ANALYSIS_PROMPT


# ── BUG-3: 소지품 regex 장르 중립 확장 ────────────────────────


def test_bug3_arc_ensemble_genre_neutral_items():
    """arc_ensemble 소지품 regex가 투자물 아이템도 매칭."""
    pattern = r"([가-힣]+(?:도|검|창|궁|패|인장|통장|계약서|인감|증명서|면허|허가증|보고서|카드|워크스테이션|노트북|폰))"
    for item in ["법인통장", "임대계약서", "법인인감", "사업자증명서", "운전면허", "투자보고서"]:
        assert re.findall(pattern, item), f"{item}이 매칭되지 않음"


def test_bug3_arc_draft_validator_weapon_keywords():
    """arc_draft_validator의 weapon_keywords가 투자물 아이템 포함."""
    from modules.domain.agents.arc_draft_validator import ArcDraftValidator

    v = ArcDraftValidator()
    for kw in ["통장", "계약서", "인감", "증명서"]:
        assert kw in v.weapon_keywords, f"{kw} 누락"


def test_bug3_get_item_suffixes_per_genre():
    """genre_schema_builder가 장르별 접미사를 반환."""
    from modules.core.genre_schema_builder import get_item_suffixes

    investment = get_item_suffixes("investment")
    for kw in ["통장", "계약서", "인감"]:
        assert kw in investment

    wuxia = get_item_suffixes("wuxia")
    for kw in ["검", "도", "비급"]:
        assert kw in wuxia


def test_bug3_get_item_suffixes_unknown_genre_union():
    """미지 장르면 전 장르 union 폴백을 반환."""
    from modules.core.genre_schema_builder import get_item_suffixes

    unknown = get_item_suffixes("unknown_genre")
    for kw in ["통장", "검", "칼", "트로피"]:
        assert kw in unknown


def test_bug3_arc_ensemble_structural_forbidden_and_inheritance():
    """ArcEnsemble가 구조적 forbidden/equipment를 우선 사용."""
    from modules.domain.agents.arc_ensemble import ArcEnsembleGenerator

    gen = ArcEnsembleGenerator.__new__(ArcEnsembleGenerator)
    candidate = {
        "arc_no": 4,
        "ep_count": 5,
        "tactical_doc": ("제 1화\n" * 5) + ("서사" * 900),
        "joint_docs": {"final_location": "서울", "physical_inventory": [], "world_joint": ""},
        "state_constraints": {
            "arc_start_state": {"location": "서울", "equipment": ["법인인감"]},
            "arc_end_state": {"location": "서울", "equipment": ["법인인감"]},
            "items_acquired": ["법인통장"],
            "items_consumed": [],
        },
        "state_changes": {
            "timeline": {"start": {}, "end": {}},
            "npc_deaths": [],
            "skill_acquisitions": [],
            "relationship_changes": [],
            "major_items": [],
            "resolved_plots": [],
        },
    }

    _, issues = gen._evaluate_candidate(
        candidate,
        prev_arc_context="",
        constraint_block="",
        prev_equipment=["법인인감", "워크스테이션"],
        forbidden_items=["법인통장"],
    )

    assert any("금지 아이템 획득 시도: 법인통장" in msg for msg in issues)
    assert any("소지품 미계승: 워크스테이션" in msg for msg in issues)


def test_bug3_state_tracker_fallback_union():
    """state_tracker_plots regex fallback이 비무협 아이템도 커버."""
    from modules.domain.agents import state_tracker_plots as mod

    acquire = mod._RE_ITEM_ACQUIRE[0]
    lose = mod._RE_ITEM_LOSE[0]

    assert acquire.search("법인통장을 획득했다")
    assert acquire.search("셰프칼을 입수했다")
    assert lose.search("트로피를 분실했다")


# ── BUG-4: dead code 제거 확인 ────────────────────────────────


def test_bug4_no_dead_expression():
    """arc_draft_validator에서 결과 미사용 expression 제거 확인."""
    import inspect
    from modules.domain.agents.arc_draft_validator import ArcDraftValidator

    source = inspect.getsource(ArcDraftValidator._validate_state_checkpoints)
    # L518 dead expression 제거
    assert 'episode_sections.get(sorted_eps[i - 1], "")' not in source
    # L523 dead expression 제거 — any(...) 결과 미사용
    lines = source.split("\n")
    for line in lines:
        stripped = line.strip()
        # any(kw ...) 가 단독 expression statement로 존재하면 안 됨
        if stripped.startswith("any(kw in content"):
            pytest.fail(f"Dead expression found: {stripped}")


# ── BUG-5: ArcValidator advisory 로깅 확인 ──────────────────────


def test_bug5_advisory_issues_logged(caplog):
    """ArcValidator가 advisory_issues를 로깅하는지 확인."""
    import logging
    from modules.domain.agents.arc_draft_validator import ArcDraftValidator

    v = ArcDraftValidator()
    # 위치 불일치를 유발하는 Arc
    prev_arc = {
        "state_constraints": {
            "arc_end_state": {"location": "서울 여의도 사무실"},
            "equipment": ["법인인감"],
        },
        "tactical_doc": "Ep 4: 여의도 사무실에서 마무리",
    }
    arc = {
        "state_constraints": {
            "arc_start_state": {"location": "부산 해운대"},
            "items_acquired": [],
        },
        "tactical_doc": "Ep 5: 부산 해운대에서 시작하는 이야기. " * 100,
        "ep_count": 4,
    }
    with caplog.at_level(logging.WARNING):
        result = v.validate(arc, [prev_arc], constraint_block="")

    # advisory_issues가 있으면 로깅되어야 함
    if result.get("advisory_issues"):
        assert any("ArcDraftValidator" in r.message and "advisory" in r.message for r in caplog.records)


# ── STRUCT-1: SC 추가투표 thinking_level 균등화 ──────────────────


def test_struct1_sc_vote_thinking_level():
    """director_auditor SC 추가투표가 medium으로 설정되었는지 확인."""
    import inspect
    from modules.domain.agents.director_auditor import DirectorQualityAuditor

    source = inspect.getsource(DirectorQualityAuditor._strategic_audit_with_self_consistency)
    # _vote_task 내부에서 thinking_level="medium" 사용
    assert 'thinking_level="low"' not in source
    # medium이 사용되어야 함
    assert 'thinking_level="medium"' in source


# ── STRUCT-2: PASS_WITH_FIX SC 다수결 분리 ────────────────────


def test_struct2_pwf_not_counted_as_pass():
    """PASS_WITH_FIX 다수 시 final_decision이 PASS_WITH_FIX여야 함."""
    import inspect
    from modules.domain.agents.director_auditor import DirectorQualityAuditor

    source = inspect.getsource(DirectorQualityAuditor._strategic_audit_with_self_consistency)
    assert "pwf_votes" in source
    assert 'PASS_WITH_FIX" if pwf_votes' in source


# ── STRUCT-3: Stage 2/3 audit Contradiction Firewall ──────────────


def test_struct3_audit_contradiction_firewall():
    """audit_strategic_plan에 Contradiction Firewall 코드 존재 확인."""
    import inspect
    from modules.domain.agents.director_auditor import DirectorQualityAuditor

    source = inspect.getsource(DirectorQualityAuditor.audit_strategic_plan)
    assert "Contradiction Firewall" in source
    assert "contradiction_check" in source
    assert "found_contradictions" in source
    assert "REJECT" in source
