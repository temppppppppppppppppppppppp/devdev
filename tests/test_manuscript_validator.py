"""
[V64 P2-7] ManuscriptValidator Unit Tests

_check_meta_references, _check_honorific_consistency, _check_intra_contradictions,
_check_cross_episode_duplication, validate_candidate 에 대한 단위 테스트.
"""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.domain.agents.manuscript_validator import ManuscriptValidator

# ══════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════


@pytest.fixture
def validator():
    """기본 ManuscriptValidator 인스턴스"""
    return ManuscriptValidator(genre_type="wuxia")


@pytest.fixture
def investment_validator():
    """투자물 ManuscriptValidator 인스턴스"""
    return ManuscriptValidator(genre_type="investment")


@pytest.fixture
def long_manuscript():
    """최소 4500자 이상의 테스트 원고"""
    base = (
        "이청풍은 검을 들고 천천히 앞으로 나아갔다. "
        "청풍검법의 제삼 초식이 그의 손끝에서 피어났다. "
        "바람처럼 가볍고 물처럼 유연한 검세가 허공을 갈랐다. "
        "상대의 눈이 크게 떠졌다. 이것이 바로 청풍산의 비전이란 말인가. "
        "철무련주는 이를 악물고 반격에 나섰다. "
        "하지만 이미 기선을 빼앗긴 상황에서 반격은 무의미했다. "
        "이청풍의 검이 마침내 상대의 어깨를 스쳤다. "
        "피가 튀었다. 첫 번째 상처였다. "
    )
    return (base * 30).strip()  # ~6000+ chars


@pytest.fixture
def sample_blueprint():
    """테스트용 블루프린트"""
    return {
        "ep_num": 10,
        "title": "결전의 날",
        "scene_breakdown": {
            "scene_1": {"summary": "청풍산장에서 결투 준비", "content": "이청풍이 검을 준비한다"},
            "scene_2": {"summary": "철무련주와의 대결", "content": "치열한 검법 대결이 벌어진다"},
        },
    }


# ══════════════════════════════════════════════════════════════
# Test 1: _check_meta_references
# ══════════════════════════════════════════════════════════════


class TestCheckMetaReferences:
    def test_episode_number_detected(self, validator):
        """EP 번호가 서술부에 노출되면 경고"""
        manuscript = "a" * 100 + " EP 6에서 주인공은 각성했다. 그때부터 모든 것이 달라졌다."
        result = validator._check_meta_references(manuscript)
        assert len(result["warnings"]) >= 1
        assert any("EP" in w for w in result["warnings"])

    def test_author_reference_detected(self, validator):
        """작가/독자 등 메타 참조 탐지"""
        manuscript = "a" * 100 + " 작가가 의도한 바와 같이 주인공은 성장했다."
        result = validator._check_meta_references(manuscript)
        assert len(result["warnings"]) >= 1

    def test_dialogue_excluded(self, validator):
        """대사 안의 메타 참조는 제외 (따옴표 내부)"""
        # 앞뒤 50자 이내에 " 쌍이 있으면 대사로 간주
        manuscript = "a" * 100 + ' "다음 회에 만나자" 라고 그가 말했다.'
        result = validator._check_meta_references(manuscript)
        # 대사 내부이므로 필터링
        assert len(result["warnings"]) == 0

    def test_clean_manuscript(self, validator):
        """메타 참조 없는 깨끗한 원고"""
        manuscript = "a" * 100 + " 이청풍은 검을 들고 싸웠다. 바람이 불었다. 승리했다."
        result = validator._check_meta_references(manuscript)
        assert len(result["warnings"]) == 0

    def test_short_manuscript_skip(self, validator):
        """100자 미만 원고는 스킵"""
        result = validator._check_meta_references("짧은 원고")
        assert result == {"warnings": [], "focus_points": []}


# ══════════════════════════════════════════════════════════════
# Test 2: _check_honorific_consistency
# ══════════════════════════════════════════════════════════════


class TestCheckHonorificConsistency:
    def test_consistent_honorifics(self, validator):
        """일관된 호칭은 경고 없음"""
        manuscript = (
            '"강형님, 어디로 가시는 겁니까?" 이청풍이 물었다. "강형님, 조심하시오." 뒤에서 다시 말했다. '
        ) * 5 + "a" * 200  # 200자 이상
        result = validator._check_honorific_consistency(manuscript)
        # "강형님"만 사용 → 불일치 없음
        assert len(result["warnings"]) == 0

    def test_short_manuscript_skip(self, validator):
        """200자 미만 원고는 스킵"""
        result = validator._check_honorific_consistency("짧은 원고")
        assert result == {"warnings": [], "focus_points": []}


# ══════════════════════════════════════════════════════════════
# Test 3: _check_intra_contradictions
# ══════════════════════════════════════════════════════════════


class TestCheckIntraContradictions:
    def test_lost_item_reuse(self, validator):
        """잃어버린 아이템을 다시 사용하면 경고"""
        manuscript = (
            "이청풍은 청풍검을 잃어버렸다. 절벽 아래로 떨어졌다. "
            "하지만 바로 다음 순간, 이청풍은 청풍검을 뽑아들었다. "
            "a" * 500  # 최소 500자
        )
        result = validator._check_intra_contradictions(manuscript)
        assert any("청풍검" in w for w in result.get("warnings", []))

    def test_recovered_item_ok(self, validator):
        """잃어버렸다가 되찾은 아이템 사용은 정상"""
        manuscript = "이청풍은 청풍검을 잃어버렸다. 그러나 곧 청풍검을 되찾았다. 다시 청풍검을 뽑아들었다. a" * 500
        result = validator._check_intra_contradictions(manuscript)
        # 되찾은 후 사용이므로 경고 없어야 함
        assert not any("청풍검" in w for w in result.get("warnings", []))

    def test_short_manuscript_skip(self, validator):
        """500자 미만 원고는 스킵"""
        result = validator._check_intra_contradictions("짧은 원고")
        assert result == {"warnings": [], "focus_points": []}


# ══════════════════════════════════════════════════════════════
# Test 4: _check_cross_episode_duplication
# ══════════════════════════════════════════════════════════════


class TestCheckCrossEpisodeDuplication:
    def test_high_overlap_warning(self, validator):
        """높은 중복률이면 WARNING"""
        # 동일한 텍스트를 현재 원고와 이전 원고에 사용
        shared_text = "이청풍은 검을 들고 나아갔다 바람이 불었다 하늘이 맑았다 " * 20
        manuscript = shared_text
        recent = [{"ep_num": 5, "content": shared_text}]
        result = validator._check_cross_episode_duplication(manuscript, recent)
        assert len(result["warnings"]) >= 1

    def test_no_overlap_clean(self, validator):
        """중복 없으면 경고 없음"""
        manuscript = "이청풍은 검을 들었다 바람은 차가웠다 하늘에 구름이 떠다녔다 " * 20
        recent = [{"ep_num": 5, "content": "완전히 다른 텍스트 내용이다 철무련주가 등장했다 " * 20}]
        result = validator._check_cross_episode_duplication(manuscript, recent)
        assert len(result["warnings"]) == 0

    def test_empty_recent_no_warning(self, validator):
        """최근 원고 없으면 경고 없음"""
        manuscript = "이청풍은 검을 들었다 " * 20
        result = validator._check_cross_episode_duplication(manuscript, [])
        assert result == {"warnings": [], "focus_points": []}

    def test_short_manuscript_skip(self, validator):
        """짧은 원고는 스킵"""
        result = validator._check_cross_episode_duplication("짧은 원고", [{"ep_num": 1, "content": "이전 원고 내용"}])
        assert result == {"warnings": [], "focus_points": []}


# ══════════════════════════════════════════════════════════════
# Test 5: validate_candidate (통합 검증)
# ══════════════════════════════════════════════════════════════


class TestValidateCandidate:
    def test_short_manuscript_warning(self, validator, sample_blueprint):
        """짧은 원고는 분량 경고"""
        short_manuscript = "이청풍은 검을 들었다." * 50  # ~1000자
        result = validator.validate_candidate(
            manuscript=short_manuscript, blueprint=sample_blueprint, prev_manuscript="", hud_report=""
        )
        # warnings에 분량 관련 경고가 있어야 함
        assert result is not None
        assert "warnings" in result
        # LENGTH_WARNING_THRESHOLD(4500) 미만이므로 분량 경고 기대
        if len(short_manuscript) < validator.LENGTH_WARNING_THRESHOLD:
            assert any("분량" in w or "글자" in w for w in result["warnings"])

    def test_adequate_manuscript(self, validator, long_manuscript, sample_blueprint):
        """충분한 분량의 원고는 분량 경고 없음"""
        result = validator.validate_candidate(
            manuscript=long_manuscript, blueprint=sample_blueprint, prev_manuscript="", hud_report=""
        )
        assert result is not None
        assert "warnings" in result
        # 분량 경고가 없거나, 있더라도 "부족" 관련은 아니어야
        length_warnings = [w for w in result["warnings"] if "분량 부족" in w]
        assert len(length_warnings) == 0

    def test_missing_scene_headers_surface_as_director_warning(self, validator, sample_blueprint):
        """씬 헤더 누락은 Director 참고용 구조 경고로 전달."""
        manuscript = (
            "청풍산장에서 결투 준비를 마친 이청풍이 검을 들었다. " * 90
            + "\n\n"
            + "철무련주와의 대결이 시작되고 치열한 검법 대결이 벌어진다. " * 90
        )

        result = validator.validate_candidate(
            manuscript=manuscript, blueprint=sample_blueprint, prev_manuscript="", hud_report=""
        )

        assert result["metrics"]["scene_headers_expected"] == 2
        assert result["metrics"]["scene_headers_found"] == 0
        assert any("씬 헤더/구분 구조 약함" in warning for warning in result["warnings"])
        assert any("씬 헤더/구분 구조 확인 필요" in point for point in result["focus_points"])

    def test_numbered_scene_headers_do_not_warn(self, validator, sample_blueprint):
        manuscript = (
            "### 씬 1: 결투 준비\n\n"
            + ("청풍산장에서 결투 준비를 마친 이청풍이 검을 들었다. " * 90)
            + "\n\n"
            + "### 씬 2: 대결\n\n"
            + ("철무련주와의 대결이 시작되고 치열한 검법 대결이 벌어진다. " * 90)
        )

        result = validator.validate_candidate(
            manuscript=manuscript, blueprint=sample_blueprint, prev_manuscript="", hud_report=""
        )

        assert result["metrics"]["scene_headers_expected"] == 2
        assert result["metrics"]["scene_headers_found"] == 2
        assert not any("씬 헤더/구분 구조 약함" in warning for warning in result["warnings"])

    def test_returns_dict_with_expected_keys(self, validator, long_manuscript, sample_blueprint):
        """반환값에 필요한 키가 존재"""
        result = validator.validate_candidate(
            manuscript=long_manuscript, blueprint=sample_blueprint, prev_manuscript="", hud_report=""
        )
        assert isinstance(result, dict)
        assert "warnings" in result
        assert "warning_count" in result
        assert "focus_points" in result
        assert "metrics" in result
        assert "has_critical_warning" in result
        assert isinstance(result["metrics"], dict)
        assert "length" in result["metrics"]

    def test_none_blueprint_graceful(self, validator, long_manuscript):
        """blueprint가 비어있어도 에러 없이 동작"""
        result = validator.validate_candidate(
            manuscript=long_manuscript, blueprint={}, prev_manuscript="", hud_report=""
        )
        assert result is not None
        assert "warnings" in result
