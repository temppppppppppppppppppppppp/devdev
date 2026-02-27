"""[LM-B] NpcDriftAdvisor 테스트 — NPC 속성 텍스트 레벨 표류 감지."""

import json

import pytest

from modules.core.npc_drift_advisor import NpcDriftAdvisor

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def sample_snapshots():
    return {
        "장백산": {
            "role_at_intro": "약초 상인",
            "first_seen_ep": 3,
            "known_attrs": {"job": {"value": "약초 상인", "changed_ep": 3}},
        },
        "이무영": {
            "role_at_intro": "호위 무사",
            "first_seen_ep": 5,
            "known_attrs": {"weapon": {"value": "창", "changed_ep": 5}},
        },
        "소연": {
            "role_at_intro": "의녀",
            "first_seen_ep": 7,
            "known_attrs": {},
        },
    }


@pytest.fixture
def sample_manuscript():
    return (
        "장백산은 약초를 들고 시장을 걸었다. "
        "이무영이 창을 들고 뒤를 따랐다. "
        "소연은 부상자를 치료하고 있었다. "
        "장백산이 다시 한번 약재를 꺼내 확인했다."
    )


# ═══════════════════════════════════════════════════════════════
# FindAppearing 테스트
# ═══════════════════════════════════════════════════════════════


class TestFindAppearing:
    def test_single_npc_found(self, sample_snapshots):
        advisor = NpcDriftAdvisor()
        ms = "장백산이 약초를 팔고 있었다."
        result = advisor._find_appearing_npcs(ms, sample_snapshots)
        assert "장백산" in result

    def test_npc_not_in_manuscript(self, sample_snapshots):
        advisor = NpcDriftAdvisor()
        ms = "아무도 없는 빈 골목이었다."
        result = advisor._find_appearing_npcs(ms, sample_snapshots)
        assert result == []

    def test_short_name_excluded(self):
        advisor = NpcDriftAdvisor()
        snaps = {"김": {"role_at_intro": "상인", "known_attrs": {}}}
        ms = "김이 말했다."
        result = advisor._find_appearing_npcs(ms, snaps)
        assert result == []

    def test_exclude_common_words(self):
        advisor = NpcDriftAdvisor()
        snaps = {"주인공": {"role_at_intro": "전사", "known_attrs": {}}}
        ms = "주인공이 전진했다."
        result = advisor._find_appearing_npcs(ms, snaps)
        assert result == []

    def test_frequency_ordering(self, sample_snapshots, sample_manuscript):
        advisor = NpcDriftAdvisor()
        result = advisor._find_appearing_npcs(sample_manuscript, sample_snapshots)
        # 장백산 2회, 이무영 1회, 소연 1회 — 장백산이 첫 번째
        assert result[0] == "장백산"


# ═══════════════════════════════════════════════════════════════
# LlmCheck 테스트
# ═══════════════════════════════════════════════════════════════


class TestLlmCheck:
    def test_drift_detected(self, sample_snapshots):
        drift_response = json.dumps(
            [
                {
                    "npc": "장백산",
                    "field": "job",
                    "expected": "약초 상인",
                    "found_in_ms": "장백산이 검을 휘둘렀다",
                }
            ],
            ensure_ascii=False,
        )

        advisor = NpcDriftAdvisor(llm_ask=lambda _: drift_response)
        ms = "장백산이 검을 휘둘렀다. 이무영이 놀란 표정으로 바라보았다."
        result = advisor.check(ms, sample_snapshots, ep_num=10)
        assert len(result) == 1
        assert result[0]["npc"] == "장백산"
        assert result[0]["severity"] == "MAJOR"
        assert result[0]["check"] == "npc_drift"

    def test_no_drift(self, sample_snapshots, sample_manuscript):
        advisor = NpcDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check(sample_manuscript, sample_snapshots, ep_num=10)
        assert result == []

    def test_no_llm_returns_empty(self, sample_snapshots, sample_manuscript):
        advisor = NpcDriftAdvisor(llm_ask=None)
        result = advisor.check(sample_manuscript, sample_snapshots, ep_num=10)
        assert result == []

    def test_llm_returns_empty_string(self, sample_snapshots, sample_manuscript):
        advisor = NpcDriftAdvisor(llm_ask=lambda _: "")
        result = advisor.check(sample_manuscript, sample_snapshots, ep_num=10)
        assert result == []

    def test_llm_exception_graceful(self, sample_snapshots, sample_manuscript):
        def _raise(_):
            raise RuntimeError("API 오류")

        advisor = NpcDriftAdvisor(llm_ask=_raise)
        result = advisor.check(sample_manuscript, sample_snapshots, ep_num=10)
        assert result == []

    def test_json_in_code_fence(self, sample_snapshots):
        fenced = '```json\n[{"npc": "장백산", "field": "job", "expected": "상인", "found_in_ms": "검사"}]\n```'
        advisor = NpcDriftAdvisor(llm_ask=lambda _: fenced)
        ms = "장백산이 검을 들고 싸웠다."
        result = advisor.check(ms, sample_snapshots, ep_num=10)
        assert len(result) == 1
        assert result[0]["npc"] == "장백산"

    def test_invalid_json_graceful(self, sample_snapshots, sample_manuscript):
        advisor = NpcDriftAdvisor(llm_ask=lambda _: "이것은 JSON이 아닙니다")
        result = advisor.check(sample_manuscript, sample_snapshots, ep_num=10)
        assert result == []


# ═══════════════════════════════════════════════════════════════
# Formatting 테스트
# ═══════════════════════════════════════════════════════════════


class TestFormatting:
    def test_format_includes_role(self, sample_snapshots):
        advisor = NpcDriftAdvisor()
        text = advisor._format_snapshot_for_prompt(sample_snapshots, ["장백산"])
        assert "약초 상인" in text
        assert "3화" in text

    def test_format_includes_known_attrs(self, sample_snapshots):
        advisor = NpcDriftAdvisor()
        text = advisor._format_snapshot_for_prompt(sample_snapshots, ["이무영"])
        assert "weapon=창" in text


# ═══════════════════════════════════════════════════════════════
# EdgeCases 테스트
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_manuscript(self, sample_snapshots):
        advisor = NpcDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check("", sample_snapshots, ep_num=10)
        assert result == []

    def test_empty_snapshots(self):
        advisor = NpcDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check("장백산이 걸었다.", {}, ep_num=10)
        assert result == []

    def test_no_role_no_attrs_skipped(self):
        snaps = {
            "홍길동": {
                "role_at_intro": "",
                "first_seen_ep": 1,
                "known_attrs": {},
            }
        }
        advisor = NpcDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check("홍길동이 걸었다.", snaps, ep_num=10)
        assert result == []
