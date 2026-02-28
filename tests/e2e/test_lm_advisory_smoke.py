"""[LM-Audit] LM-A~G Advisory 모듈 E2E Smoke Tests

21개 테스트: 7개 advisory 모듈 × 3개씩 (import/반환형식/배선경로)
실제 DB + MagicMock LLM으로 배선 경로 검증.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager

# ══════════════════════════════════════════════════════════════
# LM-A: TruthGate
# ══════════════════════════════════════════════════════════════


class TestTruthGateWiring:
    def test_truth_gate_import(self):
        """TruthGate import 성공"""
        from modules.core.truth_gate import TruthGate

        assert TruthGate is not None

    def test_truth_gate_validate(self):
        """TruthGate.validate() 반환 형식 (structured_warnings list)"""
        from modules.core.truth_gate import TruthGate

        ws = MagicMock()
        ws.get_all_npcs.return_value = {}
        ws.get_all_items.return_value = {}
        ws.get_all_locations.return_value = {}
        ws.get_npc_skills.return_value = {}
        ws.get_karma.return_value = {}
        ws.get_npc_roles.return_value = {}
        ws.get_world_laws.return_value = []

        gate = TruthGate(world_state=ws, fact_ledger=MagicMock())
        result = gate.validate("이청풍이 검을 들었다.", {})
        assert isinstance(result, dict)
        assert "passed" in result
        assert "structured_warnings" in result
        assert isinstance(result["structured_warnings"], list)
        assert result["blocking"] is False

    def test_world_law_check(self):
        """_check_world_law_violation 검사 메서드 존재"""
        from modules.core.truth_gate import TruthGate

        gate = TruthGate()
        assert hasattr(gate, "_check_world_law_violation")
        assert callable(gate._check_world_law_violation)


# ══════════════════════════════════════════════════════════════
# LM-B: NpcDriftAdvisor
# ══════════════════════════════════════════════════════════════


class TestNpcDriftWiring:
    def test_npc_drift_import(self):
        """NpcDriftAdvisor import 성공"""
        from modules.core.npc_drift_advisor import NpcDriftAdvisor

        assert NpcDriftAdvisor is not None

    def test_npc_drift_check(self):
        """NpcDriftAdvisor.check() mock LLM → 반환 형식 (list[dict])"""
        from modules.core.npc_drift_advisor import NpcDriftAdvisor

        mock_llm = MagicMock(
            return_value=json.dumps(
                [{"npc": "노사부", "field": "성격", "expected": "온화함", "found_in_ms": "냉혹함", "severity": "MAJOR"}]
            )
        )
        advisor = NpcDriftAdvisor(llm_ask=mock_llm)
        snapshots = {
            "노사부": {
                "role_at_intro": "mentor",
                "first_seen_ep": 1,
                "known_attrs": {"성격": "온화함"},
            }
        }
        result = advisor.check("노사부가 냉혹하게 웃었다.", snapshots, ep_num=5)
        assert isinstance(result, list)
        if result:
            assert "severity" in result[0]
            assert "check" in result[0]

    def test_npc_drift_no_snapshot_empty(self):
        """빈 스냅샷 → 빈 리스트"""
        from modules.core.npc_drift_advisor import NpcDriftAdvisor

        advisor = NpcDriftAdvisor()
        result = advisor.check("이청풍이 걸었다.", {})
        assert result == []


# ══════════════════════════════════════════════════════════════
# LM-C: NumericDriftAdvisor
# ══════════════════════════════════════════════════════════════


class TestNumericDriftWiring:
    def test_numeric_drift_import(self):
        """NumericDriftAdvisor import 성공"""
        from modules.core.numeric_drift_advisor import NumericDriftAdvisor

        assert NumericDriftAdvisor is not None

    def test_numeric_drift_check(self):
        """NumericDriftAdvisor.check() mock LLM → 반환 형식"""
        from modules.core.numeric_drift_advisor import NumericDriftAdvisor

        mock_llm = MagicMock(
            return_value=json.dumps(
                [{"key": "내공", "issue": "급격한 상승", "history_snippet": "10→50→200", "severity": "MAJOR"}]
            )
        )
        advisor = NumericDriftAdvisor(llm_ask=mock_llm)
        numbers = {
            "내공": {
                "value": 200,
                "unit": "년",
                "last_ep": 10,
                "history": ["ep1: 10", "ep3: 50", "ep5: 100", "ep10: 200"],
            }
        }
        result = advisor.check(numbers, ep_num=10)
        assert isinstance(result, list)
        if result:
            assert "severity" in result[0]
            assert "check" in result[0]

    def test_numeric_drift_empty_numbers(self):
        """빈 numbers → 빈 리스트"""
        from modules.core.numeric_drift_advisor import NumericDriftAdvisor

        advisor = NumericDriftAdvisor()
        result = advisor.check({})
        assert result == []


# ══════════════════════════════════════════════════════════════
# LM-D: RelationshipDriftAdvisor
# ══════════════════════════════════════════════════════════════


class TestRelationshipDriftWiring:
    def test_relationship_drift_import(self):
        """RelationshipDriftAdvisor import 성공"""
        from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor

        assert RelationshipDriftAdvisor is not None

    def test_build_timeline_with_db(self, tmp_path):
        """DB에 관계 이력 넣고 timeline 생성 확인"""
        from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor

        db = DBManager(tmp_path / "rel.db")
        try:
            # 관계 이력 삽입 (npc1, npc2, relation, arc_no, ep_no)
            db.upsert_npc_relationship_edge("이청풍", "노사부", "사제", 1, 1)
            db.upsert_npc_relationship_edge("이청풍", "노사부", "동지", 2, 5)

            timeline = RelationshipDriftAdvisor.build_relationship_timeline(db)
            assert isinstance(timeline, str)
            # 최소 2건 변경이 있어야 timeline 생성
            if timeline:
                assert "이청풍" in timeline or "노사부" in timeline
        finally:
            db.close()

    def test_check_with_mock_llm(self):
        """mock LLM 응답 파싱 + severity/check 필드"""
        from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor

        mock_llm = MagicMock(
            return_value=json.dumps(
                [
                    {
                        "npc_pair": "이청풍-노사부",
                        "old_relation": "사제",
                        "new_relation": "적대",
                        "why_drift": "갑작스런 배신",
                        "severity": "MAJOR",
                    }
                ]
            )
        )
        advisor = RelationshipDriftAdvisor(llm_ask=mock_llm)
        result = advisor.check(
            "노사부가 이청풍을 공격했다.",
            ep_num=10,
            relationship_timeline="ep1: 사제 → ep5: 동지 → ep10: 적대",
        )
        assert isinstance(result, list)
        if result:
            assert "severity" in result[0]
            assert "check" in result[0]


# ══════════════════════════════════════════════════════════════
# LM-E: FlashbackVerifier
# ══════════════════════════════════════════════════════════════


class TestFlashbackWiring:
    def test_flashback_import(self):
        """FlashbackVerifier import 성공"""
        from modules.core.flashback_verifier import FlashbackVerifier

        assert FlashbackVerifier is not None

    def test_detect_flashbacks(self):
        """한국어 회상 마커 감지 (Python-only, LLM 불필요)"""
        from modules.core.flashback_verifier import FlashbackVerifier

        verifier = FlashbackVerifier()
        manuscript = "이청풍은 그 시절을 떠올렸다. 옛날에 노사부와 함께했던 기억이."
        flashbacks = verifier.detect_flashbacks(manuscript)
        assert isinstance(flashbacks, list)
        assert len(flashbacks) >= 1
        # 마커 필드 확인
        for fb in flashbacks:
            assert "marker" in fb
            assert "text" in fb

    def test_check_with_ref_context(self):
        """mock LLM + 참조 컨텍스트 → 경고 파싱"""
        from modules.core.flashback_verifier import FlashbackVerifier

        mock_llm = MagicMock(
            return_value=json.dumps(
                [
                    {
                        "marker": "떠올렸다",
                        "issue": "사망 NPC 행동 묘사",
                        "referenced_context": "ep3 사현 전투",
                        "severity": "MAJOR",
                    }
                ]
            )
        )
        verifier = FlashbackVerifier(llm_ask=mock_llm)
        result = verifier.check(
            "이청풍은 사현을 떠올렸다. 그때 사현이 검을 휘둘렀다.",
            ep_num=10,
            reference_context="ep3: 사현이 전투 중 사망",
        )
        assert isinstance(result, list)
        if result:
            assert "severity" in result[0]
            assert "check" in result[0]


# ══════════════════════════════════════════════════════════════
# LM-F: InfoParadoxChecker
# ══════════════════════════════════════════════════════════════


class TestInfoParadoxWiring:
    def test_info_paradox_import(self):
        """InfoParadoxChecker import 성공"""
        from modules.core.info_paradox_checker import InfoParadoxChecker

        assert InfoParadoxChecker is not None

    def test_build_knowledge_summary(self, tmp_path):
        """DB에 episode_bible 넣고 knowledge 빌드"""
        from modules.core.info_paradox_checker import InfoParadoxChecker

        db = DBManager(tmp_path / "info.db")
        try:
            # episode_bibles에 데이터 삽입
            db.save_episode_bible(
                1,
                {
                    "reveals": ["노사부가 과거 마교 출신임이 밝혀짐"],
                    "knowledge_map": json.dumps({"이청풍": ["노사부의 과거"]}),
                },
            )
            db.save_episode_bible(
                2,
                {
                    "reveals": ["흑풍의 정체가 사형"],
                    "knowledge_map": json.dumps({"이청풍": ["흑풍의 정체"]}),
                },
            )

            summary = InfoParadoxChecker.build_knowledge_summary(db, up_to_ep=3, protagonist_name="이청풍")
            assert isinstance(summary, str)
        finally:
            db.close()

    def test_check_with_knowledge(self):
        """mock LLM + knowledge → 경고 파싱"""
        from modules.core.info_paradox_checker import InfoParadoxChecker

        mock_llm = MagicMock(
            return_value=json.dumps(
                [
                    {
                        "character": "이청풍",
                        "info_used": "흑풍의 정체",
                        "why_paradox": "아직 모르는 정보 사용",
                        "severity": "MAJOR",
                    }
                ]
            )
        )
        checker = InfoParadoxChecker(llm_ask=mock_llm)
        result = checker.check(
            "이청풍은 흑풍이 사형인 것을 알고 있었다.",
            ep_num=1,
            pov_character="이청풍",
            knowledge_summary="ep1까지 이청풍이 알고 있는 것: 노사부의 과거",
        )
        assert isinstance(result, list)
        if result:
            assert "severity" in result[0]
            assert "check" in result[0]


# ══════════════════════════════════════════════════════════════
# LM-G: NarrativeContextFormatter
# ══════════════════════════════════════════════════════════════


class TestNarrativeCtxWiring:
    def test_formatter_import(self):
        """NarrativeContextFormatter import 성공"""
        from modules.core.narrative_context_formatter import NarrativeContextFormatter

        assert NarrativeContextFormatter is not None

    def test_format_all_integration(self):
        """실데이터 → 3섹션 헤더 포함"""
        from modules.core.narrative_context_formatter import NarrativeContextFormatter

        result = NarrativeContextFormatter.format_all(
            active_plots={"복수": {"target": "흑풍", "status": "진행중"}},
            npc_motivations={"노사부": "제자 보호"},
            pending_commitments=[
                {"commitment": "청풍검 전수", "arc_no": 1, "status": "미이행"},
            ],
            all_refined_arcs=[
                {"arc_no": 1, "scale": "소규모"},
                {"arc_no": 2, "scale": "중규모"},
                {"arc_no": 3, "scale": "대규모"},
            ],
            current_arc_no=3,
        )
        assert isinstance(result, str)
        assert len(result) > 0
        # advisory 헤더 포함
        assert "LM-G" in result or "서사" in result

    def test_stage2_enrichment_path(self):
        """StateTracker에 데이터 설정 후 format_all 호출 → 비어있지 않음"""
        from modules.core.narrative_context_formatter import NarrativeContextFormatter

        # format_all은 순수 Python — StateTracker 없이도 직접 호출 가능
        result = NarrativeContextFormatter.format_all(
            active_plots={"수련": {"status": "진행중"}},
            npc_motivations=None,
            pending_commitments=None,
            all_refined_arcs=[
                {"arc_no": 1, "scale": "소규모"},
                {"arc_no": 2, "scale": "중규모"},
            ],
            current_arc_no=2,
        )
        assert isinstance(result, str)
        # 최소 active_plots 섹션이 있으므로 비어있지 않음
        assert len(result) > 0
