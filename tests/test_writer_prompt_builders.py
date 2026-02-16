"""[A-1] writer_prompt_builders 단위 테스트."""

from unittest.mock import MagicMock


class TestBuildMandatoryContext:
    """build_mandatory_context 함수 테스트."""

    def test_first_episode_returns_default(self):
        from modules.core.writer_prompt_builders import build_mandatory_context

        db = MagicMock()
        result = build_mandatory_context(db, {}, 1)
        assert "[MANDATORY CONTEXT]" in result
        assert "첫 에피소드" in result

    def test_with_hud_anomaly(self):
        from modules.core.writer_prompt_builders import build_mandatory_context

        db = MagicMock()
        db.get_manuscript.side_effect = [
            {"hud_snapshot": {"internal_energy": 100, "realm": "삼류"}},
            {"hud_snapshot": {"internal_energy": 100, "realm": "삼류"}},
            {"hud_snapshot": {"internal_energy": 700, "realm": "삼류"}},
        ]
        db.load_state_log.return_value = None
        result = build_mandatory_context(db, {}, 5)
        assert "내공 급상승" in result

    def test_with_recent_events_summary(self):
        from modules.core.writer_prompt_builders import build_mandatory_context

        db = MagicMock()
        db.get_manuscript.return_value = None
        db.load_state_log.return_value = {
            "summary": "주인공이 흑풍과 대결하여 승리",
            "data": {},
        }
        result = build_mandatory_context(db, {}, 5)
        assert "흑풍" in result

    def test_with_recent_events_major_changes(self):
        from modules.core.writer_prompt_builders import build_mandatory_context

        db = MagicMock()
        db.get_manuscript.return_value = None
        db.load_state_log.return_value = {
            "summary": "",
            "data": {"major_changes": [{"event": "문파 복수 성공", "consequence": "원한 해소"}]},
        }
        result = build_mandatory_context(db, {}, 5)
        assert "문파 복수 성공" in result
        assert "원한 해소" in result

    def test_with_npc_states(self):
        from modules.core.writer_prompt_builders import build_mandatory_context

        db = MagicMock()
        db.get_manuscript.return_value = None
        db.load_state_log.return_value = None
        bible = {
            "MasterBible": {
                "AssetLibrary": {
                    "KeyNPCs": [
                        {"name": "노사부", "relationship_state": "사제", "last_appearance_ep": 3},
                    ]
                }
            }
        }
        result = build_mandatory_context(db, bible, 5)
        assert "노사부" in result
        assert "사제" in result

    def test_db_none_safe(self):
        from modules.core.writer_prompt_builders import build_mandatory_context

        result = build_mandatory_context(None, {}, 5)
        assert "[MANDATORY CONTEXT]" in result


class TestBuildAntiTrope:
    """build_anti_trope_instructions 함수 테스트."""

    def test_returns_genre_name(self):
        from modules.core.writer_prompt_builders import build_anti_trope_instructions

        result = build_anti_trope_instructions("무협")
        assert "무협" in result
        assert "ANTI-TROPE" in result

    def test_contains_rules(self):
        from modules.core.writer_prompt_builders import build_anti_trope_instructions

        result = build_anti_trope_instructions("판타지")
        assert "클리셰 금지" in result


class TestBuildJustification:
    """build_justification_guidance 함수 테스트."""

    def test_no_constraints_returns_empty(self):
        from modules.core.writer_prompt_builders import build_justification_guidance

        result = build_justification_guidance("명성 100, 내공 5000", "wuxia")
        assert result == ""

    def test_physical_constraint_detected(self):
        from modules.core.writer_prompt_builders import build_justification_guidance

        result = build_justification_guidance("부상: 중상, 내공 500", "wuxia")
        assert isinstance(result, str)
        assert "[JUSTIFICATION PATTERNS]" in result

    def test_low_status_detected_with_reputation(self):
        from modules.core.writer_prompt_builders import build_justification_guidance

        result = build_justification_guidance("reputation: 10", "wuxia")
        assert isinstance(result, str)
        assert "[JUSTIFICATION PATTERNS]" in result


class TestHelpers:
    """내부 헬퍼 함수 테스트."""

    def test_extract_numeric_value_int(self):
        from modules.core.writer_prompt_builders import _extract_numeric_value

        assert _extract_numeric_value(42) == 42

    def test_extract_numeric_value_str(self):
        from modules.core.writer_prompt_builders import _extract_numeric_value

        assert _extract_numeric_value("내공 1500") == 1500

    def test_extract_npc_last_states_empty(self):
        from modules.core.writer_prompt_builders import _extract_npc_last_states

        result = _extract_npc_last_states({}, 5)
        assert result == {}
