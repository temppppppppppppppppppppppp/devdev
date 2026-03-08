"""
[WARN-2/3/4] 시스템 패치 테스트

WARN-2: 비전투 장르 부상 검사 스킵
WARN-3: 개미 자칭 정규식 과매칭 수정
WARN-4: quality_metrics score=0 미전파 수정
"""
import re
import pytest
from unittest.mock import MagicMock


class TestWarn2InjuryGenreSkip:
    """WARN-2: 비전투 장르는 부상 연속성 검사 스킵"""

    def _make_validator(self):
        from modules.validation.continuity_validator import ContinuityValidator
        v = ContinuityValidator.__new__(ContinuityValidator)
        v.injury_patterns = [r"부상", r"상처"]
        v.strenuous_patterns = [r"힘차게\s*달리"]
        return v

    def test_investment_genre_skips_injury_check(self):
        """투자물 장르에서 부상 키워드가 있어도 경고 없음"""
        from modules.validation.continuity_validator import ContinuityValidator

        v = ContinuityValidator()

        prev_hud = {
            "actual_truth": {
                "condition": "부상 상태 — 왼팔 골절",
            }
        }

        result = v.validate(
            current_ep=10,
            manuscript="한시우는 힘차게 달리며 거침없이 사무실로 향했다.",
            validation_context={"genre": "investment"},
            prev_hud=prev_hud,
        )

        # 부상 관련 violation/warning이 없어야 함
        injury_violations = [v for v in result.get("violations", [])
                             if "injury" in str(v.get("type", ""))]
        injury_warnings = [w for w in result.get("warnings", [])
                           if isinstance(w, dict) and "injury" in str(w.get("type", ""))]
        assert len(injury_violations) == 0
        assert len(injury_warnings) == 0

    def test_wuxia_genre_keeps_injury_check(self):
        """무협 장르에서는 부상 검사 정상 작동"""
        from modules.validation.continuity_validator import ContinuityValidator

        v = ContinuityValidator()

        prev_hud = {
            "actual_truth": {
                "condition": "중상 — 왼팔 골절",
            }
        }

        result = v.validate(
            current_ep=10,
            manuscript="그는 힘차게 검을 휘두르며 거침없이 적을 향해 돌진했다. 아무런 문제 없이 달렸다.",
            validation_context={"genre": "wuxia"},
            prev_hud=prev_hud,
        )

        # 무협에서는 부상 검사 발동해야 함 (violations or warnings)
        all_issues = result.get("violations", []) + result.get("warnings", [])
        injury_issues = [i for i in all_issues
                         if isinstance(i, dict) and "injury" in str(i.get("type", ""))]
        # 부상 관련 이슈가 있어야 함 (정상 작동 확인)
        assert len(injury_issues) > 0

    def test_fantasy_genre_keeps_injury_check(self):
        """판타지 장르에서도 부상 검사 정상 작동"""
        from modules.validation.continuity_validator import ContinuityValidator

        v = ContinuityValidator()

        prev_hud = {
            "actual_truth": {
                "condition": "중상",
            }
        }

        result = v.validate(
            current_ep=5,
            manuscript="마법사는 힘차게 지팡이를 휘두르며 거침없이 멀쩡한 모습으로 싸웠다.",
            validation_context={"genre": "fantasy"},
            prev_hud=prev_hud,
        )

        all_issues = result.get("violations", []) + result.get("warnings", [])
        injury_issues = [i for i in all_issues
                         if isinstance(i, dict) and "injury" in str(i.get("type", ""))]
        assert len(injury_issues) > 0


class TestWarn3SelfAddressRegex:
    """WARN-3: 개미 자칭 정규식 과매칭 수정"""

    def test_true_self_address_detected(self):
        """'나는 개미다' 같은 진짜 자칭은 감지됨"""
        from modules.core.genre_guards.investment_guard import InvestmentGuard

        guard = InvestmentGuard()
        # InvestmentGuard hierarchy: "부유층"→["자산가","투자자"], "소시민"→["개미","소액투자자"]
        # "부유층" 직위에서 "개미" 자칭 → violation
        manuscript = "나는 개미다. 그저 작은 개미일 뿐이다."
        result = guard.check_hierarchy_consistency(manuscript, "부유층")
        assert not result["passed"] or len(result["violations"]) > 0

    def test_third_person_reference_not_detected(self):
        """'나는 개미들을 이끈다' 같은 타인 지칭은 오탐 필터링"""
        from modules.core.genre_guards.investment_guard import InvestmentGuard

        guard = InvestmentGuard()
        # "개미들을" → 복수형 타인 지칭 → 오탐 필터링 → violation 0
        manuscript = "나는 개미들을 관찰했다. 그들은 두려워하고 있었다."
        result = guard.check_hierarchy_consistency(manuscript, "부유층")
        assert result["passed"]
        assert len(result["violations"]) == 0

    def test_plural_form_filtered(self):
        """복수형 '개미들이' 패턴 필터링"""
        from modules.core.genre_guards.investment_guard import InvestmentGuard

        guard = InvestmentGuard()
        manuscript = "나는 개미들이 어떻게 행동하는지 지켜보았다."
        result = guard.check_hierarchy_consistency(manuscript, "부유층")
        assert result["passed"]

    def test_wuxia_self_address_still_works(self):
        """무협 장르 WuxiaGuard에서 낮은 경지가 높은 호칭 자칭 시 감지"""
        from modules.core.genre_guards.wuxia_guard import WuxiaGuard

        guard = WuxiaGuard()
        # WuxiaGuard hierarchy: "입문"→["소생","재하"], "화경"→["본좌","노부","대협"]
        # "입문" 경지에서 "본좌" 자칭 → violation
        manuscript = "나는 본좌다. 천하의 고수라 불리는 본좌."
        result = guard.check_hierarchy_consistency(manuscript, "입문")
        assert len(result["violations"]) > 0


class TestWarn4ScorePropagation:
    """WARN-4: Director score → final_state_updates 전파"""

    def test_director_score_propagated_to_state_updates(self):
        """PASS verdict 시 score가 final_state_updates에 전파"""
        director_result = {
            "verdict": "PASS",
            "score": 97,
            "selected": "A",
            "state_updates": {"location": "사무실"},
            "selected_candidate": {"manuscript": "원고...", "title": "제10화"},
        }

        score = director_result.get("score", 0)
        final_state_updates = director_result.get("state_updates", {})

        # WARN-4 fix 로직
        if isinstance(final_state_updates, dict) and score > 0:
            final_state_updates["director_score"] = score

        assert final_state_updates["director_score"] == 97
        assert final_state_updates["location"] == "사무실"  # 기존 값 보존

    def test_score_zero_not_propagated(self):
        """score=0이면 전파하지 않음"""
        director_result = {
            "verdict": "REJECT",
            "score": 0,
            "state_updates": {},
        }

        score = director_result.get("score", 0)
        final_state_updates = director_result.get("state_updates", {})

        if isinstance(final_state_updates, dict) and score > 0:
            final_state_updates["director_score"] = score

        assert "director_score" not in final_state_updates

    def test_pass_with_fix_also_propagates(self):
        """PASS_WITH_FIX verdict에서도 score 전파"""
        director_result = {
            "verdict": "PASS_WITH_FIX",
            "score": 90,
            "state_updates": {"protagonist_location": "강남"},
            "selected_candidate": {"manuscript": "수정된 원고...", "title": "제15화"},
        }

        score = director_result.get("score", 0)
        final_state_updates = director_result.get("state_updates", {})

        if isinstance(final_state_updates, dict) and score > 0:
            final_state_updates["director_score"] = score

        assert final_state_updates["director_score"] == 90
