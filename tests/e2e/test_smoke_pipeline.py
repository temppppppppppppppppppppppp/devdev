"""[Phase 6-B] L1 Smoke — 오케스트레이터 초기화 + 검증 파이프라인 해피패스

8건:
1. Stage4Context DI 22개 슬롯 조립 성공
2. DBManager 테이블 10+ 생성 확인
3. Bible 저장 → 로드 일치
4. Blueprint 저장 → 로드 일치
5. 정상 원고(~5100자) → BlockingValidator PASS
6. 4000자 미만 → BLOCKING REJECT
7. WorldStateManager 초기화 → DB → 로드
8. FactLedger 초기화 → DB → 로드
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.fact_ledger import FactLedger
from modules.core.stage4_context import Stage4Context
from modules.core.world_state import WorldStateManager
from modules.validation.blocking_validator import BlockingValidator

from .conftest import MOCK_MANUSCRIPT

# ══════════════════════════════════════════════════════════════
# L1-1: Stage4Context DI 조립
# ══════════════════════════════════════════════════════════════


class TestStage4ContextCreation:
    def test_stage4_context_creation(self, e2e_stage4_ctx):
        """Stage4Context 확장 __slots__ 조립 성공"""
        ctx = e2e_stage4_ctx
        # 필수 5종
        assert ctx.ui is not None
        assert ctx.current_project is not None
        assert ctx.agents is not None
        assert ctx.sys is not None
        assert ctx.state_tracker is not None
        # 확장 1종 (selected_genre)
        assert ctx.selected_genre is not None
        assert ctx.selected_genre["type"] == "wuxia"
        # 콜백 미주입 → None
        assert ctx.get_int_input is None
        assert ctx.flush_audit_buffer is None
        assert ctx.safe_commit is None
        # Phase 3/4 + SC-3(context_advisor) + conditional_modules + emotion_tracker [TF7-P2-06]
        assert len(Stage4Context.__slots__) == 30  # [LOG-1] +session_logger + budget meta


# ══════════════════════════════════════════════════════════════
# L1-2: DB 스키마 완성도
# ══════════════════════════════════════════════════════════════


class TestDBSchemaComplete:
    def test_db_schema_complete(self, e2e_db):
        """DBManager 테이블 10+ 생성 확인"""
        cursor = e2e_db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        expected_tables = {
            "manuscripts",
            "blueprints",
            "anchors",
            "state_logs",
            "episode_bibles",
            "npc_history",
            "karma_status",
            "causal_graph",
            "sync_status",
        }
        missing = expected_tables - tables
        assert len(missing) == 0, f"누락 테이블: {missing}"
        assert len(tables) >= 10


# ══════════════════════════════════════════════════════════════
# L1-3: Bible DB 라운드트립
# ══════════════════════════════════════════════════════════════


class TestBibleDBRoundtrip:
    def test_bible_db_roundtrip(self, e2e_db, e2e_bible):
        """Bible → anchor 저장 → 로드 일치"""
        e2e_db.save_anchor("master_bible", e2e_bible)
        loaded = e2e_db.load_anchor("master_bible")
        assert loaded is not None
        assert loaded["MasterBible"]["ProjectData"]["CoreIdentity"]["desire"] == "천하제일"
        npcs = loaded["MasterBible"]["AssetLibrary"]["KeyNPCs"]
        assert len(npcs) == 2
        assert npcs[0]["name"] == "노사부"


# ══════════════════════════════════════════════════════════════
# L1-4: Blueprint DB 라운드트립
# ══════════════════════════════════════════════════════════════


class TestBlueprintDBRoundtrip:
    def test_blueprint_db_roundtrip(self, e2e_db, e2e_blueprint):
        """Blueprint 저장 → 로드 일치"""
        e2e_db.save_blueprint(1, e2e_blueprint)
        loaded = e2e_db.get_blueprint(1)
        assert loaded is not None
        assert loaded["title"] == "운명의 시작"
        assert len(loaded["scene_breakdown"]) == 3


# ══════════════════════════════════════════════════════════════
# L1-5: Validation 해피패스
# ══════════════════════════════════════════════════════════════


class TestValidationHappyPath:
    def test_validation_happy_path(self):
        """정상 원고(~5100자) → BlockingValidator PASS"""
        bv = BlockingValidator()
        assert len(MOCK_MANUSCRIPT) > 4000, f"MOCK_MANUSCRIPT {len(MOCK_MANUSCRIPT)}자 < 4000"
        ctx = {
            "encyclopedia": {"npcs": [], "items": [], "locations": []},
            "martial_hud": {},
        }
        result = bv.validate(MOCK_MANUSCRIPT, ctx)
        assert result["tier"] == "BLOCKING"
        assert result["passed"] is True, f"Failures: {result.get('failures')}"


# ══════════════════════════════════════════════════════════════
# L1-6: 분량 미달 REJECT
# ══════════════════════════════════════════════════════════════


class TestBlockingMinLengthReject:
    def test_blocking_min_length_reject(self):
        """4000자 미만 → BLOCKING REJECT"""
        bv = BlockingValidator()
        short_manuscript = "짧은 원고." * 100  # ~600자
        ctx = {
            "encyclopedia": {"npcs": [], "items": [], "locations": []},
            "martial_hud": {},
        }
        result = bv.validate(short_manuscript, ctx)
        assert result["passed"] is False
        length_failures = [f for f in result["failures"] if f["check"] == "minimum_length"]
        assert len(length_failures) >= 1
        assert length_failures[0]["severity"] == "CRITICAL"


# ══════════════════════════════════════════════════════════════
# L1-7: WorldStateManager 초기화/저장/로드
# ══════════════════════════════════════════════════════════════


class TestWorldStateInitSaveLoad:
    def test_world_state_init_save_load(self, e2e_db):
        """WorldStateManager 초기화 → DB 저장 → 로드 일치"""
        ws = WorldStateManager(e2e_db)
        assert ws.last_updated_ep == 0

        # 주인공 상태 갱신 + NPC 사망 처리
        ws.update_protagonist_state(1, name="이청풍", location="청풍산장")
        ws.update_from_state_changes(
            1,
            {
                "npc_deaths": [{"name": "흑풍", "cause": "전투 패배"}],
            },
        )
        ws.save()

        # 새 인스턴스로 로드
        ws2 = WorldStateManager(e2e_db)
        assert ws2.last_updated_ep == 1
        state = ws2.get_state_dict()
        assert state["protagonist"]["name"] == "이청풍"
        assert "흑풍" in state["dead_npcs"]


# ══════════════════════════════════════════════════════════════
# L1-8: FactLedger 초기화/저장/로드
# ══════════════════════════════════════════════════════════════


class TestFactLedgerInitSaveLoad:
    def test_fact_ledger_init_save_load(self, e2e_db):
        """FactLedger 초기화 → DB 저장 → 로드 일치"""
        fl = FactLedger(e2e_db)
        assert fl.last_updated_ep == 0

        # state_changes 기반 갱신
        fl.update_from_state_changes(
            1,
            {
                "npc_deaths": [{"name": "흑풍", "cause": "전투 패배"}],
                "major_items": [{"name": "청풍검", "action": "획득"}],
            },
        )
        fl.save()

        # 새 인스턴스로 로드
        fl2 = FactLedger(e2e_db)
        assert fl2.last_updated_ep == 1
        assert fl2.get_character("흑풍")["status"] == "dead"
        assert fl2.get_item("청풍검")["status"] == "획득"
        assert "흑풍" in fl2.get_dead_characters()
