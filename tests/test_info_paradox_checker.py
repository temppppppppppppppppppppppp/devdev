"""[LM-F] InfoParadoxChecker 테스트 — 1인칭 시점 정보 역설 감지."""

import json

from modules.core.info_paradox_checker import InfoParadoxChecker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeDB:
    """get_all_episode_bibles()를 제공하는 가짜 DB."""

    def __init__(self, bibles=None, world_state=None):
        self._bibles = bibles or []
        self._world_state = world_state or {}

    def get_all_episode_bibles(self):
        return self._bibles

    def get_episode_bibles_before(self, up_to_ep):
        return [b for b in self._bibles if b.get("ep_num", 0) < up_to_ep]

    def load_anchor(self, key):
        if key == "world_state":
            return self._world_state
        return None


def _make_bible(ep_num, reveals=None, knowledge_map=None):
    return {
        "ep_num": ep_num,
        "new_items": [],
        "lost_items": [],
        "new_npcs": [],
        "npc_deaths": [],
        "relationship_changes": [],
        "state_changes": {},
        "time_passed": "",
        "reveals": reveals or [],
        "causal_links": [],
        "karma_matrix": [],
        "knowledge_map": knowledge_map or {},
    }


# ===========================================================================
# BuildKnowledgeSummary 테스트
# ===========================================================================


class TestBuildKnowledgeSummary:
    """build_knowledge_summary 정적 메서드 테스트."""

    def test_empty_db(self):
        """빈 DB → 빈 문자열."""
        db = FakeDB([])
        result = InfoParadoxChecker.build_knowledge_summary(db, 5, "진우")
        assert result == ""

    def test_single_episode(self):
        """단일 에피소드의 reveals 누적."""
        db = FakeDB(
            [
                _make_bible(1, reveals=["흑풍단의 비밀 거래를 목격"]),
            ]
        )
        result = InfoParadoxChecker.build_knowledge_summary(db, 3, "진우")
        assert "흑풍단의 비밀 거래를 목격" in result
        assert "(1화)" in result
        assert "진우" in result

    def test_multiple_episodes(self):
        """다중 에피소드 누적."""
        db = FakeDB(
            [
                _make_bible(1, reveals=["비밀 통로 발견"]),
                _make_bible(2, reveals=["장로의 배신 목격"]),
                _make_bible(3, reveals=["보물 지도 입수"]),
            ]
        )
        result = InfoParadoxChecker.build_knowledge_summary(db, 4, "수현")
        assert "비밀 통로 발견" in result
        assert "장로의 배신 목격" in result
        assert "보물 지도 입수" in result

    def test_knowledge_map_processing(self):
        """witnesses와 misled 처리."""
        db = FakeDB(
            [
                _make_bible(
                    2,
                    knowledge_map={
                        "new_witnesses": ["금고 열쇠를 훔치는 장면 목격"],
                        "new_misled": ["적이 이미 죽었다고 믿음"],
                    },
                ),
            ]
        )
        result = InfoParadoxChecker.build_knowledge_summary(db, 5, "민호")
        assert "금고 열쇠를 훔치는 장면 목격" in result
        assert "적이 이미 죽었다고 믿음" in result

    def test_filters_current_ep(self):
        """up_to_ep 미만만 포함."""
        db = FakeDB(
            [
                _make_bible(1, reveals=["과거 정보"]),
                _make_bible(5, reveals=["현재 화 정보"]),
                _make_bible(6, reveals=["미래 정보"]),
            ]
        )
        result = InfoParadoxChecker.build_knowledge_summary(db, 5, "진우")
        assert "과거 정보" in result
        assert "현재 화 정보" not in result
        assert "미래 정보" not in result

    def test_no_db_returns_empty(self):
        """db=None → 빈 문자열."""
        result = InfoParadoxChecker.build_knowledge_summary(None, 5, "진우")
        assert result == ""

    def test_ep1_returns_empty(self):
        """1화 → 이전 데이터 없음."""
        db = FakeDB([_make_bible(1, reveals=["무언가"])])
        result = InfoParadoxChecker.build_knowledge_summary(db, 1, "진우")
        assert result == ""

    def test_dict_reveals(self):
        """reveals가 dict 형태일 때 처리."""
        db = FakeDB(
            [
                _make_bible(2, reveals=[{"description": "마왕의 약점 발견"}]),
            ]
        )
        result = InfoParadoxChecker.build_knowledge_summary(db, 5, "진우")
        assert "마왕의 약점 발견" in result

    def test_dict_knowledge_map_entries(self):
        """knowledge_map 항목이 dict 형태일 때 처리."""
        db = FakeDB(
            [
                _make_bible(
                    3,
                    knowledge_map={
                        "new_witnesses": [{"event": "폭발 현장 목격"}],
                        "new_misled": [{"belief": "동맹이 배신했다고 오해"}],
                    },
                ),
            ]
        )
        result = InfoParadoxChecker.build_knowledge_summary(db, 5, "수현")
        assert "폭발 현장 목격" in result
        assert "동맹이 배신했다고 오해" in result

    def test_includes_world_state_first_seen_npc_summary(self):
        db = FakeDB(
            [_make_bible(1, reveals=["은밀한 낌새"])],
            world_state={
                "alive_npcs": {
                    "노사부": {"first_seen_ep": 2},
                    "흑풍": {"first_seen_ep": 5},
                }
            },
        )

        result = InfoParadoxChecker.build_knowledge_summary(db, 5, "진우")

        assert "주요 NPC 첫 대면" in result
        assert "노사부 (ep2 첫 대면)" in result
        assert "흑풍 (ep5 첫 대면)" not in result


# ===========================================================================
# LLM 검사 테스트
# ===========================================================================


class TestLlmCheck:
    """check / _llm_check / _parse_llm_response 테스트."""

    def test_paradox_detected(self):
        """역설 감지 → MAJOR 경고."""
        response = json.dumps(
            [
                {
                    "character": "진우",
                    "info_used": "비밀 회의 내용",
                    "why_paradox": "참석하지 않은 회의의 내용을 알고 있음",
                }
            ]
        )
        checker = InfoParadoxChecker(llm_ask=lambda _: response)
        result = checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="[진우이(가) 알고 있는 정보]\n밝혀진 사실:\n  - 무언가 (1화)",
        )
        assert len(result) == 1
        assert result[0]["severity"] == "MAJOR"
        assert result[0]["check"] == "info_paradox"
        assert result[0]["info_used"] == "비밀 회의 내용"

    def test_no_paradox(self):
        """역설 없음 → 빈 리스트."""
        checker = InfoParadoxChecker(llm_ask=lambda _: "[]")
        result = checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="지식 요약",
        )
        assert result == []

    def test_no_llm_returns_empty(self):
        """llm_ask=None → 스킵."""
        checker = InfoParadoxChecker(llm_ask=None)
        result = checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="지식 요약",
        )
        assert result == []

    def test_no_knowledge_summary_returns_empty(self):
        """지식 요약 없음 → 스킵."""
        checker = InfoParadoxChecker(llm_ask=lambda _: "[]")
        result = checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="",
        )
        assert result == []

    def test_no_pov_character_returns_empty(self):
        """화자 이름 없음 → 스킵."""
        checker = InfoParadoxChecker(llm_ask=lambda _: "[]")
        result = checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="",
            knowledge_summary="지식 요약",
        )
        assert result == []

    def test_llm_exception_graceful(self):
        """LLM 예외 → 비차단."""

        def exploding_llm(_):
            raise RuntimeError("API 오류")

        checker = InfoParadoxChecker(llm_ask=exploding_llm)
        result = checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="지식 요약",
        )
        assert result == []

    def test_json_in_code_fence(self):
        """```json 펜스 파싱."""
        response = '```json\n[{"character": "진우", "info_used": "비밀", "why_paradox": "이유"}]\n```'
        result = InfoParadoxChecker._parse_llm_response(response, ep_num=5)
        assert len(result) == 1
        assert result[0]["info_used"] == "비밀"

    def test_invalid_json_graceful(self):
        """파싱 불가 → 빈 리스트."""
        result = InfoParadoxChecker._parse_llm_response("이것은 JSON이 아닙니다", ep_num=5)
        assert result == []

    def test_missing_info_used_skipped(self):
        """info_used 없는 항목은 스킵."""
        response = json.dumps(
            [
                {"character": "진우", "why_paradox": "이유만 있음"},
                {"character": "진우", "info_used": "유효한 항목", "why_paradox": "이유"},
            ]
        )
        result = InfoParadoxChecker._parse_llm_response(response, ep_num=5)
        assert len(result) == 1
        assert result[0]["info_used"] == "유효한 항목"


# ===========================================================================
# 엣지 케이스
# ===========================================================================


class TestEdgeCases:
    """엣지 케이스 테스트."""

    def test_empty_manuscript(self):
        """빈 원고 → []."""
        checker = InfoParadoxChecker(llm_ask=lambda _: "[]")
        result = checker.check(
            "",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="지식 요약",
        )
        assert result == []


# ===========================================================================
# 통합 테스트
# ===========================================================================


class TestIntegration:
    """통합 검증."""

    def test_check_returns_correct_format(self):
        """반환 형식 검증 (character, info_used, why_paradox, severity, check)."""
        response = json.dumps(
            [
                {
                    "character": "수현",
                    "info_used": "적의 비밀 기지 위치",
                    "why_paradox": "정보를 얻을 경로가 없음",
                }
            ]
        )
        checker = InfoParadoxChecker(llm_ask=lambda _: response)
        result = checker.check(
            "수현은 적의 비밀 기지가 북쪽에 있다는 것을 알고 있었다.",
            ep_num=10,
            pov_character="수현",
            knowledge_summary="[수현이(가) 알고 있는 정보]\n밝혀진 사실:\n  - 적의 존재 (3화)",
        )
        assert len(result) == 1
        item = result[0]
        assert "character" in item
        assert "info_used" in item
        assert "why_paradox" in item
        assert item["severity"] == "MAJOR"
        assert item["check"] == "info_paradox"

    def test_full_pipeline_build_then_check(self):
        """build_knowledge_summary → check 연결."""
        db = FakeDB(
            [
                _make_bible(1, reveals=["흑풍단 거래 목격"]),
                _make_bible(2, knowledge_map={"new_witnesses": ["보물 상자 발견"], "new_misled": []}),
            ]
        )
        summary = InfoParadoxChecker.build_knowledge_summary(db, 3, "진우")
        assert summary  # 빈 문자열이 아님

        checker = InfoParadoxChecker(llm_ask=lambda _: "[]")
        result = checker.check(
            "진우는 조용히 걸었다.",
            ep_num=3,
            pov_character="진우",
            knowledge_summary=summary,
        )
        assert result == []


# ===========================================================================
# [P0-1] MAX_REVEALS 확장 테스트
# ===========================================================================


class TestMaxRevealsExpansion:
    """200→500 확장 후 FIFO 트림 동작 검증."""

    def test_fifo_trim_at_500_reveals(self):
        """600 reveals → 최근 500건만 유지 (FIFO). 초기 reveals 탈락 확인."""
        bibles = [_make_bible(ep, reveals=[f"ep{ep}_A", f"ep{ep}_B"]) for ep in range(1, 301)]
        db = FakeDB(bibles)
        result = InfoParadoxChecker.build_knowledge_summary(db, 301, "진우")
        # 600 reveals 중 최근 500건만 (ep51~ep300)
        assert "ep1_A" not in result  # ep1은 FIFO 탈락
        assert "ep50_B" not in result  # ep50도 탈락
        assert "ep51_A" in result  # ep51부터 포함 (FIFO 경계)

    def test_knowledge_chars_cap_5000(self):
        """요약이 5000자 상한 + 이하 생략 여유."""
        bibles = [_make_bible(ep, reveals=[f"ep{ep}_{'가' * 50}"]) for ep in range(1, 201)]
        db = FakeDB(bibles)
        result = InfoParadoxChecker.build_knowledge_summary(db, 201, "수현")
        assert len(result) <= 5100  # 5000 + "이하 생략" 여유


# ===========================================================================
# [TF-51] 회귀자/투자 장르 예외 프롬프트 테스트
# ===========================================================================


class TestIncarnationGenreExclusion:
    """[TF-51] incarnation_type/genre_name에 따른 예외 프롬프트 주입."""

    def test_regressor_exclusion_prompt(self):
        """회귀자 → 프롬프트에 '회귀자' 전생 기억 예외 포함."""
        captured = {}

        def capture_llm(prompt):
            captured["prompt"] = prompt
            return "[]"

        checker = InfoParadoxChecker(llm_ask=capture_llm)
        checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="진우",
            knowledge_summary="지식 요약",
            incarnation_type="회귀자",
        )
        assert "회귀자" in captured["prompt"]
        assert "전생" in captured["prompt"]

    def test_investment_genre_exclusion_prompt(self):
        """투자 장르 → 프롬프트에 시장 분석 예외 포함."""
        captured = {}

        def capture_llm(prompt):
            captured["prompt"] = prompt
            return "[]"

        checker = InfoParadoxChecker(llm_ask=capture_llm)
        checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="민수",
            knowledge_summary="지식 요약",
            genre_name="투자",
        )
        assert "시장 분석" in captured["prompt"]
        assert "투자" in captured["prompt"]

    def test_default_no_extra_exclusion(self):
        """기본값 → 추가 예외 없음 (회귀자/투자 키워드 미포함)."""
        captured = {}

        def capture_llm(prompt):
            captured["prompt"] = prompt
            return "[]"

        checker = InfoParadoxChecker(llm_ask=capture_llm)
        checker.check(
            "원고 텍스트",
            ep_num=5,
            pov_character="수현",
            knowledge_summary="지식 요약",
        )
        assert "회귀자" not in captured["prompt"]
        assert "시장 분석" not in captured["prompt"]
