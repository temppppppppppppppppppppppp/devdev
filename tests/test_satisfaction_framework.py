"""
[Phase 3-D1] Reader Satisfaction Framework — 점수축/가중치 테스트

reader_satisfaction 차원 도입 + 배점/가중치 재분배 검증.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.domain.agents.director_grading import DirectorGradingSystem
from modules.validation.scoring_validator import ScoringValidator

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def sv():
    """LLM 없는 ScoringValidator (fallback 모드)"""
    return ScoringValidator(client=None, genre="wuxia")


@pytest.fixture
def sv_with_mock_llm():
    """Mock LLM이 있는 ScoringValidator"""
    client = MagicMock()
    return client, ScoringValidator(client=client, genre="wuxia")


@pytest.fixture
def grading():
    """DirectorGradingSystem (director 없음)"""
    return DirectorGradingSystem(director=None)


@pytest.fixture
def sample_manuscript():
    return "이청풍은 새벽녘에 검을 들었다. 내공이 검끝에 모이며 푸른 빛이 일었다. " * 300


@pytest.fixture
def sample_context():
    return {"genre": "wuxia", "martial_hud": {}}


# ── 1. 점수축 존재 + max=10 ────────────────────────────────────


class TestScoringDimensionExists:
    """reader_satisfaction 차원이 존재하고 max=10인지 검증"""

    def test_fallback_has_reader_satisfaction(self, sv, sample_manuscript, sample_context):
        """Fallback 모드에서 reader_satisfaction 키가 존재하고 max=10"""
        scores = sv._fallback_llm_scores(sample_manuscript, sample_context)
        assert "reader_satisfaction" in scores
        assert scores["reader_satisfaction"]["max"] == 10

    def test_llm_prompt_contains_reader_satisfaction(self, sv_with_mock_llm, sample_manuscript, sample_context):
        """LLM 프롬프트에 reader_satisfaction 키워드가 포함됨"""
        client, sv = sv_with_mock_llm

        # LLM 응답 mock
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "character_consistency": {"score": 12, "max": 15, "reason": "OK"},
                "emotion_arc": {"score": 12, "max": 15, "reason": "OK"},
                "dialogue_quality": {"score": 12, "max": 15, "reason": "OK"},
                "commercial_appeal": {"score": 12, "max": 15, "reason": "OK"},
                "pattern_diversity": {"score": 8, "max": 10, "reason": "OK"},
                "reader_satisfaction": {"score": 8, "max": 10, "reason": "OK"},
            }
        )
        client.models.generate_content.return_value = mock_response

        result = sv._calculate_llm_scores(sample_manuscript, sample_context)
        assert "reader_satisfaction" in result

        # 프롬프트에 reader_satisfaction이 포함되었는지 확인
        call_args = client.models.generate_content.call_args
        prompt = call_args.kwargs.get("contents", "") if call_args.kwargs else call_args[1].get("contents", "")
        assert "reader_satisfaction" in prompt


# ── 2. 배점 총합 80 유지 ───────────────────────────────────────


class TestLLMScoreTotal:
    """LLM 점수 총합이 80점으로 유지되는지 검증"""

    def test_fallback_max_total_is_80(self, sv, sample_manuscript, sample_context):
        """Fallback LLM 점수 max 합계 = 80"""
        scores = sv._fallback_llm_scores(sample_manuscript, sample_context)
        total_max = sum(v["max"] for v in scores.values())
        assert total_max == 80

    def test_full_validate_max_score_is_100(self, sv, sample_manuscript, sample_context):
        """Python(20) + LLM(80) = 총 100점 max"""
        result = sv.validate(sample_manuscript, sample_context)
        assert result["max_score"] == 100


# ── 3. 가중치 총합 1.00 유지 ──────────────────────────────────


class TestQualityWeightsTotal:
    """QUALITY_WEIGHTS 합계가 1.00인지 검증"""

    def test_weights_sum_is_one(self, grading):
        """QUALITY_WEIGHTS 합계 = 1.00"""
        total = sum(grading.QUALITY_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"Expected 1.0, got {total}"

    def test_satisfaction_weight_exists(self, grading):
        """satisfaction 카테고리가 0.10 가중치로 존재"""
        assert "satisfaction" in grading.QUALITY_WEIGHTS
        assert grading.QUALITY_WEIGHTS["satisfaction"] == 0.10

    def test_category_mapping_has_satisfaction(self, grading):
        """category_mapping에 satisfaction → reader_satisfaction 포함"""
        # _extract_category_score를 통해 간접 검증
        breakdown = {
            "reader_satisfaction": {"score": 8, "max": 10},
            "emotion_arc": {"score": 12, "max": 15},
        }
        score = grading._extract_category_score(breakdown, "satisfaction")
        # reader_satisfaction(80%) + emotion_arc(80%) = 평균 80
        assert score == pytest.approx(80.0, abs=0.1)


# ── 4. satisfaction 필드 포함 시 계산 반영 ─────────────────────


class TestSatisfactionCalculation:
    """satisfaction 필드가 최종 등급 계산에 반영되는지 검증"""

    def test_grade_includes_satisfaction_category(self, grading, sample_manuscript):
        """grade_manuscript_v59 결과에 satisfaction breakdown 포함"""
        validation_result = {
            "total_score": 75,
            "breakdown": {
                "scene_completeness": {"score": 4, "max": 5},
                "prose_rhythm": {"score": 4, "max": 5},
                "character_consistency": {"score": 12, "max": 15},
                "emotion_arc": {"score": 12, "max": 15},
                "commercial_appeal": {"score": 12, "max": 15},
                "pattern_diversity": {"score": 8, "max": 10},
                "reader_satisfaction": {"score": 8, "max": 10},
            },
        }
        result = grading.grade_manuscript_v59(1, sample_manuscript, validation_result)
        assert "satisfaction" in result["breakdown"]
        assert result["breakdown"]["satisfaction"]["weight"] == 0.10


# ── 5. satisfaction 누락 시 fallback ──────────────────────────


class TestSatisfactionFallback:
    """reader_satisfaction 누락 시 안전하게 동작하는지 검증"""

    def test_missing_reader_satisfaction_no_crash(self, grading, sample_manuscript):
        """breakdown에 reader_satisfaction이 없어도 정상 동작"""
        validation_result = {
            "total_score": 70,
            "breakdown": {
                "character_consistency": {"score": 12, "max": 15},
                "emotion_arc": {"score": 12, "max": 15},
                "dialogue_quality": {"score": 12, "max": 15},
                "commercial_appeal": {"score": 12, "max": 15},
                "pattern_diversity": {"score": 8, "max": 10},
                # reader_satisfaction 의도적 누락
            },
        }
        result = grading.grade_manuscript_v59(1, sample_manuscript, validation_result)
        # 에러 없이 등급 반환
        assert result["grade"] in ("A", "B", "C", "D")
        # satisfaction 카테고리는 기본값(50)으로 처리
        assert "satisfaction" in result["breakdown"]

    def test_validate_without_llm_includes_satisfaction(self, sv, sample_manuscript, sample_context):
        """LLM 없이 validate() 시 reader_satisfaction 포함"""
        result = sv.validate(sample_manuscript, sample_context)
        assert "reader_satisfaction" in result["breakdown"]
        score = result["breakdown"]["reader_satisfaction"]["score"]
        assert 0 <= score <= 10


# ── 6. 기존 샘플 입력 회귀 ────────────────────────────────────


class TestRegressionExistingFields:
    """기존 필드 계산이 변경되지 않았는지 검증"""

    def test_python_scores_unchanged(self, sv, sample_manuscript, sample_context):
        """Python 4차원(prose_rhythm, vocabulary_diversity, sensory_balance, show_dont_tell) 총합 20 유지"""
        python_scores = sv._calculate_python_scores(sample_manuscript, sample_context)
        total_max = sum(v["max"] for v in python_scores.values())
        assert total_max == 20
        assert len(python_scores) == 4

    def test_existing_llm_dimensions_present(self, sv, sample_manuscript, sample_context):
        """기존 5개 LLM 차원이 여전히 존재"""
        scores = sv._fallback_llm_scores(sample_manuscript, sample_context)
        for key in (
            "character_consistency",
            "emotion_arc",
            "dialogue_quality",
            "commercial_appeal",
            "pattern_diversity",
        ):
            assert key in scores, f"Missing key: {key}"


# ── 7. 경계값 처리 ───────────────────────────────────────────


class TestBoundaryValues:
    """reader_satisfaction 경계값(0, 10) 처리 검증"""

    def test_score_zero_contributes_nothing(self, grading, sample_manuscript):
        """reader_satisfaction=0 → satisfaction 카테고리 점수 감소"""
        validation_result = {
            "total_score": 50,
            "breakdown": {
                "reader_satisfaction": {"score": 0, "max": 10},
                "emotion_arc": {"score": 0, "max": 15},
            },
        }
        result = grading.grade_manuscript_v59(1, sample_manuscript, validation_result)
        satisfaction_score = result["breakdown"]["satisfaction"]["score"]
        assert satisfaction_score == 0.0

    def test_score_max_contributes_full(self, grading, sample_manuscript):
        """reader_satisfaction=10/10 → satisfaction 카테고리 점수 100"""
        validation_result = {
            "total_score": 90,
            "breakdown": {
                "reader_satisfaction": {"score": 10, "max": 10},
                "emotion_arc": {"score": 15, "max": 15},
            },
        }
        result = grading.grade_manuscript_v59(1, sample_manuscript, validation_result)
        satisfaction_score = result["breakdown"]["satisfaction"]["score"]
        assert satisfaction_score == 100.0

    def test_llm_clamping_reader_satisfaction(self, sv_with_mock_llm, sample_manuscript, sample_context):
        """LLM이 max 초과 점수 반환 시 클램핑"""
        client, sv = sv_with_mock_llm

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "character_consistency": {"score": 15, "max": 15, "reason": "OK"},
                "emotion_arc": {"score": 15, "max": 15, "reason": "OK"},
                "dialogue_quality": {"score": 15, "max": 15, "reason": "OK"},
                "commercial_appeal": {"score": 15, "max": 15, "reason": "OK"},
                "pattern_diversity": {"score": 10, "max": 10, "reason": "OK"},
                "reader_satisfaction": {"score": 99, "max": 10, "reason": "과대평가"},
            }
        )
        client.models.generate_content.return_value = mock_response

        result = sv._calculate_llm_scores(sample_manuscript, sample_context)
        # 클램핑: 99 → 10
        assert result["reader_satisfaction"]["score"] == 10


# ── 8. 설정 누락/오류 시 안전 동작 ────────────────────────────


class TestConfigSafety:
    """GENRE_WEIGHTS에 reader_satisfaction 키 누락 시 안전 동작"""

    def test_unknown_genre_uses_default_weight(self):
        """알 수 없는 장르 → GENRE_WEIGHTS default(1.0) 사용"""
        sv = ScoringValidator(client=None, genre="unknown_genre")
        weights = sv.GENRE_WEIGHTS.get("unknown_genre", {})
        # 없는 장르는 빈 dict → validate_v59에서 weight=1.0 fallback
        assert weights == {} or "reader_satisfaction" not in weights

    def test_validate_v59_with_reader_satisfaction(self, sv, sample_manuscript, sample_context):
        """validate_v59 장르 가중치 적용 시 reader_satisfaction 포함"""
        result = sv.validate_v59(sample_manuscript, sample_context)
        # weighted_breakdown에 reader_satisfaction 존재
        assert "reader_satisfaction" in result["weighted_breakdown"]
        weighted_data = result["weighted_breakdown"]["reader_satisfaction"]
        # wuxia 가중치 1.3 적용
        assert weighted_data["weight"] == 1.3

    def test_grading_all_categories_have_descriptions(self, grading):
        """모든 QUALITY_WEIGHTS 카테고리에 강점/약점 설명이 있는지 검증"""
        for category in grading.QUALITY_WEIGHTS:
            strength = grading._get_strength_description(category)
            weakness = grading._get_weakness_description(category)
            assert strength != "양호한 수준입니다", f"Missing strength description for {category}"
            assert weakness != "개선이 필요합니다", f"Missing weakness description for {category}"
