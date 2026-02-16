"""
[Phase 3-D3] Episode Satisfaction Tagging — DB + StateExtractor 테스트

에피소드 만족도 태깅 + DB CRUD + post-PASS 훅 검증.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.db_manager import DBManager

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def db(tmp_path):
    """In-memory DBManager"""
    d = DBManager(tmp_path / "test_sat.db")
    yield d
    d.close()


@pytest.fixture
def sample_tag():
    return {
        "ep_num": 3,
        "primary_tag": "성취",
        "satisfaction_score": 8,
        "protagonist_agency": "자력",
        "frustration_flag": False,
    }


@pytest.fixture
def state_extractor():
    """Mock LLM StateExtractor"""
    from modules.domain.agents.state_extractor import StateExtractor

    ctx = MagicMock()
    client = MagicMock()
    se = StateExtractor(ctx, client)
    return se


# ── 1. DB 테이블 생성 ──────────────────────────────────────────


class TestSatisfactionTable:
    """episode_satisfaction_tags 테이블 존재 및 스키마 검증"""

    def test_table_exists(self, db):
        """episode_satisfaction_tags 테이블이 존재"""
        cur = db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='episode_satisfaction_tags'"
        )
        assert cur.fetchone() is not None

    def test_table_columns(self, db):
        """필수 컬럼 5개 존재"""
        cur = db.cursor.execute("PRAGMA table_info(episode_satisfaction_tags)")
        columns = {row[1] for row in cur.fetchall()}
        expected = {
            "ep_num",
            "primary_tag",
            "satisfaction_score",
            "protagonist_agency",
            "frustration_flag",
            "created_at",
        }
        assert expected.issubset(columns)


# ── 2. DB CRUD ─────────────────────────────────────────────────


class TestSatisfactionCRUD:
    """save/get/get_recent CRUD 메서드 검증"""

    def test_save_and_get_roundtrip(self, db, sample_tag):
        """저장 후 조회 일치"""
        db.save_satisfaction_tag(3, sample_tag)
        result = db.get_satisfaction_tag(3)
        assert result is not None
        assert result["ep_num"] == 3
        assert result["primary_tag"] == "성취"
        assert result["satisfaction_score"] == 8
        assert result["protagonist_agency"] == "자력"
        assert result["frustration_flag"] is False

    def test_get_nonexistent_returns_none(self, db):
        """존재하지 않는 에피소드 조회 → None"""
        assert db.get_satisfaction_tag(999) is None

    def test_save_overwrites_existing(self, db, sample_tag):
        """같은 ep_num 재저장 시 덮어쓰기"""
        db.save_satisfaction_tag(3, sample_tag)
        updated = {**sample_tag, "primary_tag": "좌절", "frustration_flag": True}
        db.save_satisfaction_tag(3, updated)
        result = db.get_satisfaction_tag(3)
        assert result["primary_tag"] == "좌절"
        assert result["frustration_flag"] is True

    def test_frustration_flag_stored_as_int(self, db):
        """frustration_flag=True → DB에 1로 저장"""
        tag = {
            "primary_tag": "좌절",
            "satisfaction_score": 2,
            "protagonist_agency": "타인의존",
            "frustration_flag": True,
        }
        db.save_satisfaction_tag(1, tag)
        # 직접 SQL로 확인
        cur = db.cursor.execute("SELECT frustration_flag FROM episode_satisfaction_tags WHERE ep_num = 1")
        assert cur.fetchone()[0] == 1

    def test_get_recent_returns_time_order(self, db):
        """get_recent_satisfaction_tags가 오래된 순으로 반환"""
        for i in range(1, 6):
            tag = {"primary_tag": "일상" if i != 3 else "좌절", "satisfaction_score": 5, "frustration_flag": i == 3}
            db.save_satisfaction_tag(i, tag)

        recent = db.get_recent_satisfaction_tags(before_ep=6, lookback=5)
        assert len(recent) == 5
        assert recent[0]["ep_num"] == 1  # 가장 오래된 것 먼저
        assert recent[4]["ep_num"] == 5
        assert recent[2]["primary_tag"] == "좌절"

    def test_get_recent_lookback_limit(self, db):
        """lookback 파라미터로 조회 수 제한"""
        for i in range(1, 11):
            db.save_satisfaction_tag(i, {"primary_tag": "일상", "satisfaction_score": 5})
        recent = db.get_recent_satisfaction_tags(before_ep=11, lookback=3)
        assert len(recent) == 3
        assert recent[0]["ep_num"] == 8

    def test_get_recent_empty(self, db):
        """태그 없을 때 빈 리스트"""
        assert db.get_recent_satisfaction_tags(before_ep=1, lookback=5) == []

    def test_default_values_on_missing_keys(self, db):
        """tag_dict에 키 누락 시 기본값"""
        db.save_satisfaction_tag(1, {})
        result = db.get_satisfaction_tag(1)
        assert result["primary_tag"] == "일상"
        assert result["satisfaction_score"] == 5
        assert result["protagonist_agency"] == "자력"
        assert result["frustration_flag"] is False


# ── 3. StateExtractor 태깅 메서드 ──────────────────────────────


class TestExtractSatisfactionTag:
    """StateExtractor.extract_satisfaction_tag() 검증"""

    def test_llm_success_returns_valid_tag(self, state_extractor):
        """LLM 정상 응답 → 유효한 태그 반환"""
        mock_response = json.dumps({"primary_tag": "성취", "satisfaction_score": 9, "protagonist_agency": "자력"})
        state_extractor.ask = MagicMock(return_value=mock_response)

        result = state_extractor.extract_satisfaction_tag("이청풍이 강자를 제압했다.", 5)
        assert result["primary_tag"] == "성취"
        assert result["satisfaction_score"] == 9
        assert result["protagonist_agency"] == "자력"
        assert result["frustration_flag"] is False
        assert result["ep_num"] == 5

    def test_llm_frustration_sets_flag(self, state_extractor):
        """primary_tag=좌절 → frustration_flag=True"""
        mock_response = json.dumps({"primary_tag": "좌절", "satisfaction_score": 2, "protagonist_agency": "타인의존"})
        state_extractor.ask = MagicMock(return_value=mock_response)

        result = state_extractor.extract_satisfaction_tag("패배했다.", 3)
        assert result["frustration_flag"] is True

    def test_invalid_tag_defaults_to_ilsang(self, state_extractor):
        """유효하지 않은 primary_tag → '일상' fallback"""
        mock_response = json.dumps({"primary_tag": "알수없음", "satisfaction_score": 5})
        state_extractor.ask = MagicMock(return_value=mock_response)

        result = state_extractor.extract_satisfaction_tag("텍스트", 1)
        assert result["primary_tag"] == "일상"

    def test_score_clamped_to_range(self, state_extractor):
        """satisfaction_score 범위 1~10 클램핑"""
        mock_response = json.dumps({"primary_tag": "성취", "satisfaction_score": 99})
        state_extractor.ask = MagicMock(return_value=mock_response)

        result = state_extractor.extract_satisfaction_tag("텍스트", 1)
        assert result["satisfaction_score"] == 10

    def test_score_clamped_min(self, state_extractor):
        """satisfaction_score 최소값 1"""
        mock_response = json.dumps({"primary_tag": "좌절", "satisfaction_score": -5})
        state_extractor.ask = MagicMock(return_value=mock_response)

        result = state_extractor.extract_satisfaction_tag("텍스트", 1)
        assert result["satisfaction_score"] == 1

    def test_llm_failure_uses_fallback(self, state_extractor):
        """LLM 예외 → Python fallback"""
        state_extractor.ask = MagicMock(side_effect=Exception("API Error"))

        result = state_extractor.extract_satisfaction_tag("이청풍이 승리했다.", 1)
        assert result["primary_tag"] in {"성취", "성장", "전투", "이행", "일상", "좌절"}
        assert 1 <= result["satisfaction_score"] <= 10
        assert result["ep_num"] == 1


# ── 4. Fallback 키워드 분류 ────────────────────────────────────


class TestFallbackSatisfactionTag:
    """Python 키워드 기반 fallback 검증"""

    def test_achievement_keywords(self, state_extractor):
        result = state_extractor._fallback_satisfaction_tag("승리했다. 목표를 달성했다.", 1)
        assert result["primary_tag"] == "성취"
        assert result["satisfaction_score"] >= 7

    def test_frustration_keywords(self, state_extractor):
        result = state_extractor._fallback_satisfaction_tag("패배했다. 절망에 빠졌다.", 2)
        assert result["primary_tag"] == "좌절"
        assert result["frustration_flag"] is True

    def test_combat_keywords(self, state_extractor):
        result = state_extractor._fallback_satisfaction_tag("전투가 시작되었다. 검격이 날카로웠다.", 3)
        assert result["primary_tag"] == "전투"

    def test_empty_manuscript_defaults_ilsang(self, state_extractor):
        result = state_extractor._fallback_satisfaction_tag("", 1)
        assert result["primary_tag"] == "일상"
        assert result["satisfaction_score"] == 5

    def test_all_valid_tags_returned(self, state_extractor):
        """fallback이 항상 유효한 태그 반환"""
        valid_tags = {"성취", "성장", "전투", "이행", "일상", "좌절"}
        for text in ["승리", "패배", "전투", "이동했다", "수련했다", ""]:
            result = state_extractor._fallback_satisfaction_tag(text, 1)
            assert result["primary_tag"] in valid_tags


# ── 5. Stage4 훅 통합 ─────────────────────────────────────────


class TestStage4SatisfactionHook:
    """stage4_orchestrator의 만족도 태깅 훅 존재 검증"""

    def test_hook_code_exists_in_orchestrator(self):
        """stage4_orchestrator에 만족도 태깅 훅 코드 존재"""
        import inspect

        from modules.core.stage4_orchestrator import Stage4Orchestrator

        source = inspect.getsource(Stage4Orchestrator)
        assert "extract_satisfaction_tag" in source
        assert "save_satisfaction_tag" in source

    def test_hook_exception_non_propagating(self):
        """태깅 훅 예외가 PASS 처리를 차단하지 않음"""
        import inspect

        from modules.core.stage4_orchestrator import Stage4Orchestrator

        source = inspect.getsource(Stage4Orchestrator)
        # 만족도 태깅 코드가 try-except 내에 있는지 확인
        assert "만족도 태깅 실패 (비차단)" in source


# ── 6. 프롬프트 구조 ──────────────────────────────────────────


class TestSatisfactionPrompt:
    """SATISFACTION_TAG_PROMPT 구조 검증"""

    def test_prompt_has_6_tags(self):
        from modules.domain.agents.state_extractor import SATISFACTION_TAG_PROMPT

        for tag in ["성취", "성장", "전투", "이행", "일상", "좌절"]:
            assert tag in SATISFACTION_TAG_PROMPT

    def test_prompt_has_agency_options(self):
        from modules.domain.agents.state_extractor import SATISFACTION_TAG_PROMPT

        for agency in ["자력", "협력", "타인의존"]:
            assert agency in SATISFACTION_TAG_PROMPT

    def test_prompt_has_json_format(self):
        from modules.domain.agents.state_extractor import SATISFACTION_TAG_PROMPT

        assert "primary_tag" in SATISFACTION_TAG_PROMPT
        assert "satisfaction_score" in SATISFACTION_TAG_PROMPT
        assert "protagonist_agency" in SATISFACTION_TAG_PROMPT
