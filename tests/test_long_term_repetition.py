"""[P1-5] LongTermRepetitionAdvisor 장기 반복 감지 테스트."""

import json

from modules.core.long_term_repetition_advisor import (
    LongTermRepetitionAdvisor,
)


class TestExtractSceneTypes:
    """_extract_scene_types 정적 메서드 단위 테스트."""

    def test_single_keyword(self):
        """단일 키워드 추출."""
        scenes = LongTermRepetitionAdvisor._extract_scene_types("주인공이 전투를 시작했다.")
        assert "전투" in scenes

    def test_multiple_keywords_ordered(self):
        """복수 키워드 출현 순서 유지."""
        text = "갈등이 생겼고, 결국 전투가 벌어졌다. 위기를 넘긴 후 화해했다."
        scenes = LongTermRepetitionAdvisor._extract_scene_types(text)
        assert scenes == ["갈등", "전투", "위기", "화해"]

    def test_consecutive_dedup(self):
        """연속 동일 씬 유형 중복 제거."""
        text = "전투가 시작되었다. 싸움이 격렬해졌다. 교전 중 위기가 닥쳤다."
        scenes = LongTermRepetitionAdvisor._extract_scene_types(text)
        # 전투/싸움/교전 → 전투(연속 제거) → 위기
        assert scenes[0] == "전투"
        assert "위기" in scenes

    def test_empty_text(self):
        """빈 텍스트 → 빈 리스트."""
        assert LongTermRepetitionAdvisor._extract_scene_types("") == []
        assert LongTermRepetitionAdvisor._extract_scene_types(None) == []

    def test_no_keywords(self):
        """키워드 없는 텍스트 → 빈 리스트."""
        assert LongTermRepetitionAdvisor._extract_scene_types("날씨가 좋았다.") == []

    def test_max_10(self):
        """최대 10개 제한."""
        text = "전투 갈등 수련 위기 도발 구출 화해 발견 이별 재회 전투 수련 갈등"
        scenes = LongTermRepetitionAdvisor._extract_scene_types(text)
        assert len(scenes) <= 10


class TestBuildPatternSummary:
    """build_pattern_summary 정적 메서드 테스트."""

    def _make_mock_db(self, blueprints: dict):
        """Mock DB: get_blueprint(ep) → dict."""
        from unittest.mock import MagicMock

        db = MagicMock()
        db.get_blueprint.side_effect = lambda ep: blueprints.get(ep)
        return db

    def test_below_min_lookback(self):
        """MIN_LOOKBACK 미만 에피소드 → 빈 문자열."""
        db = self._make_mock_db({})
        assert LongTermRepetitionAdvisor.build_pattern_summary(db, current_ep=10) == ""

    def test_insufficient_blueprints(self):
        """블루프린트 5개 미만 → 빈 문자열."""
        bps = {i: {"content": "전투가 벌어졌다."} for i in range(1, 4)}
        db = self._make_mock_db(bps)
        assert LongTermRepetitionAdvisor.build_pattern_summary(db, current_ep=25) == ""

    def test_repeated_bigram_detected(self):
        """동일 2-gram 시퀀스 3회+ → 감지."""
        # 20화 중 10화에 "전투→위기" 패턴 반복
        bps = {}
        for i in range(1, 21):
            if i % 2 == 0:
                bps[i] = {"content": "전투가 벌어지고 위기가 닥쳤다."}
            else:
                bps[i] = {"content": "수련을 하며 깨달음을 얻었다."}
        db = self._make_mock_db(bps)
        result = LongTermRepetitionAdvisor.build_pattern_summary(db, current_ep=21)
        assert "전투→위기" in result
        assert "반복 시퀀스" in result

    def test_no_repetition(self):
        """다양한 패턴 → 빈 문자열."""
        patterns = ["전투", "수련", "갈등", "화해", "발견", "이별", "재회", "도발", "구출", "위기"]
        bps = {}
        for i in range(1, 21):
            p = patterns[i % len(patterns)]
            bps[i] = {"content": f"{p}이 있었다."}
        db = self._make_mock_db(bps)
        result = LongTermRepetitionAdvisor.build_pattern_summary(db, current_ep=21)
        # 2-gram이 3회 미만이면 빈 문자열
        # (각 패턴이 2회씩만 나오므로 bigram은 더 적음)
        assert result == ""

    def test_dominant_scene_detected(self):
        """특정 씬 유형 40%+ 편중 → 감지."""
        # 20화 중 12화가 전투 포함 (60%)
        bps = {}
        for i in range(1, 21):
            if i <= 12:
                bps[i] = {"content": "전투가 벌어지고 싸움이 격렬했다."}
            else:
                bps[i] = {"content": "수련을 하고 깨달음을 얻었다."}
        db = self._make_mock_db(bps)
        result = LongTermRepetitionAdvisor.build_pattern_summary(db, current_ep=21)
        assert "편중 씬 유형" in result
        assert "전투" in result


class TestCheck:
    """check 메서드 통합 테스트."""

    def test_no_llm_returns_empty(self):
        """llm_ask=None → 빈 리스트."""
        advisor = LongTermRepetitionAdvisor(llm_ask=None)
        result = advisor.check("전투가 벌어졌다.", ep_num=25, pattern_summary="[P1-5] 반복 감지")
        assert result == []

    def test_no_pattern_summary_returns_empty(self):
        """pattern_summary 빈 → 빈 리스트."""
        advisor = LongTermRepetitionAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check("전투가 벌어졌다.", ep_num=25, pattern_summary="")
        assert result == []

    def test_llm_returns_findings(self):
        """LLM이 반복 감지 시 결과 반환."""
        llm_response = json.dumps(
            [{"pattern": "전투→위기 반복", "issue": "20화 중 8회 동일 구조"}],
            ensure_ascii=False,
        )
        advisor = LongTermRepetitionAdvisor(llm_ask=lambda _: llm_response)
        result = advisor.check(
            "전투가 벌어지고 위기가 닥쳤다.",
            ep_num=25,
            pattern_summary="[P1-5] '전투→위기' × 8회",
        )
        assert len(result) == 1
        assert result[0]["check"] == "long_term_repetition"
        assert result[0]["severity"] == "MAJOR"
        assert "전투→위기" in result[0]["text"]

    def test_llm_returns_empty(self):
        """LLM이 반복 없다고 판단 → 빈 리스트."""
        advisor = LongTermRepetitionAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check(
            "새로운 전개가 펼쳐졌다.",
            ep_num=25,
            pattern_summary="[P1-5] 다양한 패턴",
        )
        assert result == []


class TestParseLlmResponse:
    """_parse_llm_response 정적 메서드 테스트."""

    def test_valid_json(self):
        """정상 JSON 배열 파싱."""
        response = '[{"pattern": "A", "issue": "B"}]'
        result = LongTermRepetitionAdvisor._parse_llm_response(response)
        assert len(result) == 1
        assert result[0]["pattern"] == "A"

    def test_json_fence(self):
        """```json ... ``` 펜스 처리."""
        response = '```json\n[{"pattern": "X", "issue": "Y"}]\n```'
        result = LongTermRepetitionAdvisor._parse_llm_response(response)
        assert len(result) == 1

    def test_empty_array(self):
        """빈 배열 → 빈 리스트."""
        assert LongTermRepetitionAdvisor._parse_llm_response("[]") == []

    def test_invalid_json(self):
        """잘못된 JSON → 빈 리스트."""
        assert LongTermRepetitionAdvisor._parse_llm_response("not json") == []

    def test_none_input(self):
        """None → 빈 리스트."""
        assert LongTermRepetitionAdvisor._parse_llm_response(None) == []
        assert LongTermRepetitionAdvisor._parse_llm_response("") == []
