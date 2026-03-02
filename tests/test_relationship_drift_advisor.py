"""[LM-D] RelationshipDriftAdvisor 테스트 — 관계도 장기 표류 감지."""

import json

import pytest

from modules.core.db_manager import DBManager
from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor  # noqa: I001

# ═══════════════════════════════════════════════════════════════
# Fixture
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def db(tmp_path):
    d = DBManager(tmp_path / "test.db")
    try:
        yield d
    finally:
        d.close()


# ═══════════════════════════════════════════════════════════════
# DBHistory 테스트
# ═══════════════════════════════════════════════════════════════


class TestDBHistory:
    def test_insert_and_get_history(self, db):
        """이력 저장·조회."""
        # 최초 등록 → 이력 없음
        db.upsert_npc_relationship_edge("알파", "베타", "동맹", arc_no=1, ep_no=1)
        # 관계 변경 → 이력 생성
        db.upsert_npc_relationship_edge("알파", "베타", "원수", arc_no=1, ep_no=5)

        history = db.get_relationship_history("알파", "베타")
        assert len(history) == 1
        assert history[0]["old_relation"] == "동맹"
        assert history[0]["new_relation"] == "원수"
        assert history[0]["change_ep"] == 5

    def test_upsert_records_change(self, db):
        """UPSERT 시 변경분만 이력 기록."""
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("A", "B", "중립", arc_no=1, ep_no=3)
        db.upsert_npc_relationship_edge("A", "B", "원수", arc_no=1, ep_no=7)

        history = db.get_relationship_history("A", "B")
        assert len(history) == 2
        assert history[0]["old_relation"] == "동맹"
        assert history[0]["new_relation"] == "중립"
        assert history[1]["old_relation"] == "중립"
        assert history[1]["new_relation"] == "원수"

    def test_upsert_same_relation_no_history(self, db):
        """동일 관계 → 이력 미생성."""
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=3)

        history = db.get_relationship_history("A", "B")
        assert len(history) == 0

    def test_new_insert_no_history(self, db):
        """최초 등록 → 이력 미생성."""
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=1)

        history = db.get_relationship_history("A", "B")
        assert len(history) == 0

    def test_sorted_key_consistency(self, db):
        """정렬 키 일관성 — (B, A)로 조회해도 동일."""
        db.upsert_npc_relationship_edge("베타", "알파", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("알파", "베타", "원수", arc_no=1, ep_no=5)

        # 순서 무관하게 조회
        history1 = db.get_relationship_history("알파", "베타")
        history2 = db.get_relationship_history("베타", "알파")
        assert len(history1) == 1
        assert history1 == history2

    def test_get_pairs_with_min_changes(self, db):
        """min_changes 필터."""
        # 쌍 1: 변경 2회
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("A", "B", "중립", arc_no=1, ep_no=3)
        db.upsert_npc_relationship_edge("A", "B", "원수", arc_no=1, ep_no=7)

        # 쌍 2: 변경 1회만
        db.upsert_npc_relationship_edge("C", "D", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("C", "D", "원수", arc_no=1, ep_no=5)

        pairs_min2 = db.get_all_relationship_pairs_with_history(min_changes=2)
        assert len(pairs_min2) == 1
        assert pairs_min2[0] == ("A", "B")

        pairs_min1 = db.get_all_relationship_pairs_with_history(min_changes=1)
        assert len(pairs_min1) == 2


# ═══════════════════════════════════════════════════════════════
# BuildTimeline 테스트
# ═══════════════════════════════════════════════════════════════


class TestBuildTimeline:
    def test_empty_db(self, db):
        """빈 DB → 빈 문자열."""
        result = RelationshipDriftAdvisor.build_relationship_timeline(db)
        assert result == ""

    def test_single_pair(self, db):
        """단일 쌍 포맷팅."""
        db.upsert_npc_relationship_edge("알파", "베타", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("알파", "베타", "중립", arc_no=1, ep_no=5)
        db.upsert_npc_relationship_edge("알파", "베타", "원수", arc_no=1, ep_no=10)

        result = RelationshipDriftAdvisor.build_relationship_timeline(db)
        assert "알파" in result
        assert "베타" in result
        assert "동맹" in result
        assert "원수" in result
        assert "↔" in result

    def test_multiple_pairs(self, db):
        """다중 쌍 포맷팅."""
        # 쌍 1: 변경 2회
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("A", "B", "중립", arc_no=1, ep_no=3)
        db.upsert_npc_relationship_edge("A", "B", "원수", arc_no=1, ep_no=7)

        # 쌍 2: 변경 2회
        db.upsert_npc_relationship_edge("C", "D", "적대", arc_no=1, ep_no=2)
        db.upsert_npc_relationship_edge("C", "D", "중립", arc_no=1, ep_no=4)
        db.upsert_npc_relationship_edge("C", "D", "협력", arc_no=1, ep_no=8)

        result = RelationshipDriftAdvisor.build_relationship_timeline(db)
        assert "[A ↔ B]" in result
        assert "[C ↔ D]" in result

    def test_no_db_returns_empty(self):
        """db=None → 빈 문자열."""
        result = RelationshipDriftAdvisor.build_relationship_timeline(None)
        assert result == ""


# ═══════════════════════════════════════════════════════════════
# LlmCheck 테스트
# ═══════════════════════════════════════════════════════════════


class TestLlmCheck:
    def test_drift_detected(self):
        """표류 감지 → MAJOR."""
        response = json.dumps(
            [
                {
                    "npc_pair": "알파 ↔ 베타",
                    "old_relation": "원수",
                    "new_relation": "협력",
                    "why_drift": "설명 없이 원수에서 협력으로 변경",
                }
            ]
        )
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: response)
        result = advisor.check(
            "원고 내용...",
            ep_num=10,
            relationship_timeline="[알파 ↔ 베타]\n  1화: 원수 → 10화: 협력",
        )
        assert len(result) == 1
        assert result[0]["severity"] == "MAJOR"
        assert result[0]["check"] == "relationship_drift"
        assert result[0]["npc_pair"] == "알파 ↔ 베타"

    def test_no_drift(self):
        """표류 없음 → []."""
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check(
            "원고 내용...",
            ep_num=10,
            relationship_timeline="[알파 ↔ 베타]\n  1화: 동맹 → 10화: 동맹",
        )
        assert result == []

    def test_no_llm_returns_empty(self):
        """llm_ask=None → []."""
        advisor = RelationshipDriftAdvisor(llm_ask=None)
        result = advisor.check(
            "원고 내용...",
            ep_num=10,
            relationship_timeline="타임라인...",
        )
        assert result == []

    def test_no_timeline_returns_empty(self):
        """타임라인 없음 → []."""
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check("원고 내용...", ep_num=10, relationship_timeline="")
        assert result == []

    def test_llm_exception_graceful(self):
        """예외 → 비차단."""

        def exploding_llm(_):
            raise RuntimeError("LLM 폭발!")

        advisor = RelationshipDriftAdvisor(llm_ask=exploding_llm)
        result = advisor.check(
            "원고 내용...",
            ep_num=10,
            relationship_timeline="타임라인...",
        )
        assert result == []

    def test_json_in_code_fence(self):
        """```json 펜스 파싱."""
        response = '```json\n[{"npc_pair": "A ↔ B", "why_drift": "이유"}]\n```'
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: response)
        result = advisor.check(
            "원고 내용...",
            ep_num=10,
            relationship_timeline="타임라인...",
        )
        assert len(result) == 1
        assert result[0]["npc_pair"] == "A ↔ B"

    def test_invalid_json_graceful(self):
        """파싱 불가 → []."""
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: "이건 JSON이 아닙니다")
        result = advisor.check(
            "원고 내용...",
            ep_num=10,
            relationship_timeline="타임라인...",
        )
        assert result == []


# ═══════════════════════════════════════════════════════════════
# EdgeCases 테스트
# ═══════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_manuscript(self):
        """빈 원고 → []."""
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: "[]")
        result = advisor.check("", ep_num=10, relationship_timeline="타임라인...")
        assert result == []

    def test_max_pairs_cap_at_20(self, db):
        """21쌍 등록 → build_relationship_timeline()에서 최대 20쌍만 포맷."""
        for i in range(21):
            a, b = f"NPC_{i:02d}_A", f"NPC_{i:02d}_B"
            db.upsert_npc_relationship_edge(a, b, "동맹", arc_no=1, ep_no=1)
            db.upsert_npc_relationship_edge(a, b, "중립", arc_no=1, ep_no=3)
            db.upsert_npc_relationship_edge(a, b, "원수", arc_no=1, ep_no=7)

        result = RelationshipDriftAdvisor.build_relationship_timeline(db)
        pair_count = result.count("↔")
        assert pair_count <= 20


# ═══════════════════════════════════════════════════════════════
# Integration 테스트
# ═══════════════════════════════════════════════════════════════


class TestIntegration:
    def test_check_returns_correct_format(self):
        """반환 형식 검증."""
        response = json.dumps(
            [
                {
                    "npc_pair": "X ↔ Y",
                    "old_relation": "동맹",
                    "new_relation": "원수",
                    "why_drift": "설명 없는 역전",
                }
            ]
        )
        advisor = RelationshipDriftAdvisor(llm_ask=lambda _: response)
        result = advisor.check(
            "원고...",
            ep_num=15,
            relationship_timeline="[X ↔ Y]\n  1화: 동맹 → 15화: 원수",
        )
        assert len(result) == 1
        item = result[0]
        assert "npc_pair" in item
        assert "old_relation" in item
        assert "new_relation" in item
        assert "why_drift" in item
        assert item["severity"] == "MAJOR"
        assert item["check"] == "relationship_drift"


# ═══════════════════════════════════════════════════════════════
# Rollback 테스트
# ═══════════════════════════════════════════════════════════════


class TestRollback:
    def test_reset_after_deletes_history(self, db):
        """롤백 시 이력 삭제."""
        # ep 1~10까지 이력 생성
        db.upsert_npc_relationship_edge("A", "B", "동맹", arc_no=1, ep_no=1)
        db.upsert_npc_relationship_edge("A", "B", "중립", arc_no=1, ep_no=5)
        db.upsert_npc_relationship_edge("A", "B", "원수", arc_no=1, ep_no=10)

        history_before = db.get_relationship_history("A", "B")
        assert len(history_before) == 2

        # ep >= 8 롤백
        db.reset_after(8)

        history_after = db.get_relationship_history("A", "B")
        # change_ep=10인 이력만 삭제, change_ep=5인 이력은 유지
        assert len(history_after) == 1
        assert history_after[0]["change_ep"] == 5
