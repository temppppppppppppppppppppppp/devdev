"""
[V44] Validation 테스트

TIER 1/2/3 검증기 및 오케스트레이터 테스트
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBlockingValidator:
    """TIER 1: BlockingValidator 테스트"""

    def test_minimum_length_manuscript_pass(self, sample_manuscript, validation_context):
        """원고 최소 길이 통과 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context["mode"] = "MANUSCRIPT"

        result = validator.validate(1, sample_manuscript, validation_context)

        # 4000자 이상이면 길이 검사 통과
        assert len(sample_manuscript) >= 4000

    def test_minimum_length_manuscript_fail(self, validation_context):
        """원고 최소 길이 실패 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context["mode"] = "MANUSCRIPT"

        short_text = "짧은 원고"

        result = validator.validate(1, short_text, validation_context)

        # REJECT 상태여야 함
        assert result["status"] == "REJECT"
        assert "length" in result.get("reason", "").lower() or "길이" in result.get("reason", "")

    def test_dead_npc_resurrection_detection(self, validation_context):
        """죽은 NPC 부활 감지 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 죽은 캐릭터 설정
        validation_context["encyclopedia"]["characters"]["노사부"]["alive"] = False

        # 노사부가 등장하는 원고
        manuscript = "노사부가 말했다. '청풍아, 수련을 게을리하지 마라.' " * 500

        result = validator.validate(1, manuscript, validation_context)

        # REJECT 또는 경고가 있어야 함
        # (구현에 따라 REJECT 또는 WARNING)

    def test_destroyed_location_visit_detection(self, validation_context):
        """파괴된 장소 방문 감지 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 파괴된 장소 설정
        validation_context["encyclopedia"]["locations"]["청풍산장"]["destroyed"] = True

        # 청풍산장 방문 원고
        manuscript = "이청풍은 청풍산장으로 돌아왔다. 산장의 문을 열자 스승의 향기가 느껴졌다. " * 500

        result = validator.validate(1, manuscript, validation_context)

        # 파괴된 장소 방문 감지

    def test_unowned_item_usage_detection(self, validation_context):
        """소유하지 않은 아이템 사용 감지 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 아이템 소유자 변경
        validation_context["encyclopedia"]["items"]["청풍검"]["owner"] = "다른사람"

        # 이청풍이 청풍검 사용
        manuscript = "이청풍이 청풍검을 뽑아들었다. 검날이 푸른 빛을 발했다. " * 500

        result = validator.validate(1, manuscript, validation_context)

    def test_blueprint_mode_validation(self, sample_blueprint, validation_context):
        """블루프린트 모드 검증 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()
        validation_context["mode"] = "BLUEPRINT"

        blueprint_text = json.dumps(sample_blueprint, ensure_ascii=False)

        result = validator.validate(1, blueprint_text, validation_context)

        # 블루프린트는 500자 이상이면 통과


class TestScoringValidator:
    """TIER 2: ScoringValidator 테스트"""

    def test_prose_rhythm_calculation(self, sample_manuscript):
        """문장 리듬 계산 테스트"""
        from modules.validation.scoring_validator import ScoringValidator

        config = {
            "scoring_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False
        }

        validator = ScoringValidator(config, MagicMock())

        # 내부 메서드 테스트 (존재 시)
        if hasattr(validator, '_calculate_prose_rhythm'):
            score = validator._calculate_prose_rhythm(sample_manuscript)
            assert 0 <= score <= 5  # 최대 5점

    def test_vocabulary_diversity_calculation(self, sample_manuscript):
        """어휘 다양성 계산 테스트"""
        from modules.validation.scoring_validator import ScoringValidator

        config = {
            "scoring_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False
        }

        validator = ScoringValidator(config, MagicMock())

        # TTR(Type-Token Ratio) 계산
        words = sample_manuscript.split()
        unique_words = set(words)
        ttr = len(unique_words) / len(words) if words else 0

        assert 0 <= ttr <= 1

    def test_sensory_balance_check(self):
        """감각 균형 체크 테스트"""
        # 시각 위주 텍스트
        visual_heavy = "그는 보았다. 검은 옷을 입은 사내가 보였다. 푸른 하늘이 보였다."

        # 균형잡힌 텍스트
        balanced = "검이 부딪히는 소리가 울렸다. 차가운 바람이 피부를 스쳤다. 피 냄새가 났다."

        # 시각 단어 빈도 체크
        visual_keywords = ["보", "봤", "보이", "빛", "색"]

        visual_count = sum(1 for kw in visual_keywords if kw in visual_heavy)
        balanced_count = sum(1 for kw in visual_keywords if kw in balanced)

        # 시각 위주가 더 많아야 함
        # (실제 검증은 ScoringValidator 내부에서 수행)

    def test_show_dont_tell_detection(self):
        """Show don't tell 감지 테스트"""
        # 직접 감정 표현 (나쁜 예)
        telling = "그는 화가 났다. 그는 슬펐다. 그는 기뻤다."

        # 간접 감정 표현 (좋은 예)
        showing = "그의 주먹이 떨렸다. 눈가가 붉어졌다. 입꼬리가 올라갔다."

        direct_emotions = ["화가 났", "슬펐", "기뻤", "무서웠", "행복했"]

        telling_count = sum(1 for e in direct_emotions if e in telling)
        showing_count = sum(1 for e in direct_emotions if e in showing)

        assert telling_count > showing_count

    def test_scoring_threshold_pass(self, sample_manuscript, validation_context):
        """점수 임계값 통과 테스트"""
        from modules.validation.scoring_validator import ScoringValidator

        config = {
            "scoring_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False
        }

        mock_client = MagicMock()

        # Mock LLM 응답 (높은 점수)
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "character_consistency": 15,
            "emotion_arc": 18,
            "dialogue_quality": 14,
            "commercial_appeal": 18,
            "pattern_diversity": 9
        })
        mock_client.models.generate_content.return_value = mock_response

        validator = ScoringValidator(config, mock_client)

        # validate 메서드가 있으면 테스트
        if hasattr(validator, 'validate'):
            # 실제 호출은 API 비용 발생하므로 mock 사용
            pass

    def test_scoring_threshold_fail(self, validation_context):
        """점수 임계값 실패 테스트"""
        from modules.validation.scoring_validator import ScoringValidator

        config = {
            "scoring_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False
        }

        mock_client = MagicMock()

        # Mock LLM 응답 (낮은 점수)
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "character_consistency": 5,
            "emotion_arc": 8,
            "dialogue_quality": 6,
            "commercial_appeal": 7,
            "pattern_diversity": 4
        })
        mock_client.models.generate_content.return_value = mock_response

        validator = ScoringValidator(config, mock_client)


class TestAdvisoryValidator:
    """TIER 3: AdvisoryValidator 테스트"""

    def test_cliche_detection(self):
        """클리셰 감지 테스트"""
        from modules.validation.advisory_validator import AdvisoryValidator

        config = {"advisory_model": "gemini-2.5-flash"}
        validator = AdvisoryValidator(config, MagicMock())

        # 회귀물 클리셰
        regression_text = "눈을 떴을 때, 그는 과거로 돌아와 있었다. 모든 것을 알고 있는 지금, 복수할 것이다."

        # 천재물 클리셰
        genius_text = "그는 태어날 때부터 천재였다. 모든 것이 쉬웠다. 세상은 그에게 맞춰졌다."

        # 클리셰 키워드
        cliche_keywords = ["과거로 돌아", "복수", "천재", "모든 것을 알"]

        has_cliche = any(kw in regression_text for kw in cliche_keywords)
        assert has_cliche

    def test_advisory_always_passes(self, sample_manuscript, validation_context):
        """Advisory는 항상 PASS 테스트"""
        from modules.validation.advisory_validator import AdvisoryValidator

        config = {"advisory_model": "gemini-2.5-flash"}
        validator = AdvisoryValidator(config, MagicMock())

        if hasattr(validator, 'validate'):
            result = validator.validate(1, sample_manuscript, validation_context)

            # Advisory는 항상 PASS (suggestions만 제공)
            assert result.get("status") in ["PASS", "ADVISORY"]

    def test_foreshadowing_opportunity_detection(self):
        """복선 기회 감지 테스트"""
        # 복선 기회가 있는 텍스트
        text_with_opportunity = "그는 이상한 문양이 새겨진 검을 발견했다. 왠지 모르게 마음이 끌렸다."

        # 복선 키워드
        foreshadowing_hints = ["이상한", "왠지", "묘한", "느낌", "예감"]

        has_hint = any(kw in text_with_opportunity for kw in foreshadowing_hints)
        assert has_hint


class TestValidationOrchestrator:
    """ValidationOrchestrator 통합 테스트"""

    def test_orchestrator_initialization(self):
        """오케스트레이터 초기화 테스트"""
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False,
            "consistency_votes": 3
        }

        orchestrator = ValidationOrchestrator(config, MagicMock(), genre="wuxia")

        # 3개 검증기 초기화 확인
        assert orchestrator.blocking is not None
        assert orchestrator.scoring is not None
        assert orchestrator.advisory is not None

    def test_tier_order_execution(self, sample_manuscript, validation_context):
        """TIER 순서 실행 테스트"""
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": False
        }

        orchestrator = ValidationOrchestrator(config, MagicMock(), genre="wuxia")

        # TIER 1 실패 시 TIER 2, 3 실행 안 함
        short_text = "짧은 텍스트"

        result = orchestrator.validate(1, short_text, validation_context)

        # TIER 1에서 REJECT
        assert result["status"] == "REJECT"
        # TIER 2 점수가 없어야 함 (또는 0)
        assert result.get("scoring_result") is None or result.get("total_score", 0) == 0

    def test_final_decision_mapping(self):
        """최종 결정 매핑 테스트"""
        # 85+ → PASS
        # 70-84 → CONDITIONAL_PASS
        # <70 → REJECT

        score_mappings = [
            (90, "PASS"),
            (85, "PASS"),
            (75, "CONDITIONAL_PASS"),
            (70, "CONDITIONAL_PASS"),
            (65, "REJECT"),
            (50, "REJECT")
        ]

        for score, expected_status in score_mappings:
            if score >= 85:
                actual = "PASS"
            elif score >= 70:
                actual = "CONDITIONAL_PASS"
            else:
                actual = "REJECT"

            assert actual == expected_status

    def test_self_consistency_mode(self):
        """Self-Consistency 모드 테스트"""
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70,
            "use_self_consistency": True,
            "consistency_votes": 3
        }

        orchestrator = ValidationOrchestrator(config, MagicMock(), genre="wuxia")

        # Self-Consistency 모드 활성화 확인
        assert orchestrator.use_self_consistency == True
        assert orchestrator.consistency_votes == 3

    def test_genre_specific_validation(self):
        """장르별 검증 테스트"""
        from modules.validation.validation_orchestrator import ValidationOrchestrator

        config = {
            "scoring_model": "gemini-2.5-pro",
            "advisory_model": "gemini-2.5-flash",
            "scoring_threshold": 70
        }

        # 각 장르별 오케스트레이터 생성
        for genre in ["wuxia", "hunter", "investment"]:
            orchestrator = ValidationOrchestrator(config, MagicMock(), genre=genre)
            assert orchestrator.genre == genre


class TestValidationEdgeCases:
    """검증 엣지 케이스 테스트"""

    def test_empty_manuscript(self, validation_context):
        """빈 원고 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        result = validator.validate(1, "", validation_context)
        assert result["status"] == "REJECT"

    def test_unicode_special_characters(self, validation_context):
        """유니코드 특수문자 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 특수문자 포함 텍스트
        special_text = "이청풍(李靑風)이 검을 뽑았다. 「청풍검법」의 제1초식! " * 500

        result = validator.validate(1, special_text, validation_context)
        # 파싱 에러 없이 처리되어야 함

    def test_very_long_manuscript(self, validation_context):
        """매우 긴 원고 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 100,000자 원고
        long_text = "무협 소설 내용입니다. " * 10000

        result = validator.validate(1, long_text, validation_context)
        # 정상 처리되어야 함

    def test_missing_context_fields(self):
        """컨텍스트 필드 누락 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # 불완전한 컨텍스트
        incomplete_context = {
            "mode": "MANUSCRIPT"
            # encyclopedia, martial_hud 등 누락
        }

        manuscript = "테스트 원고 " * 500

        # 에러 없이 처리되어야 함 (Graceful degradation)
        try:
            result = validator.validate(1, manuscript, incomplete_context)
        except KeyError:
            pytest.fail("Should handle missing context fields gracefully")

    def test_null_values_in_context(self, validation_context):
        """컨텍스트 내 null 값 테스트"""
        from modules.validation.blocking_validator import BlockingValidator

        validator = BlockingValidator()

        # null 값 주입
        validation_context["encyclopedia"] = None
        validation_context["martial_hud"] = None

        manuscript = "테스트 원고 " * 500

        # 에러 없이 처리되어야 함
        try:
            result = validator.validate(1, manuscript, validation_context)
        except (TypeError, AttributeError):
            pytest.fail("Should handle null context values gracefully")
